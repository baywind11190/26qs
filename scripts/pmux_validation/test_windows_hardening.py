"""Windows p6 fail-closed regressions; no changes to historical evidence."""
import copy
import json
import math
from pathlib import Path
import sys
import tempfile
import os
import subprocess
import unittest

sys.path.insert(0, str(Path(__file__).parent / 'runner'))
import builtin_common as B
import measure_format as M
import report as R


def summary():
    runs = [dict(side=s, rc=0, timed_out=False, stat_exists=True,
                 cpu_total_s=1.0, yosys_peak_working_set_bytes=10000,
                 memory_metric='yosys_peak_working_set_bytes',
                 metrics_valid=True, measurement_error=None)
            for s in ('baseline', 'optimized')]
    return dict(case='test1', memory_metric='yosys_peak_working_set_bytes', runs=runs,
                baseline_cpu_total_median=1.0, optimized_cpu_total_median=1.0,
                baseline_yosys_peak_working_set_bytes_median=10000,
                optimized_yosys_peak_working_set_bytes_median=10000)


class WindowsHardeningTests(unittest.TestCase):
    def test_separate_runs_choose_only_plain_cpu(self):
        self.assertTrue(hasattr(M, 'merge_cpu_memory_runs'))
        if not hasattr(M, 'merge_cpu_memory_runs'):
            return
        cpu = dict(rc=0, timed_out=False, metrics_valid=True, measurement_error=None,
                   cpu_user_s=0.8, cpu_system_s=0.2, cpu_total_s=1.0, wall_s=1.1,
                   root_debugged=False)
        memory = dict(cpu, cpu_total_s=99, root_debugged=True,
                      yosys_peak_working_set_bytes=10000, memory_capture_complete=True)
        r = M.merge_cpu_memory_runs(cpu, memory)
        self.assertEqual(r['cpu_total_s'], 1.0)
        self.assertEqual(r['memory_run']['cpu_total_s'], 99)
        self.assertTrue(r['cpu_measurement_uninstrumented'])
        self.assertEqual(r['yosys_peak_working_set_bytes'], 10000)
        cpu['rc'] = 3
        self.assertNotEqual(M.merge_cpu_memory_runs(cpu, memory)['rc'], 0)

    def test_new_scheme_requires_complete_exit_capture(self):
        s = summary()
        s['performance_scheme'] = 'pmux-perf-15p-windows-separate-cpu-exitpeak-v3'
        self.assertFalse(R.judge_case_performance(s, pairs=1)['pass'])

    def test_new_scheme_complete_passes_and_mismatched_event_rejected(self):
        s = summary()
        s['performance_scheme'] = M.EXIT_PEAK_SCHEME
        for row in s['runs']:
            row.update(performance_scheme=M.EXIT_PEAK_SCHEME, memory_capture_complete=True,
                       memory_exit_event_observed=True, cpu_measurement_uninstrumented=True,
                       subruns_stat_match=True, memory_method_version='windows-root-exit-event-v1',
                       main_pid=123, memory_exit_event_pid=123,
                       cpu_run=dict(root_debugged=False, metrics_valid=True, rc=0, stat_exists=True),
                       memory_run=dict(root_debugged=True, metrics_valid=True, rc=0, stat_exists=True,
                                       memory_capture_complete=True))
        self.assertTrue(R.judge_case_performance(s, pairs=1)['pass'])
        for field, invalid in [('memory_capture_complete', False), ('memory_exit_event_pid', 456),
                               ('cpu_measurement_uninstrumented', False), ('subruns_stat_match', False)]:
            changed = copy.deepcopy(s)
            changed['runs'][0][field] = invalid
            self.assertFalse(R.judge_case_performance(changed, pairs=1)['pass'])
    @unittest.skipUnless(os.name == 'nt', 'Windows entry')
    def test_entry_missing_fixed_python_is_explicit(self):
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / 'scripts/pmux_validation'
            dest.mkdir(parents=True)
            entry = dest / 'validate_windows.cmd'
            entry.write_bytes(Path(__file__).with_name('validate_windows.cmd').read_bytes())
            proc = subprocess.run([os.environ['COMSPEC'], '/d', '/c', str(entry), 'plan', 'abcdef0'],
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            self.assertEqual(proc.returncode, 3)
            self.assertIn(b'Fixed Python missing', proc.stdout)

    def test_invalid_measurements_never_pass_or_aggregate(self):
        changes = [dict(metrics_valid=False), dict(measurement_error='read failed'),
                   dict(timed_out=True), dict(rc=3), dict(stat_exists=False),
                   dict(cpu_total_s=math.inf), dict(yosys_peak_working_set_bytes=math.nan)]
        for change in changes:
            with self.subTest(change=change):
                s = summary()
                s['runs'][0].update(change)
                j = R.judge_case_performance(s, pairs=1)
                self.assertFalse(j['pass'])
                self.assertTrue(j['reasons'])
                self.assertEqual(M.collect_metric_values(s['runs'], 'baseline', 'cpu_total_s'), [])
        for key in ('metrics_valid', 'measurement_error', 'timed_out', 'rc', 'stat_exists', 'cpu_total_s'):
            with self.subTest(missing=key):
                s = summary()
                del s['runs'][0][key]
                self.assertFalse(R.judge_case_performance(s, pairs=1)['pass'])
        self.assertTrue(R.judge_case_performance(summary(), pairs=1)['pass'])

    def test_missing_or_nonfinite_summary_rejected(self):
        for value in (None, math.inf, math.nan, '1', 0, True):
            s = summary()
            s['baseline_cpu_total_median'] = value
            self.assertFalse(R.judge_case_performance(s, pairs=1)['pass'])

    def test_io_cells_compared_per_type(self):
        base = dict(logic_units=100, dff_count=1, io_ports=2, io_bits=2,
                    io_cell_types={}, other_cell_types={})
        for cells in ({'cycloneiv_io': 1}, {'cycloneiv_io_ibuf': 2}):
            opt = dict(base, io_cell_types=cells)
            self.assertFalse(B.compare_resource_counts(base, opt)['resource_checks_ok'])
        self.assertTrue(B.compare_resource_counts(base, base)['resource_checks_ok'])
        b = dict(base, io_cell_types={'cycloneiv_io': 2})
        self.assertTrue(B.compare_resource_counts(b, dict(b, io_cell_types={'cycloneiv_io': 1}))['io_nonincrease'])

    def test_area_thresholds_use_raw_average(self):
        self.assertTrue(hasattr(R, 'judge_area'))
        if not hasattr(R, 'judge_area'):
            return
        for mean, met, band in [(0, False, False), (-1, False, False),
                                (9.999999, False, False), (10, True, False),
                                (19.999999, True, False), (20, True, True),
                                (23.9706196581, True, True), (math.nan, False, False)]:
            with self.subTest(mean=mean):
                j = R.judge_area(mean)
                self.assertEqual(j['area_requirement_met'], met)
                self.assertEqual(j['area_20pct_band_met'], band)

    def test_report_four_cases_pass_delivery_missing_not_ready(self):
        from test_validation import BuiltinModeTests
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            BuiltinModeTests()._write_builtin_round(root, include_chains=True)
            R.build_builtin_report(root)
            manifest = json.loads((root / '11_汇总与证据_summary/manifest.json').read_text())
            self.assertEqual(manifest['verification_verdict'], 'PASS')
            self.assertEqual(manifest['delivery_verdict'], 'NOT_RUN')
            self.assertEqual(manifest['project_readiness'], 'NOT_READY')
            self.assertIn('四例', manifest['overall_verdict_scope'])

    def test_delivery_requires_current_content_identity(self):
        self.assertTrue(hasattr(R, 'judge_delivery'))
        if not hasattr(R, 'judge_delivery'):
            return
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact = root / 'package.zip'
            artifact.write_bytes(b'package')
            import hashlib
            proof = root / 'package-check.json'
            proof.write_text(json.dumps(dict(package_sha256=hashlib.sha256(b'package').hexdigest(),
                                             c55='PASS', eqy_portable='PASS')))
            evidence = dict(schema=1, target_commit='commit', source_sha256='source',
                            package_path=str(artifact), package_sha256=hashlib.sha256(b'package').hexdigest(),
                            checks={'c55': {'state': 'PASS'}, 'eqy_portable': {'state': 'PASS'}})
            for item in evidence['checks'].values():
                item.update(evidence_path=str(proof), evidence_sha256=hashlib.sha256(proof.read_bytes()).hexdigest())
            ctx = dict(target_commit='commit', source_sha256='source')
            (root / 'delivery_evidence.json').write_text(json.dumps(evidence))
            self.assertEqual(R.judge_delivery(root, ctx)['delivery_verdict'], 'PASS')
            original = proof.read_bytes()
            proof.write_bytes(b'changed')
            self.assertNotEqual(R.judge_delivery(root, ctx)['delivery_verdict'], 'PASS')
            proof.write_bytes(original)
            for state in ('PAUSED', 'NOT_RUN', 'FAIL'):
                evidence['checks']['eqy_portable']['state'] = state
                (root / 'delivery_evidence.json').write_text(json.dumps(evidence))
                self.assertNotEqual(R.judge_delivery(root, ctx)['delivery_verdict'], 'PASS')
            evidence['checks']['eqy_portable']['state'] = 'PASS'
            (root / 'delivery_evidence.json').write_text(json.dumps(evidence))
            artifact.write_bytes(b'changed')
            self.assertNotEqual(R.judge_delivery(root, ctx)['delivery_verdict'], 'PASS')
            artifact.unlink()
            self.assertNotEqual(R.judge_delivery(root, ctx)['delivery_verdict'], 'PASS')


if __name__ == '__main__':
    unittest.main()
