"""Two-call arithmetic profile regressions (no target build or formal run)."""
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).parent / 'runner'))
import integration_profiles as I
import prepare_builtin as P
import validate as V

class TwoCallTests(unittest.TestCase):
    target = 'fd24aa7c8fd98ac4c8463d4a25b15af146ff7b57'
    base = Path('D:/codex/0000_26qs/.tools/yosys-source-d0e71cfb7')
    def cfg(self):
        return {'performance_scheme':'pmux-perf-warm10-initial-review5-same-run-v9',
                'builtin':{'source_commit':'base'}, 'tools':{'compiler':{'path':'cc','sha256':'cc'}}}
    def patch(self):
        return subprocess.check_output(['git','show',self.target+':'+I.ARITH_PATCH_PATH])
    def log(self):
        return '\n'.join(['2.14. Executing FSM pass.', '2.15. Executing OPT pass.',
            '2.16. Executing PMUX_OPT arithmetic sharing.', '2.17. Executing PMUX_OPT pair-swap optimization.',
            '2.18. Executing WREDUCE pass.', '2.37. Executing ABC9 pass.',
            '2.37.5. Executing TECHMAP pass.', '2.38. Executing OPT pass.',
            '2.39. Executing AUTONAME pass.', '2.40. Executing clean pass.',
            '3. Executing RTLIL backend.', 'Output filename: post_abc.il', '4.1. Executing TECHMAP pass.'])
    def test_registered_patch_and_separate_cache(self):
        cfg=self.cfg(); I.configure(cfg,'p3-arith',None,self.patch())
        self.assertEqual(I.identity(cfg),'pmux-opt-inline-p3-arith-v1')
        self.assertFalse(I.has_lut(I.identity(cfg)))
        self.assertTrue(I.has_arith(I.identity(cfg)))
        self.assertEqual(cfg['expected_pmux_calls'],['pmux_opt -arith','pmux_opt'])
        key=P.cache_key(cfg,'source')
        self.assertEqual(key['integration_patch_sha256'],hashlib.sha256(self.patch()).hexdigest())
        for bad in (None,self.patch()+b'\n'):
            with self.assertRaises(ValueError): I.configure(self.cfg(),'p3-arith',None,bad)
        with self.assertRaises(ValueError): I.configure(self.cfg(),'p3-arith-local-lut',None,self.patch())
    def test_two_calls_and_export_boundary(self):
        integration_id='pmux-opt-inline-p3-arith-v1'; log=self.log()
        call=I.check_calls(log,integration_id,True)
        self.assertTrue(call['ok'],call)
        self.assertTrue(call['export_after_abc'])
        for bad in (log.replace('2.14. Executing FSM pass.',''), log.replace('2.14.','1.14.'),
                    log.replace('2.18.','2.19.'),log.replace('3. Executing RTLIL backend.',''),
                    log.replace('2.39. Executing AUTONAME pass.',''),
                    log+'\n5. Executing PMUX_OPT local LUT optimization (7.1).',
                    log+'\n5. Executing PMUX_OPT arithmetic sharing.'):
            self.assertFalse(I.check_calls(bad,integration_id,True)['ok'],bad)
    def test_real_formal_script_has_two_distinct_rtlil_exports(self):
        import builtin_common as B
        script=B.gen_builtin_formal_ys('fixture.v','top')
        self.assertEqual(script.count('write_rtlil '),2)
        log=self.log()+'\n5. Executing RTLIL backend.\nOutput filename: mapped.il'
        result=I.check_calls(log,I.TWO_CALL_ID,True)
        self.assertTrue(result['ok'],result)
        for bad in (
            log.replace('Output filename: post_abc.il','Output filename: forged.il'),
            log.replace('Output filename: post_abc.il','Output filename: ../post_abc.il'),
            log.replace('Output filename: mapped.il','Output filename: post_abc.il'),
            log.replace('Output filename: post_abc.il','')+'\nOutput filename: post_abc.il',
            log.replace('3. Executing RTLIL backend.\nOutput filename: post_abc.il\n','')+'\n6. Executing RTLIL backend.\nOutput filename: post_abc.il',
            log.replace('Output filename: post_abc.il','Output filename: temp.il').replace('Output filename: mapped.il','Output filename: post_abc.il').replace('Output filename: temp.il','Output filename: mapped.il'),
        ):
            self.assertFalse(I.check_calls(bad,I.TWO_CALL_ID,True)['ok'],bad)

    def test_real_new_base_insertion_is_exact_and_idempotent(self):
        c,s=[subprocess.check_output(['git','-C',str(self.base),'show','HEAD:'+p]).decode()
             for p in ('passes/opt/CMakeLists.txt','techlibs/intel/synth_intel.cc')]
        nc,ns,already=P.insert_integration(c,s,'pmux-opt-inline-p3-arith-v1')
        self.assertFalse(already)
        self.assertEqual(ns.count('run("pmux_opt -arith");'),1)
        self.assertEqual(ns.count('run("pmux_opt");'),1)
        self.assertNotIn('run("pmux_opt -lut");',ns)
        self.assertEqual(P.insert_integration(nc,ns,'pmux-opt-inline-p3-arith-v1'),(nc,ns,True))
        with self.assertRaises(P.BuildError):
            P.insert_integration(c.replace('peepopt.cc','unexpected.cc'),s,'pmux-opt-inline-p3-arith-v1')
        for bad in (ns+'\nrun("pmux_opt -lut");',ns.replace('run("pmux_opt -arith");','')):
            with self.assertRaises(P.BuildError): P.insert_integration(nc,bad,'pmux-opt-inline-p3-arith-v1')
    def test_formal_run_rejects_historical_lut_before_any_write(self):
        for old in (I.LOCAL_ID,I.ARITH_ID):
            with self.assertRaisesRegex(ValueError,'LUT'):
                V.run_builtin({'flow_revision':'v9-official1030-r1','builtin':{'integration_id':old}},b'', 'test')
    def test_runtime_closure_and_selfcheck_fingerprint(self):
        cfg=self.cfg()
        cfg.update(flow_version='v9',suite_manifest_sha256='suite', tools={n:{'sha256':n} for n in ('yosys','abc','eqy')})
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp); dep=folder/'runtime.dll'; dep.write_bytes(b'original')
            cfg['runtime_closure']=[dict(path=str(dep),sha256=hashlib.sha256(dep.read_bytes()).hexdigest())]
            self.assertEqual(V.verify_runtime_closure(cfg),cfg['runtime_closure'])
            first=V.selfcheck_fingerprints(cfg,folder)
            cfg['runtime_closure']=[dict(cfg['runtime_closure'][0],sha256='different')]
            self.assertNotEqual(first,V.selfcheck_fingerprints(cfg,folder))
            with self.assertRaisesRegex(ValueError,'closure'): V.verify_runtime_closure(cfg)

    def test_report_1030_qualification_is_current(self):
        import json
        import report_v9 as R
        from test_measure_v8 import fixture_cases
        import result_layout as L
        cfg=self.cfg(); cfg.update(same_run_policy=R.POLICY, official_cases=fixture_cases())
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'validation_context.json').write_text(json.dumps(cfg),encoding='utf-8')
            R.build_report(root)
            text=(root/L.REPORT).read_text(encoding='utf-8')
        self.assertIn('C147',text)
        self.assertIn('C148',text)
        self.assertIn('C145',text)
        self.assertIn('C149',text)
        self.assertNotIn('1—10秒逐例标为用户扩展',text)

    def test_arithmetic_evidence_is_not_skipped_without_lut(self):
        cfg=self.cfg(); I.configure(cfg,'p3-arith',None,self.patch())
        from test_measure_v8 import fixture_cases
        cfg['official_cases']=fixture_cases()
        with tempfile.TemporaryDirectory() as tmp:
            errors=I.evidence_errors(tmp,cfg)
        self.assertTrue(any('probe' in e.lower() for e in errors),errors)
        self.assertTrue(any('patch' in e for e in errors),errors)

if __name__=='__main__': unittest.main()
