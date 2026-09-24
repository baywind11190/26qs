"""Evidence classification and reporting regression tests (no EDA execution)."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parent / 'runner'))
from formal_status import summarize_eqy, check_mapped_model
from report import build_report


class EvidenceTests(unittest.TestCase):
    def test_status_requires_successful_completion(self):
        with tempfile.TemporaryDirectory() as t:
            log = Path(t) / 'verify.log'
            for text, rc, expected in [('', 0, 'INCOMPLETE'),
                ('Successfully proved equivalence of partition y',124,'TIMEOUT'),
                ('DONE (PASS, rc=0)',0,'PASS'),
                ('DONE (PASS, rc=0)',1,'TOOL_OR_CONFIG_ERROR'),
                ('ERROR: unknown command',2,'TOOL_OR_CONFIG_ERROR'),
                ('Failed to prove equivalence of partition y\nDONE (FAIL, rc=2)',2,'UNPROVEN'),
                ('partitions not equivalent\nFailed to prove equivalence of partition y\nDONE (FAIL, rc=2)',2,'COUNTEREXAMPLE_REQUIRES_REVIEW')]:
                log.write_text(text)
                log.with_suffix('.execution.json').write_text(json.dumps({'rc':rc}))
                self.assertEqual(summarize_eqy(log, Path(t)/'work')['state'], expected)
            log.with_suffix('.execution.json').unlink()
            log.write_text('DONE (PASS, rc=0)')
            self.assertEqual(summarize_eqy(log, Path(t)/'work')['state'], 'INCOMPLETE')

    def test_model_condition_is_checked(self):
        with tempfile.TemporaryDirectory() as t:
            il = Path(t) / 'test.il'
            for value in ["1'0", "1'1", '\\signal']:
                il.write_text('module \\top\n  cell \\dffeas ff\n    connect \\aload ' + value + '\n  end\nend\n')
                if value == "1'0":
                    check_mapped_model(il, 'top')
                else:
                    with self.assertRaises(ValueError):
                        check_mapped_model(il, 'top')
            il.write_text('module \\top\n  cell $not native\n  end\nend\n')
            check_mapped_model(il, 'top')
            il.write_text('module \\top\n  cell \\unknown_vendor vendor\n  end\nend\n')
            with self.assertRaises(ValueError):
                check_mapped_model(il, 'top')

    def test_empty_evidence_cannot_pass(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            self.assertEqual(build_report(root), 'NEEDS_REVIEW')
            manifest = json.loads((root/'11_汇总与证据_summary/manifest.json').read_text())
            self.assertFalse(any(manifest['gates'].values()))
            self.assertEqual(manifest['full_rtl_mapping_proof'], 'NOT_CLOSED')

    def test_review_preserves_original_report(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            (root/'00_本轮验证结论.md').write_text('original evidence')
            output = root/'supplement'
            build_report(root, output_root=output, chain_attempt='run02')
            self.assertEqual((root/'00_本轮验证结论.md').read_text(), 'original evidence')
            self.assertTrue((output/'00_本轮验证结论.md').exists())


class FourCaseRestrictionTests(unittest.TestCase):
    """默认调度收敛为官方四例；其余运行器不被调用、不依赖其资产。"""

    def test_default_plan_is_four_case_only(self):
        import validate
        names = [n for n, _, _ in validate.PLUGIN_PLAN]
        self.assertEqual(names, ['flowcheck', 'formal_selfcheck', 'measurement_selfcheck',
                                 'public', 'chains', 'performance'])
        for banned in ('regression', 'regression_eqy', 'h2', 'multidriver', 'scale'):
            self.assertNotIn(banned, names)

    def test_expected_stage_sets_match(self):
        import validate
        from report import EXPECTED_PLUGIN_STAGES
        self.assertEqual(set(validate.PLUGIN_STAGES), EXPECTED_PLUGIN_STAGES)

    def test_default_code_does_not_reference_removed_runners(self):
        import validate
        src = Path(validate.__file__).read_text()
        for banned in ('run_regression', 'run_h2_cases', 'run_scale', 'gen_multidriver',
                       'h2_cases_run01', 'scale_run01'):
            self.assertNotIn(banned, src)
        self.assertIn('suite-official4', src)


class BuiltinBlockTests(unittest.TestCase):
    """内置目标：缺证据时在启动任何进程前阻断，不退回插件。"""

    def _empty_cfg(self):
        return {
            'flow_version': 'official4-p1', 'suite_version': 'official4-v1',
            'builtin': {
                'baseline': {'path': '/nonexistent/baseline/yosys',
                             'src_repo': '/nonexistent/baseline'},
                'optimized': {'path': '/nonexistent/optimized/yosys',
                              'src_repo': '/nonexistent/optimized'},
                'abc': {'baseline': '/nonexistent/baseline/yosys-abc',
                        'optimized': '/nonexistent/optimized/yosys-abc'},
                'expected_version': '0.69',
                'integration_evidence': ['passes/opt/pmux_opt.cc'],
            },
        }

    def test_missing_builtin_tools_block_without_processes(self):
        import validate
        from unittest import mock
        calls = []

        def spy(*args, **kwargs):
            calls.append(args)
            raise AssertionError('no process may be started for missing builtin tools')

        with mock.patch('subprocess.run', side_effect=spy), \
             mock.patch('subprocess.Popen', side_effect=spy), \
             mock.patch('subprocess.check_output', side_effect=spy):
            ok, missing, evidence = validate.check_builtin_evidence(self._empty_cfg(), run_identity=True)
        self.assertFalse(ok)
        self.assertEqual(calls, [])
        self.assertTrue(any('缺失' in m for m in missing))

    def test_builtin_block_report_never_claims_success(self):
        from report import build_builtin_block_report
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            status = build_builtin_block_report(
                root, status='BUILTIN_NOT_READY',
                missing=['optimized yosys 可执行文件缺失：/x'], evidence={},
                cfg={'flow_version': 'official4-p1', 'suite_version': 'official4-v1',
                     'target_commit': '0' * 40, 'source_sha256': 'a' * 64,
                     'project_head': 'b' * 40, 'suite_verified': True})
            self.assertEqual(status, 'BUILTIN_NOT_READY')
            text = (root / '00_本轮验证结论.md').read_text()
            self.assertIn('BUILTIN_NOT_READY', text)
            self.assertIn('缺项清单', text)
            self.assertIn('后续实现清单', text)
            self.assertNotIn('FOUR_CASE_PLUGIN_CHECKS_COMPLETE', text)
            manifest = json.loads((root / '11_汇总与证据_summary/manifest.json').read_text())
            self.assertEqual(manifest['builtin_execution'], 'NOT_READY')
            self.assertEqual(manifest['official_acceptance'], 'NOT_CLAIMED')


class PerformanceJudgementTests(unittest.TestCase):
    def _summary(self, base_cpu, opt_cpu, base_rss, opt_rss, *, pairs=5, bad_run=False, case='test1'):
        runs = []
        for side, cpu, rss in (('baseline', base_cpu, base_rss), ('optimized', opt_cpu, opt_rss)):
            for i in range(pairs):
                rc = 1 if (bad_run and side == 'optimized' and i == 0) else 0
                runs.append({'side': side, 'seq': i + 1, 'rc': rc, 'timed_out': False,
                             'stat_exists': True, 'cpu_total_s': cpu, 'tree_rss_peak_kb': rss})
        return {'case': case, 'pairs': pairs, 'runs': runs,
                'baseline_cpu_total_median': base_cpu, 'optimized_cpu_total_median': opt_cpu,
                'baseline_tree_rss_peak_median': base_rss, 'optimized_tree_rss_peak_median': opt_rss}

    def test_five_percent_boundary_is_allowed(self):
        from report import judge_case_performance
        j = judge_case_performance(self._summary(1.0, 1.05, 1000, 1050.0))
        self.assertTrue(j['valid'])
        self.assertAlmostEqual(j['cpu_overhead_pct'], 5.0, places=9)
        self.assertTrue(j['cpu_ok'])
        self.assertTrue(j['mem_ok'])
        self.assertTrue(j['pass'])

    def test_above_five_percent_case_fails_even_if_others_pass(self):
        from report import judge_case_performance
        j_bad = judge_case_performance(self._summary(1.0, 1.0501, 1000, 1050.0, case='test1'))
        j_good = judge_case_performance(self._summary(1.0, 1.0, 1000, 1000.0, case='test2'))
        self.assertFalse(j_bad['cpu_ok'])
        self.assertFalse(j_bad['pass'])
        self.assertTrue(j_good['pass'])
        # 逐例独立判定：不合格例不会被其它例的零开销“平均”掉
        self.assertFalse(all(j['pass'] for j in (j_bad, j_good)))
        j_mem = judge_case_performance(self._summary(1.0, 1.0, 1000.0, 1050.1, case='test4'))
        self.assertFalse(j_mem['mem_ok'])

    def test_invalid_samples_never_pass(self):
        from report import judge_case_performance
        j = judge_case_performance(self._summary(1.0, 1.0, 1000, 1000, bad_run=True))
        self.assertFalse(j['valid'])
        self.assertFalse(j['pass'])

    def test_sixty_second_limit_uses_upstream_exception(self):
        from report import judge_case_performance
        # 原版超 60s：优化版也超属允许（原版对照例外）
        j = judge_case_performance(self._summary(70.0, 75.0, 1000, 1000))
        self.assertTrue(j['limit_ok'])
        # 原版未超：优化版超 60s 不允许
        j2 = judge_case_performance(self._summary(50.0, 61.0, 1000, 1000))
        self.assertFalse(j2['limit_ok'])


class SelfcheckCacheTests(unittest.TestCase):
    def _fp(self):
        return {'flow_version': 'official4-p1', 'baseline_yosys_sha256': 'a', 'abc_sha256': 'b',
                'eqy_sha256': 'c', 'z3_sha256': 'd', 'suite_manifest_sha256': 'e',
                'runner_sha256': {'x': '1'}, 'entry_sha256': {'y': '2'}}

    def test_fingerprint_mismatch_invalidates(self):
        import validate
        fp = self._fp()
        cache = {'cache_schema': 1, 'entries': {'flowcheck': {'fingerprint': dict(fp), 'ok': True}}}
        self.assertTrue(validate.cache_entry_valid(cache, 'flowcheck', fp))
        changed = dict(fp)
        changed['abc_sha256'] = 'CHANGED'
        self.assertFalse(validate.cache_entry_valid(cache, 'flowcheck', changed))
        self.assertFalse(validate.cache_entry_valid(cache, 'formal_selfcheck', fp))
        failed = {'cache_schema': 1, 'entries': {'flowcheck': {'fingerprint': dict(fp), 'ok': False}}}
        self.assertFalse(validate.cache_entry_valid(failed, 'flowcheck', fp))

    def test_cache_roundtrip(self):
        import validate
        with tempfile.TemporaryDirectory() as t:
            path = Path(t) / 'cache.json'
            cache = validate.load_selfcheck_cache(path)
            validate.update_selfcheck_cache(path, cache, self._fp(), 'flowcheck', True, '/tmp/round')
            again = validate.load_selfcheck_cache(path)
            self.assertTrue(validate.cache_entry_valid(again, 'flowcheck', self._fp()))


class RoundDirTests(unittest.TestCase):
    def test_round_numbering_refuses_overwrite(self):
        import validate
        with tempfile.TemporaryDirectory() as t:
            parent = Path(t)
            prefix = '2026-09-24_稳定版-四例_abc1234'
            r1 = validate.next_round_dir(parent, prefix)
            r2 = validate.next_round_dir(parent, prefix)
            self.assertEqual(r1.name, prefix + '_第01轮')
            self.assertEqual(r2.name, prefix + '_第02轮')


class PluginGateIntegrationTests(unittest.TestCase):
    """完整假轮次：唯一缺陷是 test3 性能存在无效样本 → 必须 NEEDS_REVIEW，不输出通过。"""

    def _write(self, root):
        from report import MAIN_CHAINS, CASES
        (root / '01_来源与环境_meta').mkdir(parents=True)
        ctx = {'flow_version': 'official4-p1', 'suite_version': 'official4-v1',
               'target_commit': '1dceb17' + '0' * 33, 'source_sha256': 'a' * 64,
               'project_head': 'b' * 40, 'suite_verified': True, 'mode': 'plugin',
               'chains_mode': 'main', 'performance_pairs': 5,
               'isolation': {'baseline_no_pmux': True, 'plugin_has_pmux': True},
               'plugin_sha256': 'c' * 64}
        (root / 'validation_context.json').write_text(json.dumps(ctx) + '\n')
        stages = [{'name': n, 'state': 'COMPLETED', 'rc': 0} for n in
                  ('build', 'flowcheck', 'formal_selfcheck', 'measurement_selfcheck',
                   'public', 'chains', 'performance')]
        (root / '01_来源与环境_meta/stages.json').write_text(json.dumps(stages) + '\n')
        pub_dir = root / '05_公开四例_public/round01'
        pub_dir.mkdir(parents=True)
        pub = [{'case': case, 'baseline_rc': 0, 'optimized_rc': 0,
                'baseline_check_assert': True, 'optimized_check_assert': True,
                'baseline_comb': 100, 'optimized_comb': 80,
                'baseline_dff': 10, 'optimized_dff': 10, 'dff_nonincrease': True}
               for case in CASES]
        (pub_dir / 'summary.json').write_text(json.dumps({'cases': pub}) + '\n')
        chain_dir = root / '10_验证工具自检_selfcheck/chains/run01'
        chain_dir.mkdir(parents=True)
        rows = [{'case': c, 'chain': ch, 'state': 'PASS', 'rc': 0, 'proved': 1, 'total': 1,
                 'failed': 0, 'failed_partitions': []} for c in CASES for ch in MAIN_CHAINS]
        (chain_dir / 'chains_summary.json').write_text(json.dumps(rows) + '\n')
        perf_dir = root / '09_时间内存开销_performance/round01'
        perf_dir.mkdir(parents=True)
        summaries = []
        for case in CASES:
            bad = case == 'test3'
            runs = []
            for side, cpu, rss in (('baseline', 1.0, 1000), ('optimized', 1.0, 1000)):
                for i in range(5):
                    rc = 1 if (bad and side == 'optimized' and i == 0) else 0
                    runs.append({'side': side, 'seq': i + 1, 'rc': rc, 'timed_out': False,
                                 'stat_exists': True, 'cpu_total_s': cpu, 'tree_rss_peak_kb': rss})
            summaries.append({'case': case, 'pairs': 5, 'runs': runs,
                              'baseline_cpu_total_median': 1.0, 'optimized_cpu_total_median': 1.0,
                              'baseline_tree_rss_peak_median': 1000, 'optimized_tree_rss_peak_median': 1000})
        (perf_dir / 'performance_summary.json').write_text(json.dumps(summaries) + '\n')

    def test_invalid_perf_sample_blocks_complete_status(self):
        from report import build_report
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            self._write(root)
            status = build_report(root, chain_attempt='run01', mode='plugin')
            manifest = json.loads((root / '11_汇总与证据_summary/manifest.json').read_text())
            self.assertEqual(status, 'NEEDS_REVIEW')
            self.assertFalse(manifest['gates']['四例性能逐例判定'])
            self.assertTrue(manifest['gates']['功能证明（默认链集合）'])
            self.assertEqual(manifest['final_builtin_acceptance'], 'NOT_RUN')
            self.assertEqual(manifest['marking'], '四例插件预检')
            text = (root / '00_本轮验证结论.md').read_text()
            self.assertIn('NOT_RUN', text)
            self.assertIn('NEEDS_REVIEW', text)


if __name__ == '__main__':
    unittest.main()
