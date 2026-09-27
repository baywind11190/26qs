"""Evidence classification and reporting regression tests (no EDA execution).

official4-p2：覆盖 noDF 严格转换、联合判定、支持配置预检边界、双侧报告、
功能补充复核模式与新指纹字段（模型/策略版本）。
"""
import io
import json
import contextlib
import hashlib
import subprocess
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
            # 未知端口必须阻断（每个实际连接端口必须属于受支持集合）
            il.write_text(_dffeas_il(conns={"extra_port": "\\x"}))
            with self.assertRaisesRegex(ValueError, '未知端口'):
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
            self.assertIn('后续动作', text)
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


class BuiltinModeTests(unittest.TestCase):
    """内置模式：计划路由、flowcheck 位置判定、指纹绑定、缺证明阻断、标志隔离。"""

    def test_builtin_stage_sets_match_and_no_plugin_flags(self):
        import validate
        from report import BUILTIN_EXPECTED_STAGES, BUILTIN_MAIN_CHAINS
        self.assertEqual(set(validate.BUILTIN_STAGES), BUILTIN_EXPECTED_STAGES)
        self.assertEqual(tuple(n for n, _, _ in validate.BUILTIN_PLAN),
                         validate.BUILTIN_STAGES[1:])
        self.assertEqual(BUILTIN_MAIN_CHAINS,
                         ("c4a_rtl_opt_mapped", "c4b_rtl_base_mapped"))
        for name, script, args in validate.BUILTIN_PLAN:
            self.assertNotIn("-m", args)
        chains_args = dict((n, a) for n, _, a in validate.BUILTIN_PLAN)["chains"]
        self.assertIn("--input-mode", chains_args)
        self.assertIn("builtin", chains_args)
        self.assertEqual(validate.BUILTIN_CACHED_STAGES,
                         ("formal_selfcheck", "measurement_selfcheck"))

    def test_builtin_common_routing_and_position(self):
        sys.path.insert(0, str(Path(__file__).parent / 'runner'))
        import builtin_common as B
        with tempfile.TemporaryDirectory() as t:
            base = Path(t) / 'yosys'
            opt = Path(t) / 'yosys_opt'
            base.write_text('x')
            opt.write_text('y')
            bins = B.select_binaries({'baseline': {'path': str(base)},
                                      'optimized': {'path': str(opt)}})
            self.assertEqual(bins['baseline'], base)
            self.assertEqual(bins['optimized'], opt)
            with self.assertRaises(FileNotFoundError):
                B.select_binaries({'baseline': {'path': str(base)},
                                   'optimized': {'path': str(Path(t) / 'missing')}})
        script = B.gen_builtin_synth_ys(Path('/x/test1.v'), 'test1')
        self.assertIn('synth_intel -family cycloneiv -top test1', script)
        self.assertIn('check -assert', script)
        self.assertIn('write_rtlil mapped.il', script)
        self.assertNotIn('pmux_opt', script)  # 外部脚本不出现 pmux_opt（内置调用）
        # 位置判定：以编号兄弟判定（opt 的内部子 pass 行不干扰）
        entries = [("2.14", "FSM"), ("2.15", "OPT"), ("2.15.21", "OPT_CLEAN"),
                   ("2.15.22", "OPT_EXPR"), ("2.16", "PMUX_OPT"),
                   ("2.17", "WREDUCE"), ("2.18", "PEEPOPT")]
        pos = B.check_pmux_position(entries)
        self.assertEqual(pos['count'], 1)
        self.assertTrue(pos['after_opt'])
        self.assertTrue(pos['before_wreduce'])
        bad = B.check_pmux_position([("2.15", "OPT"), ("2.16", "WREDUCE"),
                                     ("2.17", "PMUX_OPT")])
        self.assertFalse(bad['after_opt'] and bad['before_wreduce'])
        twice = B.check_pmux_position([("2.15", "OPT"), ("2.16", "PMUX_OPT"),
                                       ("2.17", "WREDUCE"), ("2.18", "PMUX_OPT"),
                                       ("2.19", "WREDUCE")])
        self.assertEqual(twice['count'], 2)
        nonum = B.check_pmux_position([(None, "PMUX_OPT")])
        self.assertEqual(nonum['count'], 1)
        self.assertFalse(nonum['after_opt'] or nonum['before_wreduce'])
        seq = B.extract_executing_sequence(
            "12.3. Executing OPT pass (legacy).\n"
            "Executing PMUX_OPT pair-swap optimization.\n"
            "24. Executing WREDUCE pass.")
        names = [B.executing_name(d).split()[0] for d in seq]
        self.assertEqual(names, ['OPT', 'PMUX_OPT', 'WREDUCE'])
        entries2 = B.extract_executing_entries(
            "12.3. Executing OPT pass (legacy).\n"
            "Executing PMUX_OPT pair-swap optimization.\n"
            "24. Executing WREDUCE pass.")
        self.assertEqual(entries2[0], ("12.3", "OPT pass (legacy)."))
        self.assertEqual(entries2[1], (None, "PMUX_OPT pair-swap optimization."))

    @staticmethod
    def _git_init(repo: Path, files):
        repo.mkdir()

        def run(*args):
            return subprocess.run(["git", *args], cwd=repo, check=True,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True)

        run("init", "-q")
        for fn, text in files.items():
            f = repo / fn
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text)
        run("-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
        run("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "c1")

    def test_builtin_precheck_fingerprint_binding_blocks(self):
        """不同算法/二进制指纹必须在启动任何进程前阻断（模拟检查）。"""
        import validate
        with tempfile.TemporaryDirectory() as t:
            base = Path(t)
            brepo = base / 'baseline-src'
            self._git_init(brepo, {'kernel/x.cc': 'int x;\n'})
            orepo = base / 'optimized-src'
            self._git_init(orepo, {'kernel/x.cc': 'int x;\n'})
            alg = "// pmux algorithm\nint pmux;\n"
            (orepo / 'passes/opt').mkdir(parents=True, exist_ok=True)
            (orepo / 'passes/opt/pmux_opt.cc').write_text(alg)
            (orepo / 'passes/opt/CMakeLists.txt').write_text(
                'yosys_pass(pmux_opt\n\tpmux_opt.cc\n)\n')
            (orepo / 'techlibs/intel').mkdir(parents=True, exist_ok=True)
            (orepo / 'techlibs/intel/synth_intel.cc').write_text(
                'run("opt");\nrun("pmux_opt");\n')
            alg_sha = hashlib.sha256(alg.encode()).hexdigest()
            diff_sha = hashlib.sha256(validate.git(orepo, 'diff').encode()).hexdigest()
            for side in ('baseline', 'optimized'):
                bdir = base / (side + '-build')
                bdir.mkdir(parents=True)
                ybin = bdir / 'yosys'
                ybin.write_text('#!/bin/sh\n')
                ybin.chmod(0o755)
                abc = bdir / 'yosys-abc'
                abc.write_text('abc')
                abc.chmod(0o755)
                (bdir / 'share/intel/cycloneiv').mkdir(parents=True)
                (bdir / 'share/intel/cycloneiv/cells_sim.v').write_text('// c\n')
                (bdir / 'share/intel/common').mkdir(parents=True)
                (bdir / 'share/intel/common/m9k_bb.v').write_text('// m\n')
            cfg = {'builtin': {
                'baseline': {'path': str(base / 'baseline-build/yosys'),
                             'src_repo': str(brepo)},
                'optimized': {'path': str(base / 'optimized-build/yosys'),
                              'src_repo': str(orepo),
                              'algorithm_source_path': 'passes/opt/pmux_opt.cc',
                              'algorithm_source_sha256': alg_sha,
                              'integration_diff_sha256': diff_sha},
                'abc': {'baseline': str(base / 'baseline-build/yosys-abc'),
                        'optimized': str(base / 'optimized-build/yosys-abc')},
                'expected_version': '0.69',
                'integration_evidence': ['passes/opt/pmux_opt.cc',
                                         'passes/opt/CMakeLists.txt',
                                         'techlibs/intel/synth_intel.cc'],
            }}
            # 场景 B：与请求提交一致 → 无阻断
            ok, missing, _ = validate.check_builtin_evidence(
                cfg, run_identity=False, source_sha256=alg_sha)
            self.assertTrue(ok, missing)
            # 场景 A：请求算法提交不同 → 阻断
            ok2, missing2, _ = validate.check_builtin_evidence(
                cfg, run_identity=False, source_sha256='f' * 64)
            self.assertFalse(ok2)
            self.assertTrue(any('与请求提交不一致' in m for m in missing2))
            # 场景 C：二进制登记指纹不符 → 阻断
            cfg2 = json.loads(json.dumps(cfg))
            cfg2['builtin']['baseline']['binary_sha256'] = '0' * 64
            ok3, missing3, _ = validate.check_builtin_evidence(
                cfg2, run_identity=False, source_sha256=alg_sha)
            self.assertFalse(ok3)
            self.assertTrue(any('与登记指纹不一致' in m for m in missing3))
            # 场景 D：优化版 diff 与登记不符 → 阻断
            cfg3 = json.loads(json.dumps(cfg))
            cfg3['builtin']['optimized']['integration_diff_sha256'] = '1' * 64
            ok4, missing4, _ = validate.check_builtin_evidence(
                cfg3, run_identity=False, source_sha256=alg_sha)
            self.assertFalse(ok4)
            self.assertTrue(any('登记集成补丁不一致' in m for m in missing4))

    def _write_builtin_round(self, root: Path, *, include_chains=True):
        from report import CASES
        (root / '01_来源与环境_meta').mkdir(parents=True)
        ctx = {'flow_version': 'official4-p3', 'suite_version': 'official4-v1',
               'target_commit': '5c44e87' + '0' * 33, 'source_sha256': 'a' * 64,
               'project_head': 'b' * 40, 'suite_verified': True, 'mode': 'builtin',
               'performance_pairs': 5}
        (root / 'validation_context.json').write_text(json.dumps(ctx) + '\n')
        stages = [{'name': n, 'state': 'COMPLETED', 'rc': 0} for n in
                  ('build', 'flowcheck', 'formal_selfcheck', 'measurement_selfcheck',
                   'public', 'chains', 'performance')]
        (root / '01_来源与环境_meta/stages.json').write_text(json.dumps(stages) + '\n')
        (root / '01_来源与环境_meta/builtin_evidence.json').write_text(json.dumps(
            {'ok': True, 'missing': [],
             'evidence': {'optimized': {'path': '/x/yosys', 'sha256': 'c' * 64}}}) + '\n')
        fc_dir = root / '04_流程一致性_flowcheck/builtin_run01'
        fc_dir.mkdir(parents=True)
        (fc_dir / 'builtin_flowcheck.json').write_text(json.dumps(
            {'all_ok': True, 'cases': [{'case': f'test{i}', 'sides': {}}
                                       for i in range(1, 5)]}) + '\n')
        pub = [{'case': case, 'baseline_rc': 0, 'optimized_rc': 0,
                'baseline_check_assert': True, 'optimized_check_assert': True,
                'baseline_comb': 100, 'optimized_comb': 80,
                'baseline_dff': 10, 'optimized_dff': 10, 'dff_nonincrease': True}
               for case in CASES]
        pub_dir = root / '05_公开四例_public/round01'
        pub_dir.mkdir(parents=True)
        (pub_dir / 'summary.json').write_text(json.dumps({'cases': pub}) + '\n')
        if include_chains:
            chain_dir = root / '10_验证工具自检_selfcheck/chains/run01'
            chain_dir.mkdir(parents=True)
            rows = [_pass_row(c, ch) for c in CASES
                    for ch in ('c4a_rtl_opt_mapped', 'c4b_rtl_base_mapped')]
            (chain_dir / 'chains_summary.json').write_text(json.dumps(rows) + '\n')
        perf = []
        for case in CASES:
            runs = []
            for side in ('baseline', 'optimized'):
                for i in range(5):
                    runs.append({'side': side, 'seq': i + 1, 'rc': 0, 'timed_out': False,
                                 'stat_exists': True, 'cpu_total_s': 1.0,
                                 'tree_rss_peak_kb': 1000})
            perf.append({'case': case, 'pairs': 5, 'runs': runs,
                         'baseline_cpu_total_median': 1.0, 'optimized_cpu_total_median': 1.0,
                         'baseline_tree_rss_peak_median': 1000,
                         'optimized_tree_rss_peak_median': 1000})
        perf_dir = root / '09_时间内存开销_performance/round01'
        perf_dir.mkdir(parents=True)
        (perf_dir / 'performance_summary.json').write_text(json.dumps(perf) + '\n')

    def test_builtin_report_blocks_without_chains_and_completes(self):
        import report as R
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            self._write_builtin_round(root, include_chains=False)
            status = R.build_builtin_report(root, chain_attempt='run01')
            self.assertEqual(status, 'NEEDS_REVIEW')
            manifest = json.loads((root / '11_汇总与证据_summary/manifest.json').read_text())
            self.assertFalse(manifest['gates']['功能证明（内置主链 c4a/c4b）'])
            self.assertEqual(manifest['builtin_local_acceptance'], 'NOT_CLOSED')
            self.assertNotEqual(manifest['builtin_execution'], 'COMPLETE')
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            self._write_builtin_round(root, include_chains=True)
            status = R.build_builtin_report(root, chain_attempt='run01')
            self.assertEqual(status, R.BUILTIN_COMPLETE_STATUS)
            manifest = json.loads((root / '11_汇总与证据_summary/manifest.json').read_text())
            self.assertTrue(all(manifest['gates'].values()))
            self.assertEqual(manifest['builtin_execution'], 'COMPLETE')
            self.assertEqual(manifest['official_acceptance'], 'NOT_CLAIMED')
            text = (root / '00_本轮验证结论.md').read_text()
            self.assertIn('官方四例内置验收（本地）', text)
            self.assertIn('c4a', text)

    def test_plugin_report_never_claims_builtin_status(self):
        import report as R
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            status = R.build_report(root)
            self.assertEqual(status, 'NEEDS_REVIEW')
            text = (root / '00_本轮验证结论.md').read_text()
            self.assertNotIn(R.BUILTIN_COMPLETE_STATUS, text)
            manifest = json.loads((root / '11_汇总与证据_summary/manifest.json').read_text())
            self.assertEqual(manifest['final_builtin_acceptance'], 'NOT_RUN')


class PrepareBuiltinCacheTests(unittest.TestCase):
    """自动内置准备：缓存键绑定、命中核验、失败不发布、plan 只读（不编译、不写文件）。"""

    def _cfg(self, base: Path):
        return {
            'repo': str(base / 'repo'),
            'flow_version': 'official4-p4',
            'builtin': {
                'expected_version': '0.69',
                'cache_dir': str(base / 'cache'),
                'source_repo': str(base / 'yosys-src'),
                'source_commit': 'a' * 40,
                'build_profile': {'cmake_build_type': 'Release', 'shared_libs': True},
                'baseline_reuse': None,
                'integration_evidence': ['passes/opt/pmux_opt.cc'],
            },
            'tools': {'compiler': {'path': '/usr/bin/c++', 'sha256': 'c' * 64}},
        }

    def _make_build(self, base: Path, tag='e'):
        """伪造一份构建树（文件与哈希自洽）。返回 (btree, otree, alg_sha)。"""
        btree = base / (tag + '-baseline-src')
        otree = base / (tag + '-optimized-src')
        for t in (btree, otree):
            (t / '.git').mkdir(parents=True)
            (t / 'build').mkdir()
            (t / 'build/yosys').write_text('yosys-' + tag)
            (t / 'build/yosys-abc').write_text('abc-' + tag)
        (otree / 'passes/opt').mkdir(parents=True)
        alg = 'algorithm for ' + tag + '\n'
        (otree / 'passes/opt/pmux_opt.cc').write_text(alg)
        return btree, otree, hashlib.sha256(alg.encode()).hexdigest()

    def _entry(self, base: Path, tag='e', status='READY'):
        btree, otree, alg_sha = self._make_build(base, tag)
        return {
            'schema': 1, 'name': 'build-' + tag, 'status': status, 'imported': False,
            'build_dir': str(base), 'key': None, 'abc_source_commit': None,
            'baseline': {'action': 'built', 'src_dir': str(btree), 'src_commit': 'a' * 40,
                         'binary': str(btree / 'build/yosys'),
                         'binary_sha256': hashlib.sha256(('yosys-' + tag).encode()).hexdigest(),
                         'abc': str(btree / 'build/yosys-abc'),
                         'abc_sha256': hashlib.sha256(('abc-' + tag).encode()).hexdigest()},
            'optimized': {'action': 'built', 'src_dir': str(otree), 'src_commit': 'a' * 40,
                          'algorithm_source_path': 'passes/opt/pmux_opt.cc',
                          'algorithm_source_sha256': alg_sha,
                          'integration_diff_sha256': 'f' * 64,
                          'binary': str(otree / 'build/yosys'),
                          'binary_sha256': hashlib.sha256(('yosys-' + tag).encode()).hexdigest(),
                          'abc': str(otree / 'build/yosys-abc'),
                          'abc_sha256': hashlib.sha256(('abc-' + tag).encode()).hexdigest()},
        }

    def test_cache_key_binds_source_profile_and_compiler(self):
        import prepare_builtin as P
        with tempfile.TemporaryDirectory() as t:
            cfg = self._cfg(Path(t))
            k1 = P.cache_key(cfg, '1' * 64)
            self.assertEqual(k1['integration_id'], P.INTEGRATION_ID)
            self.assertNotEqual(k1, P.cache_key(cfg, '2' * 64))          # 算法源码变化
            cfg2 = json.loads(json.dumps(cfg))
            cfg2['tools']['compiler']['sha256'] = '9' * 64
            self.assertNotEqual(k1, P.cache_key(cfg2, '1' * 64))         # 编译器变化
            cfg3 = json.loads(json.dumps(cfg))
            cfg3['builtin']['build_profile']['cmake_build_type'] = 'Debug'
            self.assertNotEqual(k1, P.cache_key(cfg3, '1' * 64))         # 构建参数变化
            cfg4 = json.loads(json.dumps(cfg))
            cfg4['builtin']['source_commit'] = 'b' * 40
            self.assertNotEqual(k1, P.cache_key(cfg4, '1' * 64))         # 基础提交变化

    def test_registry_reuse_requires_ready_key_and_intact_products(self):
        import prepare_builtin as P
        with tempfile.TemporaryDirectory() as t:
            base = Path(t)
            cfg = self._cfg(base)
            entry = self._entry(base, 'e')
            alg_sha = entry['optimized']['algorithm_source_sha256']
            entry['key'] = P.cache_key(cfg, alg_sha)
            reg = Path(cfg['builtin']['cache_dir']) / 'registry'
            reg.mkdir(parents=True)
            (reg / 'entry-e.json').write_text(json.dumps(entry))
            cache = cfg['builtin']['cache_dir']
            # 命中：READY + 键匹配 + 产物核验通过
            self.assertIsNotNone(P.find_cached_optimized(cache, P.cache_key(cfg, alg_sha)))
            # 算法源码被改动（哈希不符）→ 不得命中
            (Path(entry['optimized']['src_dir']) / 'passes/opt/pmux_opt.cc').write_text('tampered')
            self.assertIsNone(P.find_cached_optimized(cache, P.cache_key(cfg, alg_sha)))
            (Path(entry['optimized']['src_dir']) / 'passes/opt/pmux_opt.cc').write_text(
                'algorithm for e\n')
            # 键不同（另一个算法提交 / 不同构建参数）→ 不得命中
            self.assertIsNone(P.find_cached_optimized(cache, P.cache_key(cfg, '0' * 64)))
            # FAILED（半成品）不发布、不命中
            entry['status'] = 'FAILED'
            (reg / 'entry-e.json').write_text(json.dumps(entry))
            self.assertIsNone(P.find_cached_optimized(cache, P.cache_key(cfg, alg_sha)))
            # 二进制被替换 → 不命中
            entry['status'] = 'READY'
            (reg / 'entry-e.json').write_text(json.dumps(entry))
            Path(entry['optimized']['binary']).write_text('replaced-binary')
            self.assertIsNone(P.find_cached_optimized(cache, P.cache_key(cfg, alg_sha)))

    def test_build_failure_records_failed_entry_without_publishing(self):
        import prepare_builtin as P
        from unittest import mock
        with tempfile.TemporaryDirectory() as t:
            base = Path(t)
            cfg = self._cfg(base)
            cache = base / 'cache'
            btree, _otree, alg_sha = self._make_build(base, 'e')
            baseline_spec = {'action': 'reuse', 'src_dir': str(btree), 'src_commit': 'a' * 40,
                             'binary': str(btree / 'build/yosys'),
                             'binary_sha256': hashlib.sha256(b'yosys-e').hexdigest(),
                             'abc': str(btree / 'build/yosys-abc'),
                             'abc_sha256': hashlib.sha256(b'abc-e').hexdigest()}
            with mock.patch('prepare_builtin._copy_source_tree',
                            side_effect=P.BuildError('模拟复制失败')), \
                 mock.patch.object(P, '_current_abc_commit', return_value=None):
                with self.assertRaises(P.BuildError):
                    P._build_sides(cfg, b'alg', alg_sha, cache, need_baseline=False,
                                   baseline_spec=baseline_spec, opt_reuse_spec=None)
            reg = cache / 'registry'
            files = list(reg.glob('*.json'))
            self.assertEqual(len(files), 1)
            failed = json.loads(files[0].read_text())
            self.assertEqual(failed['status'], 'FAILED')
            # 失败条目不被复用（评审判定不会拿到半成品；旧缓存不受影响）
            self.assertIsNone(P.find_cached_optimized(cache, P.cache_key(cfg, alg_sha)))
            # 构建锁在失败后释放
            self.assertFalse((reg / '.build-lock').exists())

    def test_plan_readonly_reports_build_and_blockers(self):
        import prepare_builtin as P
        from unittest import mock
        with tempfile.TemporaryDirectory() as t:
            base = Path(t)
            cfg = self._cfg(base)
            (base / 'yosys-src').mkdir()   # 存在但不是 git 仓库 → 实际阻断项
            with mock.patch.object(P, '_current_abc_commit', return_value=None), \
                 mock.patch('subprocess.Popen',
                            side_effect=AssertionError('plan 不得启动编译进程')):
                plan = P.plan_builtin(cfg, '1' * 64)
            self.assertEqual(plan['baseline']['action'], 'build')
            self.assertEqual(plan['optimized']['action'], 'build')
            self.assertTrue(plan['build_required'])
            self.assertTrue(any(b['item'] == 'source_repo' for b in plan['blocked']))
            # plan 不写任何文件、不创建缓存目录
            self.assertFalse((base / 'cache').exists())


class BuiltinPrepareIntegrationTests(unittest.TestCase):
    """run 流程必须经过自动准备：新工具路径写入本轮 context；准备失败即失败记录。"""

    def _cfg(self, base: Path):
        return {'repo': str(base), 'performance_pairs': 15,
                'flow_version': 'official4-p4', 'suite_version': 'official4-v1',
                'target_commit': 'a' * 40, 'source_sha256': 'e' * 64,
                'project_head': 'b' * 40, 'suite_verified': True,
                'suite_manifest_sha256': '5' * 64,
                'model_version': 'dffeas-v3', 'strategy_version': 'noDF-local-r1',
                'tools': {'yosys': {'sha256': '1' * 64}, 'abc': {'sha256': '2' * 64},
                          'eqy': {'sha256': '3' * 64}, 'z3': {'sha256': '4' * 64}}}

    def test_run_builtin_goes_through_prepare_and_binds_new_paths(self):
        import validate
        from unittest import mock
        with tempfile.TemporaryDirectory() as t:
            base = Path(t)
            round_dir = base / 'round1'
            (round_dir / '01_来源与环境_meta').mkdir(parents=True)
            (round_dir / '03_脚本与插件_runner').mkdir()   # 指纹函数需要目录存在
            fake_builtin = {
                'baseline': {'path': '/fake/base/yosys', 'src_repo': '/fake/base',
                             'src_commit': 'a' * 40, 'binary_sha256': '1' * 64},
                'optimized': {'path': '/fake/opt/yosys', 'src_repo': '/fake/opt',
                              'src_commit': 'a' * 40, 'binary_sha256': '2' * 64,
                              'algorithm_source_path': 'passes/opt/pmux_opt.cc',
                              'algorithm_source_sha256': 'e' * 64,
                              'integration_diff_sha256': 'f' * 64},
                'abc': {'baseline': '/fake/base/yosys-abc', 'optimized': '/fake/opt/yosys-abc'},
                'expected_version': '0.69',
                'integration_evidence': ['passes/opt/pmux_opt.cc'],
            }
            prep = {'builtin': fake_builtin,
                    'record': {'cache_dir': '/fake/cache',
                               'summary': 'baseline 复用；optimized 新建（/fake/build）',
                               'baseline': {'action': 'reuse', 'path': '/fake/base/yosys'},
                               'optimized': {'action': 'built', 'path': '/fake/opt/yosys',
                                             'build_dir': '/fake/build'}},
                    'registry_entry': '/fake/cache/registry/x.json'}
            executed = []

            def fake_execute(root, name, cmd, stages, timeout=10800):
                executed.append((name, tuple(str(c) for c in cmd)))
                stages.append({'name': name, 'state': 'COMPLETED', 'rc': 0})
                return 0

            with mock.patch.object(validate, 'make_round', return_value=round_dir), \
                 mock.patch('prepare_builtin.prepare_builtin', return_value=prep) as prep_mock, \
                 mock.patch.object(validate, 'check_builtin_evidence',
                                   return_value=(True, [], {'ok': True})), \
                 mock.patch.object(validate, 'execute', side_effect=fake_execute), \
                 mock.patch('report.build_builtin_report', return_value='NEEDS_REVIEW'):
                rc = validate.run_builtin(self._cfg(base), b'alg', '测试')
            self.assertEqual(rc, 2)
            # 自动准备被调用，且请求的算法源码哈希正确传入
            self.assertEqual(prep_mock.call_args.kwargs.get('source_sha256'), 'e' * 64)
            # 本轮 context 绑定准备解析出的新工具路径（各阶段统一从此读取）
            ctx = json.loads((round_dir / 'validation_context.json').read_text())
            self.assertEqual(ctx['builtin']['optimized']['path'], '/fake/opt/yosys')
            self.assertEqual(ctx['builtin_prepare']['optimized']['action'], 'built')
            # 阶段调度完整；性能阶段接收 15 对
            names = [n for n, _ in executed]
            self.assertEqual(names, ['flowcheck', 'formal_selfcheck', 'measurement_selfcheck',
                                     'public', 'chains', 'performance'])
            perf_cmd = dict(executed)['performance']
            self.assertIn('--pairs', perf_cmd)
            self.assertIn('15', perf_cmd)

    def test_build_failure_records_status_and_stops(self):
        import validate
        import prepare_builtin as P
        from unittest import mock
        with tempfile.TemporaryDirectory() as t:
            base = Path(t)
            round_dir = base / 'round1'
            (round_dir / '01_来源与环境_meta').mkdir(parents=True)
            err = P.BuildError('模拟构建失败', build_dir=str(base / 'build'), logs={'dir': 'x'})
            with mock.patch.object(validate, 'make_round', return_value=round_dir), \
                 mock.patch('prepare_builtin.prepare_builtin', side_effect=err), \
                 mock.patch('report.build_builtin_build_failed_report',
                            return_value='BUILTIN_BUILD_FAILED') as fail_mock:
                rc = validate.run_builtin(self._cfg(base), b'alg', '测试')
            self.assertEqual(rc, 3)
            stages = json.loads((round_dir / '01_来源与环境_meta/stages.json').read_text())
            self.assertEqual(stages[0]['state'], 'ERROR')
            self.assertIn('工具准备失败', stages[0]['detail'])
            fail_mock.assert_called_once()


class FifteenPairMeasurementTests(unittest.TestCase):
    """十五对统一：样本数判定、失败/超限样本不通过、旧五对轮次仍按旧方案读取。"""

    def _runs(self, pairs, *, bad=False):
        runs = []
        for i in range(pairs):
            tag = 'B→O' if i % 2 == 0 else 'O→B'
            sides = ('baseline', 'optimized') if i % 2 == 0 else ('optimized', 'baseline')
            for side in sides:
                rc = 1 if (bad and side == 'optimized' and i == 0) else 0
                runs.append({'side': side, 'seq': i + 1, 'rc': rc, 'timed_out': False,
                             'stat_exists': True, 'cpu_total_s': 1.0,
                             'tree_rss_peak_kb': 1000, 'order': tag})
        return runs

    def _summary(self, pairs, *, opt=1.0, bad=False):
        return {'case': 'test1', 'pairs': pairs, 'runs': self._runs(pairs, bad=bad),
                'baseline_cpu_total_median': 1.0, 'optimized_cpu_total_median': opt,
                'baseline_tree_rss_peak_median': 1000,
                'optimized_tree_rss_peak_median': 1000}

    def test_fifteen_pair_judgement_and_count_check(self):
        from report import judge_case_performance
        j = judge_case_performance(self._summary(15), pairs=15)
        self.assertTrue(j['valid'])
        self.assertTrue(j['pass'])
        j_bad = judge_case_performance(self._summary(15, bad=True), pairs=15)
        self.assertFalse(j_bad['valid'])
        self.assertFalse(j_bad['pass'])
        j_over = judge_case_performance(self._summary(15, opt=1.06), pairs=15)
        self.assertFalse(j_over['cpu_ok'])
        self.assertFalse(j_over['pass'])
        # 数量不匹配（15 对数据按 5 对口径）→ 无效：不得用新默认值重解释旧样本
        j_mismatch = judge_case_performance(self._summary(15), pairs=5)
        self.assertFalse(j_mismatch['valid'])
        # 旧五对数据按五对判定仍有效（旧轮次读取路径）
        j_old = judge_case_performance(self._summary(5), pairs=5)
        self.assertTrue(j_old['valid'])
        self.assertTrue(j_old['pass'])

    def _write_round(self, root: Path, *, pairs: int):
        BuiltinModeTests()._write_builtin_round(root)
        if pairs == 5:
            return
        ctx = json.loads((root / 'validation_context.json').read_text())
        ctx['performance_pairs'] = pairs
        ctx['performance_scheme'] = 'pmux-perf-15p-v1'
        (root / 'validation_context.json').write_text(json.dumps(ctx) + '\n')
        perf = []
        for case in ('test1', 'test2', 'test3', 'test4'):
            runs = []
            for side in ('baseline', 'optimized'):
                for i in range(pairs):
                    runs.append({'side': side, 'seq': i + 1, 'rc': 0, 'timed_out': False,
                                 'stat_exists': True, 'cpu_total_s': 1.0,
                                 'tree_rss_peak_kb': 1000,
                                 'order': 'B→O' if i % 2 == 0 else 'O→B'})
            perf.append({'case': case, 'pairs': pairs, 'runs': runs,
                         'baseline_cpu_total_median': 1.0, 'optimized_cpu_total_median': 1.0,
                         'baseline_tree_rss_peak_median': 1000,
                         'optimized_tree_rss_peak_median': 1000})
        (root / '09_时间内存开销_performance/round01/performance_summary.json').write_text(
            json.dumps(perf) + '\n')

    def test_builtin_report_fifteen_pairs_and_old_five_pair_compat(self):
        import report as R
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            self._write_round(root, pairs=15)
            status = R.build_builtin_report(root, chain_attempt='run01')
            self.assertEqual(status, R.BUILTIN_COMPLETE_STATUS)
            text = (root / '00_本轮验证结论.md').read_text()
            self.assertIn('每侧 15 次交错运行', text)
            self.assertIn('自动内置准备 + 每例 15 对性能', text)
            manifest = json.loads((root / '11_汇总与证据_summary/manifest.json').read_text())
            self.assertEqual(manifest['performance_scheme'], 'pmux-perf-15p-v1')
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            self._write_round(root, pairs=5)   # 旧口径数据 + 旧 ctx
            status = R.build_builtin_report(root, chain_attempt='run01')
            self.assertEqual(status, R.BUILTIN_COMPLETE_STATUS)
            text = (root / '00_本轮验证结论.md').read_text()
            self.assertIn('每侧 5 次交错运行', text)
            self.assertNotIn('每侧 15 次交错运行', text)

    def test_insert_integration_idempotent_and_reports_mismatch(self):
        import prepare_builtin as P
        cmake = 'yosys_pass(muxpack\n\tmuxpack.cc\n)\nyosys_pass(opt_balance_tree\n\topt_balance_tree.cc\n)\n'
        synth = ('\t\t\trun("opt -nodffe -nosdff");\n\t\t\trun("fsm");\n'
                 '\t\t\trun("opt");\n\t\t\trun("wreduce");\n')
        c1, s1, already = P.insert_integration(cmake, synth)
        self.assertFalse(already)
        self.assertIn(P.CMAKE_BLOCK, c1)
        self.assertIn(P.SYNTH_BLOCK, s1)
        c2, s2, already2 = P.insert_integration(c1, s1)
        self.assertTrue(already2)
        self.assertEqual((c2, s2), (c1, s1))
        with self.assertRaises(P.BuildError):
            P.insert_integration('no anchor\n', s1)
        with self.assertRaises(P.BuildError):
            P.insert_integration(cmake + '#ifdef pmux_opt\n', s1)


if __name__ == '__main__':
    unittest.main()
