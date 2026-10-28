"""Proof-only recheck safety and regression tests; no official synthesis."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

PACKAGE = Path(__file__).resolve().parent
sys.path.insert(0, str(PACKAGE / 'runner'))
import function_common as F


class RecheckTests(unittest.TestCase):
    def entry(self):
        path = PACKAGE / 'recheck_eqy.py'
        self.assertTrue(path.is_file(), 'missing proof-only entrypoint')
        spec = importlib.util.spec_from_file_location('_recheck_entry_test', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def support(self):
        spec = importlib.util.spec_from_file_location('eqy_recheck_support', PACKAGE / 'runner/eqy_recheck_support.py')
        self.assertIsNotNone(spec)
        self.assertTrue(Path(spec.origin).is_file(), 'missing managed recheck support')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_short_mapping_keeps_case_and_side_distinct(self):
        W = self.support()
        root = Path('D:/eqy_work/round/a01')
        paths = [W.job_dir(root, c, s) for c in W.TARGET_CASES for s in ('baseline', 'optimized')]
        self.assertEqual(len(set(paths)), 6)
        self.assertEqual(W.job_dir(root, W.TARGET_CASES[0], 'baseline'), root / 'c01/b')
        with self.assertRaises(ValueError):
            W.job_dir(root, '../escape', 'baseline')

    def test_selection_requires_explicit_unique_known_cases(self):
        W = self.support()
        cases = [{'id': name, 'top': name} for name in W.TARGET_CASES]
        self.assertEqual(W.select_cases(cases, list(reversed(W.TARGET_CASES))), cases)
        for invalid in ([], [W.TARGET_CASES[0]] * 2, ['unknown']):
            with self.assertRaises(ValueError):
                W.select_cases(cases, invalid)

    def test_workspace_refuses_overwrite_and_links(self):
        W = self.support()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / 'work'
            W.create_workspace(root, {'source': 'fixture'})
            with self.assertRaises(FileExistsError):
                W.create_workspace(root, {'source': 'other'})
            with self.assertRaises(ValueError):
                W.safe_root(Path(td) / '../escape path')

    def test_partition_set_and_path_budget_are_checked(self):
        W = self.support()
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / 'work'
            s = work / 'strategies/top.out/simple'
            s.mkdir(parents=True)
            p = work / 'partitions'; p.mkdir()
            (p / 'top.out.sv').write_text('module miter; endmodule')
            (p / 'top.out.il').write_text('module \\miter\nend\n')
            (s / 'run.ys').write_text('read_verilog -sv ../../../partitions/top.out.sv\nread_rtlil ../../../partitions/top.out.il\n')
            audit = W.check_work(work, ['top.out'], limit=1000)
            self.assertEqual(audit['partitions'], ['top.out'])
            self.assertEqual(len(audit['references']), 2)
            with self.assertRaises(ValueError):
                W.check_work(work, ['missing'], limit=1000)
            with self.assertRaises(ValueError):
                W.check_work(work, ['top.out'], limit=20)

    def test_errors_and_nonzero_exit_cannot_be_sat(self):
        text = 'SAT solving finished - model found:\nERROR: missing file\n'
        self.assertEqual(F.classify_probe_result(text, 0)['state'], 'TOOL_OR_CONFIG_ERROR')
        self.assertEqual(F.classify_probe_result('SAT solving finished - model found:', 1)['state'], 'TOOL_OR_CONFIG_ERROR')
        self.assertEqual(F.classify_probe_result('', 124)['state'], 'TIMEOUT')
        self.assertEqual(F.classify_probe_result('SAT solving finished - no model found.', 0)['verdict'], 'PREMISES_UNSAT')

    def test_chain_completeness_requires_exact_six_rows(self):
        W = self.support()
        rows = [{'case': c, 'chain': chain, 'state': 'PASS', 'verified': True,
                 'probes_noDF_all_sat': True, 'partitions_total': 1, 'partitions_pass': 1}
                for c in W.TARGET_CASES for chain in W.CHAINS]
        self.assertTrue(W.complete(rows, list(W.TARGET_CASES)))
        self.assertFalse(W.complete(rows[:-1], list(W.TARGET_CASES)))
        self.assertFalse(W.complete(rows[:-1] + [rows[0]], list(W.TARGET_CASES)))

    def test_archive_verifies_exact_bytes_and_keeps_source(self):
        W = self.support()
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / 'source'; src.mkdir()
            (src / 'partial.log').write_bytes(b'FAIL\r\n')
            (src / 'empty').mkdir()
            dst = Path(td) / 'archive'
            audit = W.archive_tree(src, dst)
            self.assertEqual(len(audit), 1)
            self.assertEqual((dst / 'partial.log').read_bytes(), b'FAIL\r\n')
            self.assertTrue((src / 'partial.log').is_file())
            self.assertTrue((dst / 'empty').is_dir())
            with self.assertRaises(FileExistsError):
                W.archive_tree(src, dst)

    def source_fixture(self, root):
        W = self.support()
        ctx = {'repo': str(root), 'target_commit': '17f9361099dcda757c16bb81caa18ddb52d74c4e',
               'integration_profile': 'p3-local-lut', 'source_sha256': '', 'tools': {}, 'official_cases': []}
        def put(rel, data):
            p = root / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data)
            return p
        src = put('02_assets/tree/src/pmux_opt.cc', b'algorithm fixture')
        ctx['source_sha256'] = W.sha(src)
        for tool in ('yosys', 'eqy', 'abc'):
            p = put('tools/' + tool, tool.encode())
            ctx['tools'][tool] = {'path': str(p), 'sha256': W.sha(p)}
        put('03_runner/form_cells_cycloneiv.v', b'module model; endmodule\n')
        for case in W.TARGET_CASES:
            rel = 'pmux_case/competition_case/' + case + '/' + case + '.v'
            p = put('02_assets/tree/' + rel, ('module '+case+'; endmodule\n').encode())
            ctx['official_cases'].append({'id': case, 'top': case, 'file': 'tree/' + rel, 'sha256': W.sha(p),
                                         'canonical_file': rel, 'canonical_sha256': W.sha(p), 'default_parameters': {}})
            for side, chain in [('optimized', W.CHAINS[0]), ('baseline', W.CHAINS[1])]:
                net = put('05_public/round01/'+case+'/'+side+'/post_abc.il', b'netlist')
                put('10_selfcheck/chains/run01/'+case+'/'+chain+'/summary.json', json.dumps({
                    'formal_netlist_sha256': W.sha(net), 'partition_states': {case+'.out': 'PASS'}}).encode())
        put('validation_context.json', json.dumps(ctx).encode())
        hashes = W.inventory(root)
        put('11_summary/ALL_SHA256.txt', ''.join(v['sha256']+'  '+k+'\n' for k,v in hashes.items()).encode())
        return ctx

    def test_plan_is_readonly_and_blocks_changed_source(self):
        E = self.entry(); W = self.support()
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / 'source'; source.mkdir()
            self.source_fixture(source)
            short = Path(td) / 'short'
            before = W.inventory(source)
            plan = E.build_plan(source, list(W.TARGET_CASES), short)
            self.assertEqual(plan['blocked'], [])
            self.assertEqual(plan['formal_synthesis_expected_runs'], 0)
            self.assertEqual(plan['functional_expected_chains'], 6)
            self.assertEqual(W.inventory(source), before)
            self.assertFalse(short.exists())
            tool=source/'tools/yosys'; original=tool.read_bytes();tool.write_bytes(b'changed')
            self.assertTrue(E.build_plan(source,list(W.TARGET_CASES),short)['blocked'])
            tool.write_bytes(original)
            long_root=Path(td)/('x'*180)
            self.assertTrue(E.build_plan(source,list(W.TARGET_CASES),long_root)['blocked'])
            (source/'05_public/round01'/W.TARGET_CASES[0]/'baseline/post_abc.il').write_text('changed')
            self.assertTrue(E.build_plan(source, list(W.TARGET_CASES), short)['blocked'])

    def test_interrupted_run_preserves_archive_and_marks_unfinished_not_run(self):
        from unittest import mock
        import contextlib,io
        E=self.entry();W=self.support()
        with tempfile.TemporaryDirectory() as td:
            source=Path(td)/'source';source.mkdir();self.source_fixture(source)
            (source/'POLICY.md').write_text('source rules')
            (source/'results/official_eval').mkdir(parents=True)
            index=W.inventory(source)
            (source/'11_summary/ALL_SHA256.txt').write_text(''.join(v['sha256']+'  '+k+'\n' for k,v in index.items() if not k.endswith('ALL_SHA256.txt')))
            plan=E.build_plan(source,list(W.TARGET_CASES),Path(td)/'short')
            process=mock.Mock();process.wait.side_effect=[KeyboardInterrupt,0]
            with mock.patch.object(E.subprocess,'Popen',return_value=process),\
                 mock.patch.object(E,'terminate_process_tree') as terminate,contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(E.run(plan),2)
            terminate.assert_called_once_with(process)
            result=next((source/'results/official_eval').iterdir())
            summary=json.loads((result/'11_summary/recheck_summary.json').read_text(encoding='utf-8'))
            # A real result directory inside the source is detected as a source change in this fixture.
            self.assertTrue(summary['archive_verified'])
            self.assertEqual([r['state'] for r in summary['chains']],['NOT_RUN']*6)
            self.assertEqual(summary['process_rc'],130)
            self.assertTrue((Path(plan['workspace'])/'workspace_manifest.json').is_file())

    def test_truncated_summary_and_path_audit_do_not_skip_archival(self):
        from unittest import mock
        import contextlib,io
        E=self.entry();W=self.support()
        with tempfile.TemporaryDirectory() as td:
            source=Path(td)/'source';source.mkdir();self.source_fixture(source)
            (source/'POLICY.md').write_text('source rules')
            (source/'results/official_eval').mkdir(parents=True)
            index=W.inventory(source)
            (source/'11_summary/ALL_SHA256.txt').write_text(''.join(v['sha256']+'  '+k+'\n' for k,v in index.items() if not k.endswith('ALL_SHA256.txt')))
            plan=E.build_plan(source,list(W.TARGET_CASES),Path(td)/'short')
            def launch(command,**kwargs):
                root=Path(command[4]).parents[1]
                cdir=root/'10_selfcheck/chains/run01'/W.TARGET_CASES[0]/W.CHAINS[0]
                cdir.mkdir(parents=True);(cdir/'summary.json').write_text('{truncated')
                job=W.job_dir(Path(plan['workspace']),W.TARGET_CASES[0],'optimized')
                job.mkdir(parents=True);(job/'path_audit.json').write_text('{truncated')
                p=mock.Mock();p.wait.return_value=1;return p
            with mock.patch.object(E.subprocess,'Popen',side_effect=launch),contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(E.run(plan),2)
            root=next((source/'results/official_eval').iterdir())
            result=json.loads((root/'11_summary/recheck_summary.json').read_text(encoding='utf-8'))
            self.assertTrue(result['archive_verified'])
            self.assertEqual(result['chains'][0]['state'],'INCOMPLETE')
            self.assertTrue(any('summary.json' in p for p in result['problems']))
            self.assertTrue(any('path_audit.json' in p for p in result['problems']))
            self.assertTrue((root/'00_report.md').is_file())

    def test_probe_errors_take_precedence_over_premises(self):
        W = self.support()
        parts = {'out': {'proof': {'state': 'TOOL_OR_CONFIG_ERROR'},
                         'probes': {'noDF': {'verdict': 'OTHER', 'rc': 1}}}}
        self.assertEqual(W.proof_gate(parts), 'TOOL_OR_CONFIG_ERROR')
        parts['out'] = {'proof': {'state': 'PASS'}, 'probes': {'noDF': {'verdict': 'PREMISES_SAT', 'rc': 0}}}
        self.assertIsNone(W.proof_gate(parts))

    def test_builtin_recheck_runs_only_bound_six_jobs_in_short_root(self):
        from types import SimpleNamespace
        from unittest import mock
        import contextlib
        import io
        from test_validation import _dffeas_il
        W = self.support()
        with tempfile.TemporaryDirectory() as td:
            source=Path(td)/'source'; source.mkdir()
            ctx=self.source_fixture(source)
            for c in W.TARGET_CASES:
                for side in ('baseline','optimized'):
                    p=source/'05_public/round01'/c/side/'post_abc.il'
                    p.write_text(_dffeas_il(top=c))
            index=W.inventory(source)
            (source/'11_summary/ALL_SHA256.txt').write_text(''.join(v['sha256']+'  '+k+'\n' for k,v in index.items() if not k.endswith('ALL_SHA256.txt')))
            root=Path(td)/'result'; root.mkdir()
            workspace=Path(td)/'short/source/a01'
            # The controlled MINGW64 child renders paths with '/' while its native parent uses '\\'.
            W.create_workspace(workspace,{'source_round':str(source.resolve()).replace('\\','/'),
                                          'result_round':str(root).replace('\\','/')})
            ctx['functional_recheck']={'root':str(Path(td)/'short'),'workspace':str(workspace),'cases':list(W.TARGET_CASES)}
            ctx['builtin']={'integration_id':'pmux-opt-inline-p3-v1'}
            context=SimpleNamespace(CONTEXT=ctx,ROUND_DIR=root,REPO=Path(td),TREE=root/'02_assets/tree',
                SCRIPT_DIR=PACKAGE/'runner',TOOL_YOSYS='fixture',EQY_ABC='fixture',TOOL_EQY='fixture',
                sha256_file=W.sha,rel=lambda p:str(p),refuse_overwrite=lambda p:None)
            spec=importlib.util.spec_from_file_location('_recheck_chains_fixture',PACKAGE/'runner/run_eqy_chains.py')
            module=importlib.util.module_from_spec(spec)
            with mock.patch.dict(sys.modules,{'p3_common':context}):
                spec.loader.exec_module(module)
            observed=[]
            def setup(config,work,log,**kwargs):
                case=next(c for c in W.TARGET_CASES if c in config.read_text())
                observed.append(work)
                strategy=work/'strategies'/(case+'.out')/'simple';strategy.mkdir(parents=True)
                parts=work/'partitions';parts.mkdir()
                for suffix in ('sv','il'):(parts/(case+'.out.'+suffix)).write_text('fixture')
                (strategy/'run.ys').write_text('read_verilog -sv ../../../partitions/'+case+'.out.sv\n')
                log.write_text('setup')
                return 0
            def partitions(work,**kwargs):
                name=next((work/'strategies').iterdir()).name
                return {name:{'proof':{'state':'PASS'},'probes':{'noDF':{'verdict':'PREMISES_SAT','rc':0},'DF':{'verdict':'PREMISES_UNSAT','rc':0}}}}
            args=['run_eqy_chains.py','--input-mode','builtin','--frozen-round',str(source),
                  '--cases',*W.TARGET_CASES,'--eqy-work-root',str(Path(td)/'short')]
            with mock.patch.object(sys,'argv',args),mock.patch.object(module.F,'setup_eqy',side_effect=setup),\
                 mock.patch.object(module,'run_partitions',side_effect=partitions),contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(module.main(),0)
            self.assertEqual(len(observed),6)
            self.assertTrue(all(p.is_relative_to(workspace) for p in observed))
            rows=json.loads((root/'10_selfcheck/chains/run01/chains_summary.json').read_text())
            self.assertTrue(W.complete(rows,list(W.TARGET_CASES)))
            self.assertEqual(len(list((workspace/'inputs').glob('*_mapped.il'))),6)


if __name__ == '__main__':
    unittest.main()
