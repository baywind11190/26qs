import unittest
from test_local_lut_integration import LocalLutIntegrationTests
import integration_profiles as I
import prepare_builtin as P

class ArithIntegrationTests(LocalLutIntegrationTests):
    def test_arith_profile(self):
        import subprocess
        patch = subprocess.check_output(['git','show','59f8bf8d1f1c6f363216ba3132987f6e606e070f:integration/yosys_0_69_stable_pmux.patch'])
        cfg=self.cfg(); cfg['performance_scheme']='pmux-perf-warm10-initial-review5-same-run-v9'
        I.configure(cfg,'p3-arith-local-lut',self.patch,patch)
        self.assertEqual(I.identity(cfg),I.ARITH_ID)
        self.assertEqual(P.cache_key(cfg,'source')['integration_patch_sha256'],I.ARITH_PATCH_SHA256)
        for profile in ('p3','p3-local-lut'):
            with self.assertRaises(ValueError): I.configure(self.cfg(),profile,self.patch,patch)
        for bad in (None,patch+b'\n'):
            with self.assertRaises(ValueError): I.configure(cfg,'p3-arith-local-lut',self.patch,bad)

    def arith_log(self):
        return self.log().replace('2.16. Executing PMUX_OPT pair-swap optimization.', '2.16. Executing PMUX_OPT arithmetic sharing.\n2.17. Executing PMUX_OPT pair-swap optimization.').replace('2.17. Executing WREDUCE','2.18. Executing WREDUCE')

    def test_arith_calls(self):
        log=self.arith_log()
        self.assertTrue(I.check_calls(log,I.ARITH_ID,True)['ok'])
        self.assertFalse(I.check_calls(log,I.LOCAL_ID,True)['ok'])
        for bad in (log.replace('arithmetic sharing','unknown'),log.replace('2.16. Executing PMUX_OPT arithmetic sharing.',''),log+'\n5. Executing PMUX_OPT arithmetic sharing.',log.replace('2.16.',''),log.replace('2.17.','2.19.'),log.replace('3. Executing RTLIL backend.','')):
            self.assertFalse(I.check_calls(bad,I.ARITH_ID,True)['ok'],bad)

    def test_review_call_counterexamples(self):
        log=self.arith_log()
        self.assertFalse(I.check_calls(log.replace('local LUT optimization (7.1).','local LUT totally unknown.'),I.ARITH_ID,True)['ok'])
        a='2.16. Executing PMUX_OPT arithmetic sharing.'
        b='2.17. Executing PMUX_OPT pair-swap optimization.'
        self.assertFalse(I.check_calls(log.replace(a+'\n'+b,b+'\n'+a),I.ARITH_ID,True)['ok'])

    def test_arith_template(self):
        import subprocess
        base='9f75ca1f9834a39a863915b5dae0c7b1e33533bc'
        repo='D:/codex/0000_26qs/.tools/yosys-source-lf'
        c,s=[subprocess.check_output(['git','-C',repo,'show',base+':'+p]).decode() for p in ('passes/opt/CMakeLists.txt','techlibs/intel/synth_intel.cc')]
        nc,ns,already=P.insert_integration(c,s,I.ARITH_ID)
        self.assertFalse(already)
        self.assertEqual(P.insert_integration(nc,ns,I.ARITH_ID),(nc,ns,True))
        for bad in (ns.replace('run("pmux_opt -arith");',''),ns+'\nrun("pmux_opt -arith");',ns.replace('run("wreduce");','run("opt");')):
            with self.assertRaises(P.BuildError): P.insert_integration(nc,bad,I.ARITH_ID)

    def test_probe_evidence_tamper(self):
        import tempfile
        from pathlib import Path
        from arith_probe import verify_probe, sha, freeze_probe
        self.assertTrue(verify_probe(None))
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); probe={'ok':True,'binary_sha256':'fake','cases':{}}
            for name,n in (('shareable',1),('observed',0)):
                folder=root/name;folder.mkdir()
                files={}
                for f in ('fixture.v','probe.ys','before.json','after.json','after.il','probe.log'):
                    path=folder/f;path.write_text(f);files[f]={'path':str(path),'sha256':sha(path)}
                probe['cases'][name]={'shares':n,'equivalence':'PASS','files':files}
            self.assertTrue(verify_probe(probe))
            import json
            for name,n in (('shareable',1),('observed',0)):
                folder=root/name
                (folder/'before.json').write_text(json.dumps({'design':{'num_cells_by_type':{'$add':1,'$sub':1}}}))
                (folder/'after.json').write_text(json.dumps({'design':{'num_cells_by_type':{'$alu':1} if n else {'$add':1,'$sub':1}}}))
                (folder/'probe.log').write_text('ARITH_SHARE total=%d all=1\nEquivalence successfully proven!'%n)
                for f,spec in probe['cases'][name]['files'].items(): spec['sha256']=sha(spec['path'])
            self.assertEqual(verify_probe(probe),[])
            self.assertTrue(verify_probe(probe,'different-binary'))
            frozen=freeze_probe(probe,root/'round')
            self.assertEqual(verify_probe(frozen),[])
            Path(frozen['cases']['shareable']['files']['after.il']['path']).write_text('changed')
            self.assertTrue(verify_probe(frozen))
