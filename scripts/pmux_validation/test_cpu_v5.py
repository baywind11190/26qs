"""Synthetic evidence tests; these never qualify a real ETW method."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
PACKAGE=Path('D:/codex/0000_26qs/scripts/pmux_validation')
sys.path[:0]=[str(PACKAGE),str(PACKAGE/'runner')]

def rows(percent=4):
    import cpu_statistics_v5 as S
    result=[]
    for b in range(1,21):
        for p in range(1,16):
            for side in ('baseline','optimized'):
                t=1_000_000 if side=='baseline' else round(1_000_000*(1+percent/100))
                result.append(dict(block=b,pair=p,side=side,rc=0,timed_out=False,metrics_valid=True,
                    measurement_error=None,root_debugged=False,cpu_descendants_included=True,
                    cpu_user_ticks=99_000_000,cpu_kernel_ticks=1_000_000,cpu_total_ticks=100_000_000,
                    wall_s=999,stat_exists=True,resource_match=True,flow_match=True,
                    execution_kind='synthesis',performance_scheme=S.SCHEME,cpu_primary_method=S.METHOD,
                    cpu_etw_total_ticks=t,etw_capture_complete=True,reference_events_lost=0,
                    reference_buffers_lost=0,job_total_processes=1,reference_processes=[dict(cpu_us=t//10)]))
    return result

class Statistics(unittest.TestCase):
    def test_event_mean_and_exact_integer_boundary(self):
        import cpu_statistics_v5 as S
        for percent,verdict in [(4,'PASS'),(5,'PASS'),(5.001,'FAIL')]:
            stats=S.analyse_cpu_runs(rows(percent))
            self.assertTrue(stats['valid']);self.assertEqual(S.judge_cpu(stats)['cpu_verdict'],verdict)
            self.assertAlmostEqual(stats['baseline_mean_s'],.1)
    def test_job_wall_interval_and_aa_difference_do_not_grade(self):
        import cpu_statistics_v5 as S
        r=rows(4);r[0]['wall_s']=100000
        stats=S.analyse_cpu_runs(r);stats['ci95_pct']=[-4,12]
        self.assertEqual(S.judge_cpu(stats)['cpu_verdict'],'PASS')
        self.assertEqual(r[0]['cpu_user_ticks'],99_000_000)
    def test_invalid_event_never_falls_back_to_job(self):
        import cpu_statistics_v5 as S
        variants=[rows()[:-1],rows()+[rows()[0]]]
        for key,value in [('cpu_etw_total_ticks',None),('reference_events_lost',1),
                          ('etw_capture_complete',False),('cpu_primary_method','Job'),
                          ('job_total_processes',2),('performance_scheme','unknown')]:
            r=rows();r[0][key]=value;variants.append(r)
        for r in variants:
            self.assertFalse(S.analyse_cpu_runs(r)['valid'])
            self.assertEqual(S.judge_cpu(S.analyse_cpu_runs(r))['cpu_verdict'],'INVALID')
    def test_event_sum_and_raw_precision_checked(self):
        import cpu_statistics_v5 as S
        r=rows();r[0]['cpu_etw_total_ticks']+=1
        self.assertFalse(S.analyse_cpu_runs(r)['valid'])
    def test_slow_event_is_kept(self):
        import cpu_statistics_v5 as S
        r=rows(0);r[1]['cpu_etw_total_ticks']=40_000_000;r[1]['reference_processes']=[dict(cpu_us=4_000_000)]
        stats=S.analyse_cpu_runs(r)
        self.assertTrue(stats['valid']);self.assertGreater(stats['optimized_mean_s'],.1)
        self.assertEqual(stats['optimized_total_ticks'],sum(x['cpu_etw_total_ticks'] for x in r if x['side']=='optimized'))

class Integration(unittest.TestCase):
    def execute_fake(self,root,fail_trace=False,expire=False,fail_memory=False,expire_stats=False):
        import measure_v5 as M
        import cpu_statistics_v5 as S
        log=[];clock=[0]
        stat={'design':{'num_cells_by_type':{'lut':5},'num_ports':1,'num_port_bits':1}}
        for case in M.CASES:
            for side in ('baseline','optimized'):
                d=root/f'05_公开四例_public/round01/{case}/{side}';d.mkdir(parents=True)
                (d/'stat.json').write_text(json.dumps(stat))
        class Rec:
            def __init__(self,p):self.root=p;p.mkdir(parents=True);self.active=False
            def start(self):self.active=True;log.append('start')
            def stop(self,name):
                self.active=False;log.append('stop');p=self.root/(name+'.etl');p.write_bytes(b'synthetic');return p
            def close(self):self.active=False;log.append('close')
        def sample(cmd,*,cwd,log_path,timeout_s,memory=False):
            log.append('memory' if memory else 'cpu')
            if expire:clock[0]=1801
            (cwd/'stat.json').write_text(json.dumps(stat))
            r=dict(rc=0,timed_out=False,metrics_valid=True,measurement_error=None,root_debugged=memory,
                   cpu_descendants_included=True,cpu_user_ticks=900000,cpu_kernel_ticks=100000,cpu_total_ticks=1000000,
                   wall_s=.2,main_pid=len(log),process_create_filetime=len(log)*1000,process_exit_filetime=len(log)*1000+10,job_total_processes=1)
            if memory:r.update(memory_capture_complete=True,memory_exit_event_observed=True,memory_exit_event_pid=r['main_pid'],
                               memory_method_version='windows-root-exit-event-v1',yosys_peak_working_set_bytes=1000)
            if memory and fail_memory:r['memory_capture_complete']=False
            return r
        def analyse(etl,rows,context,out,remaining):
            log.append('analyse')
            if fail_trace:raise ValueError('synthetic missing/lost event')
            result=[]
            for row in rows:
                t=1120000 if row['purpose']=='aa' and row['side']=='optimized' else 1040000 if row['actual_side']=='optimized' else 1000000
                result.append(dict(row,cpu_etw_total_ticks=t,etw_capture_complete=True,reference_events_lost=0,
                                   reference_buffers_lost=0,reference_processes=[dict(cpu_us=t//10)]))
            return result
        cfg=dict(performance_scheme=S.SCHEME,cpu_policy=S.POLICY)
        original_analyse=M.analyse_cpu_runs
        def final_stats(*a,**kw):
            result=original_analyse(*a,**kw)
            if expire_stats:clock[0]=1801
            return result
        with patch.object(M,'environment',return_value={}),patch.object(M.time,'monotonic',side_effect=lambda:clock[0]),patch.object(M,'analyse_cpu_runs',side_effect=final_stats):
            rc=M.run(cfg,root,{'baseline':Path('b'),'optimized':Path('o')},{c:'flow\n' for c in M.CASES},
                cpu_execute=sample,memory_execute=lambda *a,**kw:sample(*a,memory=True,**kw),
                recorder_factory=Rec,trace_analyser=analyse,
                selfcheck_provider=lambda *a:dict(qualified=True,certificate={},fingerprint={}))
        return rc,log,root/'09_时间内存开销_performance/round01'
    def test_fixed_2720_runs_and_memory_after_analysis(self):
        with tempfile.TemporaryDirectory() as t:
            rc,log,out=self.execute_fake(Path(t))
            self.assertEqual(rc,0);self.assertEqual(log.count('cpu'),2600);self.assertEqual(log.count('memory'),120)
            self.assertEqual(log.count('start'),20);self.assertEqual(log.count('stop'),20)
            self.assertLess(max(i for i,x in enumerate(log) if x=='analyse'),log.index('memory'))
            summaries=json.loads((out/'performance_summary.json').read_text(encoding='utf-8'))
            self.assertTrue(all(s['cpu_decision']['cpu_verdict']=='PASS' and s['quality_warnings'] for s in summaries))
    def test_lost_event_stops_before_memory_and_no_job_fallback(self):
        with tempfile.TemporaryDirectory() as t:
            rc,log,out=self.execute_fake(Path(t),fail_trace=True)
            self.assertEqual(rc,1);self.assertEqual(log.count('memory'),0)
            self.assertTrue(all(s['cpu_decision']['cpu_verdict']=='INVALID' for s in json.loads((out/'performance_summary.json').read_text(encoding='utf-8'))))
    def test_deadline_preserves_invalid_first_sample(self):
        with tempfile.TemporaryDirectory() as t:
            rc,log,out=self.execute_fake(Path(t),expire=True)
            self.assertEqual(rc,1);self.assertEqual(log.count('cpu'),1);self.assertEqual(log.count('memory'),0)
            self.assertEqual(len(json.loads((out/'cpu_raw_all.json').read_text(encoding='utf-8'))),1)
    def test_memory_failure_cannot_leave_raw_cpu_pass(self):
        with tempfile.TemporaryDirectory() as t:
            rc,log,out=self.execute_fake(Path(t),fail_memory=True)
            self.assertEqual(rc,1)
            self.assertTrue(all(s['cpu_decision']['cpu_verdict']=='INVALID' for s in json.loads((out/'performance_summary.json').read_text(encoding='utf-8'))))
    def test_event_parser_deadline_is_checked_during_read(self):
        from etw_reference import read_reference
        from test_etw_interrupts import TRACE,SAMPLE
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'events.csv';p.write_text(TRACE)
            def expired():raise TimeoutError('deadline')
            with self.assertRaises(TimeoutError):read_reference(p,[SAMPLE],deadline_check=expired)
    def test_summary_time_is_inside_protection_limit(self):
        with tempfile.TemporaryDirectory() as t:
            rc,log,out=self.execute_fake(Path(t),expire_stats=True)
            self.assertEqual(rc,1)
            self.assertTrue(all(s['cpu_decision']['cpu_verdict']=='INVALID' for s in json.loads((out/'performance_summary.json').read_text(encoding='utf-8'))))
    def test_v5_preflight_requires_exact_policy_and_reference_tools(self):
        import validate as V
        import cpu_statistics_v5 as S
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'tool';p.write_bytes(b'test')
            cfg=dict(performance_scheme=S.SCHEME,cpu_policy=S.POLICY,cpu_reference_tools={'wpr':str(p),'xperf':str(p)})
            V.validate_performance_policy(cfg)
            cfg['cpu_policy']=dict(S.POLICY,blocks=2)
            with self.assertRaises(ValueError):V.validate_performance_policy(cfg)
    def test_v5_report_does_not_use_v4_certificate_or_ci(self):
        import report as R
        import cpu_statistics_v5 as S
        memory=[]
        for side in ('baseline','optimized'):
            for p in range(1,16):
                memory.append(dict(performance_scheme=S.SCHEME,side=side,pair=p,rc=0,timed_out=False,metrics_valid=True,
                    measurement_error=None,root_debugged=True,stat_exists=True,resource_match=True,flow_match=True,
                    memory_capture_complete=True,memory_exit_event_observed=True,memory_exit_event_pid=7,main_pid=7,
                    memory_method_version='windows-root-exit-event-v1',yosys_peak_working_set_bytes=1000))
        sample=rows(4);aa=[]
        for r in rows(12):
            if r['pair']<=5:aa.append(r)
        summary=dict(case='test2',performance_scheme=S.SCHEME,cpu_policy=S.POLICY,cpu_runs=sample,
                     memory_runs=memory,aa_runs=aa,execution_complete=True,method_selfcheck={},selfcheck_fingerprint={})
        with patch('cpu_selfcheck_v5.certificate_valid',return_value=(True,None)):
            judgment=R.judge_case_performance(summary)
        self.assertTrue(judgment['pass']);self.assertEqual(judgment['cpu_verdict'],'PASS')
        self.assertTrue(judgment['quality_warnings'])
    def test_cache_rejects_missing_or_tampered_evidence(self):
        import cpu_selfcheck_v5 as Q
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);proof=p/'result.json'
            proof.write_text(json.dumps(dict(ok=True,scope=Q.SCOPE,fingerprint={'x':1})),encoding='utf-8')
            cert=dict(ok=True,scope=Q.SCOPE,fingerprint={'x':1},evidence_root=str(p),
                      evidence_sha256={'result.json':Q.sha_file(proof)})
            self.assertTrue(Q.certificate_valid(cert,{'x':1})[0])
            proof.write_text('{}',encoding='utf-8');self.assertFalse(Q.certificate_valid(cert,{'x':1})[0])

if __name__=='__main__':unittest.main()
