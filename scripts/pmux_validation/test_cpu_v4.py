"""Mean CPU policy tests; synthetic measurements never qualify a real method."""
import copy
import importlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
import subprocess
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent / 'runner'))


def samples(percent=3, blocks=20, pairs=15):
    rows=[]
    for block in range(1,blocks+1):
        for pair in range(1,pairs+1):
            for side in ('baseline','optimized'):
                ticks=10_000_000 if side=='baseline' else round(10_000_000*(1+percent/100))
                rows.append(dict(side=side,block=block,pair=pair,rc=0,timed_out=False,
                    metrics_valid=True,measurement_error=None,root_debugged=False,
                    cpu_descendants_included=True,cpu_user_ticks=ticks,cpu_kernel_ticks=0,
                    cpu_total_ticks=ticks,stat_exists=True,resource_match=True,flow_match=True,
                    execution_kind='synthesis'))
    return rows


class CpuV4Tests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('cpu_statistics'), 'v4 statistics missing')
        self.S=importlib.import_module('cpu_statistics')

    def test_mean_and_full_block_interval(self):
        r=self.S.analyse_cpu_runs(samples(3))
        self.assertTrue(r['valid'])
        self.assertAlmostEqual(r['baseline_mean_s'],1)
        self.assertAlmostEqual(r['optimized_mean_s'],1.03)
        self.assertAlmostEqual(r['overhead_pct'],3)
        self.assertAlmostEqual(r['ci95_pct'][0],3)
        self.assertEqual(self.S.judge_cpu(r,qualified=True,guard_pct=.2,aa_ok=True)['cpu_verdict'],'PASS')

    def test_crossing_boundary_is_inconclusive_even_if_point_passes(self):
        r=self.S.analyse_cpu_runs(samples(4.84))
        j=self.S.judge_cpu(r,qualified=True,guard_pct=.3,aa_ok=True)
        self.assertTrue(j['cpu_point_requirement_met'])
        self.assertEqual(j['cpu_verdict'],'INCONCLUSIVE')

    def test_fail_and_exact_boundary(self):
        for percent,expected in [(8,'FAIL'),(5,'PASS')]:
            r=self.S.analyse_cpu_runs(samples(percent))
            self.assertEqual(self.S.judge_cpu(r,qualified=True,guard_pct=0,aa_ok=True)['cpu_verdict'],expected)

    def test_no_qualification_or_aa_failure_cannot_pass(self):
        r=self.S.analyse_cpu_runs(samples(0))
        for qualified,aa in [(False,True),(True,False)]:
            self.assertEqual(self.S.judge_cpu(r,qualified=qualified,guard_pct=0,aa_ok=aa)['cpu_verdict'],'INCONCLUSIVE')

    def test_missing_duplicate_corrupt_or_debugged_sample_invalidates_mean(self):
        good=samples()
        changes=[good[:-1],good+[good[0]],copy.deepcopy(good),copy.deepcopy(good),copy.deepcopy(good)]
        changes[2][0]['cpu_total_ticks']+=1
        changes[3][0]['root_debugged']=True
        changes[4][0]['resource_match']=False
        for rows in changes:
            r=self.S.analyse_cpu_runs(rows)
            self.assertFalse(r['valid'])
            self.assertIsNone(r['baseline_mean_s'])
            self.assertEqual(self.S.judge_cpu(r,qualified=True,guard_pct=0,aa_ok=True)['cpu_verdict'],'INVALID')

    def test_slow_sample_kept_and_bootstrap_repeatable(self):
        rows=samples(0)
        rows[1]['cpu_user_ticks']=rows[1]['cpu_total_ticks']=100_000_000
        a=self.S.analyse_cpu_runs(rows)
        b=self.S.analyse_cpu_runs(rows)
        self.assertAlmostEqual(a['optimized_mean_s'],1.03)
        self.assertEqual(a['ci95_pct'],b['ci95_pct'])
        self.assertEqual(a['optimized_max_s'],10)

    def test_aa_fake_difference_and_zero_reference(self):
        for percent,ok in [(0,True),(10,False)]:
            r=self.S.analyse_cpu_runs(samples(percent,pairs=5),pairs_per_block=5)
            self.assertEqual(self.S.aa_is_healthy(r),ok)

    def test_reference_difference_uses_same_draws_and_preserves_pairing(self):
        rows=samples(4,blocks=10,pairs=10)
        for row in rows:
            row['cpu_reference_ticks']=10_000_000 if row['side']=='baseline' else 10_300_000
        r=self.S.analyse_reference_difference(rows,blocks=10,pairs_per_block=10)
        self.assertAlmostEqual(r['guard_pct'],1)
        self.assertTrue(r['valid'])
        rows[0]['cpu_reference_ticks']=None
        self.assertFalse(self.S.analyse_reference_difference(rows,blocks=10,pairs_per_block=10)['valid'])


class ScheduleAndQualificationTests(unittest.TestCase):
    def test_failed_agreement_guard_stops_before_tracking_impact(self):
        import qualify_cpu_method as Q
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);calls=[]
            class FakeRecorder:
                def __init__(self,*args):pass
                def start(self):pass
                def stop(self,*args):return root/'reference.etl'
                def close(self):pass
            def measured(command,*,cwd,log_path,timeout_s):
                calls.append(command);(cwd/'stat.json').write_text('{}')
                return dict(rc=0,timed_out=False,metrics_valid=True,measurement_error=None,root_debugged=False,
                    cpu_descendants_included=True,cpu_user_ticks=1000000,cpu_kernel_ticks=0,cpu_total_ticks=1000000)
            cfg={'tools':{'compiler':{'path':str(root/'c++.exe')}},'ascii_bridge':str(root)}
            with patch.object(Q,'fingerprint',return_value={}),patch.object(Q,'qualification_status',return_value={'qualified':False}),\
                 patch.object(Q.subprocess,'run',return_value=type('Built',(),{'returncode':0,'stdout':'','stderr':''})()),\
                 patch.object(Q,'sha_file',return_value='synthetic'),patch.object(Q,'Recorder',FakeRecorder),\
                 patch.object(Q,'run_cpu_measured',side_effect=measured),patch.object(Q,'resource_signature',return_value={}),\
                 patch.object(Q,'export_trace',return_value=root),patch.object(Q,'read_reference',side_effect=lambda path,rows:rows),\
                 patch.object(Q,'analyse_reference_difference',return_value={'valid':True,'guard_pct':1.1}):
                cfg['cpu_reference_tools']={'xperf':'synthetic'}
                rc=Q.qualify(cfg,root,{'baseline':Path('base')},{c:'flow\n' for c in ('test1','test2','test3','test4')})
            self.assertEqual(rc,1)
            self.assertEqual(len(calls),1400,'failed qualification must not start 200 tracking-impact targets')
            out=root/'10_验证工具自检_selfcheck/cpu_method_qualification'
            result=json.loads((out/'qualification_result.json').read_text())
            self.assertIn('exceeds 1',result['error'])
            self.assertTrue((out/'diagnostic_means.json').is_file())

    def test_evidence_hash_streams_instead_of_reading_entire_trace(self):
        import cpu_qualification as Q
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'trace.etl';path.write_bytes(b'abc'*500000)
            expected=hashlib.sha256(b'abc'*500000).hexdigest()
            with patch.object(Path,'read_bytes',side_effect=MemoryError('entire ETW export is too large')):
                self.assertEqual(Q.sha_file(path),expected)

    def test_teardown_cpu_requires_terminal_switch_and_no_global_tid_reuse(self):
        from etw_reference import read_reference
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'events.csv'
            text='''BeginHeader
P-Start, TimeStamp, Process Name ( PID), ParentPID, SessionID, UniqueKey
P-End, TimeStamp, Process Name ( PID), ParentPID, SessionID, UniqueKey
T-Start, TimeStamp, Process Name ( PID), ThreadID
T-End, TimeStamp, Process Name ( PID), ThreadID
CSwitch, TimeStamp, Old Process Name ( PID), Old TID, InSwitchTime, OldState, CPU
DPC_ISR_CSWITCH_PCT, TimeStamp, StartTime, Period, IsrDpc, OldPid, OldTid, CPU
EndHeader
OS Version: test, Events Lost: 0, Buffers lost: 0, Trace Start: 1000000
P-Start, 10000, parent.exe (7), 1, 1, 0x2
T-Start, 10100, parent.exe (7), 30
CSwitch, 10200, parent.exe (7), 30, 80, Waiting, 0
DPC_ISR_CSWITCH_PCT, 10200, 0, 80, 0, 7, 30, 0
T-End, 10500, parent.exe (7), 30
P-End, 10600, parent.exe (7), 1, 1, 0x2
CSwitch, 16000, parent.exe (7), 30, 20, Waiting, 0
DPC_ISR_CSWITCH_PCT, 16000, 0, 20, 0, 7, 30, 0
CSwitch, 90000, parent.exe (7), 30, 10, Terminated, 0
DPC_ISR_CSWITCH_PCT, 90000, 0, 10, 0, 7, 30, 0
'''
            p.write_text(text)
            sample=dict(main_pid=7,process_create_filetime=1100000,process_exit_filetime=1106000,job_total_processes=1)
            r=read_reference(p,[sample])[0]
            self.assertEqual(r['cpu_reference_ticks'],1100,'complete teardown CPU must not depend on a 5ms delay cap')
            p.write_text(text.replace('CSwitch, 16000, parent.exe (7), 30, 20, Waiting, 0\nDPC_ISR_CSWITCH_PCT, 16000, 0, 20, 0, 7, 30, 0\n','').replace('CSwitch, 90000, parent.exe (7), 30, 10, Terminated, 0\nDPC_ISR_CSWITCH_PCT, 90000, 0, 10, 0, 7, 30, 0\n',''))
            with self.assertRaises(ValueError):read_reference(p,[sample])
            p.write_text(text.replace(', 10, Terminated',', 10, Waiting'))
            with self.assertRaises(ValueError):read_reference(p,[sample])
            p.write_text(text.replace('CSwitch, 90000','T-Start, 20000, other.exe (9), 30\nCSwitch, 90000'))
            with self.assertRaises(ValueError):read_reference(p,[sample])

    def test_missing_reference_dependency_blocks_before_run(self):
        import validate as V
        from cpu_statistics import POLICY,SCHEME
        self.assertTrue(hasattr(V,'validate_performance_policy'),'v4 reference dependency preflight missing')
        with self.assertRaises(ValueError):
            V.validate_performance_policy({'performance_scheme':SCHEME,'cpu_policy':POLICY,'cpu_reference_tools':{}})
        with self.assertRaises(ValueError):
            V.validate_performance_policy({'performance_scheme':SCHEME,'cpu_policy':POLICY,
                'cpu_reference_tools':{'wpr':'missing-wpr.exe','xperf':'missing-xperf.exe'}})

    def test_unknown_summary_scheme_cannot_infer_legacy_median(self):
        import report as R
        rows=[dict(side=s,rc=0,timed_out=False,stat_exists=True,cpu_total_s=1,tree_rss_peak_kb=10000) for s in ('baseline','optimized')]
        s=dict(case='test2',performance_scheme='unknown-future-method',runs=rows,
               baseline_cpu_total_median=1,optimized_cpu_total_median=1,
               baseline_tree_rss_peak_median=10000,optimized_tree_rss_peak_median=10000)
        self.assertFalse(R.judge_case_performance(s,pairs=1)['pass'])

    def test_collector_launch_timeout_leaves_diagnostic_evidence(self):
        from etw_reference import Recorder
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'collector'
            with patch('etw_reference.subprocess.run',side_effect=subprocess.TimeoutExpired('private collector launch',120)):
                with self.assertRaises(subprocess.TimeoutExpired):Recorder(root)
            self.assertTrue((root/'collector_launch_error.json').is_file())
            self.assertTrue((root/'elevation.log').is_file())

    def test_collector_cleanup_releases_an_uncertain_start(self):
        from etw_reference import Recorder
        obj=Recorder.__new__(Recorder);obj.owned=False;obj.sequence=0
        server={'owned':True,'preserved':False}
        def protocol(action,name=None):
            if action=='abort':server.update(owned=False,preserved=True)
            elif action=='finish' and server['owned']:raise RuntimeError('server owns an unacknowledged recording')
        obj.request=protocol
        error=None
        try:obj.close()
        except RuntimeError as exc:error=str(exc)
        self.assertIsNone(error,'uncertain start must not leave a private recording active')
        self.assertFalse(server['owned'])
        self.assertTrue(server['preserved'])

    def test_fingerprint_uses_actual_build_and_flow_not_algorithm_commit(self):
        import cpu_qualification as Q
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);src=Path(__file__).parent/'runner'
            for p in src.iterdir():
                if p.is_file():(root/p.name).write_bytes(p.read_bytes())
            for name in ('baseline.exe','other.exe','abc.exe','c++.exe','gcc.exe'):(root/name).write_text(name)
            share=root/'share/yosys';(share/'intel/cycloneiv').mkdir(parents=True)
            (share/'intel/cycloneiv/cells_map.v').write_text('fixture')
            data=share/'techmap.v';data.write_text('original techmap')
            cfg=dict(repo=str(root),yosys_source=str(root),tools={k:{'path':str(root/n),'sha256':'declared'} for k,n in [('yosys','baseline.exe'),('abc','abc.exe'),('compiler','c++.exe')]},
                     builtin={'baseline':{'path':str(root/'baseline.exe')},'abc':{'baseline':str(root/'abc.exe')}},
                     cpu_reference_tools={},runtime_tools={},suite_manifest_sha256='frozen',target_commit='one')
            cfg['tool_data']=[{'path':str(data)}]
            cfg['tool_data_fourcase_filter']={'include_subpaths':[],'direct_share_files':['techmap.v']}
            with patch.object(Q,'environment',return_value={}),patch.object(Q.subprocess,'check_output',return_value='same-abc-source'):
                first=Q.fingerprint(cfg,root)
                cfg['target_commit']='two'
                self.assertEqual(first,Q.fingerprint(cfg,root))
                cfg['builtin']['baseline']['path']=str(root/'other.exe')
                self.assertNotEqual(first,Q.fingerprint(cfg,root),'actual baseline build must invalidate qualification')
                cfg['builtin']['baseline']['path']=str(root/'baseline.exe')
                (root/'p3_common.py').write_text('changed flow generator')
                self.assertNotEqual(first,Q.fingerprint(cfg,root),'flow changes must invalidate qualification')
                (root/'p3_common.py').write_bytes((src/'p3_common.py').read_bytes())
                data.write_text('changed techmap')
                self.assertNotEqual(first,Q.fingerprint(cfg,root),'actual tool data must invalidate qualification')

    def test_reused_thread_id_cannot_hide_missing_end_event(self):
        from etw_reference import read_reference
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'events.csv'
            p.write_text('''BeginHeader
P-Start, TimeStamp, Process Name ( PID), ParentPID, SessionID, UniqueKey
P-End, TimeStamp, Process Name ( PID), ParentPID, SessionID, UniqueKey
T-Start, TimeStamp, Process Name ( PID), ThreadID
T-End, TimeStamp, Process Name ( PID), ThreadID
CSwitch, TimeStamp, Old Process Name ( PID), Old TID, InSwitchTime, OldState, CPU
DPC_ISR_CSWITCH_PCT, TimeStamp, StartTime, Period, IsrDpc, OldPid, OldTid, CPU
EndHeader
OS Version: test, Events Lost: 0, Buffers lost: 0, Trace Start: 1000000
P-Start, 10000, parent.exe (7), 1, 1, 0x2
T-Start, 10110, parent.exe (7), 30
CSwitch, 10200, parent.exe (7), 30, 80, Terminated, 0
DPC_ISR_CSWITCH_PCT, 10200, 0, 80, 0, 7, 30, 0
T-End, 10210, parent.exe (7), 30
T-Start, 10300, parent.exe (7), 30
CSwitch, 10400, parent.exe (7), 30, 80, Terminated, 0
DPC_ISR_CSWITCH_PCT, 10400, 0, 80, 0, 7, 30, 0
P-End, 10500, parent.exe (7), 1, 1, 0x2
''')
            r=dict(main_pid=7,process_create_filetime=1100000,process_exit_filetime=1105000,job_total_processes=1)
            with self.assertRaises(ValueError):read_reference(p,[r])

    def test_v4_absolute_limits_and_unique_cases_remain_blocking(self):
        import report as R
        self.assertTrue(hasattr(R,'v4_non_cpu_performance_ok'),'v4 structural performance gate missing')
        rows=[dict(case=c,valid=True,limit_ok=True) for c in ('test1','test2','test3','test4')]
        self.assertTrue(R.v4_non_cpu_performance_ok(rows))
        rows[0]['limit_ok']=False
        self.assertFalse(R.v4_non_cpu_performance_ok(rows))
        rows[0]['limit_ok']=True;rows[0]['case']='test2'
        self.assertFalse(R.v4_non_cpu_performance_ok(rows))

    def test_executor_stops_on_first_invalid_without_replacement(self):
        import measure_v4 as M
        from cpu_statistics import POLICY
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for case in M.CASES:
                for side in ('baseline','optimized'):
                    d=root/f'05_公开四例_public/round01/{case}/{side}';d.mkdir(parents=True)
                    (d/'stat.json').write_text(json.dumps({'design':{'num_cells_by_type':{'lut':1}}}))
            calls=[]
            def failed(cmd,*,cwd,log_path,timeout_s):
                calls.append(cmd)
                (cwd/'stat.json').write_text(json.dumps({'design':{'num_cells_by_type':{'lut':1}}}))
                log_path.write_text('intentional measurement selftest failure')
                return dict(rc=7,timed_out=False,metrics_valid=True,measurement_error=None,root_debugged=False,
                            cpu_descendants_included=True,cpu_user_ticks=10,cpu_kernel_ticks=0,cpu_total_ticks=10)
            qual={'qualified':True,'certificate':{},'fingerprint':{}}
            with patch.object(M,'qualification_status',return_value=qual),patch.object(M,'environment',return_value={}):
                rc=M.run({'cpu_policy':POLICY},root,{'baseline':Path('base'),'optimized':Path('opt')},
                         {c:'flow\n' for c in M.CASES},cpu_execute=failed,memory_execute=failed)
            self.assertEqual(rc,1)
            self.assertEqual(len(calls),1)
            status=json.loads((root/'09_时间内存开销_performance/round01/execution_status.json').read_text())
            self.assertFalse(status['complete'])
            result=json.loads((root/'09_时间内存开销_performance/round01/performance_summary.json').read_text())
            self.assertTrue(all(s['cpu_statistics']['baseline_mean_s'] is None for s in result))

    def test_complete_executor_keeps_aa_separate_and_memory_after_cpu(self):
        import measure_v4 as M
        from cpu_statistics import POLICY
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for case in M.CASES:
                for side in ('baseline','optimized'):
                    d=root/f'05_公开四例_public/round01/{case}/{side}';d.mkdir(parents=True)
                    (d/'stat.json').write_text(json.dumps({'design':{'num_cells_by_type':{'lut':1}}}))
            purposes=[]
            def fake(cmd,*,cwd,log_path,timeout_s):
                memory='memory' in cwd.parts;purposes.append('memory' if memory else 'cpu')
                (cwd/'stat.json').write_text(json.dumps({'design':{'num_cells_by_type':{'lut':1}}}))
                log_path.write_text('synthetic scheduler selftest; no native measurement')
                ticks=1030000 if str(cmd[0])=='opt' else 1000000
                return dict(rc=0,timed_out=False,metrics_valid=True,measurement_error=None,root_debugged=memory,
                    cpu_descendants_included=True,cpu_user_ticks=ticks,cpu_kernel_ticks=0,cpu_total_ticks=ticks,
                    memory_capture_complete=memory,memory_exit_event_observed=memory,memory_method_version='windows-root-exit-event-v1',
                    main_pid=1,memory_exit_event_pid=1,yosys_peak_working_set_bytes=10000)
            qual={'qualified':True,'certificate':{'guard_pct':0},'fingerprint':{}}
            with patch.object(M,'qualification_status',return_value=qual),patch.object(M,'environment',return_value={}):
                rc=M.run({'cpu_policy':POLICY},root,{'baseline':Path('base'),'optimized':Path('opt')},
                         {c:'flow\n' for c in M.CASES},cpu_execute=fake,memory_execute=fake)
            self.assertEqual(rc,0)
            self.assertEqual(purposes,['cpu']*2600+['memory']*120)
            out=root/'09_时间内存开销_performance/round01'
            rows=json.loads((out/'performance_summary.json').read_text())
            for row in rows:
                self.assertEqual(len(row['cpu_runs']),600)
                self.assertEqual(len(row['memory_runs']),30)
                self.assertAlmostEqual(row['cpu_statistics']['overhead_pct'],3)
                self.assertEqual(row['cpu_decision']['cpu_verdict'],'PASS')
            self.assertEqual(len(json.loads((out/'aa_raw.json').read_text())),200)

    def test_report_uses_mean_and_inconclusive_not_cpu_fail(self):
        import report as R
        with tempfile.TemporaryDirectory() as tmp:
            from cpu_qualification import sha_file
            root=Path(tmp);fp={'method':'unit-test'}
            proof=root/'qualification_result.json';proof.write_text(json.dumps(dict(ok=True,guard_pct=.3,fingerprint=fp)))
            cert=dict(ok=True,guard_pct=.3,fingerprint=fp,evidence_root=str(root),evidence_sha256={'qualification_result.json':sha_file(proof)})
            mem=[]
            for side in ('baseline','optimized'):
                for pair in range(1,16):
                    mem.append(dict(side=side,pair=pair,rc=0,timed_out=False,metrics_valid=True,
                        measurement_error=None,root_debugged=True,stat_exists=True,resource_match=True,flow_match=True,
                        memory_capture_complete=True,memory_exit_event_observed=True,memory_method_version='windows-root-exit-event-v1',
                        main_pid=1,memory_exit_event_pid=1,yosys_peak_working_set_bytes=10000))
            from cpu_statistics import POLICY,SCHEME
            cpu=samples(4.84)
            for row in cpu:row['performance_scheme']=SCHEME
            summ=dict(case='test2',performance_scheme=SCHEME,cpu_policy=POLICY,cpu_runs=cpu,memory_runs=mem,
                      aa_runs=samples(0,pairs=5),method_certificate=cert,qualification_fingerprint=fp)
            j=R.judge_case_performance(summ)
            self.assertEqual(j.get('cpu_verdict'),'INCONCLUSIVE')
            self.assertAlmostEqual(j['base_cpu_s'],1)
            self.assertAlmostEqual(j['opt_cpu_s'],1.0484)
            self.assertTrue(j['mem_ok'])
            self.assertNotIn('CPU 相对开销超过 5%',j['reasons'])
            self.assertEqual(R.verification_verdict_v4({'cpu':'INCONCLUSIVE','formal':'PASS','resources':'PASS','memory':'PASS'},True),'INCONCLUSIVE')
            self.assertEqual(R.verification_verdict_v4({'cpu':'INCONCLUSIVE','formal':'FAIL','resources':'PASS','memory':'PASS'},True),'FAIL')

    def test_etw_process_reuse_and_lost_event_rejected(self):
        E=importlib.import_module('etw_reference')
        self.assertTrue(hasattr(E,'read_reference'),'ETW reference analysis missing')
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'events.csv'
            text='''BeginHeader
P-Start, TimeStamp, Process Name ( PID), ParentPID, SessionID, UniqueKey
P-End, TimeStamp, Process Name ( PID), ParentPID, SessionID, UniqueKey
T-Start, TimeStamp, Process Name ( PID), ThreadID
T-End, TimeStamp, Process Name ( PID), ThreadID
CSwitch, TimeStamp, Old Process Name ( PID), Old TID, InSwitchTime, OldState, CPU
DPC_ISR_CSWITCH_PCT, TimeStamp, StartTime, Period, IsrDpc, OldPid, OldTid, CPU
EndHeader
OS Version: test, Events Lost: 0, Buffers lost: 0, Trace Start: 1000000
P-Start, 10, old.exe (7), 1, 1, 0x1
P-End, 20, old.exe (7), 1, 1, 0x1
P-Start, 10000, parent.exe (7), 1, 1, 0x2
T-Start, 10000, parent.exe (7), 30
P-Start, 12000, child.exe (8), 7, 1, 0x3
T-Start, 12000, child.exe (8), 31
CSwitch, 13500, parent.exe (7), 30, 100, Terminated, 0
DPC_ISR_CSWITCH_PCT, 13500, 0, 100, 0, 7, 30, 0
CSwitch, 14000, child.exe (8), 31, 150, Terminated, 0
DPC_ISR_CSWITCH_PCT, 14000, 0, 150, 0, 8, 31, 0
T-End, 15000, child.exe (8), 31
P-End, 15000, child.exe (8), 7, 1, 0x3
T-End, 16000, parent.exe (7), 30
P-End, 16000, parent.exe (7), 1, 1, 0x2
'''
            p.write_text(text)
            sample=dict(main_pid=7,process_create_filetime=1100000,process_exit_filetime=1160000,job_total_processes=2)
            r=E.read_reference(p,[sample])[0]
            self.assertEqual(r['cpu_reference_ticks'],2500)
            with self.assertRaises(ValueError):E.read_reference(p,[sample,sample])
            shifted=dict(sample,process_create_filetime=sample['process_create_filetime']+900000,
                         process_exit_filetime=sample['process_exit_filetime']+900000)
            with self.assertRaises(ValueError):E.read_reference(p,[shifted])
            p.write_text(text.replace('Events Lost: 0','Events Lost: 1'))
            with self.assertRaises(ValueError):E.read_reference(p,[sample])

    def test_fixed_schedule_balanced_and_memory_last(self):
        self.assertIsNotNone(importlib.util.find_spec('measure_v4'),'v4 scheduling missing')
        M=importlib.import_module('measure_v4')
        rows=list(M.schedule())
        self.assertEqual(len(rows),2720)
        self.assertEqual(sum(r['purpose']=='cpu' for r in rows),2400)
        self.assertEqual(sum(r['purpose']=='aa' for r in rows),200)
        self.assertEqual(sum(r['purpose']=='memory' for r in rows),120)
        self.assertTrue(all(r['purpose']=='memory' for r in rows[2600:]))
        for case in ('test1','test2','test3','test4'):
            self.assertEqual(sum(r['case']==case and r['purpose']=='cpu' and r['side']=='baseline' for r in rows),300)
            first=[r['side'] for r in rows if r['case']==case and r['purpose']=='cpu' and r['pair']==1]
            self.assertEqual(first.count('baseline'),first.count('optimized'))

    def test_qualification_requires_attested_evidence_and_guard(self):
        self.assertIsNotNone(importlib.util.find_spec('cpu_qualification'),'qualification missing')
        Q=importlib.import_module('cpu_qualification')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);evidence=root/'qualification_result.json'
            fingerprint={'method':'test'}
            evidence.write_text(json.dumps(dict(ok=True,guard_pct=.2,fingerprint=fingerprint)))
            cert=dict(ok=True,fingerprint=fingerprint,guard_pct=.2,evidence_root=str(root),
                      evidence_sha256={'qualification_result.json':Q.sha_file(evidence)})
            self.assertTrue(Q.certificate_valid(cert,fingerprint)[0])
            evidence.write_text('changed')
            self.assertFalse(Q.certificate_valid(cert,fingerprint)[0])
            cert['evidence_sha256']={}
            self.assertFalse(Q.certificate_valid(cert,fingerprint)[0])
            self.assertFalse(Q.certificate_valid(dict(cert,guard_pct=1.1),fingerprint)[0])
            self.assertFalse(Q.certificate_valid(cert,{'method':'other'})[0])


if __name__=='__main__': unittest.main()
