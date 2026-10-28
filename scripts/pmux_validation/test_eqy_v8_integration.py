"""Orchestrator/cache/report integration guards; no official EDA execution."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

import validate
import test_validation as T


class ManagedV8IntegrationTests(unittest.TestCase):
    def test_workspace_fingerprint_is_stable_across_rounds_but_sensitive_to_root(self):
        with tempfile.TemporaryDirectory() as td:
            cfg=T.BuiltinPrepareIntegrationTests()._cfg(Path(td))
            cfg.update(eqy_workspace_version='managed-short-v1',eqy_work_root='D:/eqy_work',eqy_path_limit=200)
            fp=validate.selfcheck_fingerprints(cfg,Path(validate.__file__).parent/'runner')
            self.assertEqual(fp.get('eqy_workspace_version'),'managed-short-v1')
            cfg['eqy_workspace']={'workspace':'D:/eqy_work/other_round/a01'}
            self.assertEqual(fp,validate.selfcheck_fingerprints(cfg,Path(validate.__file__).parent/'runner'))
            cfg['eqy_work_root']='D:/other_eqy'
            self.assertNotEqual(fp,validate.selfcheck_fingerprints(cfg,Path(validate.__file__).parent/'runner'))

    def test_managed_formal_cache_without_bound_archive_is_rejected(self):
        fp={'eqy_workspace_version':'managed-short-v1'}
        cache={'entries':{'formal_selfcheck':{'ok':True,'fingerprint':fp,'evidence_root':'missing'}}}
        self.assertFalse(validate.cache_entry_valid(cache,'formal_selfcheck',fp))

    def test_formal_cache_uses_verified_archive_without_external_workspace(self):
        import eqy_workspace as EW
        from test_measure_v8 import fixture_cases
        with tempfile.TemporaryDirectory() as td:
            base=Path(td).resolve();root=base/'round';root.mkdir()
            cfg={'eqy_work_root':str(base/'short'),'eqy_workspace_version':EW.VERSION,'eqy_path_limit':200,
                 'official_cases':fixture_cases(),'tools':{},'target_commit':'a'*40,'source_sha256':'b'*64}
            cfg['eqy_workspace']=EW.create_workspace(cfg,root,[{'name':'positive'}])
            ws=Path(cfg['eqy_workspace']['workspace']);(ws/'proof.log').write_text('verified fixture')
            checks=root/'10_selfcheck/assets/checks.json';checks.parent.mkdir(parents=True)
            checks.write_text(json.dumps({'checks':[{'name':'positive'}]}))
            summary=root/'10_selfcheck/attempt01/selfcheck_summary.json';summary.parent.mkdir()
            summary.write_text(json.dumps({'selfcheck_ok':True,'cases':[{'name':'positive','ok':True}]}))
            self.assertTrue(EW.archive(cfg,root)['ok'])
            fp={'eqy_workspace_version':EW.VERSION}
            cache={'entries':{}};validate.update_selfcheck_cache(base/'cache.json',cache,fp,'formal_selfcheck',True,root)
            saved=ws.parent/'saved_fixture';saved.relative_to(base);ws.relative_to(base)
            ws.rename(saved)
            try:
                self.assertTrue(validate.cache_entry_valid(cache,'formal_selfcheck',fp))
                (root/'10_selfcheck/eqy_archive/proof.log').write_text('tampered')
                self.assertFalse(validate.cache_entry_valid(cache,'formal_selfcheck',fp))
            finally:
                saved.rename(ws)

    def test_build_failure_finalizes_workspace_before_failure_report(self):
        import prepare_builtin as P
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);root=base/'round';(root/'01_meta').mkdir(parents=True)
            cfg=T.BuiltinPrepareIntegrationTests()._cfg(base)
            cfg.update(eqy_workspace_version='managed-short-v1',eqy_work_root=str(base/'short'),eqy_path_limit=200)
            events=[]
            def init(cfg,root):
                events.append('init');cfg['eqy_workspace']={'workspace':str(base/'short')}
            def final(root,cfg):
                events.append('archive');return {'ok':True}
            def failure(*args,**kwargs):events.append('report');return 'BUILTIN_BUILD_FAILED'
            self.assertTrue(hasattr(validate,'init_eqy_workspace'),'missing workspace initialization')
            self.assertTrue(hasattr(validate,'finalize_eqy'),'missing unconditional finalizer')
            with mock.patch.object(validate,'make_round',return_value=root),\
                 mock.patch.object(validate,'init_eqy_workspace',side_effect=init),\
                 mock.patch.object(validate,'finalize_eqy',side_effect=final),\
                 mock.patch('prepare_builtin.prepare_builtin',side_effect=P.BuildError('fixture failure')),\
                 mock.patch('report.build_builtin_build_failed_report',side_effect=failure):
                self.assertEqual(validate.run_builtin(cfg,b'alg','fixture'),3)
            self.assertEqual(events,['init','archive','report'])

    def test_managed_report_requires_archive_gate_even_with_no_proof_rows(self):
        import report_v8
        from test_measure_v8 import V8Tests,fixture_cases,v8
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);V8Tests().invoke_fake(root)
            cfg={'official_cases':fixture_cases(),'performance_scheme':v8.SCHEME,'same_run_policy':v8.POLICY,
                 'suite_verified':True,'builtin':{'integration_id':'pmux-opt-inline-p3-v1'},
                 'eqy_workspace_version':'managed-short-v1','eqy_workspace':{'workspace':str(root/'absent')}}
            (root/'validation_context.json').write_text(json.dumps(cfg))
            report_v8.build_report(root)
            result=json.loads((root/'11_summary/manifest.json').read_text())
            self.assertFalse(result['gates'].get('EQY现场归档完整',True))
            self.assertTrue(all(p['valid'] for p in result['performance']))
            # A valid-looking manifest alone cannot override a failed/missing finalizer status.
            with mock.patch('eqy_workspace.verify_archive',return_value={'ok':True}):
                report_v8.build_report(root)
            result=json.loads((root/'11_summary/manifest.json').read_text())
            self.assertFalse(result['gates']['EQY现场归档完整'])


if __name__=='__main__':unittest.main()
