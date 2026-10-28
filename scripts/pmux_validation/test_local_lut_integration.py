"""7.1 integration identity, invocation ordering and fail-closed evidence tests."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent / 'runner'))
sys.path.insert(0, str(Path(__file__).parent))
import integration_profiles as I
import prepare_builtin as P
import validate as V
from test_measure_v8 import fixture_cases

class LocalLutIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import subprocess
        cls.patch = subprocess.check_output(['git', 'show',
            '24e6758ec8cc98db7ca292b21d0069dc824ce461:' + I.PATCH_PATH],
            cwd=Path(__file__).resolve().parents[2])

    def cfg(self):
        return {'official_cases': fixture_cases(), 'performance_scheme': 'pmux-perf-single-powershell-same-run-exitpeak-v8', 'builtin': {
            'integration_id': P.INTEGRATION_ID, 'source_commit': 'base',
            'build_profile': {}}, 'tools': {'compiler': {'path': 'cc', 'sha256': 'cc'}}}

    def test_profile_rejects_omission_unknown_patch_and_cpu_mode(self):
        with self.assertRaisesRegex(ValueError, 'p3-local-lut'):
            I.configure(self.cfg(), 'p3', self.patch)
        with self.assertRaises(ValueError):
            I.configure(self.cfg(), 'p3-local-lut', self.patch + b'\n')
        with self.assertRaises(ValueError):
            I.configure(self.cfg(), 'p3-local-lut', None)
        cfg = self.cfg(); cfg['performance_scheme'] = 'v6'
        with self.assertRaises(ValueError):
            I.configure(cfg, 'p3-local-lut', self.patch)

    def test_key_is_separate_and_p3_key_unchanged(self):
        cfg = self.cfg()
        old = P.cache_key(cfg, 'source')
        I.configure(cfg, 'p3', None)
        self.assertEqual(old, P.cache_key(cfg, 'source'))
        I.configure(cfg, 'p3-local-lut', self.patch)
        new = P.cache_key(cfg, 'source')
        self.assertNotEqual(old, new)
        self.assertEqual(new['integration_id'], I.LOCAL_ID)
        self.assertEqual(new['integration_patch_sha256'], hashlib.sha256(self.patch).hexdigest())

    def test_binary_without_lut_support_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            binary = Path(tmp) / 'yosys.exe'; binary.write_bytes(b'fake')
            replies = [SimpleNamespace(returncode=0, stdout='Yosys 0.69'),
                       SimpleNamespace(returncode=0, stdout='pmux_opt early pass')]
            with patch.object(P.subprocess, 'run', side_effect=replies):
                with self.assertRaisesRegex(P.BuildError, '-lut support'):
                    P._verify_binary(binary, True, '0.69', integration_id=I.LOCAL_ID)

    def test_nested_abc9_execution_is_not_a_second_mapping_pass(self):
        log = self.log().replace('2.37.5. Executing TECHMAP pass.',
            '2.37.5. Executing TECHMAP pass.\n2.37.11.4. Executing ABC9.')
        self.assertTrue(I.check_calls(log, I.LOCAL_ID, require_export=True)['ok'])

    def test_insert_is_idempotent_and_rejects_wrong_or_duplicate_positions(self):
        cmake = P.CMAKE_ANCHOR
        synth = P.SYNTH_ANCHOR + I.LUT_ANCHOR
        c, s, already = P.insert_integration(cmake, synth, integration_id=I.LOCAL_ID)
        self.assertFalse(already)
        self.assertEqual(s.count('run("pmux_opt");'), 1)
        self.assertEqual(s.count('run("pmux_opt -lut");'), 1)
        self.assertEqual(P.insert_integration(c, s, integration_id=I.LOCAL_ID), (c, s, True))
        for bad in (s + '\nrun("pmux_opt -lut");',
                    s.replace(I.LUT_BLOCK, I.LUT_ANCHOR) + '\nrun("pmux_opt -lut");',
                    P.SYNTH_ANCHOR):
            with self.assertRaises((ValueError, P.BuildError)):
                P.insert_integration(c, bad, integration_id=I.LOCAL_ID)

    def log(self):
        return '\n'.join(['2.15. Executing OPT pass.',
            '2.16. Executing PMUX_OPT pair-swap optimization.',
            '2.17. Executing WREDUCE pass.',
            '2.37. Executing ABC9 pass.',
            '2.37.5. Executing TECHMAP pass.',
            '2.40. Executing PMUX_OPT local LUT optimization (7.1).',
            '3. Executing RTLIL backend.', '4.1. Executing TECHMAP pass.'])

    def test_invocations_and_export_must_follow_abc9_before_cell_mapping(self):
        self.assertTrue(I.check_calls(self.log(), I.LOCAL_ID, require_export=True)['ok'])
        for bad in (self.log().replace('2.40. Executing PMUX_OPT local LUT optimization (7.1).', ''),
                    self.log() + '\n5. Executing PMUX_OPT local LUT optimization (7.1).',
                    self.log().replace('2.37. Executing ABC9 pass.', '2.37. Executing ABC pass.'),
                    self.log().replace('3. Executing RTLIL backend.', '').replace(
                        '2.37. Executing ABC9 pass.', '1. Executing RTLIL backend.\n2.37. Executing ABC9 pass.')):
            self.assertFalse(I.check_calls(bad, I.LOCAL_ID, require_export=True)['ok'])

    def test_rc_zero_but_failed_or_missing_functional_evidence_blocks_performance(self):
        rows = [dict(case=case['id'], chain=chain, state='PASS', rc=0,
                     verified=True, probes_noDF_all_sat=True)
                for case in fixture_cases() for chain in I.CHAINS]
        self.assertTrue(I.formal_chains_ok(rows, self.cfg()))
        rows[0]['state'] = 'FAIL'
        self.assertFalse(I.formal_chains_ok(rows, self.cfg()))
        self.assertFalse(I.formal_chains_ok(rows[1:], self.cfg()))

    def test_performance_gate_requires_matching_export_and_actual_eqy_input(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); cfg = self.cfg()
            I.configure(cfg, 'p3-local-lut', self.patch)
            def save(rel, value):
                path = root / rel; path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(value))
            patch = root / '02_assets/tree' / I.PATCH_PATH
            patch.parent.mkdir(parents=True); patch.write_bytes(self.patch)
            fc, public, chains = [], [], []
            for case in I.S.case_ids(cfg):
                call = I.check_calls(self.log(), I.LOCAL_ID, require_export=True)
                fc.append({'case': case, 'sides': {'optimized': {'integration_calls': call}}})
                pub = {'case': case, 'optimized_integration_calls': call}
                for side, chain in zip(('optimized', 'baseline'), I.CHAINS):
                    path = root / '05_public/round01' / case / side / 'post_abc.il'
                    path.parent.mkdir(parents=True); path.write_bytes((case + side).encode())
                    sha = hashlib.sha256(path.read_bytes()).hexdigest()
                    pub[side + '_post_abc_sha256'] = sha
                    chains.append(dict(case=case, chain=chain, state='PASS', rc=0, verified=True,
                                       probes_noDF_all_sat=True, formal_netlist_sha256=sha))
                public.append(pub)
            save('04_flowcheck/builtin_run01/builtin_flowcheck.json', {'all_ok': True, 'cases': fc})
            save('05_public/round01/summary.json', {'cases': public})
            rel = '10_selfcheck/chains/run01/chains_summary.json'
            save(rel, chains)
            self.assertEqual(V.performance_precondition(root, cfg), [])
            chains[0]['formal_netlist_sha256'] = '0' * 64
            save(rel, chains)
            self.assertTrue(V.performance_precondition(root, cfg))
            chains[0]['state'] = 'FAIL'; chains[0]['rc'] = 0
            save(rel, chains)
            self.assertTrue(V.performance_precondition(root, cfg))


if __name__ == '__main__':
    unittest.main()
