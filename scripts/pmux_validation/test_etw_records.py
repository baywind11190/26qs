"""xperf event records are physical lines, command tails are not RFC CSV."""
from pathlib import Path
import tempfile,sys,unittest
sys.path[:0]=['D:/codex/0000_26qs/scripts/pmux_validation','D:/codex/0000_26qs/scripts/pmux_validation/runner']
from etw_reference import read_reference
from test_etw_interrupts import TRACE,SAMPLE

class PhysicalRecords(unittest.TestCase):
    def parse(self,text):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'events.csv';p.write_text(text)
            return read_reference(p,[SAMPLE])[0]['cpu_reference_ticks']
    def test_other_process_command_quote_cannot_swallow_events(self):
        text=TRACE.replace('P-End, TimeStamp, Process Name ( PID), ParentPID, UniqueKey',
                           'P-End, TimeStamp, Process Name ( PID), ParentPID, UniqueKey, Command Line')
        text=text.replace('P-Start, 10000,', 'P-End, 9000, other.exe (99), 1, z, "unclosed command\nP-Start, 10000,')
        self.assertEqual(self.parse(text),650)
    def test_target_command_tail_does_not_change_identity_or_cpu(self):
        text=TRACE.replace('P-Start, TimeStamp, Process Name ( PID), ParentPID, UniqueKey',
                           'P-Start, TimeStamp, Process Name ( PID), ParentPID, UniqueKey, Command Line')
        text=text.replace('P-Start, 10000, target.exe (7), 1, k\n','P-Start, 10000, target.exe (7), 1, k, "unclosed command\n')
        self.assertEqual(self.parse(text),650)

if __name__=='__main__':unittest.main()
