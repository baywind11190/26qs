import unittest, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent/'runner'))
import builtin_common as B
from report import judge_case_performance
import types
from unittest.mock import patch
with patch.dict(sys.modules, {'p3_common': types.ModuleType('p3_common')}):
    from measure import run_measured

class P5Tests(unittest.TestCase):
    def test_export_not_in_timed_script(self):
        self.assertTrue(hasattr(B, 'gen_builtin_formal_ys'))
        f=B.gen_builtin_formal_ys('/tmp/a.v','top')
        self.assertLess(f.index('post_abc.il'), f.index('-run map_cells:'))
        self.assertNotIn('post_abc.il',B.gen_builtin_synth_ys('/tmp/a.v','top'))
        self.assertIn('-run begin:map_cells',f)
    def test_abc9_required(self):
        self.assertTrue(hasattr(B,'abc9_mapping_ok'))
        self.assertTrue(B.abc9_mapping_ok('2. Executing ABC9 pass.\n2.1. Executing ABC9.'))
        self.assertFalse(B.abc9_mapping_ok('2. Executing ABC pass.'))
    def test_other_resources(self):
        self.assertTrue(hasattr(B,'compare_other_resources'))
        d=B.compare_other_resources({'dffeas':2,'foo':1},{'dffeas':2,'foo':2})
        self.assertFalse(d['ok']); self.assertIn('foo',d['increases'])
    def test_new_memory_no_tree_fallback(self):
        s={'memory_metric':'yosys_main_rss_peak_kb','runs':[]}
        for side in ['baseline','optimized']:
            s['runs'].append(dict(side=side,rc=0,timed_out=False,stat_exists=True,cpu_total_s=1,tree_rss_peak_kb=10))
        s.update(baseline_cpu_total_median=1,optimized_cpu_total_median=1,baseline_tree_rss_peak_median=10,optimized_tree_rss_peak_median=10)
        self.assertFalse(judge_case_performance(s,pairs=1)['valid'])
    def test_main_memory_excludes_child(self):
        with tempfile.TemporaryDirectory() as d:
            code="import subprocess,sys,time; a=bytearray(12*1024*1024); subprocess.run([sys.executable,'-c','import time; a=bytearray(96*1024*1024); time.sleep(0.3)']); time.sleep(0.05)"
            r=run_measured([sys.executable,'-c',code],cwd=d,log_path=Path(d)/'run.log')
            self.assertIn('yosys_main_rss_peak_kb',r)
            self.assertGreater(r['yosys_main_rss_peak_kb'],12*1024)
            self.assertLess(r['yosys_main_rss_peak_kb'],70*1024)

    def test_main_memory_is_selected_and_cpu_limit_retained(self):
        s={'memory_metric':'yosys_main_rss_peak_kb','runs':[],
           'baseline_cpu_total_median':1,'optimized_cpu_total_median':1.06,
           'baseline_yosys_main_rss_peak_median':100,'optimized_yosys_main_rss_peak_median':100,
           'baseline_tree_rss_peak_median':100,'optimized_tree_rss_peak_median':1000}
        for side in ['baseline','optimized']:
            s['runs'].append(dict(side=side,rc=0,timed_out=False,stat_exists=True,cpu_total_s=1,yosys_main_rss_peak_kb=100))
        j=judge_case_performance(s,pairs=1)
        self.assertTrue(j['mem_ok']);self.assertFalse(j['cpu_ok']);self.assertFalse(j['pass'])
        s['optimized_cpu_total_median']=1.05
        self.assertTrue(judge_case_performance(s,pairs=1)['pass'])
    def test_legacy_tree_memory_preserved(self):
        s={'runs':[], 'baseline_cpu_total_median':1,'optimized_cpu_total_median':1,
           'baseline_tree_rss_peak_median':100,'optimized_tree_rss_peak_median':106}
        for side in ['baseline','optimized']:
            s['runs'].append(dict(side=side,rc=0,timed_out=False,stat_exists=True,cpu_total_s=1,tree_rss_peak_kb=100))
        self.assertFalse(judge_case_performance(s,pairs=1)['mem_ok'])
    def test_post_abc_rejects_final_netlist(self):
        from formal_status import check_post_abc_model
        from test_validation import _lcell_il
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.il';p.write_text(_lcell_il())
            with self.assertRaises(ValueError):check_post_abc_model(p,'top')
    def test_new_resource_type_detected(self):
        self.assertFalse(B.compare_other_resources({}, {'io_cell':1})['ok'])
        self.assertTrue(B.compare_other_resources({'dffeas':2},{'dffeas':1})['ok'])
