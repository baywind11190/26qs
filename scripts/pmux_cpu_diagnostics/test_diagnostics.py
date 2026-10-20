"""Focused contracts for stage accounting and the fixed diagnostic schedule."""
import unittest
import copy
from pathlib import Path
from unittest.mock import patch
import analysis

class DiagnosticTests(unittest.TestCase):
    def test_cache_identity_rejects_staged_or_wrong_head(self):
        import sys
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pmux_validation/runner'))
        import build
        def git(repo,*args):
            if args==('rev-parse','HEAD'):return 'abc-head' if Path(repo).name=='abc' else 'base-head'
            if args==('diff','--cached','--name-only'):return ''
            if args==('ls-files','--others','--exclude-standard'):
                return 'src/base/main/diag_cpu_shared.h' if Path(repo).name=='abc' else 'kernel/diag_cpu_impl.inc\nkernel/diag_cpu_shared.h'
            raise AssertionError(args)
        with patch.object(build.P,'_git',side_effect=git):
            build.check_source_identity(Path('cache/baseline-src'),False,'base-head','abc-head')
            self.assertRaises(ValueError,build.check_source_identity,Path('cache/baseline-src'),False,'wrong-head','abc-head')
        def staged(repo,*args):
            return 'passes/other/unapproved.cc' if args==('diff','--cached','--name-only') else git(repo,*args)
        with patch.object(build.P,'_git',side_effect=staged):
            self.assertRaises(ValueError,build.check_source_identity,Path('cache/baseline-src'),False,'base-head','abc-head')

    def test_fixed_schedule(self):
        rows=list(analysis.schedule())
        self.assertEqual(len(rows),40)
        self.assertEqual(rows[0],(1,'test1','baseline'))
        self.assertEqual(rows[8],(2,'test1','optimized'))
        self.assertEqual(len(set(rows)),40)

    def test_overlap_keeps_directional_clue_unproven(self):
        r=analysis.directional_clue([0,2,1,4,3],[3,4,3,2,3],[3,6,4,6,6],1)
        self.assertTrue(r['clue']);self.assertTrue(r['overlap']);self.assertFalse(r['confirmed'])
        self.assertFalse(analysis.directional_clue([1]*5,[0]*5,[1]*5,1)['clue'])

    def test_partition_does_not_double_count_abc(self):
        marks=[]
        for i,label in enumerate(analysis.MAIN_MARKS):
            marks.append(dict(label=label,root_user=i*10,root_kernel=0,job_user=i*20,job_kernel=0,call_id=0))
        marks.insert(6,dict(label='abc_call_begin',root_user=42,root_kernel=0,job_user=83,job_kernel=0,call_id=1))
        marks.insert(7,dict(label='abc_call_end',root_user=48,root_kernel=0,job_user=97,job_kernel=0,call_id=1))
        result=analysis.partition(marks)
        self.assertEqual(sum(s['root_ticks'] for s in result),marks[-1]['root_user']-marks[0]['root_user'])
        self.assertEqual(sum(s['job_ticks'] for s in result),marks[-1]['job_user']-marks[0]['job_user'])
        self.assertEqual(len(result),len(analysis.MAIN_MARKS)-1)

    def test_missing_or_nonmonotonic_marks_rejected(self):
        self.assertRaises(ValueError,analysis.partition,[])
        marks=[dict(label=v,root_user=i,root_kernel=0,job_user=i,job_kernel=0,call_id=0) for i,v in enumerate(analysis.MAIN_MARKS)]
        marks[-1]['job_user']=0
        self.assertRaises(ValueError,analysis.partition,marks)

    def test_two_abc_calls_identity_and_zero_cpu(self):
        marks=[dict(label=v,root_user=i*10,root_kernel=0,job_user=i*20,job_kernel=0,call_id=0) for i,v in enumerate(analysis.MAIN_MARKS)]
        for label,r,j,id in reversed([('abc_call_begin',51,101,1),('abc_call_end',52,103,1),('abc_call_begin',53,104,2),('abc_call_end',54,108,2)]):
            marks.insert(6,dict(label=label,root_user=r,root_kernel=0,job_user=j,job_kernel=0,call_id=id))
        marks[-1]['processes']=4
        abc=[dict(call_id=i,ready=2,pid=42+i,created=100+i,exit_code=0,launcher_exit=0,start_user=0,start_kernel=0,end_user=0,end_kernel=0) for i in (1,2)]
        d=dict(schema=1,method=analysis.METHOD,valid=True,error=0,pid=42,created=100,marks=marks,abc=abc)
        native=dict(main_pid=42,process_create_filetime=100,cpu_total_ticks=200,job_total_processes=5)
        self.assertEqual(analysis.validate(d,native)['abc_process_ticks'],0)
        bad=copy.deepcopy(d);bad['abc'][1]['pid']=bad['abc'][0]['pid'];bad['abc'][1]['created']=bad['abc'][0]['created']
        self.assertRaises(ValueError,analysis.validate,bad,native)
        bad=copy.deepcopy(d);bad['abc'][1]['ready']=1
        self.assertRaises(ValueError,analysis.validate,bad,native)
        self.assertRaises(ValueError,analysis.validate,d,dict(native,main_pid=99))

if __name__=='__main__':unittest.main()
