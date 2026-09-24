#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P3 v1 validation runner; adapted from the preserved 2026-09-22 round.
See ../POLICY.md for scope, provenance and limitations.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p3_common as C

SRC = (
    C.ROUND_DIR
    / "07_负例与边界_negative"
    / "h2_cases_run01"
    / "flows"
    / "h2p_c3_lw1"
    / "optimized"
    / "optimized_pre_p3.il"
)
OUT_DIR = C.ROUND_DIR / "07_负例与边界_negative" / "h2_cases_run01" / "driver_anomaly_run01"


def main():
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()

    if args.build or not (OUT_DIR / "h2n_multidriver.il").exists():
        C.refuse_overwrite(OUT_DIR)
        OUT_DIR.mkdir(parents=True)
        text = SRC.read_text()
        lines = text.splitlines()

        # 定位模块 h2p_c3_lw1 的顶格 end
        mod_start = None
        for i, ln in enumerate(lines):
            if ln.startswith("module \\h2p_c3_lw1"):
                mod_start = i
                break
        if mod_start is None:
            raise SystemExit("module not found")
        mod_end = None
        for j in range(mod_start + 1, len(lines)):
            if lines[j] == "end":
                mod_end = j
                break
        if mod_end is None:
            raise SystemExit("module end not found")

        # 找第一个 $eq cell 块
        eq_start = None
        for k in range(mod_start, mod_end):
            if lines[k].startswith("  cell $eq "):
                eq_start = k
                break
        if eq_start is None:
            raise SystemExit("no $eq cell found")
        eq_end = None
        for m in range(eq_start + 1, mod_end):
            if lines[m].strip() == "end":
                eq_end = m
                break
        block = lines[eq_start : eq_end + 1]
        orig_name = block[0].split()[2]
        clone = list(block)
        clone[0] = f"  cell $eq $injected_multi$0"
        # 插入到模块 end 之前
        new_lines = lines[:mod_end] + clone + lines[mod_end:]
        (OUT_DIR / "h2n_multidriver.il").write_text("\n".join(new_lines) + "\n")

        meta = {
            "source": C.rel(SRC),
            "source_sha256": C.sha256_file(SRC),
            "out_sha256": C.sha256_file(OUT_DIR / "h2n_multidriver.il"),
            "original_cell": orig_name,
            "injected_cell": "$injected_multi$0",
            "note": "克隆同一 $eq 条件 cell（同 A/B，同 Y）造成 selector 网络多驱动",
        }
        (OUT_DIR / "build_meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2) + "\n"
        )
        print(json.dumps(meta, ensure_ascii=False))
        if not args.run:
            return 0

    il = OUT_DIR / "h2n_multidriver.il"

    # baseline: check -assert 预期报问题
    ys_check = f"read_rtlil {il}\ncheck -assert\n"
    rc = C.run_yosys(ys_check, OUT_DIR / "baseline_check.log")
    check_text = (OUT_DIR / "baseline_check.log").read_text(errors="replace")
    problems = [l for l in check_text.splitlines() if "Warning" in l or "ERROR" in l]
    (OUT_DIR / "baseline_check_result.json").write_text(
        json.dumps(
            {
                "rc": rc,
                "problems": problems[:20],
                "expected": "check -assert 报告多驱动问题（rc!=0 或存在 Warning）",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    print(f"baseline check -assert rc={rc} problems={len(problems)}")

    # 插件：不崩溃、无 H2 REBUILT
    ys_plugin = f"read_rtlil {il}\npmux_opt\n"
    rc2 = C.run_yosys(ys_plugin, OUT_DIR / "plugin_run.log", plugin=True)
    plug_text = (OUT_DIR / "plugin_run.log").read_text(errors="replace")
    h2c = plug_text.count("H2 ROTATION CANDIDATE")
    h2r = plug_text.count("H2 ROTATION REBUILT")
    crashed = "Segmentation" in plug_text or "Aborted" in plug_text or rc2 not in (0, 1)
    (OUT_DIR / "plugin_run_result.json").write_text(
        json.dumps(
            {
                "rc": rc2,
                "h2_candidate": h2c,
                "h2_rebuilt": h2r,
                "crashed": crashed,
                "expected": "不崩溃；H2 不重构（multi-driver 网表不属于合法 H2 结构）",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    print(f"plugin rc={rc2} h2_candidate={h2c} h2_rebuilt={h2r} crashed={crashed}")

    ok = rc == 1 and "multiple conflicting drivers" in check_text.lower() and rc2 == 0 and "Executing PMUX_OPT" in plug_text and h2r == 0 and not crashed
    print(f"driver_anomaly_ok={ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
