#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P3 v1 validation runner; adapted from the preserved 2026-09-22 round.
See ../POLICY.md for scope, provenance and limitations.
"""

import csv
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p3_common as C

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_eqy_chains import (  # noqa: E402
    discover_modules,
    net_side_prelude,
    make_cfg,
    summarize_eqy,
)


from formal_status import run_eqy


def main():
    reg = C.ROUND_DIR / "06_模式回归_regression" / "run01"
    out = C.ROUND_DIR / "06_模式回归_regression" / "eqy_run01"
    C.refuse_overwrite(out)
    out.mkdir(parents=True)
    bridge = C.ASCII_BRIDGE

    cases = []
    for subdir in ("pattern_a", "pattern_b", "pattern_c", "pattern_d", "h1"):
        for case_dir in sorted((reg / subdir).glob("*")):
            if case_dir.is_dir():
                cases.append((subdir, case_dir))

    rows = []
    # top 字典
    tops = {}
    for r in json.loads((reg / "regression_summary.json").read_text()):
        tops[r["case"]] = r["top"]

    for subdir, case_dir in cases:
        name = case_dir.name
        top = tops[name]
        cdir_out = out / subdir / name
        cdir_out.mkdir(parents=True)
        # 暂存 4 个网表到桥
        files = {}
        for side, kind in (
            ("baseline", "coarse_done"),
            ("optimized", "coarse_done"),
            ("optimized", "pre_p3"),
            ("optimized", "post_p3"),
        ):
            src = case_dir / side / f"{side}_{kind}.il"
            dst = C.stage_to_ascii_bridge(
                src, f"regression/{subdir}/{name}/{side}_{kind}.il"
            )
            files[(side, kind)] = dst
        for chain, ((g_side, g_kind), (a_side, a_kind)) in {
            "c1_local": (
                ("optimized", "pre_p3"),
                ("optimized", "post_p3"),
            ),
            "c2_stage": (
                ("baseline", "coarse_done"),
                ("optimized", "coarse_done"),
            ),
        }.items():
            cfg_text = make_cfg(
                net_side_prelude(files[(g_side, g_kind)], top),
                net_side_prelude(files[(a_side, a_kind)], top),
            )
            cd = cdir_out / chain
            cd.mkdir()
            cfg = cd / "config.eqy"
            cfg.write_text(cfg_text)
            rc = run_eqy(cfg, cd / "work", cd / "verify.log", timeout_s=300)
            summ = summarize_eqy(cd / "verify.log", cd / "work")
            summ.update({"case": name, "group": subdir, "chain": chain, "rc": rc})
            (cd / "summary.json").write_text(
                json.dumps(summ, ensure_ascii=False, indent=2) + "\n"
            )
            rows.append(summ)
            print(
                f"{name:24s} {chain}: rc={rc} {summ['state']} "
                f"{summ['proved']}/{summ['total']}"
            )

    with open(out / "regression_eqy_summary.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["case", "group", "chain", "rc", "state", "proved", "total", "failed", "failed_detail"])
        for r in rows:
            w.writerow(
                [
                    r.get("case"),
                    r.get("group"),
                    r.get("chain"),
                    r.get("rc"),
                    r.get("state"),
                    r.get("proved"),
                    r.get("total"),
                    r.get("failed"),
                    "; ".join(
                        f"{p['name']}={p['status']}"
                        for p in r.get("failed_partitions", [])
                    ),
                ]
            )
    (out / "regression_eqy_summary.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n"
    )
    print(f"\n结果目录: {C.rel(out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
