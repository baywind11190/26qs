import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).parent/'runner'))
import result_layout as L
import eqy_workspace as EW
import validate
from test_measure_v8 import fixture_cases


class V9IntegrationTests(unittest.TestCase):
    def test_external_result_root_is_required_and_readonly(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'external'
            cfg=dict(results_root=str(root),performance_scheme='pmux-perf-warm10-initial-review5-same-run-v9')
            self.assertEqual(L.result_parent(cfg),root/'r')
            self.assertEqual(L.selfcheck_cache(cfg),root/'c/selfcheck_v9.json')
            self.assertFalse(root.exists())
            with self.assertRaises(ValueError):L.result_parent(dict(cfg,results_root=''))

    def test_eqy_short_identity_and_mapping_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg=dict(eqy_work_root=str(Path(tmp)/'e'),eqy_workspace_version=EW.VERSION,
                     eqy_workspace_naming='round-sha256-16-v1',eqy_path_limit=200,official_cases=fixture_cases())
            a=EW.plan_workspace(cfg,'2026-10-27_1400_v9_17f9361_r01',[])
            b=EW.plan_workspace(cfg,'2026-10-27_1400_v9_17f9361_r02',[])
            self.assertFalse(a['blocked']);self.assertNotEqual(a['workspace'],b['workspace'])
            self.assertLess(len(Path(a['workspace']).parent.name),20)
            Path(a['workspace']).mkdir(parents=True)
            self.assertTrue(EW.plan_workspace(cfg,'2026-10-27_1400_v9_17f9361_r01',[])['blocked'])

    def test_default_entry_configuration_is_v9_and_v8_cli_is_retired(self):
        cfg=json.loads(validate.CONFIG_PATH.read_text(encoding='utf-8'))
        self.assertTrue(cfg['performance_scheme'].endswith('-v9'))
        text=(Path(__file__).parent/'validate_windows_v8.cmd').read_text(encoding='utf-8')
        self.assertIn('RETIRED',text);self.assertNotIn('validate.py %*',text)
        self.assertEqual(validate.entrypoint_names(cfg),['validate.py','report.py','report_v9.py','validate_windows_v9.cmd'])


if __name__=='__main__':unittest.main()
