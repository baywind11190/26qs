import sys,unittest,os,tempfile
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'runner'))
import heap_policy as H
class Tests(unittest.TestCase):
 def test_environment_copy_casefold(self):
  for env in [{},{'_NO_DEBUG_HEAP':'0'},{'_NO_DEBUG_HEAP':'1'},{'_no_debug_heap':'0','_NO_DEBUG_HEAP':'0'}]:
   before=env.copy();out=H.target_environment(env);self.assertEqual(env,before);self.assertEqual([(k,v) for k,v in out.items() if k.upper()=='_NO_DEBUG_HEAP'],[('_NO_DEBUG_HEAP','1')])
  self.assertEqual(H.target_environment(None)['_NO_DEBUG_HEAP'],'1')
 def test_evidence_recomputed(self):
  good=dict(pid=42,ntglobal_flags=0,heap_flags=2,heap_force_flags=0,heap_signature=0xffeeffee,layout='win64-ntheap-v1',verified=True)
  row=dict(main_pid=42,measurement_revision=H.REVISION,heap_policy=H.POLICY,debug_heap_env='1',heap_observation=good)
  self.assertEqual(H.sample_errors(row),[])
  for key,value in [('pid',43),('ntglobal_flags',0x70),('heap_flags',0x62),('heap_force_flags',0x60),('heap_signature',0),('verified',False)]:
   altered=dict(row,heap_observation=dict(good,**{key:value}));self.assertTrue(H.sample_errors(altered))
  for key in ['measurement_revision','heap_policy','debug_heap_env','heap_observation']:
   altered=row.copy();altered.pop(key);self.assertTrue(H.sample_errors(altered))
class NativeFailureTests(unittest.TestCase):
 @unittest.skipUnless(os.name=='nt','Windows only')
 def test_read_failure_invalidates_actual_process(self):
  import win_measure
  with tempfile.TemporaryDirectory() as tmp, patch.object(H,'observe',side_effect=OSError('forced readonly failure')):
   row=win_measure.run_measured([sys.executable,'-c','pass'],cwd=tmp,log_path=Path(tmp)/'run.log',timeout_s=10,measurement_revision=H.REVISION,heap_policy=H.POLICY)
  self.assertFalse(row['metrics_valid']);self.assertIn('forced readonly failure',row['measurement_error'])
 def test_wrong_policy_rejected_before_process(self):
  import win_measure
  with tempfile.TemporaryDirectory() as tmp:
   with self.assertRaises(ValueError):
    win_measure.run_measured([sys.executable,'-c','pass'],cwd=tmp,log_path=Path(tmp)/'run.log',measurement_revision='old',heap_policy=H.POLICY)

if __name__=='__main__':unittest.main()
