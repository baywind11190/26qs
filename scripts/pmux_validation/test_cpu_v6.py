"""Focused v6 contract tests; no repeated performance experiments."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).parent / 'runner'))
import measure_v6 as v6

class V6Tests(unittest.TestCase):
    def test_schedule(self):
        rows=list(v6.schedule())
        self.assertEqual(len(rows),16)
        self.assertEqual([r['purpose'] for r in rows],['cpu']*8+['memory']*8)
        self.assertEqual(len({(r['purpose'],r['case'],r['side']) for r in rows}),16)

    def test_threshold(self):
        self.assertEqual(v6.compare(100,105)['verdict'],'PASS')
        self.assertEqual(v6.compare(100,106)['verdict'],'FAIL')
        self.assertEqual(v6.compare(0,1)['verdict'],'INVALID')
        self.assertEqual(v6.compare(100,99)['verdict'],'PASS')

    def test_runtime_identity_and_missing(self):
        native=dict(main_pid=42,process_create_filetime=123)
        raw=dict(schema=1,method=v6.METHOD,main_pid=42,process_create_filetime=123,
                 cpu_user_ticks=100,cpu_kernel_ticks=20,cpu_total_ticks=120,
                 total_processes=3,active_processes=1,valid=True,error=None)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'runtime.json'
            self.assertRaises(ValueError,v6.read_runtime,p,native)
            p.write_text(json.dumps(raw))
            self.assertEqual(v6.read_runtime(p,native)['cpu_total_ticks'],120)
            raw['main_pid']=43;p.write_text(json.dumps(raw))
            self.assertRaises(ValueError,v6.read_runtime,p,native)
            raw['main_pid']=42;raw['cpu_total_ticks']=121;p.write_text(json.dumps(raw))
            self.assertRaises(ValueError,v6.read_runtime,p,native)

    def test_exactly_sixteen_runs_and_report(self):
        calls=[]
        stat={'design':{'num_cells_by_type':{'cycloneiv_lcell_comb':2},'num_ports':2,'num_port_bits':2}}
        def execute(cmd,*,cwd,log_path,timeout_s):
            memory='--runtime-json' not in cmd
            calls.append(memory)
            (cwd/'stat.json').write_text(json.dumps(stat))
            raw=dict(schema=1,method=v6.METHOD,main_pid=42,process_create_filetime=123,
                     cpu_user_ticks=100,cpu_kernel_ticks=20,cpu_total_ticks=120,
                     total_processes=3,active_processes=1,valid=True,error=None)
            (cwd/'runtime.json').write_text(json.dumps(raw))
            return dict(main_pid=42,process_create_filetime=123,rc=0,timed_out=False,
                        metrics_valid=True,measurement_error=None,root_debugged=memory,
                        memory_capture_complete=memory,memory_exit_event_observed=memory,
                        memory_exit_event_pid=42,memory_method_version='windows-root-exit-event-v1',
                        yosys_peak_working_set_bytes=1000)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for c in v6.CASES:
                for side in ('baseline','optimized'):
                    folder=root/f'05_公开四例_public/round01/{c}/{side}';folder.mkdir(parents=True)
                    (folder/'stat.json').write_text(json.dumps(stat))
            rc=v6.run(dict(performance_scheme=v6.SCHEME,cpu_policy=v6.POLICY),root,
                      dict(baseline='base',optimized='opt'),{c:'synth' for c in v6.CASES},
                      cpu_execute=execute,memory_execute=execute)
            self.assertEqual(rc,0)
            self.assertEqual(calls,[False]*8+[True]*8)
            rows=json.loads((root/'09_时间内存开销_performance/round01/performance_summary.json').read_text(encoding='utf-8'))
            self.assertTrue(all(v6.judge_case(r)['pass'] for r in rows))
            self._assert_absolute_limit_blocks_report(root/'report-test',rows)
            rows[0]['execution_complete']=False
            self.assertEqual(v6.judge_case(rows[0])['cpu_verdict'],'INVALID')


    def _assert_absolute_limit_blocks_report(self,root,rows):
        import copy
        import report
        from test_validation import BuiltinModeTests
        BuiltinModeTests()._write_builtin_round(root)
        def load(rel):return json.loads((root/rel).read_text())
        def save(rel,d):(root/rel).write_text(json.dumps(d))
        ctx=load('validation_context.json')
        ctx.update(flow_version='official4-p6-windows',performance_scheme=v6.SCHEME,performance_pairs=1)
        save('validation_context.json',ctx)
        pub=load('05_公开四例_public/round01/summary.json')
        pub['public_mean_logic_reduction_pct']=20
        for r in pub['cases']:
            r.update(resource_checks_ok=True,io_nonincrease=True,other_resources_nonincrease=True,logic_reduction_pct=20)
            for side,n in [('baseline',100),('optimized',80)]:
                r.update({side+'_lut_count':n,side+'_inverter_count':0,side+'_logic_units':n,
                          side+'_abc9_ok':True,side+'_formal_netlist_stage':'post_abc',side+'_split_full_resources_match':True,
                          side+'_resources':dict(logic_units=n,dff_count=10,io_ports=2,io_bits=2,other_cell_types={})})
        save('05_公开四例_public/round01/summary.json',pub)
        chains=load('10_验证工具自检_selfcheck/chains/run01/chains_summary.json')
        for r in chains:r['formal_netlist_stage']='post_abc'
        save('10_验证工具自检_selfcheck/chains/run01/chains_summary.json',chains)
        samples=copy.deepcopy(rows)
        for r in samples[0]['cpu_runs']:
            t=590000000 if r['side']=='baseline' else 610000000
            r['runtime'].update(cpu_user_ticks=t,cpu_kernel_ticks=0,cpu_total_ticks=t)
        save('09_时间内存开销_performance/round01/performance_summary.json',samples)
        report.build_builtin_report(root)
        result=load('11_汇总与证据_summary/manifest.json')
        self.assertEqual(result['category_status']['cpu'],'PASS')
        self.assertFalse(result['performance'][0]['limit_ok'])
        self.assertEqual(result['verification_verdict'],'FAIL')


    def test_selfcheck_cache_requires_intact_evidence(self):
        sys.path.insert(0,str(Path(__file__).parent))
        import validate
        fp={'performance_scheme':v6.SCHEME}
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);proof=root/'proof.json';proof.write_text('{"selftest_ok":true}')
            entry=dict(ok=True,fingerprint=fp,measurement_evidence=dict(path=str(proof),sha256=validate.digest(proof)))
            cache={'entries':{'measurement_selfcheck':entry}}
            self.assertTrue(validate.cache_entry_valid(cache,'measurement_selfcheck',fp))
            proof.write_text('changed')
            self.assertFalse(validate.cache_entry_valid(cache,'measurement_selfcheck',fp))

if __name__=='__main__': unittest.main()
