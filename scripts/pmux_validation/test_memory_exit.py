"""Real Windows lifetime tests for peak capture, including hostile exits."""
import ctypes
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent / 'runner'))
import win_measure as W


@unittest.skipUnless(os.name == 'nt', 'Windows lifetime measurement')
class ExitPeakTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        repo = Path(__file__).resolve().parents[2]
        compiler = repo / '.tools/msys64/mingw64/bin/gcc.exe'
        build_env = dict(os.environ, PATH=str(compiler.parent) + os.pathsep + os.environ.get('PATH', ''))
        cls.exe = cls.root / 'peak.exe'
        subprocess.run([str(compiler), '-O2', '-o', str(cls.exe),
                        str(Path(__file__).parent / 'runner/memory_exit_probe.c'), '-lpsapi'], check=True, env=build_env)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def measure(self, mode, **kw):
        folder = self.root / (mode + '-' + str(time.perf_counter_ns()))
        folder.mkdir()
        r = W.run_measured([str(self.exe), mode], cwd=folder, log_path=folder / 'run.log', **kw)
        text = (folder / 'run.log').read_text(errors='replace')
        (folder / 'result.json').write_text(json.dumps(r, indent=2))
        return r, text

    def test_burst_free_and_immediate_exit_has_complete_peak(self):
        r, text = self.measure('burst')
        self.assertEqual(r['rc'], 0)
        self.assertGreaterEqual(r['yosys_peak_working_set_bytes'], 96 * 1024 * 1024)
        self.assertTrue(r.get('memory_capture_complete'))
        reference = int(re.search(r'SELF_PEAK=(\d+)', text)[1])
        self.assertLessEqual(abs(r['yosys_peak_working_set_bytes'] - reference), 256 * 1024)

    def test_delayed_reader_does_not_lose_peak(self):
        original = W._process_peak_working_set
        def delayed(*args):
            time.sleep(0.1)
            return original(*args)
        with patch.object(W, '_process_peak_working_set', side_effect=delayed):
            r, text = self.measure('burst')
        self.assertTrue(r.get('memory_capture_complete'))
        self.assertGreaterEqual(r['yosys_peak_working_set_bytes'], 96 * 1024 * 1024)

    def test_child_memory_is_excluded_and_child_not_debugged(self):
        r, text = self.measure('parent')
        self.assertEqual(r['rc'], 0)
        self.assertGreater(r['cpu_total_s'], 0.1)
        self.assertLess(r['yosys_peak_working_set_bytes'], 40 * 1024 * 1024)
        self.assertIn('CHILD_DEBUGGED=0', text)
        self.assertTrue(r.get('memory_capture_complete'))

    def test_abnormal_last_thread_and_crash_retain_state(self):
        for mode, success in [('thread', True), ('terminate', False), ('crash', False), ('breakpoint', False)]:
            with self.subTest(mode=mode):
                r, text = self.measure(mode)
                self.assertEqual(r['rc'] == 0, success)
                self.assertTrue(r.get('memory_capture_complete'))
                self.assertGreaterEqual(r['yosys_peak_working_set_bytes'], 96 * 1024 * 1024)

    def test_timeout_releases_pending_exit_event(self):
        start = time.perf_counter()
        r, _ = self.measure('timeout', timeout_s=0.3)
        self.assertEqual(r['rc'], 124)
        self.assertTrue(r['timed_out'])
        self.assertLess(time.perf_counter() - start, 3)
        self.assertTrue(r.get('memory_capture_complete'))

    def test_failed_final_read_never_claims_complete(self):
        with patch.object(W, '_process_peak_working_set', side_effect=OSError('injected read failure')):
            r, _ = self.measure('burst')
        self.assertFalse(r.get('memory_capture_complete'))
        self.assertFalse(r['metrics_valid'])
        self.assertIn('injected read failure', r['measurement_error'])

    def test_empty_process_and_handle_cleanup(self):
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.GetCurrentProcess.restype = ctypes.c_void_p
        kernel.GetProcessHandleCount.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        def handles():
            n = ctypes.c_ulong()
            self.assertTrue(kernel.GetProcessHandleCount(kernel.GetCurrentProcess(), ctypes.byref(n)))
            return n.value
        before = handles()
        for _ in range(12):
            r, _ = self.measure('empty')
            self.assertEqual(r['rc'], 0)
            self.assertTrue(r['memory_capture_complete'])
        self.assertLessEqual(handles(), before + 2)

    def test_event_api_failure_releases_debugged_process(self):
        kernel, psapi = W._api()
        with patch.object(kernel, 'WaitForDebugEvent', side_effect=OSError('injected event failure')):
            with patch.object(W, '_api', return_value=(kernel, psapi)):
                start = time.perf_counter()
                r, _ = self.measure('burst')
        self.assertFalse(r['metrics_valid'])
        self.assertIn('injected event failure', r['measurement_error'])
        self.assertLess(time.perf_counter() - start, 3)

    def test_cpu_measurement_runs_without_debugger_and_includes_child(self):
        self.assertTrue(hasattr(W, 'run_cpu_measured'))
        if not hasattr(W, 'run_cpu_measured'):
            return
        folder = self.root / ('cpu-' + str(time.perf_counter_ns()))
        folder.mkdir()
        r = W.run_cpu_measured([str(self.exe), 'parent'], cwd=folder, log_path=folder / 'run.log')
        self.assertEqual(r['rc'], 0)
        self.assertGreater(r['cpu_total_s'], 0.1)
        self.assertIn('ROOT_DEBUGGED=0', (folder / 'run.log').read_text())


if __name__ == '__main__':
    unittest.main()
