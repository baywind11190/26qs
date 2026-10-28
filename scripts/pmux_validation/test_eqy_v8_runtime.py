"""Tool-free runtime regressions for managed EQY execution."""
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

PACKAGE = Path(__file__).resolve().parent
sys.path.insert(0, str(PACKAGE))
sys.path.insert(0, str(PACKAGE / 'runner'))

def load(name):
    spec = importlib.util.spec_from_file_location('_runtime_' + name, PACKAGE / 'runner' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {'p3_common': SimpleNamespace(CONTEXT={})}):
        spec.loader.exec_module(module)
    return module

class RuntimeTests(unittest.TestCase):
    def test_reject_requires_clean_counterexample(self):
        runner = load('run_selfcheck')
        for rc, errors in [(1, []), (124, []), (0, ['backend failed'])]:
            result = {'state': 'RUN_DONE', 'partitions': {'out': {
                'proof': {'state': 'FAIL', 'rc': rc, 'errors': errors},
                'probes': {'noDF': {'verdict': 'PREMISES_SAT', 'rc': 0, 'state': 'VALID'},
                           'DF': {'verdict': 'PREMISES_UNSAT'}}}}}
            with self.subTest(rc=rc, errors=errors):
                self.assertFalse(runner.judge({'expect': 'REJECT'}, result)[0])
        result['partitions']['out']['proof'] = {'state': 'FAIL', 'rc': 0, 'errors': []}
        self.assertTrue(runner.judge({'expect': 'REJECT'}, result)[0])

    def test_reject_does_not_hide_another_partition_tool_failure(self):
        runner = load('run_selfcheck')
        probe = {'noDF': {'verdict':'PREMISES_SAT','rc':0,'state':'VALID'}, 'DF': {'verdict':'PREMISES_UNSAT'}}
        result = {'state':'RUN_DONE', 'partitions': {
            'counterexample': {'proof': {'state':'FAIL','rc':0,'errors':[]}, 'probes':probe},
            'broken': {'proof': {'state':'TOOL_OR_CONFIG_ERROR','rc':1}, 'probes':probe}}}
        self.assertFalse(runner.judge({'expect':'REJECT'},result)[0])

    def test_reject_requires_sat_premises_in_every_partition(self):
        runner = load('run_selfcheck')
        for verdict in ('PREMISES_UNSAT', 'OTHER'):
            result = {'state': 'RUN_DONE', 'partitions': {
                'counterexample': {'proof': {'state': 'FAIL', 'rc': 0, 'errors': []},
                    'probes': {'noDF': {'verdict': 'PREMISES_SAT', 'rc': 0, 'state': 'VALID'},
                               'DF': {'verdict': 'PREMISES_UNSAT'}}},
                'invalid_premise': {'proof': {'state': 'PASS', 'rc': 0, 'errors': []},
                    'probes': {'noDF': {'verdict': verdict, 'rc': 0, 'state': 'VALID'},
                               'DF': {'verdict': 'PREMISES_UNSAT'}}}}}
            with self.subTest(verdict=verdict):
                self.assertFalse(runner.judge({'expect': 'REJECT'}, result)[0])
        result['partitions']['invalid_premise']['probes']['noDF']['verdict'] = 'PREMISES_SAT'
        self.assertTrue(runner.judge({'expect': 'REJECT'}, result)[0])

    def test_pass_and_premise_require_valid_probe(self):
        runner = load('run_selfcheck')
        result = {'state': 'RUN_DONE', 'partitions': {'out': {
            'proof': {'state': 'PASS', 'rc': 0},
            'probes': {'noDF': {'verdict': 'PREMISES_SAT', 'rc': 1, 'state': 'TOOL_OR_CONFIG_ERROR'},
                       'DF': {'verdict': 'PREMISES_UNSAT'}}}}}
        for expect in ['PASS', 'PREMISE_SAT']:
            self.assertFalse(runner.judge({'expect': expect}, result)[0])

    def test_merged_sat_text_with_failed_exit_cannot_pass(self):
        import tempfile
        runner = load('run_eqy_chains')
        runner.C.SCRIPT_DIR = PACKAGE / 'runner'
        with tempfile.TemporaryDirectory() as td:
            d = Path(td); work = d/'work'
            for name in ['test3.rw', 'test3.sr', 'test3.sr_out', 'test3.gpioout']:
                (work/'strategies'/name).mkdir(parents=True)
            (work/'modules').mkdir()
            (work/'modules/test3.il').write_text('fixture')
            def tool(script, log, cwd, **kw):
                if script.name.startswith('probe'):
                    log.write_text('SAT solving finished - model found:')
                    return 1
                log.write_text('fixture')
                return 0
            proof = {'state': 'PASS', 'asserts': ['x'+x for x in runner.MERGED['test3']['assert_suffixes']], 'induct_len': 1}
            with patch.object(runner.F, 'run_yosys_script', side_effect=tool), patch.object(runner.F, 'classify_proof_text', return_value=proof):
                result = runner.run_merged('test3', d, yosys='fixture')
            self.assertNotEqual(result['state'], 'PASS')

    def test_managed_official_runs_all_nine_case_sides(self):
        import contextlib, io, json, tempfile
        import eqy_workspace as manager
        from test_measure_v8 import fixture_cases
        from test_validation import _dffeas_il
        runner = load('run_eqy_chains')
        cases = fixture_cases()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)/'round'; root.mkdir()
            tree = root/'02_assets/tree'
            cfg = {'official_cases': cases, 'eqy_work_root': str(Path(td)/'short'),
                   'target_commit': 'a'*40, 'source_sha256': 'b'*64, 'tools': {},
                   'builtin': {'integration_id': 'pmux-opt-inline-p3-v1'}}
            cfg['eqy_workspace'] = manager.create_workspace(cfg, root, [])
            for case in cases:
                rtl = tree / case['file'][5:]; rtl.parent.mkdir(parents=True, exist_ok=True)
                rtl.write_text('module '+case['top']+'; endmodule')
                for side in ('baseline', 'optimized'):
                    net = root/'05_public/round01'/case['id']/side/'post_abc.il'
                    net.parent.mkdir(parents=True); net.write_text(_dffeas_il(top=case['top']))
            runner.C = SimpleNamespace(CONTEXT=cfg, ROUND_DIR=root, TREE=tree,
                SCRIPT_DIR=PACKAGE/'runner', REPO=Path(td), TOOL_YOSYS='fixture', EQY_ABC='fixture',
                TOOL_EQY='fixture', sha256_file=manager.sha, rel=lambda p:str(p), refuse_overwrite=lambda p:None)
            observed=[]
            def setup(config, work, log, **kw):
                observed.append(work)
                self.assertTrue(config.is_relative_to(Path(cfg['eqy_workspace']['workspace'])))
                strategy=work/'strategies/top.out/simple'; strategy.mkdir(parents=True)
                parts=work/'partitions'; parts.mkdir()
                for ext in ('sv','il'): (parts/('top.out.'+ext)).write_text('fixture')
                (strategy/'run.ys').write_text('read_verilog -sv ../../../partitions/top.out.sv\nread_rtlil ../../../partitions/top.out.il\n')
                log.write_text('setup')
                return 0
            def prove(work, **kw):
                return {'top.out': {'proof': {'state':'PASS'}, 'probes': {
                    'noDF': {'verdict':'PREMISES_SAT','rc':0,'state':'VALID'},
                    'DF': {'verdict':'PREMISES_UNSAT','rc':0,'state':'VALID'}}}}
            with patch.object(sys, 'argv', ['chains','--input-mode','builtin']), patch.object(runner.F,'setup_eqy',side_effect=setup), patch.object(runner,'run_partitions',side_effect=prove), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(runner.main(), 0)
            self.assertEqual(len(observed), 18)
            self.assertEqual(len(set(observed)), 18)
            rows=json.loads((root/'10_selfcheck/chains/run01/chains_summary.json').read_text())
            self.assertEqual({(r['case'],r['chain']) for r in rows},
                {(c['id'],chain) for c in cases for chain in ('c4a_rtl_opt_mapped','c4b_rtl_base_mapped')})
            self.assertTrue(all(r['verified'] for r in rows))
            self.assertTrue(all(Path(r['formal_netlist_input']).is_relative_to(Path(cfg['eqy_workspace']['workspace'])) for r in rows))
            self.assertEqual(len(list(Path(cfg['eqy_workspace']['workspace']).glob('chains/inputs/*_mapped.il'))), 18)

    def test_managed_selfcheck_rejects_overbudget_job_before_setup(self):
        import tempfile
        runner = load('run_selfcheck')
        runner.C = SimpleNamespace(CONTEXT={'eqy_workspace': {}}, TOOL_YOSYS='fixture', EQY_ABC='fixture', TOOL_EQY='fixture')
        # An identity object is present in production; this isolates the last pre-tool path check.
        runner.C.CONTEXT['eqy_workspace'] = {'version':'managed-short-v1'}
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)/('x'*170); d.mkdir()
            with patch.object(runner.F, 'setup_eqy', return_value=1) as setup:
                with self.assertRaisesRegex(ValueError, 'path budget'):
                    runner.run_check({'kind':'rtl','top':'top'},d/'g.v',d/'b.v',d/'m.v',d)
                setup.assert_not_called()

    def test_managed_selfcheck_stages_bytes_and_keeps_round_summary(self):
        import contextlib, io, json, tempfile
        import eqy_workspace as manager
        runner=load('run_selfcheck')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'round'; root.mkdir()
            assets=root/'10_selfcheck/assets'; assets.mkdir(parents=True)
            checks=[{'name':'positive','kind':'rtl','top':'top','expect':'PASS','gold':'gold.v','gate':'gate.v'}]
            (assets/'checks.json').write_text(json.dumps({'version':'fixture','checks':checks}))
            for name in ('gold.v','gate.v'): (assets/name).write_bytes(b'module top; endmodule\r\n')
            cfg={'eqy_work_root':str(Path(td)/'short'),'official_cases':[{'id':'fixture'}]}
            cfg['eqy_workspace']=manager.create_workspace(cfg,root,checks)
            runner.C=SimpleNamespace(CONTEXT=cfg,ROUND_DIR=root,SCRIPT_DIR=PACKAGE/'runner',
                sha256_file=manager.sha,rel=lambda p:str(p),refuse_overwrite=lambda p:None)
            observed=[]
            def run(check,gold,gate,model,d):
                observed.append(d)
                self.assertEqual(gold.read_bytes(), b'module top; endmodule\r\n')
                for path in (gold,gate,model,d):
                    self.assertTrue(path.is_relative_to(Path(cfg['eqy_workspace']['workspace'])))
                return {'state':'RUN_DONE','partitions':{'top.out':{'proof':{'state':'PASS','rc':0},
                    'probes':{'noDF':{'verdict':'PREMISES_SAT','rc':0,'state':'VALID'},'DF':{'verdict':'PREMISES_SAT'}}}}}
            with patch.object(runner,'run_check',side_effect=run),contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(runner.main(),0)
            self.assertEqual(observed,[Path(cfg['eqy_workspace']['workspace'])/'sc/s01'])
            self.assertTrue((root/'10_selfcheck/attempt01/positive/summary.json').is_file())
            self.assertTrue((root/'10_selfcheck/attempt01/hash_manifest.json').is_file())

    def test_managed_selfcheck_audits_generated_set_before_proof(self):
        import tempfile
        runner = load('run_selfcheck')
        import eqy_workspace as real_manager
        manager = SimpleNamespace(check_work=lambda *a, **k: {"partitions": ["top.out"]}, check_paths=real_manager.check_paths)
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            runner.C.CONTEXT = {'eqy_workspace': {'workspace': td}}
            runner.C.TOOL_YOSYS = runner.C.EQY_ABC = runner.C.TOOL_EQY = 'fixture'
            with patch.dict(sys.modules, {'eqy_workspace': manager}), patch.object(runner.F, 'setup_eqy', return_value=0):
                # Setup emits no strategy: a successful setup must not permit missing result rows.
                result = runner.run_check({'kind': 'rtl', 'top': 'top'}, d/'g.v', d/'b.v', d/'m.v', d)
            self.assertEqual(result['state'], 'TOOL_OR_CONFIG_ERROR')
            self.assertIn('partition result set', result['error'])

if __name__ == '__main__': unittest.main()
