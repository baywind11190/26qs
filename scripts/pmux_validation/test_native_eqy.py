"""Native EQY safety gates; tests intentionally exercise semantic mutations."""
import copy
import importlib.util
import sys
import unittest
import tempfile
import subprocess
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'runner'))
try:
    import native_eqy as N
except ImportError:
    N = None

class NativeEqyTests(unittest.TestCase):
    def require(self):
        self.assertIsNotNone(N, 'native EQY implementation missing')

    def design(self):
        return {'modules': {'t': {'cells': {'ff': {'type': '$dff', 'connections': {'Q': [2,3], 'D': ['x','z']}}}, 'netnames': {'q': {'bits':[2,3], 'attributes':{'init':'1x'}}, 'comb': {'bits':[4], 'attributes':{}}}, 'ports':{'y': {'bits':['x','z']}}}}}

    def test_zero_only_missing_q_initials_preserves_logic_and_explicit_one(self):
        self.require()
        before=self.design(); after,audit=N.zero_init_json(before)
        self.assertEqual(after['modules']['t']['netnames']['q']['attributes']['init'],'10')
        self.assertEqual(before,self.design())
        self.assertEqual(after['modules']['t']['cells'],before['modules']['t']['cells'])
        self.assertEqual(after['modules']['t']['ports'],before['modules']['t']['ports'])
        self.assertTrue(audit['only_init_attributes_changed'])
        self.assertEqual(audit['initialized_bits'],1)

    def test_alias_explicit_initial_one_cannot_be_overwritten(self):
        self.require()
        before=self.design(); before['modules']['t']['netnames']['alias']={'bits':[2], 'attributes':{'init':'1'}}
        after,audit=N.zero_init_json(before)
        self.assertEqual(after['modules']['t']['netnames']['q']['attributes']['init'],'11')
        self.assertEqual(audit['initialized_bits'],0)

    def test_conflicting_explicit_alias_initials_block(self):
        self.require()
        before=self.design(); before['modules']['t']['netnames']['alias']={'bits':[3], 'attributes':{'init':'0'}}
        with self.assertRaises(ValueError): N.zero_init_json(before)

    def test_native_config_test3_merge_is_native_and_keeps_depth16(self):
        self.require()
        cfg=N.make_cfg('g.json','r.json','test3')
        self.assertIn('[partition test3]\nmerge *',cfg)
        self.assertIn('depth 16',cfg)
        self.assertNotIn('nomatch',cfg)

    def test_probe_preserves_native_defined_formal_and_same_horizon(self):
        self.require()
        script='read_rtlil p.il\nsat -tempinduct -set-init-undef -set-def-formal -set-def-inputs -maxsteps 16 -set-assumes -prove-asserts -show-public -dump_vcd trace.vcd miter\n'
        probe=N.make_probe(script)
        self.assertIn('-seq 16',probe)
        self.assertIn('-set-def-formal',probe)
        self.assertIn('-set-assumes',probe)
        self.assertNotIn('-prove-asserts',probe)

    def test_pass_requires_native_status_cover_and_satisfiable_premises(self):
        self.require()
        parts={'p':{'proof':{'state':'PASS'},'probe':{'state':'VALID','verdict':'PREMISES_SAT'},'coverage_ok':True}}
        self.assertEqual(N.aggregate(0,'PASS',[],parts)['state'],'PASS')
        self.assertNotEqual(N.aggregate(0,'UNKNOWN',[],parts)['state'],'PASS')
        self.assertNotEqual(N.aggregate(0,'PASS',['ERROR: late failure'],parts)['state'],'PASS')
        parts['p']['probe']['verdict']='PREMISES_UNSAT'
        self.assertEqual(N.aggregate(0,'PASS',[],parts)['state'],'PREMISES_NOT_SAT')
        parts['p']['probe']['verdict']='PREMISES_SAT';parts['p']['coverage_ok']=False
        self.assertNotEqual(N.aggregate(0,'PASS',[],parts)['state'],'PASS')

    def test_report_native_requires_all_real_evidence(self):
        from report import row_functional_ok
        row={'state':'PASS','rc':0,'verified':True,'method':'native_eqy',
             'strategy_version':'eqy-zero-init-r1','native_status':'PASS','native_rc':0,
             'native_errors':[],'premises_all_sat':True,'coverage_ok':True,'init_audit_ok':True,
             'init_audits':{side:{'only_init_attributes_changed':True,'explicit_01_preserved':True} for side in ['gold','gate']},
             'partitions_total':1,'partitions_pass':1,
             'partitions':{'p':{'proof':{'state':'PASS','errors':[]},'native_status':'PASS','coverage_ok':True,
                 'probe':{'state':'VALID','rc':0,'verdict':'PREMISES_SAT'}}}}
        self.assertTrue(row_functional_ok(row))
        for field in ['native_status','native_rc','premises_all_sat','coverage_ok','init_audit_ok','partitions','init_audits']:
            bad=copy.deepcopy(row);bad.pop(field)
            self.assertFalse(row_functional_ok(bad),field)

    def test_chain_deadline_does_not_return_a_fresh_timeout_budget(self):
        self.require()
        self.assertTrue(hasattr(N, 'remaining_seconds'), 'chain deadline helper missing')
        self.assertEqual(N.remaining_seconds(5, now=6), 0)
        self.assertEqual(N.remaining_seconds(5, now=3), 2)

    def test_merged_matchpoint_coverage_cannot_drop_sr_or_rw(self):
        self.require()
        self.assertTrue(hasattr(N,'merged_coverage'), 'merged matchpoint audit missing')
        self.assertTrue(N.merged_coverage({'gpioout','sr_out','rw','sr'}, {'gpioout','sr_out','rw','sr'}))
        self.assertFalse(N.merged_coverage({'gpioout','sr_out','rw','sr'}, {'gpioout','sr_out'}))

    def test_probe_timeout_cannot_be_downgraded_to_inconclusive(self):
        self.require()
        parts={'p':{'proof':{'state':'PASS'},'probe':{'state':'VALID','rc':124,'verdict':'OTHER'},'coverage_ok':True}}
        self.assertEqual(N.aggregate(0,'PASS',[],parts)['state'],'TIMEOUT')
        parts['p']['probe'].update(state='TIMEOUT',rc=124)
        self.assertEqual(N.aggregate(0,'PASS',[],parts)['state'],'TIMEOUT')

    def partial_run(self, root, timeout):
        def prepare(ys, log, cwd, **kw):
            side=Path(ys).stem
            (root/(side+'.before.json')).write_text(__import__('json').dumps(self.design()))
            Path(log).write_text('preparation complete\n')
            return 0
        class PartialEqy:
            def __init__(inner,*a,**kw):
                (root/'work/strategies/t.y/simple').mkdir(parents=True)
                (root/'work/partition.log').write_text('partial generation preserved\n')
                if not timeout: (root/'work/PASS').touch()
                inner.waits=0
            def wait(inner,timeout=None):
                inner.waits+=1
                if inner.waits==1 and timeout_case:
                    raise subprocess.TimeoutExpired('eqy',timeout)
                return 0
        timeout_case=timeout
        with patch.object(N.F,'run_yosys_script',side_effect=prepare), patch.object(N,'frozen_env',return_value=({},{})), patch.object(N.subprocess,'Popen',PartialEqy), patch.object(N,'terminate_process_tree'):
            return N.run_chain([],[],'t',root,yosys='yosys',abc='abc',eqy='eqy')

    def test_timeout_during_strategy_generation_preserves_partial_evidence(self):
        self.require()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            try: result=self.partial_run(root,True)
            except FileNotFoundError as exc: self.fail('TIMEOUT was masked by missing generated script: '+str(exc))
            self.assertEqual(result['state'],'TIMEOUT')
            self.assertEqual(set(result['init_audits']),{'gold','gate'})
            self.assertTrue((root/'native_summary.json').is_file())
            self.assertTrue((root/'work/partition.log').is_file())
            import eqy_workspace as W
            with patch.object(W,'check_work',side_effect=AssertionError('partial timeout must not require complete strategies')):
                audit=N.audit_workspace(root/'work',result)
            self.assertFalse(audit['complete'])
            self.assertEqual(result['state'],'TIMEOUT')

    def test_non_timeout_incomplete_strategy_is_an_error_not_pass(self):
        self.require()
        with tempfile.TemporaryDirectory() as d:
            try: result=self.partial_run(Path(d),False)
            except FileNotFoundError as exc: self.fail('Missing strategy should produce an evidence result: '+str(exc))
            self.assertIn(result['state'],('TOOL_OR_CONFIG_ERROR','INCOMPLETE'))
            self.assertFalse(N.audit_workspace(Path(d)/'work',result)['complete'])
            self.assertEqual(result['state'],'TOOL_OR_CONFIG_ERROR')

if __name__=='__main__': unittest.main()
