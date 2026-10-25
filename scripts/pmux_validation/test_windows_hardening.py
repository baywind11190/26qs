"""Windows V8 fail-closed regressions; no changes to historical evidence."""
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
import measure_v8 as V8
from test_measure_v8 import raw as v8_raw
import report as R


def summary():
    return dict(case='test1', performance_scheme=V8.SCHEME, same_run_policy=V8.POLICY,
                memory_metric='yosys_peak_working_set_bytes', execution_complete=True,
                samples=[v8_raw(), v8_raw('optimized')])


class WindowsHardeningTests(unittest.TestCase):
    @unittest.skipUnless(os.name == 'nt', 'Windows entry')
    def test_entry_missing_fixed_python_is_explicit(self):
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / 'scripts/pmux_validation'
            dest.mkdir(parents=True)
            entry = dest / 'validate_windows_v8.cmd'
            entry.write_bytes(Path(__file__).with_name('validate_windows_v8.cmd').read_bytes())
            proc = subprocess.run([os.environ['COMSPEC'], '/d', '/c', str(entry), 'plan', 'abcdef0'],
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            self.assertEqual(proc.returncode, 3)
            self.assertIn(b'Fixed Python missing', proc.stdout)

    def test_invalid_measurements_never_pass(self):
        changes = [dict(metrics_valid=False), dict(measurement_error='read failed'),
                   dict(timed_out=True), dict(rc=3), dict(output_capture_complete=False),
                   dict(time_span_ticks=math.inf), dict(yosys_peak_working_set_bytes=math.nan),
                   dict(memory_capture_complete=False), dict(memory_exit_event_observed=False),
                   dict(memory_exit_event_pid=456)]
        for change in changes:
            with self.subTest(change=change):
                s = summary()
                s['samples'][0].update(change)
                j = R.judge_case_performance(s)
                self.assertFalse(j['valid'])
                self.assertFalse(j['pass'])
                self.assertTrue(j['reasons'])
        for key in ('metrics_valid', 'measurement_error', 'timed_out', 'rc',
                    'output_capture_complete', 'time_span_ticks', 'memory_exit_event_pid'):
            with self.subTest(missing=key):
                s = summary()
                del s['samples'][0][key]
                self.assertFalse(R.judge_case_performance(s)['pass'])
        self.assertTrue(R.judge_case_performance(summary())['pass'])

    def test_missing_or_nonfinite_summary_rejected(self):
        for field in ('time_span_ticks', 'yosys_peak_working_set_bytes'):
            for value in (None, math.inf, math.nan, '1', 0, True):
                with self.subTest(field=field, value=value):
                    s = summary()
                    s['samples'][0][field] = value
                    self.assertFalse(R.judge_case_performance(s)['pass'])

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
            manifest = json.loads((root / '11_summary/manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['verification_verdict'], 'PASS')
            self.assertEqual(manifest['delivery_verdict'], 'NOT_RUN')
            self.assertEqual(manifest['project_readiness'], 'NOT_READY')
            self.assertEqual(manifest['performance_scheme'], V8.SCHEME)

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
            for field in ('target_commit', 'source_sha256'):
                self.assertNotEqual(R.judge_delivery(root, dict(ctx, **{field: 'old'}))['delivery_verdict'], 'PASS')
                missing = dict(ctx)
                missing.pop(field)
                self.assertNotEqual(R.judge_delivery(root, missing)['delivery_verdict'], 'PASS')
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
