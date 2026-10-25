#!/usr/bin/env python3
import result_layout as L
# -*- coding: utf-8 -*-
"""V8 计量自检入口；正式八次综合由 measure_v8.py 直接执行。"""
import argparse
import os
import sys


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--selftest', action='store_true')
    args = ap.parse_args()
    if not args.selftest:
        ap.error('measure.py only supports V8 --selftest; use measure_v8.py for performance')
    import p3_common as C
    from measure_v8 import SCHEME, POLICY
    if (os.name != 'nt' or C.CONTEXT.get('mode') != 'builtin'
            or C.CONTEXT.get('performance_scheme') != SCHEME
            or C.CONTEXT.get('same_run_policy') != POLICY):
        raise ValueError('measurement selftest requires the fixed Windows V8 builtin context')
    from selfcheck_v8 import run
    return run(C.CONTEXT, C.ROUND_DIR / (L.PERFORMANCE + '/selftest'))


if __name__ == '__main__':
    sys.exit(main())
