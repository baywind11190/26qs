#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P3 v1 validation runner; adapted from the preserved 2026-09-22 round.
See ../POLICY.md for scope, provenance and limitations.
"""

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p3_common as C
from run_eqy_chains import make_cfg, net_side_prelude
from formal_status import summarize_eqy as summarize_enhanced


from formal_status import run_eqy


def count_il_cells(il_path: Path) -> dict:
    """统计 RTLIL 网表中 module 内 cell 计数与类型（粗解析）。"""
    import re

    types = {}
    n = 0
    for line in il_path.read_text(errors="replace").splitlines():
        m = re.match(r"^\s+cell (\S+) ", line)
        if m:
            n += 1
            t = m.group(1)
            types[t] = types.get(t, 0) + 1
    return {"num_cells": n, "by_type": types}


def main():
    base = C.ROUND_DIR / "08_规模与隐藏风格_scale_hidden" / "scale_run01"
    inputs = base / "inputs"
    flows = base / "flows"
    C.refuse_overwrite(flows)
    flows.mkdir(parents=True)
    bridge = C.ASCII_BRIDGE

    cases = [
        ("mixed_100", 100),
        ("mixed_250", 250),
        ("mixed_500", 500),
        ("mixed_750", 750),
        ("mixed_1000", 1000),
        ("pattern_a_1000", 1000),
        ("expr_1000", 1000),
        ("negative_1000", 1000),
        ("h2_1000", 1000),
        ("h1h2_1000", 1000),
        ("random_1000", 1000),
    ]

    rows = []
    for name, target in cases:
        rtl = inputs / f"{name}.v"
        meta = json.loads((inputs / f"{name}.v.json").read_text())
        d = flows / name
        d.mkdir()
        row = {
            "case": name,
            "target": target,
            "generator_nodes": meta["nodes_generator_caliber"],
            "units": json.dumps(meta["units"], ensure_ascii=False),
            "input_sha256": C.sha256_file(rtl),
        }

        for side, optimized in (("baseline", False), ("optimized", True)):
            sd = d / side
            sd.mkdir()
            ys = C.gen_split_flow_ys(
                rtl, "stress_top", optimized=optimized, dump_dir=sd, tag=side,
                stat_json=sd / "stat.json",
            )
            (sd / "flow.ys").write_text(ys)
            rc = C.run_yosys(ys, sd / "run.log", plugin=optimized, timeout=600)
            row[f"{side}_rc"] = rc
            if rc == 0 and (sd / "stat.json").exists():
                stat = C.parse_stat_json(sd / "stat.json")
                row[f"{side}_total"] = stat["total_cells"]
                row[f"{side}_comb"] = stat["comb"]
                row[f"{side}_dff"] = stat["dffeas"]
                row[f"{side}_check"] = C.check_assert_ok(sd / "run.log")
                if optimized:
                    trig = C.extract_triggers(sd / "run.log")
                    row["triggers"] = {
                        k: trig.get(k, 0)
                        for k in (
                            "h2_candidate_cells", "h2_rebuilt",
                            "pairswap_candidate", "pairswap_rebuilt",
                            "branch_const_fold", "branch_expr_const_fold",
                            "guard_aware",
                        )
                    }
            # P3 前实际节点
            pre = sd / f"{side}_pre_p3.il"
            if pre.exists():
                cinfo = count_il_cells(pre)
                if side == "optimized":
                    row["p3_pre_cells"] = cinfo["num_cells"]
                    top_types = sorted(
                        cinfo["by_type"].items(), key=lambda kv: -kv[1]
                    )[:10]
                    row["p3_pre_top_types"] = json.dumps(
                        dict(top_types), ensure_ascii=False
                    )

        # EQY c1/c2
        for chain, ((g_side, g_kind), (a_side, a_kind)) in {
            "c1_local": (("optimized", "pre_p3"), ("optimized", "post_p3")),
            "c2_stage": (("baseline", "coarse_done"), ("optimized", "coarse_done")),
        }.items():
            g = d / g_side / f"{g_side}_{g_kind}.il"
            a = d / a_side / f"{a_side}_{a_kind}.il"
            if not (g.exists() and a.exists()):
                row[f"{chain}_state"] = "NOT_RUN"
                continue
            gb = C.stage_to_ascii_bridge(g, f"scale/{name}/{g_side}_{g_kind}.il")
            ab = C.stage_to_ascii_bridge(a, f"scale/{name}/{a_side}_{a_kind}.il")
            cfg = make_cfg(
                net_side_prelude(gb, "stress_top"),
                net_side_prelude(ab, "stress_top"),
            )
            cd = d / chain
            cd.mkdir()
            (cd / "config.eqy").write_text(cfg)
            rc = run_eqy(cd / "config.eqy", cd / "work", cd / "verify.log",
                         timeout_s=600)
            row[f"{chain}_rc"] = rc
            summ = summarize_enhanced(cd / "verify.log", cd / "work")
            row[f"{chain}_state"] = summ["state"]
            row[f"{chain}_proved"] = f"{summ['proved']}/{summ['total']}"

        rows.append(row)
        print(
            f"{name:16s} gen={row['generator_nodes']:5d} "
            f"p3pre={row.get('p3_pre_cells')} "
            f"comb={row.get('baseline_comb')}->{row.get('optimized_comb')} "
            f"c1={row.get('c1_local_state')} c2={row.get('c2_stage_state')}"
        )

    fields = [
        "case", "target", "generator_nodes", "units", "input_sha256",
        "p3_pre_cells", "p3_pre_top_types",
        "baseline_rc", "baseline_total", "baseline_comb", "baseline_dff",
        "baseline_check", "optimized_rc", "optimized_total", "optimized_comb",
        "optimized_dff", "optimized_check",
        "h2_candidate", "h2_rebuilt", "pairswap_rebuilt",
        "branch_const_fold", "branch_expr_fold", "guard_aware",
        "c1_local_state", "c1_local_proved", "c2_stage_state", "c2_stage_proved",
    ]
    with open(base / "scale_summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            t = r.get("triggers", {})
            w.writerow(
                {
                    **r,
                    "h2_candidate": t.get("h2_candidate_cells"),
                    "h2_rebuilt": t.get("h2_rebuilt"),
                    "pairswap_rebuilt": t.get("pairswap_rebuilt"),
                    "branch_const_fold": t.get("branch_const_fold"),
                    "branch_expr_fold": t.get("branch_expr_const_fold"),
                    "guard_aware": t.get("guard_aware"),
                }
            )
    (base / "scale_summary.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n"
    )
    print(f"\n结果: {C.rel(base)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
