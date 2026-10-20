import importlib.util
from pathlib import Path
import sys
import unittest

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))

class Contract(unittest.TestCase):
    def test_signed_residual_statistics_preserve_negative_samples(self):
        a=self.load()
        with self.assertRaises(ValueError):a.describe([-156250,0])
        result=a.describe([-156250,0,156250],allow_signed=True)
        self.assertEqual(result['minimum'],-156250)
        self.assertEqual(result['mean'],0)
        self.assertEqual(result['count'],3)

    def test_trace_uses_same_explicit_temp_directory_as_main_diagnostic(self):
        import json
        import trace_v2
        cfg=json.loads(Path('D:/codex/0000_26qs/scripts/pmux_validation/config.windows.json').read_text(encoding='utf-8'))
        env=trace_v2.target_environment(cfg,Path('D:/diag_work'))
        self.assertEqual([env[k] for k in ('TEMP','TMP','TMPDIR')],['D:\\diag_work']*3)

    def test_cpp_names_yosys_caller_root_instead_of_abc_parent(self):
        text=(HERE/'diag_v2_impl.inc').read_text(encoding='utf-8')
        self.assertNotIn(r'\"ppid\":%lu',text)
        self.assertIn(r'\"root_pid\":%lu',text)

    def test_trace_projection_ignores_non_utf8_metadata_without_touching_numeric_fields(self):
        import tempfile
        from analyze_trace_v2 import project
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);raw=b'FileVersion, bad\xae\nP-Start, TimeStamp, Process Name ( PID), ParentPID\nP-Start, 123, yosys.exe ( 7), 6\n'
            (root/'raw.csv').write_bytes(raw)
            project(root/'raw.csv',root/'projection.csv',{7})
            self.assertEqual((root/'raw.csv').read_bytes(),raw)
            self.assertEqual((root/'projection.csv').read_text(encoding='utf-8'),'P-Start, TimeStamp, Process Name ( PID), ParentPID\nP-Start, 123, yosys.exe ( 7), 6\n')

    def test_projection_keeps_matching_interrupt_record_by_header_not_fixed_column(self):
        import tempfile
        from analyze_trace_v2 import project
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);text='DPC_ISR_CSWITCH_PCT, TimeStamp, StartTime, Period, Formula, IsrDpc, OldPid, OldTid, CPU\nDPC_ISR_CSWITCH_PCT, 123, 0, 123, x, 0, 7, 8, 0\n'
            (root/'raw').write_text(text)
            project(root/'raw',root/'filtered',{7})
            self.assertEqual((root/'filtered').read_text(),text)

    def test_unknown_cpu_is_not_helper_and_abc_parent_is_not_root(self):
        a=self.load()
        native={'root_pid':1,'TotalProcesses':3,'processes':[dict(pid=1,created=1,ppid=9,image='yosys.exe',user=10,kernel=0),dict(pid=2,created=2,ppid=8,image='yosys-abc.exe',user=20,kernel=0),dict(pid=3,created=3,ppid=0,image='',user=30,kernel=0)]}
        r=a.classify_processes(native)
        self.assertTrue(r['process_cpu_complete']);self.assertFalse(r['process_metadata_complete'])
        self.assertEqual(r['helper_cpu'],0);self.assertEqual(r['unknown_cpu'],30)
        diag={'abc':[dict(pid=2,created=2,ppid=1)]}
        normalized=a.normalize_abc(diag,native)
        self.assertEqual(normalized['abc'][0]['ppid'],8)
        self.assertEqual(normalized['abc'][0]['root_pid'],1)
        self.assertEqual(diag['abc'][0]['ppid'],1)

    def test_protection_failure_blocks_complete_and_trace_has_remaining_budget(self):
        a=self.load()
        self.assertFalse(a.completion_status(100,None,False)['complete'])
        self.assertTrue(a.completion_status(100,None,True)['complete'])
        self.assertEqual(a.trace_timeout_ms(1799.5),500)
        with self.assertRaises(TimeoutError):a.trace_timeout_ms(1800)

    def test_final_manifest_covers_updated_trace_and_preserves_previous(self):
        import tempfile
        sys.path.insert(0,'D:/codex/0000_26qs/scripts/pmux_validation/runner')
        import tools_v2 as t
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'trace').mkdir();(root/'trace/status.json').write_text('pending')
            t.seal(root)
            previous=(root/'SHA256.json').read_bytes()
            (root/'trace/status.json').write_text('captured')
            t.seal(root,preserve_previous=True)
            self.assertEqual((root/'SHA256_before_trace.json').read_bytes(),previous)
            self.assertEqual(t.read(root/'SHA256.json')['trace/status.json'],t.sha(root/'trace/status.json'))

    def test_entry_import_does_not_require_official_round_context(self):
        import diagnose_v2
        self.assertEqual(diagnose_v2.COMMIT,'6862831899247fd0e8f5c1e590693b1291bfa71e')

    def load(self):
        spec=importlib.util.find_spec('analysis_v2')
        self.assertIsNotNone(spec,'v2 diagnostic analysis has not been implemented')
        import analysis_v2
        return analysis_v2

    def test_schedule_is_fixed_and_roles_do_not_flip(self):
        a=self.load(); runs=a.schedule()
        self.assertEqual(len(runs),100)
        self.assertEqual([r['group'] for r in runs[::20]],list(a.GROUPS))
        for start in range(0,100,20):
            group=runs[start:start+20]
            self.assertEqual([r['role'] for r in group[:4]],['A','B','B','A'])
            self.assertEqual(sum(r['role']=='A' for r in group),10)
            self.assertEqual(sum(r['role']=='B' for r in group),10)

    def test_statistics_preserve_outlier_order_and_large_integers(self):
        a=self.load(); values=[2**54+156250*i for i in (0,1,2,100)]
        r=a.describe(values)
        self.assertEqual(r['raw'],values)
        self.assertEqual(r['observed_gcd_ticks'],2)
        self.assertEqual(r['observed_gap_gcd_ticks'],156250)
        self.assertEqual(r['minimum_positive_gap_ticks'],156250)
        self.assertEqual(r['range_ticks'],15625000)
        self.assertEqual(a.describe([None,10])['missing'],1)

    def test_pair_direction_and_threshold_use_role_not_run_order(self):
        a=self.load(); rows=[dict(group='baseline_aa',pair=1,role='B',cpu=106),dict(group='baseline_aa',pair=1,role='A',cpu=100)]
        r=a.pairs(rows)[0]
        self.assertEqual(r['delta_ticks'],6)
        self.assertTrue(r['above_plus_5pct'])
        rows[0]['cpu']=105
        self.assertFalse(a.pairs(rows)[0]['above_plus_5pct'])
        rows[1]['cpu']=0
        self.assertIsNone(a.pairs(rows)[0]['overhead_pct'])

    def test_missing_process_is_not_zero_and_identity_is_creation_bound(self):
        a=self.load()
        r=a.process_accounting([dict(pid=1,created=2,user=10,kernel=20),dict(pid=3,created=4,user=None,kernel=None)],total_processes=2)
        self.assertFalse(r['complete']);self.assertIsNone(r['sum_ticks'])
        with self.assertRaises(ValueError):
            a.process_accounting([dict(pid=1,created=2,user=1,kernel=0)]*2,2)
        self.assertTrue(a.process_accounting([dict(pid=1,created=2,user=1,kernel=0),dict(pid=1,created=3,user=2,kernel=0)],2)['complete'])

    def test_stage_root_partition_excludes_abc_subtotal(self):
        a=self.load()
        marks=[dict(label=n,root_user=i*100,root_kernel=0,job_user=i*150,job_kernel=0,qpc=i*1000) for i,n in enumerate(a.MARKS)]
        r=a.partition(marks)
        self.assertEqual(sum(s['root_ticks'] for s in r),marks[-1]['root_user'])
        with self.assertRaises(ValueError):a.partition(marks[:-1])
        marks[3]['root_user']=-1
        with self.assertRaises(ValueError):a.partition(marks)

    def test_patch_keeps_exactly_one_private_job_and_whole_pass_switch(self):
        project=Path('D:/codex/0000_26qs')
        sys.path.insert(0,str(project/'scripts/pmux_validation/runner'))
        import patch_v2
        original={name:(project/'.tools/yosys-source-lf'/name).read_text(encoding='utf-8') for name in patch_v2.FILES}
        base=patch_v2.contents(original,False);opt=patch_v2.contents(original,True)
        self.assertEqual(base['kernel/driver.cc'].count('CreateJobObjectW'),1)
        self.assertIn('info.TotalUserTime.QuadPart + info.TotalKernelTime.QuadPart',base['kernel/driver.cc'])
        self.assertIn('if (!diag_v2_skip()) run("pmux_opt")',opt['techlibs/intel/synth_intel.cc'])
        self.assertNotIn('run("pmux_opt")',base['techlibs/intel/synth_intel.cc'])
        self.assertNotIn('test4',opt['techlibs/intel/synth_intel.cc'])
        with self.assertRaises(ValueError):patch_v2.contents(base,False)

if __name__=='__main__':unittest.main(verbosity=2)
