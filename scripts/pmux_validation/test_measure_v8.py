"""V8: exactly 2N joint samples and immutable, shared synthesis evidence."""
import copy
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent / 'runner'))
try:
    import measure_v8 as v8
except ImportError:
    v8 = None


def fixture_cases():
    return json.loads((Path(__file__).parent / 'suite-official/manifest.json').read_text(encoding='utf-8'))['cases']


def raw(side='baseline', ticks=10_000_000, peak=100_000_000):
    return dict(side=side, sample_id='sample-' + side, case='test1',
                performance_scheme='pmux-perf-single-powershell-same-run-exitpeak-v8',
                wall_time_method='powershell-measure-command-same-run-wall-v2',
                time_span_ticks=ticks, total_milliseconds=ticks / 10_000,
                yosys_peak_working_set_bytes=peak, main_pid=42, yosys_pid=42,
                time_pid=42, memory_exit_event_pid=42, memory_capture_complete=True,
                memory_exit_event_observed=True, memory_root_process_only=True,
                memory_method_version='windows-root-exit-event-v1', memory_sample_count=1,
                metrics_valid=True, root_debugged=True, rc=0, timed_out=False,
                measurement_error=None, process_exit_observed=True,
                output_capture_complete=True, powershell_major=5, powershell_minor=1)


class V8Tests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(v8, 'V8 joint measurement is not implemented')

    def test_2n_unique_case_side_pairs_in_manifest_order(self):
        rows = list(v8.schedule({'official_cases': fixture_cases()}))
        self.assertEqual([(r['case'], r['side']) for r in rows],
                         [(c['id'], s) for c in fixture_cases()
                          for s in ('baseline', 'optimized')])
        self.assertEqual(len({(r['case'], r['side']) for r in rows}), 18)

    def test_compare_is_independent_of_removed_v7_module(self):
        spec = importlib.util.spec_from_file_location('isolated_v8', Path(v8.__file__))
        independent = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'measure_v7': None}):
            try:
                spec.loader.exec_module(independent)
            except ImportError as exc:
                self.fail('V8 comparison still requires the removed V7 module: ' + str(exc))
        self.assertEqual(independent.compare(100, 105)['wall_5pct'], 'PASS')

    def test_compare_rejects_invalid_ticks_and_preserves_integer_boundaries(self):
        invalid = {'wall_overhead_pct': None, 'wall_5pct': 'INVALID',
                   'wall_15pct': 'INVALID', 'wall_verdict': 'INVALID',
                   'official_midband_score': 'NOT_DETERMINED'}
        for base, opt in ((0, 1), (1, 0), (-1, 1), (1, -1), (True, 1),
                          (1, False), (1.0, 1), (1, '1'), (None, 1)):
            with self.subTest(base=base, opt=opt):
                self.assertEqual(v8.compare(base, opt), invalid)
        for opt, five, fifteen, score in (
                (105, 'PASS', 'PASS', 'UP_TO_5_THRESHOLD'),
                (106, 'FAIL', 'PASS', 'NOT_DETERMINED'),
                (115, 'FAIL', 'PASS', 'NOT_DETERMINED'),
                (116, 'FAIL', 'FAIL', 'ABOVE_15_THRESHOLD')):
            result = v8.compare(100, opt)
            self.assertEqual((result['wall_5pct'], result['wall_15pct'],
                              result['wall_verdict'], result['official_midband_score']),
                             (five, fifteen, five, score))

    def test_default_preflight_reads_v8_configuration(self):
        import validate
        class StopBeforeToolChecks(Exception):
            pass
        seen = []
        def capture(cfg):
            seen.append(cfg)
            raise StopBeforeToolChecks
        with patch.object(validate, 'validate_performance_policy', side_effect=capture):
            with self.assertRaises(StopBeforeToolChecks):
                validate.preflight('not-a-real-commit')
        import measure_v9
        self.assertEqual(seen[0]['performance_scheme'], measure_v9.SCHEME)
        self.assertEqual(seen[0]['same_run_policy'], measure_v9.POLICY)

    def test_policy_rejects_retired_schemes_and_nonwindows_configuration(self):
        import validate
        import measure_v9
        cfg = dict(platform='win32-msys2-mingw64', performance_scheme=measure_v9.SCHEME,
                   same_run_policy=measure_v9.POLICY)
        validate.validate_performance_policy(cfg)
        for scheme in (None, 'pmux-perf-15p-mainrss-v2', 'pmux-perf-5p-mainrss-v1',
                       'pmux-perf-15p-windows-separate-cpu-exitpeak-v3',
                       'pmux-perf-single-windows-internalcpu-exitpeak-v6',
                       'pmux-perf-single-powershell-wall-exitpeak-v7'):
            with self.subTest(scheme=scheme), self.assertRaises(ValueError):
                validate.validate_performance_policy(dict(cfg, performance_scheme=scheme))
        with self.assertRaises(ValueError):
            validate.validate_performance_policy(dict(cfg, platform='linux'))
        with self.assertRaises(ValueError):
            validate.validate_performance_policy(dict(cfg, same_run_policy={}))

    def test_cli_rejects_plugin_before_preflight(self):
        import prepare_builtin
        import validate
        calls = []
        def preflight(*args):
            calls.append(args)
            return dict(performance_scheme=v8.SCHEME, source_sha256='source'), b'algorithm'
        with patch.object(sys, 'argv', ['validate.py', 'plan', 'commit', '--mode', 'plugin']), \
             patch.object(validate, 'preflight', side_effect=preflight), \
             patch.object(prepare_builtin, 'plan_builtin', return_value={}), \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            try:
                rc = validate.main()
            except SystemExit as exc:
                rc = exc.code
        self.assertEqual(rc, 2)
        self.assertEqual(calls, [])

    def test_joint_counter_identity_and_positive_peak_are_required(self):
        self.assertEqual(v8.sample_errors(raw()), [])
        for field, value in [('time_pid', 43), ('memory_exit_event_pid', 43),
                             ('yosys_peak_working_set_bytes', 0),
                             ('memory_capture_complete', False),
                             ('memory_exit_event_observed', False),
                             ('memory_root_process_only', False),
                             ('measurement_error', 'ContinueDebugEvent failed')]:
            with self.subTest(field=field):
                row = raw(); row[field] = value
                self.assertTrue(v8.sample_errors(row))

    def test_elapsed_units_and_powershell_version_are_checked(self):
        for field, value in [('time_span_ticks', 0), ('total_milliseconds', 3),
                             ('powershell_major', 7), ('output_capture_complete', False)]:
            row = raw(); row[field] = value
            self.assertTrue(v8.sample_errors(row))

    def summary(self, ticks=10_500_000, peak=105_000_000):
        return dict(case='test1', performance_scheme=v8.SCHEME,
                    same_run_policy=v8.POLICY, execution_complete=True,
                    memory_metric='yosys_peak_working_set_bytes',
                    samples=[raw(), raw('optimized', ticks, peak)])

    def test_exact_five_percent_boundary(self):
        result = v8.evaluate_summary(self.summary())
        self.assertTrue(result['valid'])
        self.assertTrue(result['pass'])
        self.assertEqual(result['wall_5pct'], 'PASS')
        self.assertTrue(result['mem_ok'])
        result = v8.evaluate_summary(self.summary(ticks=10_500_001))
        self.assertFalse(result['pass'])

    def test_shared_report_dispatch_uses_joint_evaluation(self):
        import report
        self.assertTrue(report.judge_case_performance(self.summary())['pass'])

    def test_either_metric_over_fifteen_is_reported(self):
        result = v8.evaluate_summary(self.summary(ticks=10_000_000, peak=115_000_001))
        self.assertTrue(result['any_over_15pct'])
        self.assertEqual(result['official_midband_score'], 'ABOVE_15_THRESHOLD')
        self.assertFalse(result['pass'])
        self.assertFalse(v8.evaluate_summary(self.summary(ticks=11_500_000,
                                                        peak=115_000_000))['any_over_15pct'])

    def test_missing_duplicate_or_incomplete_pair_is_invalid(self):
        for samples in ([raw()], [raw(), raw()], [raw(), raw('optimized'), raw('optimized')]):
            summary = self.summary(); summary['samples'] = samples
            self.assertFalse(v8.evaluate_summary(summary)['valid'])
        summary = self.summary(); summary['execution_complete'] = False
        self.assertFalse(v8.evaluate_summary(summary)['valid'])

    def invoke_fake(self, root, fail_at=None):
        rtl = root / 'input.v'; rtl.write_text('module test1; endmodule')
        calls = []
        def execute(command, *, cwd, **kwargs):
            calls.append((command, Path(cwd)))
            row = raw(ticks=10_000_000 + len(calls))
            row.update(powershell_path=sys.executable, powershell_sha256=v8.sha(sys.executable))
            if fail_at == len(calls):
                row['memory_capture_complete'] = False
            for name in ('post_abc.il', 'mapped.il'):
                (Path(cwd) / name).write_text('module \\test1\nend\n')
            for name in ('post_abc_stat.json', 'stat.json'):
                (Path(cwd) / name).write_text('{}')
            Path(kwargs['log_path']).write_text('complete output')
            return row
        cfg = dict(mode='builtin', performance_scheme=v8.SCHEME,
                   same_run_policy=v8.POLICY, official_cases=fixture_cases(), wall_time_tool={'path': sys.executable})
        flows = {c['id']: f'read_verilog -sv {rtl.as_posix()}\n' for c in fixture_cases()}
        rc = v8.run(cfg, root, {'baseline': Path(sys.executable),
                              'optimized': Path(sys.executable)}, flows, execute=execute)
        return rc, calls

    def test_driver_runs_only_2n_and_stores_shared_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            rc, calls = self.invoke_fake(root)
            self.assertEqual(rc, 0)
            self.assertEqual(len(calls), 18)
            samples = list(root.glob('05_*/round01/*/*/measure_result.json'))
            self.assertEqual(len(samples), 18)
            ids = {json.loads(p.read_text(encoding='utf-8'))['sample_id'] for p in samples}
            self.assertEqual(len(ids), 18)
            ledger = json.loads((root / '09_performance/round01/synthesis_ledger.json').read_text(encoding='utf-8'))
            self.assertEqual(ledger['attempted_runs'], 18)
            self.assertEqual(ledger['started_runs'], 18)
            self.assertTrue(ledger['execution_complete'])
            self.assertTrue(all(str(p.relative_to(root)).isascii() for p in root.rglob('*')))
            self.assertFalse(any(p.name.startswith('_eval_') for p in root.rglob('*')))

    def test_failure_preserves_raw_and_stops_without_replacement(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            rc, calls = self.invoke_fake(root, fail_at=2)
            self.assertNotEqual(rc, 0)
            self.assertEqual(len(calls), 2)
            result = json.loads((root / '05_public/round01/test1/optimized/measure_result.json').read_text(encoding='utf-8'))
            self.assertFalse(result['memory_capture_complete'])
            summaries = json.loads((root / '09_performance/round01/performance_summary.json').read_text(encoding='utf-8'))
            self.assertTrue(all(not s['execution_complete'] for s in summaries))
            self.assertFalse(any(p.name.startswith('_eval_') for p in root.rglob('*')))

    def test_saved_artifact_change_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); self.invoke_fake(root)
            folder = root / '05_public/round01/test1/baseline'
            row = json.loads((folder / 'measure_result.json').read_text(encoding='utf-8'))
            self.assertEqual(v8.sample_errors(row, require_outputs=True), [])
            (folder / 'post_abc.il').write_text('changed')
            self.assertTrue(v8.sample_errors(row, require_outputs=True))

    def test_v8_stage_order_and_policy_location_are_explicit(self):
        import validate
        cfg = {'performance_scheme': validate.SAME_RUN_SCHEME}
        stages = validate.builtin_stage_plan(cfg)
        names = [s[0] for s in stages]
        self.assertEqual(names, ['formal_selfcheck', 'measurement_selfcheck',
                                 'performance', 'flowcheck', 'public', 'chains'])
        self.assertEqual(validate.policy_identity()['path'],
                         str(Path(validate.__file__).with_name('POLICY.md').resolve()))

    def test_report_keeps_raw_measurements_but_never_passes_without_proofs(self):
        try:
            import report_v8
        except ImportError:
            report_v8 = None
        self.assertIsNotNone(report_v8, 'V8 report is not implemented')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); self.invoke_fake(root)
            (root / 'validation_context.json').write_text(json.dumps({
                'official_cases': fixture_cases(), 'performance_scheme': v8.SCHEME, 'same_run_policy': v8.POLICY,
                'suite_verified': True, 'builtin': {'integration_id': 'pmux-opt-inline-p3-v1'}}), encoding='utf-8')
            result = report_v8.build_report(root)
            self.assertEqual(result, 'NEEDS_REVIEW')
            manifest = json.loads((root / '11_summary/manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['formal_synthesis_attempted_runs'], 18)
            self.assertEqual(manifest['category_status']['formal'], 'NOT_RUN')
            self.assertNotEqual(manifest['verification_verdict'], 'PASS')
            self.assertTrue(all(p['valid'] for p in manifest['performance']))
            self.assertFalse(manifest['official_acceptance'] == 'PASS')

    def test_v8_snapshots_include_report_module_and_entrypoint(self):
        import validate
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            validate.snapshot_entrypoints(folder, {'performance_scheme': validate.SAME_RUN_SCHEME})
            for name in ('validate.py', 'report.py', 'report_v9.py', 'validate_windows_v9.cmd'):
                self.assertEqual((folder / (name + '.snapshot')).read_bytes(),
                                 (Path(validate.__file__).parent / name).read_bytes())
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            validate.snapshot_entrypoints(folder, {'performance_scheme': 'legacy'})
            self.assertFalse((folder / 'report_v8.py.snapshot').exists())

    def test_v8_tool_smoke_does_not_use_a_public_case(self):
        import prepare_builtin
        self.assertTrue(hasattr(prepare_builtin, '_smoke_input'),
                        'V8 needs a dedicated smoke fixture')
        with tempfile.TemporaryDirectory() as temp:
            rtl, top = prepare_builtin._smoke_input(Path(temp), {'performance_scheme': v8.SCHEME})
            self.assertEqual(top, 'v8_tool_smoke')
            self.assertNotIn('competition_case', str(rtl))
            self.assertTrue(Path(rtl).is_file())

    @unittest.skipUnless(os.name == 'nt', 'Windows PowerShell integration')
    def test_real_wrapper_in_unicode_directory_preserves_full_record(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp) / '同次探针'; folder.mkdir()
            ps=Path(os.environ['SystemRoot']) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
            row=v8.run_combined_measured([sys.executable, '-c', "print('late-output-complete',flush=True)"],
                cwd=folder, log_path=folder/'probe.log', timeout_s=15,
                powershell_path=ps, env=os.environ.copy())
            self.assertEqual(v8.sample_errors(row), [])
            self.assertEqual(row['powershell_sha256'],v8.sha(ps))
            self.assertIn('late-output-complete',(folder/'probe.log').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
