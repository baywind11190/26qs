#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P3 v1 validation runner; adapted from the preserved 2026-09-22 round.
See ../POLICY.md for scope, provenance and limitations.
"""

import csv
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p3_common as C


def run_case(top: str, out_root: Path) -> dict:
    rtl = C.TREE / "pmux_case" / "competition_case" / top / f"{top}.v"
    case_dir = out_root / top
    case_dir.mkdir(parents=True, exist_ok=False)

    result = {"case": top, "input": C.rel(rtl), "input_sha256": C.sha256_file(rtl)}

    for side, optimized in (("baseline", False), ("optimized", True)):
        side_dir = case_dir / side
        side_dir.mkdir()
        tag = side
        ys = C.gen_split_flow_ys(
            rtl,
            top,
            optimized=optimized,
            dump_dir=side_dir,
            tag=tag,
            stat_json=side_dir / "stat.json",
        )
        (side_dir / "flow.ys").write_text(ys)
        t0 = time.perf_counter()
        rc = C.run_yosys(ys, side_dir / "run.log", plugin=optimized)
        wall = time.perf_counter() - t0

        if rc != 0:
            raise RuntimeError(f"{top} {side} synthesis rc={rc}; see run.log")
        stat = C.parse_stat_json(side_dir / "stat.json")
        pre = C.extract_pmux_stats_from_il(side_dir / f"{tag}_pre_p3.il")
        post = C.extract_pmux_stats_from_il(side_dir / f"{tag}_post_p3.il")
        triggers = (
            C.extract_triggers(side_dir / "run.log") if optimized else {"plugin_ran": False}
        )
        ca_ok = C.check_assert_ok(side_dir / "run.log")

        entries = {
            f"{side}_rc": rc,
            f"{side}_wall_s": round(wall, 3),
            f"{side}_total": stat["total_cells"],
            f"{side}_comb": stat["comb"],
            f"{side}_dff": stat["dffeas"],
            f"{side}_pre_p3_pmux": pre["pmux_cells"],
            f"{side}_post_p3_pmux": post["pmux_cells"],
            f"{side}_pre_p3_s_widths": pre["s_widths"],
            f"{side}_post_p3_s_widths": post["s_widths"],
            f"{side}_check_assert": ca_ok,
            f"{side}_mapped_sha256": C.sha256_file(side_dir / f"{tag}_mapped.il"),
            f"{side}_coarse_done_sha256": C.sha256_file(
                side_dir / f"{tag}_coarse_done.il"
            ),
        }
        result.update(entries)
        (side_dir / "cell_types.json").write_text(
            json.dumps(stat["cell_types"], ensure_ascii=False, indent=2)
        )
        (side_dir / "triggers.json").write_text(
            json.dumps(triggers, ensure_ascii=False, indent=2)
        )

    # 缩减计算（未舍入，展示两位小数时再处理）
    def red(b, o):
        return (b - o) / b * 100.0 if b else None

    result["total_reduction_pct"] = red(result["baseline_total"], result["optimized_total"])
    result["comb_reduction_pct"] = red(result["baseline_comb"], result["optimized_comb"])
    result["dff_nonincrease"] = result["optimized_dff"] <= result["baseline_dff"]
    # 触发汇总（optimized 侧）
    trig = json.loads((case_dir / "optimized" / "triggers.json").read_text())
    if not trig.get("plugin_ran"):
        raise RuntimeError("Missing plugin execution evidence")
    result["h2_candidate"] = trig.get("h2_candidate_cells", 0)
    result["h2_rebuilt"] = trig.get("h2_rebuilt", 0)
    result["pairswap_rebuilt"] = trig.get("pairswap_rebuilt", 0)
    result["total_pmux_seen"] = trig.get("total_pmux", 0)
    # Formal results live in chains_summary.json; do not publish stale phase placeholders.
    return result


def main():
    out = C.ROUND_DIR / "05_公开四例_public" / "round01"
    C.refuse_overwrite(out)
    out.mkdir(parents=True)

    rows = []
    for i in range(1, 5):
        row = run_case(f"test{i}", out)
        rows.append(row)
        print(
            f"test{i}: total {row['baseline_total']}->{row['optimized_total']} "
            f"comb {row['baseline_comb']}->{row['optimized_comb']} "
            f"dff {row['baseline_dff']}->{row['optimized_dff']} "
            f"h2r={row['h2_rebuilt']} psr={row['pairswap_rebuilt']}"
        )

    # 公开均值（四例算术平均；缺测不缩分母）
    comb_reds = [r["comb_reduction_pct"] for r in rows]
    total_reds = [r["total_reduction_pct"] for r in rows]
    mean_comb = sum(comb_reds) / 4 if len(comb_reds) == 4 and None not in comb_reds else None
    mean_total = sum(total_reds) / 4 if len(total_reds) == 4 and None not in total_reds else None

    with open(out / "summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(
                {
                    k: ("" if v is None else v)
                    for k, v in r.items()
                }
            )

    summary = {
        "round": C.ROUND_DIR.name,
        "flow": "split-P3 (synth_intel coarse, pmux_opt between fsm;opt and wreduce)",
        "cases": rows,
        "public_mean_comb_reduction_pct": mean_comb,
        "public_mean_total_reduction_pct": mean_total,
    }
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    )
    print(f"\n公开均值: comb {mean_comb}%  total {mean_total}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
