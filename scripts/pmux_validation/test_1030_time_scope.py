import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'runner'))
import measure_v9 as M


class Official1030TimeScope(unittest.TestCase):
    def test_official_1_to_10_seconds(self):
        for ticks in (10_000_000, 50_000_000, 99_999_999):
            self.assertEqual(M.recheck_decision(ticks, ticks * 106 // 100),
                             dict(required=True, scope='OFFICIAL_1_TO_10S'))

    def test_threshold_boundaries_and_under_one_second(self):
        self.assertEqual(M.recheck_decision(100_000_000, 106_000_000),
                         dict(required=False, scope=None))
        self.assertEqual(M.recheck_decision(50_000_000, 52_500_000),
                         dict(required=False, scope=None))
        self.assertEqual(M.recheck_decision(1_000_000, 1_060_000),
                         dict(required=True, scope='OFFICIAL_UNDER_1S'))


if __name__ == '__main__':
    unittest.main()
