"""Managed workspace tests use real temporary bytes, never official tools."""
import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).parent / 'runner'))

class WorkspaceTests(unittest.TestCase):
    def manager(self):
        self.assertIsNotNone(importlib.util.find_spec('eqy_workspace'), 'common workspace manager missing')
        return importlib.import_module('eqy_workspace')

    def fixture(self, td):
        cfg = {'eqy_work_root': str(Path(td)/'short'), 'official_cases': [{'id':'first'}, {'id':'ninth'}],
               'target_commit':'abc', 'source_sha256':'123', 'tools':{'eqy':{'sha256':'456'}}}
        root = Path(td)/'round'; root.mkdir()
        return cfg, root

    def test_plan_is_readonly_and_manifest_binds_jobs(self):
        W=self.manager()
        with tempfile.TemporaryDirectory() as td:
            cfg,root=self.fixture(td)
            plan=W.plan_workspace(cfg,'round',[{'name':'positive'}])
            self.assertEqual(plan['blocked'],[])
            self.assertFalse(Path(cfg['eqy_work_root']).exists())
            self.assertEqual(plan['case_map'],{'first':'c01','ninth':'c02'})
            ctx=dict(cfg,eqy_workspace=W.create_workspace(cfg,root,[{'name':'positive'}]))
            self.assertEqual(W.job_dir(ctx,'chains',case='ninth',side='optimized'),Path(plan['workspace'])/'chains/c02/o')
            self.assertEqual(W.job_dir(ctx,'sc',check='positive'),Path(plan['workspace'])/'sc/s01')
            with self.assertRaises(ValueError): W.job_dir(ctx,'chains',case='unknown',side='baseline')
            with self.assertRaises(FileExistsError): W.create_workspace(cfg,root,[])
            ctx['source_sha256']='tampered'
            with self.assertRaises(ValueError): W.job_dir(ctx,'sc',check='positive')

    def test_input_binding_refuses_same_bytes_from_other_source(self):
        W=self.manager()
        with tempfile.TemporaryDirectory() as td:
            cfg,root=self.fixture(td);ctx=dict(cfg,eqy_workspace=W.create_workspace(cfg,root,[]))
            src=Path(td)/'source.il';src.write_bytes(b'A\r\n\x00')
            copied=W.stage_input(ctx,'chains',src,'input.il')
            self.assertEqual(copied.read_bytes(),b'A\r\n\x00')
            self.assertEqual(W.stage_input(ctx,'chains',src,'input.il'),copied)
            other=Path(td)/'other.il';other.write_bytes(src.read_bytes())
            with self.assertRaises(ValueError): W.stage_input(ctx,'chains',other,'input.il')
            src.write_bytes(b'changed')
            with self.assertRaises(ValueError): W.stage_input(ctx,'chains',src,'input.il')

    def test_setup_checks_actual_partitions_and_raw_paths(self):
        W=self.manager()
        with tempfile.TemporaryDirectory() as td:
            work=Path(td)/'work'; d=work/'strategies/top.out/simple'; d.mkdir(parents=True)
            p=work/'partitions';p.mkdir()
            for suffix in ('sv','il'): (p/('top.out.'+suffix)).write_bytes(b'fixture')
            (d/'run.ys').write_text('read_verilog -sv ../../../partitions/top.out.sv\nread_rtlil ../../../partitions/top.out.il\n')
            a=W.check_work(work,limit=1000)
            self.assertEqual(a['partitions'],['top.out']);self.assertEqual(len(a['references']),2)
            with self.assertRaises(ValueError): W.check_work(work,['other'],1000)
            with self.assertRaises(ValueError): W.check_work(work,limit=20)
            (p/'uncovered.sv').write_bytes(b'bad')
            with self.assertRaises(ValueError): W.check_work(work,limit=1000)

    def test_archive_survives_external_removal_and_detects_changes(self):
        W=self.manager()
        with tempfile.TemporaryDirectory() as td:
            cfg,root=self.fixture(td);ctx=dict(cfg,eqy_workspace=W.create_workspace(cfg,root,[]))
            ws=Path(ctx['eqy_workspace']['workspace']); (ws/'empty').mkdir();p=ws/'proof.log';p.write_bytes(b'FAIL\r\n')
            status=W.archive(ctx,root);self.assertTrue(status['ok'],status)
            self.assertTrue((root/'10_selfcheck/eqy_archive/empty').is_dir())
            import shutil
            shutil.rmtree(ws)
            self.assertTrue(W.verify_archive(root)['ok'])
            resolved=W.resolve_evidence(root,str(p).replace('\\','/'))
            self.assertEqual(resolved.read_bytes(),b'FAIL\r\n')
            with self.assertRaises(ValueError): W.resolve_evidence(root,Path(td)/'outside')
            resolved.write_bytes(b'changed')
            self.assertFalse(W.verify_archive(root)['ok'])
            with self.assertRaises(ValueError): W.resolve_evidence(root,p)

    def test_unsafe_roots_and_long_static_jobs_block_without_writes(self):
        W=self.manager()
        with tempfile.TemporaryDirectory() as td:
            cfg,root=self.fixture(td)
            for unsafe in ('bad space','x'*180):
                cfg['eqy_work_root']=str(Path(td)/unsafe)
                self.assertTrue(W.plan_workspace(cfg,'round',[])['blocked'])
                self.assertFalse(Path(cfg['eqy_work_root']).exists())
            self.assertEqual(W.path_identity('D:/EQY/a/../b'),W.path_identity('d:\\eqy\\b'))

    def test_strategy_absolute_escape_is_rejected(self):
        W=self.manager()
        with tempfile.TemporaryDirectory() as td:
            work=Path(td)/'work'; d=work/'strategies/top.out/simple';d.mkdir(parents=True)
            p=work/'partitions';p.mkdir()
            for suffix in ('sv','il'): (p/('top.out.'+suffix)).write_bytes(b'x')
            outside=Path(td)/'external.il';outside.write_bytes(b'x')
            (d/'run.ys').write_text('read_verilog -sv ../../../partitions/top.out.sv\nread_rtlil '+outside.as_posix()+'\n')
            with self.assertRaises(ValueError): W.check_work(work,limit=1000)

    def test_archive_extra_file_and_no_overwrite(self):
        W=self.manager()
        with tempfile.TemporaryDirectory() as td:
            cfg,root=self.fixture(td);ctx=dict(cfg,eqy_workspace=W.create_workspace(cfg,root,[]))
            (Path(ctx['eqy_workspace']['workspace'])/'log').write_bytes(b'original')
            self.assertTrue(W.archive(ctx,root)['ok'])
            self.assertFalse(W.archive(ctx,root)['ok'])
            archive=root/'10_selfcheck/eqy_archive'
            self.assertEqual((archive/'log').read_bytes(),b'original')
            (archive/'extra').write_bytes(b'extra')
            self.assertFalse(W.verify_archive(root)['ok'])

    def test_linked_source_is_rejected_without_copy(self):
        W=self.manager()
        with tempfile.TemporaryDirectory() as td:
            cfg,root=self.fixture(td);ctx=dict(cfg,eqy_workspace=W.create_workspace(cfg,root,[]))
            source=Path(td)/'real.il';source.write_bytes(b'x');link=Path(td)/'link.il'
            try: link.symlink_to(source)
            except OSError as exc: self.skipTest('Host cannot create symlink: '+str(exc))
            with self.assertRaises(ValueError): W.stage_input(ctx,'sc',link)
            self.assertFalse((Path(ctx['eqy_workspace']['workspace'])/'sc').exists())

    def test_raw_reference_budget_is_checked_before_normalization(self):
        W=self.manager()
        with tempfile.TemporaryDirectory() as td:
            cwd=Path(td)/'job'
            with self.assertRaises(ValueError):
                W.check_paths(['../'*100+'file.il'],cwd=cwd,limit=200)

if __name__=='__main__': unittest.main()
