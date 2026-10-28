import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).parent / 'runner'))
import builtin_common as B
import measure_v8 as V8


def cases(n=9):
    return [dict(id='case_%d' % i, top='top_%d' % i,
                 file='tree/inputs/case_%d.v' % i,
                 canonical_file='originals/case_%d.v' % i,
                 canonical_sha256='a'*64, sha256='b'*64,
                 default_parameters={}) for i in range(n)]


class OfficialSuiteTests(unittest.TestCase):
    def test_schedule_uses_nine_explicit_cases(self):
        rows = list(V8.schedule({'official_cases': cases()}))
        self.assertEqual(len(rows), 18)
        self.assertEqual([r['case'] for r in rows[::2]], [c['id'] for c in cases()])

    def test_runtime_rejects_missing_case_set(self):
        with self.assertRaises(ValueError):
            list(V8.schedule({}))

    def test_logic_increase_blocks_even_with_other_savings(self):
        base = dict(logic_units=10, dff_count=2, io_ports=2, io_bits=2, other_cell_types={})
        opt = dict(base, logic_units=11, dff_count=0)
        self.assertFalse(B.compare_resource_counts(base, opt)['resource_checks_ok'])
        self.assertFalse(B.compare_resource_counts(base, opt)['logic_nonincrease'])

    def test_manifest_hashes_paths_top_and_duplicates(self):
        import official_suite as S
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); suite = root / 'suite'; suite.mkdir()
            rec = cases(1)[0]; raw = b'module top_0;\r\nendmodule\r\n'
            canonical = root / rec['canonical_file']; canonical.parent.mkdir(); canonical.write_bytes(raw)
            execution = suite / rec['file']; execution.parent.mkdir(parents=True); execution.write_bytes(raw.replace(b'\r\n', b'\n'))
            rec['canonical_sha256'] = hashlib.sha256(raw).hexdigest()
            rec['sha256'] = hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest()
            manifest = dict(cases=[rec], files=[dict(file=rec['file'], sha256=rec['sha256'])])
            path = suite / 'manifest.json'
            def load(value):
                path.write_text(json.dumps(value)); return S.load_suite(path, root)
            self.assertEqual(load(manifest), [rec])
            for key, value in [('top', 'wrong_top'), ('sha256', '0'*64),
                               ('canonical_sha256', '0'*64), ('file', '../escape.v'),
                               ('canonical_file', '../escape.v')]:
                bad = copy.deepcopy(manifest); bad['cases'][0][key] = value
                with self.subTest(key=key), self.assertRaises(ValueError): load(bad)
            bad = copy.deepcopy(manifest); bad['cases'].append(copy.deepcopy(rec))
            with self.assertRaises(ValueError): load(bad)

    def test_duplicate_normalized_execution_path_is_rejected(self):
        import official_suite as S
        records=cases(2)
        records[1]['file']='tree/inputs/./case_0.v'
        with self.assertRaises(ValueError): S.validate_cases(records)

    def test_case_fingerprint_changes_with_ninth_case(self):
        import official_suite as S
        self.assertNotEqual(S.cases_sha256(cases(8)), S.cases_sha256(cases(9)))
        changed=cases(); changed[-1]['top']='different_top'
        self.assertNotEqual(S.cases_sha256(cases()), S.cases_sha256(changed))

    def test_frozen_context_detects_ninth_case_tampering(self):
        import official_suite as S
        context={'official_cases':cases(), 'official_cases_sha256':S.cases_sha256(cases())}
        context['official_cases'][-1]['top']='changed_top'
        with self.assertRaises(ValueError): S.context_cases(context)

    def test_precheck_explicit_underscore_top(self):
        import precheck_supported_config as P
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'case_0_baseline_mapped.il').write_text('module \\top_0\nend\n')
            self.assertEqual(P.main(['--dir',tmp,'--expect','case_0:baseline',
                                     '--top-map','case_0:top_0']),0)

class NineReportTests(unittest.TestCase):
    def fixture(self, root):
        from test_validation import BuiltinModeTests
        BuiltinModeTests()._write_builtin_round(root)

    def report(self, root):
        import report_v8
        status = report_v8.build_report(root)
        result = json.loads((root / '11_summary/manifest.json').read_text(encoding='utf-8'))
        return status, result

    def test_missing_ninth_or_duplicate_resource_or_one_proof_blocks(self):
        for fault in ('missing_ninth', 'duplicate_public', 'missing_proof', 'duplicate_proof'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); self.fixture(root)
                proof = 'proof' in fault
                path = root / ('10_selfcheck/chains/run01/chains_summary.json' if proof else '05_public/round01/summary.json')
                data = json.loads(path.read_text(encoding='utf-8')); rows = data if proof else data['cases']
                if fault.startswith('missing'): rows.pop()
                else: rows[-1] = copy.deepcopy(rows[0])
                path.write_text(json.dumps(data), encoding='utf-8')
                status, result = self.report(root)
                self.assertEqual(status, 'NEEDS_REVIEW')
                self.assertEqual(result['formal_synthesis_expected_runs'], 18)
                if not proof: self.assertIsNone(result['mean_logic_reduction_pct'])
                self.assertFalse(result['gates']['原始RTL功能证明与同次postABC哈希绑定' if proof else '最终资源统计与同次来源完整'])

    def test_wrong_ledger_schedule_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); self.fixture(root)
            path=root/'09_performance/round01/synthesis_ledger.json'
            data=json.loads(path.read_text(encoding='utf-8')); data['schedule'][-1]=data['schedule'][0]
            path.write_text(json.dumps(data),encoding='utf-8')
            self.assertEqual(self.report(root)[0], 'NEEDS_REVIEW')

    def set_logic_count(self, root, case, side, count):
        # Rewrite the actual tiny fixture and all same-run provenance references.
        folder=root/'05_public/round01'/case/side
        path=folder/'stat.json'; stat=json.loads(path.read_text(encoding='utf-8'))
        stat['design']['num_cells_by_type']['cycloneiv_lcell_comb']=count
        stat['design']['num_cells']=count+10
        path.write_text(json.dumps(stat),encoding='utf-8')
        resources=B.parse_resource_counts(stat,(folder/'mapped.il').read_text(encoding='utf-8'),case)
        public_path=root/'05_public/round01/summary.json'
        public=json.loads(public_path.read_text(encoding='utf-8'))
        next(row for row in public['cases'] if row['case']==case)[side+'_resources']=resources
        public_path.write_text(json.dumps(public),encoding='utf-8')
        sample_path=folder/'measure_result.json'; sample=json.loads(sample_path.read_text(encoding='utf-8'))
        sample['artifacts']['stat.json']['sha256']=V8.sha(path)
        sample_path.write_text(json.dumps(sample),encoding='utf-8')
        perf_path=root/'09_performance/round01/performance_summary.json'
        perf=json.loads(perf_path.read_text(encoding='utf-8'))
        next(row for row in perf if row['case']==case)['samples']=[sample if row['side']==side else row for row in next(row for row in perf if row['case']==case)['samples']]
        perf_path.write_text(json.dumps(perf),encoding='utf-8')

    def test_equal_weight_nine_mean_and_single_logic_increase(self):
        from test_measure_v8 import fixture_cases
        for optimized in (5, 11, 0):
            with self.subTest(optimized=optimized), tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp); self.fixture(root); case=fixture_cases()[-1]['id']
                self.set_logic_count(root,case,'baseline',10)
                self.set_logic_count(root,case,'optimized',optimized)
                status,result=self.report(root)
                self.assertAlmostEqual(result['mean_logic_reduction_pct'], (8*20+(10-optimized)/10*100)/9)
                if optimized == 11:
                    self.assertGreater(result['mean_logic_reduction_pct'],10)
                    self.assertFalse(result['resource_comparisons'][case]['logic_nonincrease'])
                    self.assertEqual(result['category_status']['resources'],'FAIL')
                    self.assertEqual(status,'NEEDS_REVIEW')

    def test_invalid_public_provenance_or_ledger_cannot_produce_valid_mean(self):
        for fault in ('public_sample_id', 'public_resources', 'duplicate_attempt', 'wrong_schedule'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp); self.fixture(root)
                ledger='attempt' in fault or 'schedule' in fault
                path=root/('09_performance/round01/synthesis_ledger.json' if ledger else '05_public/round01/summary.json')
                data=json.loads(path.read_text(encoding='utf-8'))
                if fault=='public_sample_id': data['cases'][-1]['optimized_sample_id']='wrong-source'
                elif fault=='public_resources': data['cases'][-1]['optimized_resources']['logic_units']+=1
                elif fault=='duplicate_attempt': data['attempts'][-1]=copy.deepcopy(data['attempts'][0])
                else: data['schedule'][-1]=copy.deepcopy(data['schedule'][0])
                path.write_text(json.dumps(data),encoding='utf-8')
                status,result=self.report(root)
                self.assertIsNone(result['mean_logic_reduction_pct'])
                self.assertFalse(result['area_requirement_met'])
                self.assertEqual(status,'NEEDS_REVIEW')

    def test_invalid_sample_artifact_input_script_or_tool_invalidates_mean(self):
        from test_measure_v8 import fixture_cases
        for fault in ('metrics_valid','artifact','input_sha256','flow_sha256','executable_sha256'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp); self.fixture(root); case=fixture_cases()[-1]['id']
                folder=root/'05_public/round01'/case/'optimized'
                if fault=='artifact':
                    (folder/'stat.json').write_text('{}',encoding='utf-8')
                else:
                    path=folder/'measure_result.json'; sample=json.loads(path.read_text(encoding='utf-8'))
                    sample[fault]=False if fault=='metrics_valid' else '0'*64
                    path.write_text(json.dumps(sample),encoding='utf-8')
                    path=root/'09_performance/round01/performance_summary.json'; perf=json.loads(path.read_text(encoding='utf-8'))
                    case_row=next(row for row in perf if row['case']==case)
                    case_row['samples']=[sample if row['side']=='optimized' else row for row in case_row['samples']]
                    path.write_text(json.dumps(perf),encoding='utf-8')
                status,result=self.report(root)
                self.assertIsNone(result['mean_logic_reduction_pct'])
                self.assertFalse(result['area_requirement_met'])
                self.assertEqual(status,'NEEDS_REVIEW')

    def test_missing_proof_preserves_independently_valid_resource_mean(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); self.fixture(root)
            path=root/'10_selfcheck/chains/run01/chains_summary.json'
            data=json.loads(path.read_text(encoding='utf-8')); data.pop()
            path.write_text(json.dumps(data),encoding='utf-8')
            status,result=self.report(root)
            self.assertEqual(result['mean_logic_reduction_pct'],20)
            self.assertTrue(result['area_requirement_met'])
            self.assertEqual(result['category_status']['resources'],'PASS')
            self.assertEqual(result['category_status']['formal'],'FAIL')
            self.assertEqual(status,'NEEDS_REVIEW')

    def test_zero_baseline_cannot_produce_mean_or_pass(self):
        from unittest.mock import patch
        from test_measure_v8 import fixture_cases
        import report_v8
        original=B.parse_resource_counts
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); self.fixture(root)
            def parse(stat,text,top):
                row=original(stat,text,top)
                if top==fixture_cases()[-1]['top']: row['logic_units']=0
                return row
            with patch.object(report_v8.B,'parse_resource_counts',side_effect=parse):
                status,result=self.report(root)
            self.assertIsNone(result['mean_logic_reduction_pct'])
            self.assertEqual(status,'NEEDS_REVIEW')

if __name__ == '__main__': unittest.main()
