"""Evidence classification and reporting regression tests (no EDA execution).

覆盖 noDF 严格转换、联合判定、支持配置预检边界、双侧报告、
V8同次原始证据、构建缓存和新指纹字段（模型/策略版本）。
"""
import io
import json
import contextlib
import hashlib
import os
import subprocess
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parent / 'runner'))
from formal_status import summarize_eqy, check_mapped_model
from function_common import (transform_run_ys, make_probe_ys, classify_proof_text,
                             classify_probe_text, verify_expected_asserts, TransformError)
import function_common as F
from report import build_report, row_functional_ok
import measure_v8 as V8
from test_measure_v8 import raw as v8_raw, fixture_cases


def _v8_context():
    return dict(mode='builtin', performance_scheme=V8.SCHEME, same_run_policy=V8.POLICY,
                result_layout_version='ascii-v1', official_cases=fixture_cases(),
                flow_version='official4-v8', suite_verified=True,
                target_commit='a' * 40, source_sha256='b' * 64,
                policy_source={'path': str(Path(__file__).with_name('POLICY.md'))})


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

    def test_missing_joint_fields_and_bad_merged_probes_cannot_pass(self):
        row = _pass_row('test1', 'c4a_rtl_opt_mapped')
        self.assertTrue(row_functional_ok(row))
        for field in ('verified', 'probes_noDF_all_sat'):
            changed = dict(row)
            changed.pop(field)
            self.assertFalse(row_functional_ok(changed))
        for field, value in (('state', 'FAIL'), ('rc', 1), ('verified', False)):
            self.assertFalse(row_functional_ok(dict(row, **{field: value})))
        merged = _pass_row('test3', 'c4b_rtl_base_mapped')
        self.assertTrue(row_functional_ok(merged))
        for field, value in (('probe', 'PREMISES_UNSAT'), ('assert_cover_ok', False)):
            changed = dict(merged, merged=dict(merged['merged'], **{field: value}))
            self.assertFalse(row_functional_ok(changed))

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
            (root / 'validation_context.json').write_text(json.dumps(_v8_context()))
            self.assertEqual(build_report(root), 'NEEDS_REVIEW')
            manifest = json.loads((root / '11_summary/manifest.json').read_text(encoding='utf-8'))
            self.assertTrue(manifest['gates']['V8身份与规则位置'])
            self.assertFalse(any(passed for name, passed in manifest['gates'].items()
                                 if name != 'V8身份与规则位置'))
            self.assertEqual(manifest['verification_verdict'], 'FAIL')
            self.assertEqual(manifest['category_status']['formal'], 'NOT_RUN')

    def test_review_preserves_original_report(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            (root / '00_report.md').write_text('original evidence')
            (root / 'validation_context.json').write_text(json.dumps(_v8_context()))
            output = root / 'supplement'
            build_report(root, output_root=output, chain_attempt='run02')
            self.assertEqual((root / '00_report.md').read_text(encoding='utf-8'), 'original evidence')
            self.assertTrue((output / '00_report.md').exists())


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

    def test_eqy_work_is_final_contained_ascii_path(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            work = F.eqy_workdir(root, '10_selfcheck/chains/run01/test1/c4a/work')
            self.assertEqual(work, root / '10_selfcheck/chains/run01/test1/c4a/work')
            self.assertTrue(str(work).isascii())
            self.assertFalse(work.exists(), 'path validation must not create evidence')
            with self.assertRaises(ValueError):
                F.eqy_workdir(root, '../../escape')
            with self.assertRaises(ValueError):
                F.eqy_workdir(root, '中文/work')

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
            text = (root / '00_report.md').read_text()
            self.assertIn('BUILTIN_NOT_READY', text)
            self.assertIn('缺项清单', text)
            self.assertIn('后续动作', text)
            self.assertNotIn('FOUR_CASE_PLUGIN_CHECKS_COMPLETE', text)
            manifest = json.loads((root / '11_summary/manifest.json').read_text())
            self.assertEqual(manifest['builtin_execution'], 'NOT_READY')
            self.assertEqual(manifest['official_acceptance'], 'NOT_CLAIMED')


class PerformanceJudgementTests(unittest.TestCase):
    def _summary(self, base_s, opt_s, base_rss, opt_rss, *, bad_run=False, case='test1'):
        rows = [v8_raw('baseline', round(base_s * 10_000_000), int(base_rss)),
                v8_raw('optimized', round(opt_s * 10_000_000), int(opt_rss))]
        for row in rows:
            row['case'] = case
        if bad_run:
            rows[1]['rc'] = 1
        return dict(case=case, performance_scheme=V8.SCHEME, same_run_policy=V8.POLICY,
                    memory_metric='yosys_peak_working_set_bytes',
                    execution_complete=True, samples=rows)

    def test_five_percent_boundary_is_allowed(self):
        from report import judge_case_performance
        j = judge_case_performance(self._summary(1.0, 1.05, 1000, 1050))
        self.assertTrue(j['valid'])
        self.assertAlmostEqual(j['wall_overhead_pct'], 5.0, places=9)
        self.assertEqual(j['wall_5pct'], 'PASS')
        self.assertTrue(j['mem_ok'])
        self.assertTrue(j['pass'])

    def test_above_five_percent_case_fails_even_if_others_pass(self):
        from report import judge_case_performance
        j_bad = judge_case_performance(self._summary(1.0, 1.0501, 10000, 10500, case='test1'))
        j_good = judge_case_performance(self._summary(1.0, 1.0, 10000, 10000, case='test2'))
        self.assertEqual(j_bad['wall_5pct'], 'FAIL')
        self.assertFalse(j_bad['pass'])
        self.assertTrue(j_good['pass'])
        self.assertFalse(all(j['pass'] for j in (j_bad, j_good)))
        j_mem = judge_case_performance(self._summary(1.0, 1.0, 10000, 10501, case='test4'))
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

    def test_two_gib_limit_uses_upstream_exception(self):
        from report import judge_case_performance
        limit = 2 * 1024**3
        self.assertTrue(judge_case_performance(self._summary(1, 1, limit + 1, limit + 2))['limit_ok'])
        self.assertFalse(judge_case_performance(self._summary(1, 1, limit, limit + 1))['limit_ok'])

    def test_windows_peak_working_set_bytes_are_the_memory_metric(self):
        from report import judge_case_performance
        summary = self._summary(1.0, 1.0, 1000, 1040)
        for row in summary['samples']:
            row['tree_rss_peak_kb'] = 999999999
        result = judge_case_performance(summary)
        self.assertTrue(result['valid'])
        self.assertEqual(result['base_memory_bytes'], 1000)
        self.assertAlmostEqual(result['mem_overhead_pct'], 4.0)
        self.assertTrue(result['pass'])


@unittest.skipUnless(os.name == 'nt', 'Windows Job Object implementation')
class WindowsMeasurementTests(unittest.TestCase):
    def test_job_cpu_includes_child_and_peak_memory_is_main_process_only(self):
        import win_measure

        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            native_python = getattr(sys, '_base_executable', sys.executable)
            child = "import time; end=time.perf_counter()+0.65; x=0\nwhile time.perf_counter()<end: x+=1"
            parent = "import subprocess; subprocess.run(" + repr([native_python, '-c', child]) + ",check=True)"
            result = win_measure.run_measured(
                [native_python, '-c', parent], cwd=root,
                log_path=root / 'child.log', timeout_s=15)

            self.assertEqual(result['rc'], 0)
            self.assertGreaterEqual(result['cpu_total_s'], 0.5)
            self.assertGreater(result['yosys_peak_working_set_bytes'], 0)
            self.assertLess(result['yosys_peak_working_set_bytes'], 64 * 1024 * 1024)
            self.assertEqual(result['memory_metric'], 'yosys_peak_working_set_bytes')
            self.assertGreater(result['memory_sample_count'], 0)
            self.assertTrue(result['memory_sampled_before_exit'])

            child_memory = ("import time; a=bytearray(96*1024*1024); "
                            "[a.__setitem__(i,1) for i in range(0,len(a),4096)]; "
                            "time.sleep(0.3)")
            parent_memory = ("import subprocess; a=bytearray(12*1024*1024); "
                             "[a.__setitem__(i,1) for i in range(0,len(a),4096)]; "
                             "subprocess.run(" + repr([native_python, '-c', child_memory]) + ",check=True)")
            memory = win_measure.run_measured(
                [native_python, '-c', parent_memory], cwd=root,
                log_path=root / 'child-memory.log', timeout_s=15)
            self.assertEqual(memory['rc'], 0)
            self.assertGreater(memory['yosys_peak_working_set_bytes'], 12 * 1024 * 1024)
            self.assertLess(memory['yosys_peak_working_set_bytes'], 70 * 1024 * 1024)
            self.assertTrue(memory['memory_sampled_before_exit'])

    def test_job_timeout_and_nonzero_exit_are_retained(self):
        import win_measure

        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            timeout = win_measure.run_measured(
                [getattr(sys, '_base_executable', sys.executable), '-c', 'import time; time.sleep(10)'],
                cwd=root, log_path=root / 'timeout.log', timeout_s=0.4)
            failed = win_measure.run_measured(
                [getattr(sys, '_base_executable', sys.executable), '-c', 'raise SystemExit(7)'],
                cwd=root, log_path=root / 'nonzero.log', timeout_s=10)

            self.assertTrue(timeout['timed_out'])
            self.assertEqual(timeout['rc'], 124)
            self.assertTrue(failed['metrics_valid'])
            self.assertEqual(failed['rc'], 7)
            self.assertGreater(failed['yosys_peak_working_set_bytes'], 0)


class SelfcheckCacheTests(unittest.TestCase):

    def test_v8_measurement_cache_requires_bound_unchanged_evidence(self):
        import validate
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fp = dict(self._fp(), performance_scheme=validate.SAME_RUN_SCHEME)
            path = root / 'cache.json'
            cache = validate.load_selfcheck_cache(path)
            with self.assertRaisesRegex(ValueError, 'evidence missing'):
                validate.update_selfcheck_cache(path, cache, fp, 'measurement_selfcheck', True, root)
            proof = root / '09_performance/selftest/selftest_results.json'
            proof.parent.mkdir(parents=True)
            proof.write_text(json.dumps({'selftest_ok': True, 'method': V8.METHOD}), encoding='utf-8')
            validate.update_selfcheck_cache(path, cache, fp, 'measurement_selfcheck', True, root)
            saved = validate.load_selfcheck_cache(path)
            self.assertTrue(validate.cache_entry_valid(saved, 'measurement_selfcheck', fp))
            self.assertFalse(validate.cache_entry_valid(saved, 'measurement_selfcheck',
                                                       dict(fp, runner_sha256={'x': 'changed'})))
            original = proof.read_bytes()
            proof.write_bytes(b'changed evidence')
            self.assertFalse(validate.cache_entry_valid(saved, 'measurement_selfcheck', fp))
            proof.write_bytes(original)
            proof.unlink()
            self.assertFalse(validate.cache_entry_valid(saved, 'measurement_selfcheck', fp))
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
                           ('strategy_version', 'DF'),
                           ('official_cases', fixture_cases()),
                           ('official_cases_sha256', 'CHANGED')):
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
            prefix = '2026-09-24_v8_same_run_abc1234'
            r1 = validate.next_round_dir(parent, prefix)
            r2 = validate.next_round_dir(parent, prefix)
            self.assertEqual(r1.name, prefix + '_r01')
            self.assertEqual(r2.name, prefix + '_r02')


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






class BuiltinModeTests(unittest.TestCase):
    """内置模式：计划路由、flowcheck 位置判定、指纹绑定、缺证明阻断、标志隔离。"""

    def test_builtin_stage_sets_match_and_no_plugin_flags(self):
        import validate
        import integration_profiles as I
        plan = validate.builtin_stage_plan({'performance_scheme': validate.SAME_RUN_SCHEME})
        self.assertEqual(tuple(n for n, _, _ in plan),
                         ('formal_selfcheck', 'measurement_selfcheck', 'performance',
                          'flowcheck', 'public', 'chains'))
        self.assertEqual(set(validate.BUILTIN_STAGES), {'build'} | {n for n, _, _ in plan})
        self.assertEqual(I.CHAINS, ('c4a_rtl_opt_mapped', 'c4b_rtl_base_mapped'))
        for name, script, args in plan:
            self.assertNotIn('-m', args)
        chains_args = dict((n, a) for n, _, a in plan)['chains']
        self.assertIn('--input-mode', chains_args)
        self.assertIn('builtin', chains_args)
        self.assertEqual(validate.BUILTIN_CACHED_STAGES,
                         ('formal_selfcheck', 'measurement_selfcheck'))
        for banned in ('regression', 'regression_eqy', 'h2', 'multidriver', 'scale'):
            self.assertNotIn(banned, [n for n, _, _ in plan])

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


    def test_resource_counts_include_vector_and_scalar_inverters(self):
        import builtin_common as B

        stat = {"design": {
            "num_ports": 9,
            "num_port_bits": 18,
            "num_cells_by_type": {
                "cycloneiv_lcell_comb": 5,
                "$not": 1,
                "$_NOT_": 2,
                "dffeas": 2,
            },
        }}
        mapped = (
            "module \\top\n"
            "  cell $not vector_not\n"
            "    parameter \\Y_WIDTH 4\n"
            "  end\n"
            "  cell \\$_NOT_ scalar_not_a\n"
            "  end\n"
            "  cell \\$_NOT_ scalar_not_b\n"
            "  end\n"
            "end\n"
        )

        result = B.parse_resource_counts(stat, mapped, "top")

        self.assertEqual(result["lut_count"], 5)
        self.assertEqual(result["inverter_count"], 6)
        self.assertEqual(result["logic_units"], 11)
        self.assertEqual(result["dff_count"], 2)
        self.assertEqual(result["io_ports"], 9)
        self.assertEqual(result["io_bits"], 18)

    def test_unclassified_cell_blocks_resource_conclusion(self):
        import builtin_common as B

        stat = {"design": {"num_cells_by_type": {"$_AND_": 1}}}
        with self.assertRaisesRegex(ValueError, "unclassified"):
            B.parse_resource_counts(stat, "module \\top\nend\n", "top")

    def test_abc9_required(self):
        import builtin_common as B
        self.assertTrue(B.abc9_mapping_ok('2. Executing ABC9 pass.\n2.1. Executing ABC9.'))
        self.assertFalse(B.abc9_mapping_ok('2. Executing ABC pass.'))

    def test_other_resources(self):
        import builtin_common as B
        result = B.compare_other_resources({'dffeas': 2, 'foo': 1}, {'dffeas': 2, 'foo': 2})
        self.assertFalse(result['ok'])
        self.assertIn('foo', result['increases'])

    def test_post_abc_rejects_final_netlist(self):
        from formal_status import check_post_abc_model
        with tempfile.TemporaryDirectory() as temp:
            netlist = Path(temp) / 'a.il'
            netlist.write_text(_lcell_il())
            with self.assertRaises(ValueError):
                check_post_abc_model(netlist, 'top')

    def test_new_resource_type_detected(self):
        import builtin_common as B
        self.assertFalse(B.compare_other_resources({}, {'io_cell': 1})['ok'])
        self.assertTrue(B.compare_other_resources({'dffeas': 2}, {'dffeas': 1})['ok'])

    def test_resource_comparison_uses_logic_units_and_checks_all_other_resources(self):
        import builtin_common as B

        base = {"logic_units": 10, "dff_count": 2, "io_ports": 4, "io_bits": 8,
                "other_cell_types": {"VCC": 1}}
        optimized = {"logic_units": 8, "dff_count": 2, "io_ports": 4, "io_bits": 8,
                     "other_cell_types": {"VCC": 1}}

        result = B.compare_resource_counts(base, optimized)

        self.assertEqual(result["logic_reduction_pct"], 20.0)
        self.assertTrue(result["resource_checks_ok"])
        optimized["io_bits"] = 9
        self.assertFalse(B.compare_resource_counts(base, optimized)["resource_checks_ok"])
        optimized["io_bits"] = 8
        optimized["other_cell_types"]["VCC"] = 2
        self.assertFalse(B.compare_resource_counts(base, optimized)["resource_checks_ok"])

    def test_v8_report_uses_inverter_adjusted_average_and_requires_full_resources(self):
        import report as R
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            self._write_builtin_round(root, base_luts=20, opt_luts=15,
                                      base_not_bits=1, opt_not_bits=2)
            status = R.build_builtin_report(root, chain_attempt='run01')
            manifest = json.loads((root / '11_summary/manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(status, 'BUILTIN_SUITE_LOCAL_ACCEPTANCE_COMPLETE')
            self.assertTrue(manifest['gates']['最终资源统计与同次来源完整'])
            self.assertAlmostEqual(manifest['mean_logic_reduction_pct'], 4 / 21 * 100)
            self.assertEqual(manifest['resources']['test1']['baseline']['logic_units'], 21)
            self.assertEqual(manifest['resources']['test1']['optimized']['logic_units'], 17)
            self.assertEqual(manifest['category_status']['formal'], 'PASS')
            stat = root / '05_public/round01/test1/optimized/stat.json'
            stat.unlink()
            self.assertEqual(R.build_builtin_report(root), 'NEEDS_REVIEW')
            manifest = json.loads((root / '11_summary/manifest.json').read_text(encoding='utf-8'))
            self.assertFalse(manifest['gates']['最终资源统计与同次来源完整'])
            self.assertEqual(manifest['overall_verdict'], 'FAIL')

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
            f.write_bytes(text.encode('utf-8'))
        run("-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
        run("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "c1")

    def test_builtin_precheck_fingerprint_binding_blocks(self):
        """不同算法/二进制指纹必须在启动任何进程前阻断（模拟检查）。"""
        import validate
        with tempfile.TemporaryDirectory() as t:
            base = Path(t)
            brepo = base / 'baseline-src'
            self._git_init(brepo, {'kernel/x.cc': 'int x;\n',
                                  'kernel/driver.cc': 'int main() {}\n'})
            orepo = base / 'optimized-src'
            self._git_init(orepo, {'kernel/x.cc': 'int x;\n',
                                  'kernel/driver.cc': 'int main() {}\n'})
            alg = "// pmux algorithm\nint pmux;\n"
            (orepo / 'passes/opt').mkdir(parents=True, exist_ok=True)
            (orepo / 'passes/opt/pmux_opt.cc').write_bytes(alg.encode('utf-8'))
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
                (bdir / 'share/intel/cycloneiv/cells_map.v').write_text('// map\n')
                (bdir / 'share/intel/cycloneiv/cells_sim.v').write_text('// c\n')
                (bdir / 'share/intel/common').mkdir(parents=True)
                (bdir / 'share/intel/common/m9k_bb.v').write_text('// m\n')
            cfg = {'performance_scheme': V8.SCHEME,
                   'builtin': {
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

    def _write_builtin_round(self, root: Path, *, include_chains=True,
                             base_luts=100, opt_luts=80, base_not_bits=0, opt_not_bits=0):
        ctx = _v8_context()
        def save(rel, value):
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(value), encoding='utf-8')
        ctx['builtin'] = {'integration_id': 'pmux-opt-inline-p3-v1'}
        for side in ('baseline', 'optimized'):
            ctx['builtin'][side] = {'binary_sha256': V8.sha(sys.executable)}
        save('validation_context.json', ctx)
        save('01_meta/stages.json', [dict(name=n, state='COMPLETED', rc=0) for n in
             ('build', 'formal_selfcheck', 'measurement_selfcheck', 'performance', 'flowcheck', 'public', 'chains')])
        save('01_meta/builtin_evidence.json', {'ok': True, 'missing': []})
        flows = {}
        for case in (c['id'] for c in fixture_cases()):
            rtl = root / f'02_assets/tree/pmux_case/competition_case/{case}/{case}.v'
            rtl.parent.mkdir(parents=True, exist_ok=True)
            rtl.write_text('module ' + case + '; endmodule', encoding='utf-8')
            flows[case] = f'read_verilog -sv "{rtl.as_posix()}"\n'
        def execute(command, *, cwd, log_path, **kwargs):
            folder = Path(cwd); case = folder.parent.name; side = folder.name
            luts = base_luts if side == 'baseline' else opt_luts
            inv = base_not_bits if side == 'baseline' else opt_not_bits
            cells = {'cycloneiv_lcell_comb': luts, 'dffeas': 10}
            mapped = 'module \\' + case + '\n'
            if inv:
                cells['$not'] = 1
                mapped += '  cell $not inverter\n    parameter \\Y_WIDTH ' + str(inv) + '\n  end\n'
            mapped += 'end\n'
            stat = {'design': {'num_ports': 4, 'num_port_bits': 8,
                              'num_cells': luts + 10 + bool(inv), 'num_cells_by_type': cells}}
            (folder / 'mapped.il').write_text(mapped, encoding='utf-8')
            (folder / 'post_abc.il').write_text('module \\' + case + '\nend\n', encoding='utf-8')
            for name in ('stat.json', 'post_abc_stat.json'):
                (folder / name).write_text(json.dumps(stat), encoding='utf-8')
            log = ('2.15. Executing OPT pass.\n' +
                   ('2.16. Executing PMUX_OPT pair-swap optimization.\n' if side == 'optimized' else '') +
                   '2.17. Executing WREDUCE pass.\n2.37. Executing ABC9 pass.\n3. Executing RTLIL backend.\n')
            Path(log_path).write_text(log, encoding='utf-8')
            return dict(v8_raw(side), powershell_path=sys.executable,
                        powershell_sha256=V8.sha(sys.executable))
        with contextlib.redirect_stdout(io.StringIO()):
            rc = V8.run(dict(ctx, wall_time_tool={'path': sys.executable}), root,
                        {'baseline': Path(sys.executable), 'optimized': Path(sys.executable)},
                        flows, execute=execute)
        self.assertEqual(rc, 0)
        save('04_flowcheck/builtin_run01/builtin_flowcheck.json',
             {'all_ok': True, 'analysis_only': True})
        public = []
        proofs = []
        for case in (c['id'] for c in fixture_cases()):
            row = {'case': case}
            for side, chain in (('optimized', 'c4a_rtl_opt_mapped'), ('baseline', 'c4b_rtl_base_mapped')):
                folder = root / '05_public/round01' / case / side
                sample = json.loads((folder / 'measure_result.json').read_text(encoding='utf-8'))
                luts = base_luts if side == 'baseline' else opt_luts
                inv = base_not_bits if side == 'baseline' else opt_not_bits
                cells = {'cycloneiv_lcell_comb': luts, 'dffeas': 10}
                if inv:
                    cells['$not'] = 1
                row[side + '_sample_id'] = sample['sample_id']
                row[side + '_resources'] = dict(lut_count=luts, comb=luts, inverter_count=inv,
                    logic_units=luts + inv, dff_count=10, dff_cell_types={'dffeas': 10},
                    io_ports=4, io_bits=8, io_cell_types={}, other_cell_types={}, cell_types=cells)
                proof = _pass_row(case, chain)
                proof.update(formal_netlist_stage='post_abc',
                    formal_netlist_sha256=sample['artifacts']['post_abc.il']['sha256'])
                proofs.append(proof)
            public.append(row)
        save('05_public/round01/summary.json', {'cases': public})
        if include_chains:
            save('10_selfcheck/chains/run01/chains_summary.json', proofs)

    def test_builtin_report_blocks_without_chains_and_completes(self):
        import report as R
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            self._write_builtin_round(root, include_chains=False)
            status = R.build_builtin_report(root, chain_attempt='run01')
            self.assertEqual(status, 'NEEDS_REVIEW')
            manifest = json.loads((root / '11_summary/manifest.json').read_text(encoding='utf-8'))
            self.assertFalse(manifest['gates']['原始RTL功能证明与同次postABC哈希绑定'])
            self.assertEqual(manifest['category_status']['formal'], 'NOT_RUN')
            self.assertNotEqual(manifest['verification_verdict'], 'PASS')
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            self._write_builtin_round(root, include_chains=True)
            status = R.build_builtin_report(root, chain_attempt='run01')
            self.assertEqual(status, 'BUILTIN_SUITE_LOCAL_ACCEPTANCE_COMPLETE')
            manifest = json.loads((root / '11_summary/manifest.json').read_text(encoding='utf-8'))
            self.assertTrue(all(manifest['gates'].values()), manifest['reasons'])
            self.assertEqual(manifest['verification_verdict'], 'PASS')
            self.assertEqual(manifest['official_acceptance'], 'NOT_CLAIMED')
            text = (root / '00_report.md').read_text(encoding='utf-8')
            self.assertIn('V8', text)
            self.assertIn('工程套件验证', text)

    def test_report_rejects_missing_ledger_and_unbound_proof(self):
        import report as R
        for fault in ('missing_ledger', 'unverified_proof', 'bad_merged_probe', 'wrong_netlist_hash'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                self._write_builtin_round(root)
                if fault == 'missing_ledger':
                    (root / '09_performance/round01/synthesis_ledger.json').unlink()
                else:
                    chain_file = root / '10_selfcheck/chains/run01/chains_summary.json'
                    rows = json.loads(chain_file.read_text(encoding='utf-8'))
                    if fault == 'unverified_proof':
                        rows[0].pop('verified')
                    elif fault == 'bad_merged_probe':
                        next(r for r in rows if r['case'] == 'test3')['merged']['probe'] = 'PREMISES_UNSAT'
                    else:
                        rows[0]['formal_netlist_sha256'] = '0' * 64
                    chain_file.write_text(json.dumps(rows), encoding='utf-8')
                self.assertEqual(R.build_builtin_report(root), 'NEEDS_REVIEW')
                manifest = json.loads((root / '11_summary/manifest.json').read_text(encoding='utf-8'))
                self.assertNotEqual(manifest['verification_verdict'], 'PASS')
                gate = ('正式综合完整且无补跑' if fault == 'missing_ledger'
                        else '原始RTL功能证明与同次postABC哈希绑定')
                self.assertFalse(manifest['gates'][gate])



class PrepareBuiltinCacheTests(unittest.TestCase):

    def test_v8_cache_key_retains_null_runtime_patch_identity(self):
        import prepare_builtin as P
        with tempfile.TemporaryDirectory() as temp:
            cfg = self._cfg(Path(temp))
            cfg.update(performance_scheme=V8.SCHEME, same_run_policy=V8.POLICY)
            key = P.cache_key(cfg, '1' * 64)
            self.assertIn('runtime_patch', key)
            self.assertIsNone(key['runtime_patch'])
            without_field = dict(key)
            without_field.pop('runtime_patch')
            self.assertTrue(P.reference_key_matches(without_field, key))
            patched = dict(key, runtime_patch={'sha256': 'old'})
            self.assertFalse(P.reference_key_matches(patched, key))
            self.assertFalse(P.reference_key_matches(patched, patched))

    def test_nonnull_runtime_patch_entry_is_never_reused(self):
        import prepare_builtin as P
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cfg = self._cfg(root)
            entry = self._entry(root)
            entry['key'] = P.cache_key(cfg, entry['optimized']['algorithm_source_sha256'])
            self.assertTrue(P.verify_entry_files(entry)[0])
            for location in ('key', 'baseline', 'optimized'):
                with self.subTest(location=location):
                    changed = json.loads(json.dumps(entry))
                    changed[location]['runtime_patch'] = {'sha256': 'old'}
                    valid, reasons = P.verify_entry_files(changed)
                    self.assertFalse(valid)
                    self.assertTrue(reasons)

    def test_import_prebuilt_rejects_existing_patched_ready_entry(self):
        import prepare_builtin as P
        from unittest import mock
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cfg = self._cfg(root)
            entry = self._entry(root)
            entry['key'] = P.cache_key(cfg, entry['optimized']['algorithm_source_sha256'])
            registry = Path(cfg['builtin']['cache_dir']) / 'registry'
            registry.mkdir(parents=True)
            for location in ('key', 'baseline', 'optimized'):
                with self.subTest(location=location):
                    changed = json.loads(json.dumps(entry))
                    changed[location]['runtime_patch'] = {'sha256': 'old'}
                    (registry / 'existing.json').write_text(json.dumps(changed), encoding='utf-8')
                    with mock.patch.object(P.subprocess, 'run',
                                           side_effect=AssertionError('rejected entry must not run a tool')), \
                         mock.patch.object(P.subprocess, 'Popen',
                                           side_effect=AssertionError('rejected entry must not start a process')):
                        with self.assertRaises(P.BuildError):
                            P.import_prebuilt(cfg, root, name=entry['name'])
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

    """自动内置准备：缓存键绑定、命中核验、失败不发布、plan 只读（不编译、不写文件）。"""

    def test_windows_source_copy_ignores_only_root_build_directory(self):
        import prepare_builtin as P
        with tempfile.TemporaryDirectory() as t:
            root = Path(t) / 'source'
            (root / 'build').mkdir(parents=True)
            (root / 'build/cache.txt').write_text('generated')
            (root / 'pyosys/build').mkdir(parents=True)
            (root / 'pyosys/build/local_backend.py').write_text('tracked source')
            (root / 'submodule/build').mkdir(parents=True)
            (root / 'submodule/build/tracked.txt').write_text('tracked submodule source')
            copied = Path(t) / 'copy'
            P.shutil.copytree(root, copied, ignore=P._ignore_root_build(root))
            self.assertFalse((copied / 'build').exists())
            self.assertEqual((copied / 'pyosys/build/local_backend.py').read_text(encoding='utf-8'), 'tracked source')
            self.assertEqual((copied / 'submodule/build/tracked.txt').read_text(encoding='utf-8'),
                             'tracked submodule source')

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
        (otree / 'passes/opt/pmux_opt.cc').write_bytes(alg.encode('utf-8'))
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

    def test_windows_build_products_use_exe_suffix_and_msys_root(self):
        import prepare_builtin as P
        self.assertEqual(str(P._build_product_path(Path('C:/cache/side'), 'yosys', windows=True)),
                         str(Path('C:/cache/side') / 'build' / 'yosys.exe'))
        self.assertEqual(str(P._build_product_path(Path('C:/cache/side'), 'yosys-abc', windows=False)),
                         str(Path('C:/cache/side') / 'build' / 'yosys-abc'))
        if os.name == 'nt':
            from unittest import mock
            cfg = {'tools': {'bash': {'path': 'C:/tools/msys64/usr/bin/bash.exe'}}}
            env = P._build_env(cfg)
            self.assertIn(str(Path('C:/tools/msys64/mingw64/bin')), env['PATH'].split(os.pathsep))
            self.assertIn(str(Path('C:/tools/msys64/usr/bin')), env['PATH'].split(os.pathsep))
            self.assertEqual(env['MSYSTEM'], 'MINGW64')
            with mock.patch.dict(P.os.environ, {'PATH': 'C:/Windows/Git/cmd;C:/Windows/System32'}):
                ordered = P._build_env(cfg)['PATH'].split(os.pathsep)
            self.assertLess(ordered.index(str(Path('C:/tools/msys64/usr/bin'))),
                            ordered.index('C:/Windows/Git/cmd'))


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
            (Path(entry['optimized']['src_dir']) / 'passes/opt/pmux_opt.cc').write_bytes(
                b'tampered')
            self.assertIsNone(P.find_cached_optimized(cache, P.cache_key(cfg, alg_sha)))
            (Path(entry['optimized']['src_dir']) / 'passes/opt/pmux_opt.cc').write_bytes(
                b'algorithm for e\n')
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

    def test_unpatched_reference_accepts_git_stripped_final_newline(self):
        import prepare_builtin as P
        from unittest import mock
        with tempfile.TemporaryDirectory() as t:
            base = Path(t)
            commit = 'a' * 40
            roots = {side: base / side for side in ('baseline', 'optimized')}
            for root in roots.values():
                (root / 'kernel').mkdir(parents=True)
                (root / 'kernel' / 'driver.cc').write_text('int main() {}\n')
            tracked = {'passes/opt/CMakeLists.txt', 'techlibs/intel/synth_intel.cc'}
            status = (' M passes/opt/CMakeLists.txt\n'
                      ' M techlibs/intel/synth_intel.cc\n'
                      '?? passes/opt/pmux_opt.cc')

            def fake_git(repo, *args):
                side = Path(repo).name
                if args == ('rev-parse', 'HEAD'):
                    return commit
                if args == ('show', 'HEAD:kernel/driver.cc'):
                    return 'int main() {}'  # prepare_builtin._git strips the final newline
                if args == ('diff',):
                    return ''
                if args == ('status', '--porcelain'):
                    # _git() strips the first row's leading status column.
                    return '' if side == 'baseline' else status.strip()
                if args == ('diff', '--name-only'):
                    return '\n'.join(sorted(tracked))
                if args == ('diff', '--', 'passes/opt/CMakeLists.txt',
                            'techlibs/intel/synth_intel.cc'):
                    return 'expected integration diff'
                raise AssertionError((side, args))

            entry = {
                'status': 'READY',
                'abc_source_commit': 'b' * 40,
                'baseline': {'src_dir': str(roots['baseline']), 'src_commit': commit},
                'optimized': {'src_dir': str(roots['optimized']), 'src_commit': commit,
                              'integration_diff_sha256': 'f' * 64},
            }
            cfg = {'builtin': {'source_commit': commit}}
            with mock.patch.object(P, '_git', side_effect=fake_git), \
                 mock.patch.object(P, '_current_abc_commit', return_value='b' * 40), \
                 mock.patch.object(P, '_check_integration_diff', return_value='f' * 64):
                self.assertTrue(P._verify_unpatched_reference(entry, cfg))

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
            failed = json.loads(files[0].read_text(encoding='utf-8'))
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


class WindowsConfigTests(unittest.TestCase):

    def _package_fixture(self, root):
        names = ('validate.py', 'report.py', 'report_v9.py', 'validate_windows_v9.cmd',
                 'config.windows.v9.json', 'POLICY.md', 'README.md', 'SKILL.md',
                 'test_measure_v8.py', 'test_local_lut_integration.py', 'test_memory_exit.py',
                 'test_validation.py', 'test_windows_hardening.py')
        package = Path(__file__).parent
        files = {}
        for name in names:
            files[name] = (package / name).read_bytes()
        files['runner/probe.py'] = b'pass\n'
        files['suite-official/probe.json'] = b'{}\n'
        manifest = {}
        for name, contents in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(contents)
            manifest[name] = hashlib.sha256(contents.replace(b'\r\n', b'\n')).hexdigest()
        (root / 'PACKAGE_SHA256.json').write_text(json.dumps(manifest), encoding='utf-8')
        return manifest

    def test_package_manifest_rejects_missing_required_root_even_if_unregistered(self):
        import validate as V
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._package_fixture(root)
            V.verify_package_manifest(root)
            (root / 'validate.py').unlink()
            manifest.pop('validate.py')
            (root / 'PACKAGE_SHA256.json').write_text(json.dumps(manifest), encoding='utf-8')
            with self.assertRaises(ValueError):
                V.verify_package_manifest(root)

    def test_package_manifest_rejects_unregistered_root_and_runner_shared_object(self):
        import validate as V
        for relative in ('unregistered.md', 'runner/unregistered.so'):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                self._package_fixture(root)
                (root / relative).write_bytes(b'unregistered')
                with self.assertRaises(ValueError):
                    V.verify_package_manifest(root)

    def test_package_manifest_rejects_missing_or_changed_registered_file(self):
        import validate as V
        for missing in (True, False):
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                self._package_fixture(root)
                target = root / 'runner/probe.py'
                if missing:
                    target.unlink()
                else:
                    target.write_bytes(b'changed\n')
                with self.assertRaises(ValueError):
                    V.verify_package_manifest(root)
    def test_crlf_checkout_is_verified_and_frozen_as_lf(self):
        import validate as V
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / 'input.v'
            f.write_bytes(b'module top;\r\nendmodule\r\n')
            expected = hashlib.sha256(b'module top;\nendmodule\n').hexdigest()
            self.assertEqual(V.digest_package_file(f), expected)
            self.assertTrue(V.normalize_text_file(f))
            self.assertEqual(f.read_bytes(), b'module top;\nendmodule\n')
            self.assertEqual(V.digest(f), expected)

    def test_tool_data_filter_matches_windows_paths(self):
        import validate as V
        cfg = {
            'tool_data': [
                {'path': 'C:/tools/yosys/share/yosys/abc9_map.v', 'sha256': 'a'},
                {'path': 'C:/tools/yosys/share/yosys/intel/cycloneiv/cells_map.v', 'sha256': 'b'},
                {'path': 'C:/tools/yosys/share/yosys/xilinx/cells_map.v', 'sha256': 'c'},
            ],
            'tool_data_fourcase_filter': {
                'include_subpaths': ['/share/yosys/intel/'],
                'direct_share_files': ['abc9_map.v'],
            },
        }
        selected = V.selected_tool_data(cfg)
        self.assertEqual([x['sha256'] for x in selected], ['a', 'b'])

    def test_yosys_intel_data_root_supports_install_and_build_layouts(self):
        import validate as V
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            install = root / 'install'
            binary = install / 'bin' / 'yosys.exe'
            data = install / 'share' / 'yosys' / 'intel' / 'cycloneiv'
            data.mkdir(parents=True)
            (data / 'cells_map.v').write_text('module x; endmodule\n')
            self.assertEqual(V.yosys_share_root(binary), data.parents[1])
            build = root / 'source' / 'build'
            build_data = build / 'share' / 'intel' / 'cycloneiv'
            build_data.mkdir(parents=True)
            (build_data / 'cells_map.v').write_text('module x; endmodule\n')
            self.assertEqual(V.yosys_share_root(build / 'yosys.exe'), build / 'share')


class InPlaceEqyEvidenceTests(unittest.TestCase):
    """Proof setup writes only to the final case directory, including failures."""

    def _load_selfcheck(self, root):
        import importlib.util
        from types import SimpleNamespace
        from unittest import mock
        context = SimpleNamespace(ASCII_BRIDGE=root / '_eval_ascii_forbidden',
                                  TOOL_YOSYS='fixture-yosys', EQY_ABC='fixture-abc',
                                  TOOL_EQY='fixture-eqy')
        spec = importlib.util.spec_from_file_location(
            '_selfcheck_inplace_fixture', Path(__file__).parent / 'runner/run_selfcheck.py')
        module = importlib.util.module_from_spec(spec)
        with mock.patch.dict(sys.modules, {'p3_common': context}):
            spec.loader.exec_module(module)
        return module

    def test_setup_fail_timeout_and_interrupt_preserve_partial_work_in_place(self):
        from unittest import mock
        for outcome in (2, 124, 'interrupt'):
            with self.subTest(outcome=outcome), tempfile.TemporaryDirectory() as t:
                root = Path(t)
                module = self._load_selfcheck(root)
                case = root / '10_selfcheck/attempt01/rtl_positive'
                case.mkdir(parents=True)
                observed = []

                def setup(config, work, log, **kwargs):
                    observed.append(work)
                    work.mkdir(parents=True)
                    (work / 'partial.log').write_text('partial proof evidence')
                    log.write_text('partial setup evidence')
                    if outcome == 'interrupt':
                        raise KeyboardInterrupt()
                    return outcome

                with mock.patch.object(module.F, 'setup_eqy', side_effect=setup):
                    if outcome == 'interrupt':
                        with self.assertRaises(KeyboardInterrupt):
                            module.run_check({'kind': 'rtl', 'top': 'top'},
                                             root / 'gold.v', root / 'gate.v', root / 'model.v', case)
                    else:
                        result = module.run_check({'kind': 'rtl', 'top': 'top'},
                                                  root / 'gold.v', root / 'gate.v', root / 'model.v', case)
                        self.assertEqual(result['state'], 'TOOL_OR_CONFIG_ERROR')
                self.assertEqual(observed, [case / 'work'])
                self.assertEqual((case / 'work/partial.log').read_text(), 'partial proof evidence')
                self.assertTrue((case / 'setup.log').exists())
                self.assertFalse(any(p.name.startswith('_eval_') for p in root.rglob('*')))

    def test_successful_proof_keeps_transforms_and_probes_in_final_work(self):
        from unittest import mock
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            module = self._load_selfcheck(root)
            case = root / '10_selfcheck/attempt01/rtl_positive'
            case.mkdir(parents=True)
            observed = []

            def setup(config, work, log, **kwargs):
                observed.append(work)
                strategy = work / 'strategies/top/simple'
                strategy.mkdir(parents=True)
                (strategy / 'run.ys').write_text(TransformAndVerdictTests.SAMPLE)
                log.write_text('setup complete')
                return 0

            def yosys(script, log, cwd, **kwargs):
                text = ('Trying induction with length 1\nBase case for induction length 1 proven\n'
                        'Induction step proven: SUCCESS!\nImport proof for assert: \\top.ok\n'
                        if script.name == 'run.ys' else 'SAT solving finished - model found:\n')
                log.write_text(text)
                return 0

            with mock.patch.object(module.F, 'setup_eqy', side_effect=setup), \
                 mock.patch.object(module.F, 'run_yosys_script', side_effect=yosys):
                result = module.run_check({'kind': 'rtl', 'top': 'top'},
                                          root / 'gold.v', root / 'gate.v', root / 'model.v', case)
            self.assertEqual(observed, [case / 'work'])
            self.assertEqual(result['partitions']['top']['proof']['state'], 'PASS')
            strategy = case / 'work/strategies/top/simple'
            self.assertEqual((strategy / 'run.ys.eqy-generated').read_text(), TransformAndVerdictTests.SAMPLE)
            self.assertNotIn(' -set-def-formal', (strategy / 'run.ys').read_text())
            self.assertTrue((strategy / 'status_noDF.json').is_file())
            self.assertFalse(any(p.name.startswith('_eval_') for p in root.rglob('*')))

    def test_chains_keeps_eight_bound_inputs_and_merged_work_in_place(self):
        import importlib.util
        import shutil
        from types import SimpleNamespace
        from unittest import mock
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            runner = Path(__file__).parent / 'runner'
            tree = root / '02_assets/tree'
            for case in (c['id'] for c in fixture_cases()):
                rtl = tree / f'pmux_case/competition_case/{case}/{case}.v'
                rtl.parent.mkdir(parents=True)
                rtl.write_text(f'module {case}; endmodule\n')
                for side in ('baseline', 'optimized'):
                    il = root / '05_public/round01' / case / side / 'post_abc.il'
                    il.parent.mkdir(parents=True)
                    il.write_text(_dffeas_il(top=case))
            bridge = root / '_eval_ascii_forbidden'

            def legacy_stage(src, relative):
                target = bridge / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, target)
                return target

            def refuse(path):
                if path.exists():
                    raise FileExistsError(str(path))

            context = SimpleNamespace(ROUND_DIR=root, REPO=root, TREE=tree, SCRIPT_DIR=runner,
                ASCII_BRIDGE=bridge, stage_to_ascii_bridge=legacy_stage,
                TOOL_YOSYS='fixture-yosys', EQY_ABC='fixture-abc', TOOL_EQY='fixture-eqy',
                CONTEXT={'official_cases': fixture_cases(), 'builtin': {'integration_id': 'pmux-opt-inline-p3-v1'}},
                sha256_file=F.sha256_file, rel=lambda p: str(p), refuse_overwrite=refuse)
            spec = importlib.util.spec_from_file_location('_chains_inplace_fixture', runner / 'run_eqy_chains.py')
            module = importlib.util.module_from_spec(spec)
            with mock.patch.dict(sys.modules, {'p3_common': context}):
                spec.loader.exec_module(module)
            observed, merged = [], []

            def setup(config, work, log, **kwargs):
                observed.append((config, work))
                work.mkdir(parents=True)
                (work / 'partial.log').write_text('partition evidence')
                log.write_text('setup evidence')
                return 0

            def parts(work, **kwargs):
                failed = 'test3' in work.parts
                return {'partition': {'proof': {'state': 'FAIL' if failed else 'PASS'},
                    'probes': {'noDF': {'verdict': 'PREMISES_SAT'},
                               'DF': {'verdict': 'PREMISES_UNSAT'}}}}

            def merge(case, cdir, *, workdir, merged_dir, **kwargs):
                merged.append((cdir, workdir, merged_dir))
                merged_dir.mkdir()
                (merged_dir / 'merged.log').write_text('merged evidence')
                return {'state': 'PASS', 'probe': 'PREMISES_SAT', 'assert_cover_ok': True, 'k': 3}

            with mock.patch.object(sys, 'argv', ['run_eqy_chains.py', '--input-mode', 'builtin']), \
                 mock.patch.object(module.F, 'setup_eqy', side_effect=setup), \
                 mock.patch.object(module, 'run_partitions', side_effect=parts), \
                 mock.patch.object(module, 'run_merged', side_effect=merge), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(module.main(), 0)
            out = root / '10_selfcheck/chains/run01'
            self.assertEqual(len(observed), 18)
            for config, work in observed:
                self.assertEqual(work, config.parent / 'work')
                self.assertEqual((work / 'partial.log').read_text(), 'partition evidence')
            self.assertEqual(len(merged), 2)
            for cdir, workdir, merged_dir in merged:
                self.assertEqual(workdir, cdir / 'work')
                self.assertEqual(merged_dir, cdir / 'merged')
                self.assertTrue((merged_dir / 'merged.log').is_file())
            self.assertEqual(len(list((out / 'inputs').glob('*_mapped.il'))), 18)
            self.assertTrue((out / 'inputs/form_cells_cycloneiv.v').is_file())
            rows = json.loads((out / 'chains_summary.json').read_text())
            for row in rows:
                side = 'optimized' if row['chain'] == 'c4a_rtl_opt_mapped' else 'baseline'
                source = root / '05_public/round01' / row['case'] / side / 'post_abc.il'
                self.assertEqual(row['formal_netlist_sha256'], F.sha256_file(source))
                self.assertEqual(F.sha256_file(Path(row['formal_netlist_input'])), F.sha256_file(source))
            self.assertFalse(any(p.name.startswith('_eval_') for p in root.rglob('*')))


class BuiltinPrepareIntegrationTests(unittest.TestCase):
    """run 流程必须经过自动准备：新工具路径写入本轮 context；准备失败即失败记录。"""

    def _cfg(self, base: Path):
        return dict(_v8_context(), **{'repo': str(base), 'performance_pairs': 1,
                'performance_scheme': __import__('measure_v9').SCHEME, 'same_run_policy': __import__('measure_v9').POLICY,
                'results_root': str(base / 'external_results'),
                'flow_version': 'official4-p4', 'suite_version': 'official4-v1',
                'target_commit': 'a' * 40, 'source_sha256': 'e' * 64,
                'project_head': 'b' * 40, 'suite_verified': True,
                'suite_manifest_sha256': '5' * 64,
                'model_version': 'dffeas-v3', 'strategy_version': 'noDF-local-r1',
                'tools': {'yosys': {'sha256': '1' * 64}, 'abc': {'sha256': '2' * 64},
                          'eqy': {'sha256': '3' * 64}, 'z3': {'sha256': '4' * 64}}})

    def test_run_builtin_goes_through_prepare_and_binds_new_paths(self):
        import validate
        from unittest import mock
        with tempfile.TemporaryDirectory() as t:
            base = Path(t)
            round_dir = base / 'round1'
            (round_dir / '01_meta').mkdir(parents=True)
            (round_dir / '03_runner').mkdir()   # 指纹函数需要目录存在
            fake_base_abc = base / 'baseline-yosys-abc.exe'
            fake_opt_abc = base / 'optimized-yosys-abc.exe'
            fake_base_abc.write_bytes(b'baseline abc fixture')
            fake_opt_abc.write_bytes(b'optimized abc fixture')
            fake_builtin = {
                'baseline': {'path': '/fake/base/yosys', 'src_repo': '/fake/base',
                             'src_commit': 'a' * 40, 'binary_sha256': '1' * 64},
                'optimized': {'path': '/fake/opt/yosys', 'src_repo': '/fake/opt',
                              'src_commit': 'a' * 40, 'binary_sha256': '2' * 64,
                              'algorithm_source_path': 'passes/opt/pmux_opt.cc',
                              'algorithm_source_sha256': 'e' * 64,
                              'integration_diff_sha256': 'f' * 64},
                'abc': {'baseline': str(fake_base_abc), 'optimized': str(fake_opt_abc)},
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
                if name == 'measurement_selfcheck':
                    proof = root / '09_performance/selftest/selftest_results.json'
                    proof.parent.mkdir(parents=True)
                    proof.write_text(json.dumps(dict(selftest_ok=True, method=V8.METHOD)), encoding='utf-8')
                return 0

            with mock.patch.object(validate, 'make_round', return_value=round_dir), \
                 mock.patch('prepare_builtin.prepare_builtin', return_value=prep) as prep_mock, \
                 mock.patch.object(validate, 'check_builtin_evidence',
                                   return_value=(True, [], {'ok': True})), \
                 mock.patch.object(validate, 'execute', side_effect=fake_execute), \
                 mock.patch('report.build_builtin_report', return_value='NEEDS_REVIEW'):
                rc = validate.run_builtin(self._cfg(base), b'alg', 'fixture')
            self.assertEqual(rc, 2)
            # 自动准备被调用，且请求的算法源码哈希正确传入
            self.assertEqual(prep_mock.call_args.kwargs.get('source_sha256'), 'e' * 64)
            # 本轮 context 绑定准备解析出的新工具路径（各阶段统一从此读取）
            ctx = json.loads((round_dir / 'validation_context.json').read_text())
            self.assertEqual(ctx['builtin']['optimized']['path'], '/fake/opt/yosys')
            self.assertEqual(ctx['builtin_prepare']['optimized']['action'], 'built')
            # V8先采集唯一8次正式综合，再只读分析与独立证明。
            names = [n for n, _ in executed]
            self.assertEqual(names, ['formal_selfcheck', 'measurement_selfcheck', 'performance',
                                     'flowcheck', 'public', 'chains'])
            perf_cmd = dict(executed)['performance']
            self.assertTrue(any(str(c).endswith('measure_v9.py') for c in perf_cmd))
            self.assertNotIn('--pairs', perf_cmd)

    def test_build_failure_records_status_and_stops(self):
        import validate
        import prepare_builtin as P
        from unittest import mock
        with tempfile.TemporaryDirectory() as t:
            base = Path(t)
            round_dir = base / 'round1'
            (round_dir / '01_meta').mkdir(parents=True)
            err = P.BuildError('模拟构建失败', build_dir=str(base / 'build'), logs={'dir': 'x'})
            with mock.patch.object(validate, 'make_round', return_value=round_dir), \
                 mock.patch('prepare_builtin.prepare_builtin', side_effect=err), \
                 mock.patch('report.build_builtin_build_failed_report',
                            return_value='BUILTIN_BUILD_FAILED') as fail_mock:
                rc = validate.run_builtin(self._cfg(base), b'alg', 'fixture')
            self.assertEqual(rc, 3)
            stages = json.loads((round_dir / '01_meta/stages.json').read_text())
            self.assertEqual(stages[0]['state'], 'ERROR')
            self.assertIn('工具准备失败', stages[0]['detail'])
            fail_mock.assert_called_once()




if __name__ == '__main__':
    unittest.main()
