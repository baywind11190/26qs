import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import analysis


class Gates(unittest.TestCase):
    def test_frequency_is_not_qpc_frequency(self):
        rows = [{'tsc_delta': 480000000, 'qpc_delta': 2000000}]
        self.assertEqual(analysis.calibration_hz(rows[0], 10000000), 2400000000)

    def test_frequency_threshold_and_last_value(self):
        self.assertEqual(analysis.frequency_gate([2400000000, 2400000000, 2401200000])[0], True)
        self.assertFalse(analysis.frequency_gate([2400000000, 2403000000])[0])
        self.assertFalse(analysis.frequency_gate([0, 2400000000])[0])

    def test_no_silent_fallback_or_false_full_coverage(self):
        self.assertEqual(analysis.verdict(False, False, False), '本机方案不可用')
        self.assertEqual(analysis.verdict(True, True, False), '仅部分计量可行')
        self.assertEqual(analysis.verdict(True, True, True), '本机试验可行')

    def test_wait_is_cpu_not_elapsed_and_resolution_is_observed(self):
        self.assertTrue(analysis.increment_gate([0.7, 8.0, 90.0, 250.0], 4000)['valid'])
        self.assertFalse(analysis.increment_gate([0.7, 8.0], 5000)['valid'])
        self.assertFalse(analysis.increment_gate([200, 250], 1)['valid'])

    def test_terminated_job_shortfall_must_stop(self):
        def bracket(lo, job, hi):
            return dict(sum_low=lo,job_cycles=job,sum_high=hi,valid=True,
                        ntstatus=0,returned_bytes=432,processes=3,active=1)
        row=dict(initial=bracket(100,110,120),live=bracket(200,210,220),
                 exited=bracket(500,480,520),handles_closed=bracket(550,530,570),
                 identities_valid=True,codes_valid=True,list_valid=True,
                 live_pids=[1,2,3],root_pid=1,child={'pid':2,'exit':0},
                 grandchild={'pid':3,'exit':0})
        row['initial']['processes']=1
        row['live']['active']=3
        result=analysis.tree_gate(row)
        self.assertFalse(result['valid'])
        self.assertEqual(result['exited']['residual_from_lower_cycles'], -20)
        self.assertIn('exited_outside_bracket', result['failures'])
        row['exited']['job_cycles']=510
        row['handles_closed']['job_cycles']=560
        self.assertTrue(analysis.tree_gate(row)['valid'])

    def test_fixed_sample_protocol_cannot_pass_incomplete_or_invalid_data(self):
        blocks=[]
        for n,t in [(0,1),(100,1),(1000,3),(10000,20),(100000,200)]:
            blocks += [dict(iterations=n,process_cycles=t+50,thread_cycles=t,
                            process_ticks=0,thread_ticks=0,valid=True) for _ in range(3)]
        row=dict(blocks=blocks,wait=dict(requested_ms=200,process_cycles=30,
                                       thread_cycles=2,valid=True))
        self.assertTrue(analysis.summarize_increments(row,1000000)['valid'])
        row['blocks']=blocks[:-1]
        self.assertFalse(analysis.summarize_increments(row,1000000)['valid'])
        row['blocks']=blocks
        row['wait']['process_cycles']=-1
        self.assertFalse(analysis.summarize_increments(row,1000000)['valid'])
        row['wait']['process_cycles']=30
        row['blocks'][0]['valid']='true'
        self.assertFalse(analysis.summarize_increments(row,1000000)['valid'])


if __name__ == '__main__':
    unittest.main()
