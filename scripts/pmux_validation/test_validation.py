"""Evidence classification and reporting regression tests (no EDA execution).

official4-p2：覆盖 noDF 严格转换、联合判定、支持配置预检边界、双侧报告、
功能补充复核模式与新指纹字段（模型/策略版本）。
"""
import io
import json
import contextlib
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parent / 'runner'))
from formal_status import summarize_eqy, check_mapped_model
from function_common import (transform_run_ys, make_probe_ys, classify_proof_text,
                             classify_probe_text, verify_expected_asserts, TransformError)
from report import build_report, row_functional_ok


def _dffeas_il(conns=None, params=None, top='top'):
    c = {"d": "\\d", "q": "\\q", "clk": "\\clk", "clrn": "1'1", "prn": "1'1",
         "ena": "1'1", "asdata": "1'0", "aload": "1'0", "sclr": "1'0", "sload": "1'0"}
    c.update(conns or {})
    p = {"power_up": '"low"', "is_wysiwyg": '"TRUE"'}
    p.update(params or {})
    body = "".join("    parameter \\{} {}\n".format(k, v) for k, v in p.items() if v is not None)
    body += "".join("    connect \\{} {}\n".format(k, v) for k, v in c.items() if v is not None)
    return "module \\{}\n  cell \\dffeas ff\n".format(top) + body + "  end\nend\n"


def _lcell_il(missing=None):
    ports = {"dataa": "\\a", "datab": "\\b", "datac": "\\c", "datad": "\\d", "combout": "\\y"}
    if missing:
        ports.pop(missing, None)
    body = "    parameter \\lut_mask 16'h0008\n    parameter \\sum_lutc_input \"datac\"\n"
    body += "".join("    connect \\{} {}\n".format(k, v) for k, v in ports.items())
    return "module \\top\n  cell \\cycloneiv_lcell_comb lut\n" + body + "  end\nend\n"


class EvidenceTests(unittest.TestCase):
    def test_status_requires_successful_completion(self):
        with tempfile.TemporaryDirectory() as t:
            log = Path(t) / 'verify.log'
            for text, rc, expected in [('', 0, 'INCOMPLETE'),
                ('Successfully proved equivalence of partition y', 124, 'TIMEOUT'),
                ('DONE (PASS, rc=0)', 0, 'PASS'),
                ('DONE (PASS, rc=0)', 1, 'TOOL_OR_CONFIG_ERROR'),
                ('ERROR: unknown command', 2, 'TOOL_OR_CONFIG_ERROR'),
                ('Failed to prove equivalence of partition y\nDONE (FAIL, rc=2)', 2, 'UNPROVEN'),
                ('partitions not equivalent\nFailed to prove equivalence of partition y\nDONE (FAIL, rc=2)', 2, 'COUNTEREXAMPLE_REQUIRES_REVIEW')]:
                log.write_text(text)
                log.with_suffix('.execution.json').write_text(json.dumps({'rc': rc}))
                self.assertEqual(summarize_eqy(log, Path(t) / 'work')['state'], expected)
            log.with_suffix('.execution.json').unlink()
            log.write_text('DONE (PASS, rc=0)')
            self.assertEqual(summarize_eqy(log, Path(t) / 'work')['state'], 'INCOMPLETE')

    def test_mapped_model_supported_config(self):
        with tempfile.TemporaryDirectory() as t:
            il = Path(t) / 'test.il'
            # 受支持配置（含 clrn/ena 为信号）
            il.write_text(_dffeas_il(conns={"clrn": "\\rst_n", "ena": "\\en"}))
            check_mapped_model(il, 'top')
            # 缺失控制端口必须阻断（不得当作合法信号）
            il.write_text(_dffeas_il(conns={"clrn": None}))
            with self.assertRaisesRegex(ValueError, 'clrn'):
                check_mapped_model(il, 'top')
            il.write_text(_dffeas_il(conns={"ena": None}))
            with self.assertRaisesRegex(ValueError, 'ena'):
                check_mapped_model(il, 'top')
            # 常量约束
            il.write_text(_dffeas_il(conns={"aload": "1'1"}))
            with self.assertRaisesRegex(ValueError, 'aload'):
                check_mapped_model(il, 'top')
            il.write_text(_dffeas_il(conns={"prn": "\\p"}))
            with self.assertRaisesRegex(ValueError, 'prn'):
                check_mapped_model(il, 'top')
            # 未知参数/端口取值
            il.write_text(_dffeas_il(params={"power_up": '"dontcare"'}))
            with self.assertRaisesRegex(ValueError, 'power_up'):
                check_mapped_model(il, 'top')
            il.write_text(_dffeas_il(params={"extra_param": '1'}))
            with self.assertRaisesRegex(ValueError, '未知参数'):
                check_mapped_model(il, 'top')
            # 纯组合（lcell）合法；缺必需端口阻断
            il.write_text(_lcell_il())
            check_mapped_model(il, 'top')
            il.write_text(_lcell_il(missing='datad'))
            with self.assertRaisesRegex(ValueError, 'datad'):
                check_mapped_model(il, 'top')
            # 内建 $ 单元允许；未知单元阻断
            il.write_text('module \\top\n  cell $not native\n  end\nend\n')
            check_mapped_model(il, 'top')
            il.write_text('module \\top\n  cell \\unknown_vendor vendor\n  end\nend\n')
            with self.assertRaises(ValueError):
                check_mapped_model(il, 'top')

    def test_empty_evidence_cannot_pass(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            self.assertEqual(build_report(root), 'NEEDS_REVIEW')
            manifest = json.loads((root / '11_汇总与证据_summary/manifest.json').read_text())
            self.assertFalse(any(manifest['gates'].values()))
            self.assertEqual(manifest['full_rtl_mapping_proof'], 'NOT_CLOSED')

    def test_review_preserves_original_report(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            (root / '00_本轮验证结论.md').write_text('original evidence')
            output = root / 'supplement'
            build_report(root, output_root=output, chain_attempt='run02')
            self.assertEqual((root / '00_本轮验证结论.md').read_text(), 'original evidence')
            self.assertTrue((output / '00_本轮验证结论.md').exists())


class TransformAndVerdictTests(unittest.TestCase):
    SAMPLE = ("verilog_defaults -add -D CHECK_OUTPUTS\n"
              "read_verilog -sv ../../../partitions/t.sv\n"
              "hierarchy -top miter; proc; chformal -cover -remove\n"
              "sat -tempinduct -set-init-undef -set-def-formal -set-def-inputs "
              "-maxsteps 5 -set-assumes -prove-asserts miter\n")

    def test_transform_removes_exactly_one_token(self):
        new, info = transform_run_ys(self.SAMPLE)
        self.assertNotIn('set-def-formal', new)
        self.assertEqual(new, self.SAMPLE.replace(' -set-def-formal', ''))
        self.assertEqual(info['removed_def_formal'], 1)

    def test_transform_refuses_unexpected_formats(self):
        for bad in ("no sat line\n",
                    "sat -tempinduct -set-def-inputs miter\n",
                    "sat -tempinduct -set-def-formal a\nsat -tempinduct -set-def-formal b\n",
                    "sat -tempinduct -set-def-formal x -set-def-formal y miter\n"):
            with self.assertRaises(TransformError):
                transform_run_ys(bad)
        # 无 token 的 sat 行也必须停止（不得静默通过）
        with self.assertRaises(TransformError):
            transform_run_ys("sat -tempinduct -set-init-undef miter\n")

    def test_probe_variants(self):
        noDF = make_probe_ys(self.SAMPLE.replace(' -set-def-formal', ''), 'noDF')
        self.assertIn('chformal -assert -remove', noDF)
        self.assertIn('sat -seq 1 -set-init-undef -set-def-inputs -set-assumes miter', noDF)
        DF = make_probe_ys(self.SAMPLE, 'DF')
        self.assertIn('sat -seq 1 -set-init-undef -set-def-formal -set-def-inputs '
                      '-set-assumes miter', DF)

    def test_classify_proof_joint_verdict(self):
        real_pass = ("** Trying induction with length 1 **\n"
                     "Base case for induction length 1 proven.\n"
                     "Induction step proven: SUCCESS!\n"
                     "Import proof for assert: \\__mp_rw__assert.okay when 1'1.\n")
        p = classify_proof_text(real_pass)
        self.assertEqual((p['state'], p['induct_len'], p['base_proven']),
                         ('PASS', 1, 1))
        # 不真实格式（缺 Trying 行）不得判 PASS
        self.assertNotEqual(
            classify_proof_text(real_pass.replace("** Trying induction with length 1 **\n", ""))['state'],
            'PASS')
        # 成功标记 + ERROR 行不得判 PASS
        self.assertNotEqual(classify_proof_text(real_pass + "ERROR: boom\n")['state'], 'PASS')
        # 基例数少于归纳长度不得判 PASS
        short = ("** Trying induction with length 3 **\n"
                 "Base case for induction length 1 proven.\n"
                 "Induction step proven: SUCCESS!\n"
                 "Import proof for assert: \\a.okay\n")
        self.assertNotEqual(classify_proof_text(short)['state'], 'PASS')
        # FAIL / UNKNOWN
        self.assertEqual(classify_proof_text(
            "Trying induction with length 2\n[base case 2]\nmodel found for base case: FAIL!\n")['state'], 'FAIL')
        self.assertEqual(classify_proof_text("Reached maximum number of time steps -> proof failed.\n")['state'],
                         'UNKNOWN')

    def test_classify_probe_and_assert_coverage(self):
        v = classify_probe_text("SAT solving finished - model found:\n")
        self.assertEqual(v['verdict'], 'PREMISES_SAT')
        v = classify_probe_text("SAT solving finished - no model found.\n")
        self.assertEqual(v['verdict'], 'PREMISES_UNSAT')
        ok, missing = verify_expected_asserts(
            ["__mp_rw__assert.okay", "__po_gpioout__assert.okay"],
            ["\\__mp_rw__assert.okay", "\\__mp_gate__assert.okay"])
        self.assertFalse(ok)
        self.assertEqual(missing, ["__po_gpioout__assert.okay"])


class PrecheckBoundaryTests(unittest.TestCase):
    def _run(self, argv):
        import precheck_supported_config as P
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = P.main(argv)
        return rc, buf.getvalue()

    def test_empty_dir_fails(self):
        with tempfile.TemporaryDirectory() as t:
            rc, out = self._run(["--dir", t])
            self.assertEqual(rc, 2)
            self.assertIn("未匹配到任何输入文件", out)

    def test_expected_files_must_be_complete(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / 'test1_baseline_mapped.il').write_text(_dffeas_il())
            rc, out = self._run(["--dir", t, "--expect", "test1:baseline", "test1:optimized",
                                 "--top-from-name"])
            self.assertEqual(rc, 2)
            self.assertIn("test1_optimized_mapped.il", out)

    def test_valid_set_passes_and_model_required(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / 'test1_baseline_mapped.il').write_text(_dffeas_il(top='test1'))
            (Path(t) / 'form_cells_cycloneiv.v').write_text("// model stub\n")
            rc, out = self._run(["--dir", t, "--expect", "test1:baseline",
                                 "--top-from-name", "--model", "form_cells_cycloneiv.v"])
            self.assertEqual(rc, 0, out)
            rc, out = self._run(["--dir", t, "--expect", "test1:baseline",
                                 "--top-from-name", "--model", "missing_model.v"])
            self.assertEqual(rc, 2)
            self.assertIn("缺少模型文件", out)


class FourCaseRestrictionTests(unittest.TestCase):
    """默认调度收敛为官方四例；其余运行器不被调用、不依赖其资产。"""

    def test_default_plan_is_four_case_only(self):
        import validate
        names = [n for n, _, _ in validate.PLUGIN_PLAN]
        self.assertEqual(names, ['flowcheck', 'formal_selfcheck', 'measurement_selfcheck',
                                 'public', 'chains', 'performance'])
        for banned in ('regression', 'regression_eqy', 'h2', 'multidriver', 'scale'):
            self.assertNotIn(banned, names)
        fnames = [n for n, _, _ in validate.FUNCTION_ONLY_PLAN]
        self.assertEqual(fnames, ['formal_selfcheck', 'chains'])
        skipped = [n for n, _ in validate.FUNCTION_ONLY_SKIPPED]
        self.assertEqual(set(fnames) | set(skipped) | {'build'}, set(validate.PLUGIN_STAGES))

    def test_expected_stage_sets_match(self):
        import validate
        from report import EXPECTED_PLUGIN_STAGES, FUNCTION_ONLY_EXEC, FUNCTION_ONLY_SKIPPED
        self.assertEqual(set(validate.PLUGIN_STAGES), EXPECTED_PLUGIN_STAGES)
        self.assertEqual(tuple(n for n, _, _ in validate.FUNCTION_ONLY_PLAN), FUNCTION_ONLY_EXEC[1:])
        self.assertEqual(set(FUNCTION_ONLY_EXEC) | set(FUNCTION_ONLY_SKIPPED),
                         set(validate.PLUGIN_STAGES))

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
            'flow_version': 'official4-p2', 'suite_version': 'official4-v1',
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
                cfg={'flow_version': 'official4-p2', 'suite_version': 'official4-v1',
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
        j = judge_case_performance(self._summary(70.0, 75.0, 1000, 1000))
        self.assertTrue(j['limit_ok'])
        j2 = judge_case_performance(self._summary(50.0, 61.0, 1000, 1000))
        self.assertFalse(j2['limit_ok'])


class SelfcheckCacheTests(unittest.TestCase):
    def _fp(self):
        return {'flow_version': 'official4-p2', 'model_version': 'dffeas-v3',
                'strategy_version': 'noDF-local-r1', 'baseline_yosys_sha256': 'a',
                'abc_sha256': 'b', 'eqy_sha256': 'c', 'z3_sha256': 'd',
                'suite_manifest_sha256': 'e', 'runner_sha256': {'x': '1'},
                'entry_sha256': {'y': '2'}}

    def test_fingerprint_mismatch_invalidates(self):
        import validate
        fp = self._fp()
        cache = {'cache_schema': 1, 'entries': {'flowcheck': {'fingerprint': dict(fp), 'ok': True}}}
        self.assertTrue(validate.cache_entry_valid(cache, 'flowcheck', fp))
        for key, value in (('abc_sha256', 'CHANGED'), ('model_version', 'dffeas-v2'),
                           ('strategy_version', 'DF')):
            changed = dict(fp)
            changed[key] = value
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

    def test_cache_creates_missing_parent_directory(self):
        """首次运行场景：共享缓存目录尚不存在时，写入必须先创建父目录。"""
        import validate
        with tempfile.TemporaryDirectory() as t:
            path = Path(t) / 'missing' / 'nested' / 'cache.json'
            cache = validate.load_selfcheck_cache(path)
            self.assertEqual(cache, {'cache_schema': 1, 'entries': {}})
            validate.update_selfcheck_cache(path, cache, self._fp(), 'flowcheck', True, '/tmp/round')
            self.assertTrue(path.is_file())
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


def _pass_row(case, chain):
    if case == 'test3' and chain in ('c4a_rtl_opt_mapped', 'c4b_rtl_base_mapped'):
        return {'case': case, 'chain': chain, 'state': 'PASS', 'rc': 0, 'verified': True,
                'method': 'merged_miter', 'probes_noDF_all_sat': True,
                'partitions_total': 4, 'partitions_pass': 0,
                'partition_states': {'test3.rw': 'FAIL'},
                'merged': {'state': 'PASS', 'probe': 'PREMISES_SAT', 'assert_cover_ok': True,
                           'k': 11 if 'c4a' in chain else 14}}
    return {'case': case, 'chain': chain, 'state': 'PASS', 'rc': 0, 'verified': True,
            'method': 'partition', 'probes_noDF_all_sat': True,
            'partitions_total': 1, 'partitions_pass': 1, 'partition_states': {'x': 'PASS'}}


class PluginGateIntegrationTests(unittest.TestCase):
    """完整假轮次（p2 行结构）：唯一缺陷是 test3 性能存在无效样本 → NEEDS_REVIEW。"""

    def _write(self, root):
        from report import MAIN_CHAINS, CASES
        (root / '01_来源与环境_meta').mkdir(parents=True)
        ctx = {'flow_version': 'official4-p2', 'suite_version': 'official4-v1',
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
        rows = [_pass_row(c, ch) for c in CASES for ch in MAIN_CHAINS]
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
            # 每例两侧分别报告（不再“两链同结果”）
            self.assertIn('每例两侧功能状态', text)
            self.assertIn('test3：c4a 合并证明', text)
            self.assertIn('不使用“两链同结果”推断', text)

    def test_missing_joint_fields_block_functional_gate(self):
        """不能只看 state=PASS：缺少 verified/探针字段时功能门必须不通过。"""
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            self._write(root)
            chain_file = root / '10_验证工具自检_selfcheck/chains/run01/chains_summary.json'
            rows = json.loads(chain_file.read_text())
            rows[0] = dict(rows[0], state='PASS', rc=0)
            rows[0].pop('verified', None)
            rows[0].pop('probes_noDF_all_sat', None)
            chain_file.write_text(json.dumps(rows) + '\n')
            build_report(root, chain_attempt='run01', mode='plugin')
            manifest = json.loads((root / '11_汇总与证据_summary/manifest.json').read_text())
            self.assertFalse(manifest['gates']['功能证明（默认链集合）'])

    def test_merged_row_with_bad_probe_blocks_gate(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            self._write(root)
            chain_file = root / '10_验证工具自检_selfcheck/chains/run01/chains_summary.json'
            rows = json.loads(chain_file.read_text())
            for r in rows:
                if r['case'] == 'test3' and r['chain'] == 'c4b_rtl_base_mapped':
                    r['merged'] = dict(r['merged'], probe='PREMISES_UNSAT')
            chain_file.write_text(json.dumps(rows) + '\n')
            build_report(root, chain_attempt='run01', mode='plugin')
            manifest = json.loads((root / '11_汇总与证据_summary/manifest.json').read_text())
            self.assertFalse(manifest['gates']['功能证明（默认链集合）'])
            bad = next(r for r in rows if r['case'] == 'test3'
                       and r['chain'] == 'c4b_rtl_base_mapped')
            self.assertFalse(row_functional_ok(bad))


class FunctionRecheckReportTests(unittest.TestCase):
    """功能补充复核模式：冻结输入、只功能阶段、报告标注与完成状态。"""

    def _write(self, root, *, frozen_ok=True):
        from report import MAIN_CHAINS, CASES, FUNCTION_ONLY_EXEC, FUNCTION_ONLY_SKIPPED
        (root / '01_来源与环境_meta').mkdir(parents=True)
        ctx = {'flow_version': 'official4-p2', 'suite_version': 'official4-v1',
               'model_version': 'dffeas-v3', 'strategy_version': 'noDF-local-r1',
               'target_commit': '5c44e87' + '0' * 33, 'source_sha256': 'a' * 64,
               'project_head': '8' * 40, 'suite_verified': True, 'mode': 'plugin',
               'function_only': True, 'frozen_round': '/frozen/round',
               'chains_mode': 'main', 'performance_pairs': 5,
               'isolation': {'baseline_no_pmux': True, 'plugin_has_pmux': True},
               'plugin_sha256': 'c' * 64}
        (root / 'validation_context.json').write_text(json.dumps(ctx) + '\n')
        stages = [{'name': n, 'state': 'COMPLETED', 'rc': 0} for n in FUNCTION_ONLY_EXEC]
        stages += [{'name': n, 'state': 'NOT_RUN', 'reason': '功能复核：未重新综合/未测性能'}
                   for n in FUNCTION_ONLY_SKIPPED]
        (root / '01_来源与环境_meta/stages.json').write_text(json.dumps(stages) + '\n')
        chain_dir = root / '10_验证工具自检_selfcheck/chains/run01'
        chain_dir.mkdir(parents=True)
        rows = [_pass_row(c, ch) for c in CASES for ch in MAIN_CHAINS]
        (chain_dir / 'chains_summary.json').write_text(json.dumps(rows) + '\n')
        (chain_dir / 'frozen_input_verification.json').write_text(json.dumps(
            {'ok': frozen_ok, 'frozen_round': '/frozen/round',
             'files': [{'file': '05_公开四例_public/round01/test1/baseline/baseline_mapped.il',
                        'match': frozen_ok}]}) + '\n')
        (chain_dir / 'precheck_report.txt').write_text('[通过] 支持配置预检：8 个输入文件全部在受支持集内\n')

    def test_complete_status_and_marking(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            self._write(root)
            status = build_report(root, chain_attempt='run01', mode='plugin')
            self.assertEqual(status, 'FUNCTION_RECHECK_COMPLETE')
            text = (root / '00_本轮验证结论.md').read_text()
            self.assertIn('插件版功能补充复核', text)
            self.assertIn('未重新综合、未重测性能', text)
            self.assertIn('NOT_RUN', text)
            self.assertIn('每例两侧功能状态', text)
            manifest = json.loads((root / '11_汇总与证据_summary/manifest.json').read_text())
            self.assertTrue(manifest['function_only'])
            self.assertEqual(manifest['marking'], '插件版功能补充复核')
            self.assertEqual(manifest['final_builtin_acceptance'], 'NOT_RUN')
            self.assertTrue(all(manifest['gates'].values()))

    def test_frozen_hash_mismatch_blocks(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            self._write(root, frozen_ok=False)
            status = build_report(root, chain_attempt='run01', mode='plugin')
            self.assertEqual(status, 'NEEDS_REVIEW')
            manifest = json.loads((root / '11_汇总与证据_summary/manifest.json').read_text())
            self.assertFalse(manifest['gates']['冻结输入来源核验'])
            self.assertFalse(manifest['official_acceptance'] == 'PASSED')


if __name__ == '__main__':
    unittest.main()
