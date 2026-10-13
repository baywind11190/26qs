"""Dumper interrupt reports must be applied, not just requested at export."""
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).parent/'runner'))
from etw_reference import read_reference

TRACE='''P-Start, TimeStamp, Process Name ( PID), ParentPID, UniqueKey
P-End, TimeStamp, Process Name ( PID), ParentPID, UniqueKey
T-Start, TimeStamp, Process Name ( PID), ThreadID
T-End, TimeStamp, Process Name ( PID), ThreadID
CSwitch, TimeStamp, Old Process Name ( PID), Old TID, InSwitchTime, OldState, CPU
DPC_ISR_CSWITCH_PCT, TimeStamp, StartTime, Period, IsrDpc, OldPid, OldTid, CPU
OS Version: test, Events Lost: 0, Buffers lost: 0, Trace Start: 1000000
P-Start, 10000, target.exe (7), 1, k
T-Start, 10100, target.exe (7), 30
CSwitch, 10200, target.exe (7), 30, 80, Terminated, 2
DPC_ISR_CSWITCH_PCT, 10200, 10120, 80, 15, 7, 30, 2
T-End, 10300, target.exe (7), 30
P-End, 10400, target.exe (7), 1, k
'''
SAMPLE=dict(main_pid=7,process_create_filetime=1100000,process_exit_filetime=1104000,job_total_processes=1)

class InterruptTests(unittest.TestCase):
    def parse(self,text):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'events.csv';p.write_text(text)
            return read_reference(p,[SAMPLE])[0]
    def test_interrupt_time_is_removed(self):
        self.assertEqual(self.parse(TRACE)['cpu_reference_ticks'],650)
    def test_missing_mismatched_duplicate_and_excess_reports_rejected(self):
        report='DPC_ISR_CSWITCH_PCT, 10200, 10120, 80, 15, 7, 30, 2\n'
        for text in [TRACE.replace(report,''),TRACE.replace('15, 7, 30, 2','15, 8, 30, 2'),
                     TRACE.replace(report,report*2),TRACE.replace('80, 15, 7','80, 81, 7')]:
            with self.subTest(text=text),self.assertRaises(ValueError):self.parse(text)

if __name__=='__main__':unittest.main()
