#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P3 v1 validation runner; adapted from the preserved 2026-09-22 round.
See ../POLICY.md for scope, provenance and limitations.
"""

import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p3_common as C

TREE = C.TREE


def find_top(rtl: Path) -> str:
    text = rtl.read_text(errors="replace")
    m = re.search(r"^\s*module\s+([A-Za-z_][A-Za-z0-9_]*)", text, re.M)
    if not m:
        raise SystemExit(f"no module found in {rtl}")
    return m.group(1)


def collect_cases():
    cases = []
    for v in sorted((TREE / "regression" / "pattern_a").glob("*.v")):
        cases.append(("A", "pattern_a", v))
    for v in sorted((TREE / "regression" / "pattern_b").glob("*.v")):
        cases.append(("B", "pattern_b", v))
    for v in sorted((TREE / "regression" / "pattern_c").glob("*.v")):
        cases.append(("C", "pattern_c", v))
    for v in sorted((TREE / "tests" / "pattern_d").glob("*.v")):
        cases.append(("D", "pattern_d", v))
    for v in sorted((TREE / "tests" / "h1").glob("*.v")):
        cases.append(("H1", "h1", v))
    return cases


# H1 预期（来自 tests/h1/README.md，P 流程 stable / H1 预期 pair-swap 次数；
# 在 P3 口径下作为参照，实际触发以本轮日志为准）
H1_EXPECT = {
    "h1_n1_three_special": "拒绝(0/0)",
    "h1_n2_small_two_special": "拒绝(0/0)",
    "h1_n3_width_mismatch": "拒绝(0/0)",
    "h1_n4_different_control": "拒绝(0/0)",
    "h1_n5_partial_decode": "拒绝(0/0)",
    "h1_n6_ctrlwidth1": "拒绝(0/0)",
    "h1_p1_threshold": "接受阈值(0/1)",
    "h1_p2_swapbit2": "非零swap bit(0/1)",
    "h1_p3_shuffle": "分支乱序(0/1)",
    "h1_p4_large": "较大结构(0/1)",
    "h1_p5_zero_special": "旧功能(1/1)",
    "h1_p6_one_special": "旧功能(1/1)",
}


def main():
    out = C.ROUND_DIR / "06_模式回归_regression" / "run01"
    C.refuse_overwrite(out)
    out.mkdir(parents=True)

    cases = collect_cases()
    print(f"共 {len(cases)} 个用例")

    rows = []
    for group, subdir, rtl in cases:
        name = rtl.stem
        top = find_top(rtl)
        d = out / subdir
        d.mkdir(exist_ok=True)
        case_dir = d / name
        case_dir.mkdir(exist_ok=False)

        row = {
            "case": name,
            "group": group,
            "top": top,
            "input_sha256": C.sha256_file(rtl),
            "expect_ref": H1_EXPECT.get(name, ""),
        }
        for side, optimized in (("baseline", False), ("optimized", True)):
            side_dir = case_dir / side
            side_dir.mkdir()
            ys = C.gen_split_flow_ys(
                rtl,
                top,
                optimized=optimized,
                dump_dir=side_dir,
                tag=side,
                stat_json=side_dir / "stat.json",
            )
            (side_dir / "flow.ys").write_text(ys)
            rc = C.run_yosys(ys, side_dir / "run.log", plugin=optimized)
            entry = {"rc": rc}
            if rc == 0 and (side_dir / "stat.json").exists():
                stat = C.parse_stat_json(side_dir / "stat.json")
                pre = C.extract_pmux_stats_from_il(side_dir / f"{side}_pre_p3.il")
                post = C.extract_pmux_stats_from_il(
                    side_dir / f"{side}_post_p3.il"
                )
                entry.update(
                    {
                        "total": stat["total_cells"],
                        "comb": stat["comb"],
                        "dff": stat["dffeas"],
                        "pre_pmux": pre["pmux_cells"],
                        "post_pmux": post["pmux_cells"],
                        "pre_s_widths": ",".join(map(str, pre["s_widths"])),
                        "check_assert": C.check_assert_ok(side_dir / "run.log"),
                    }
                )
                if optimized:
                    trig = C.extract_triggers(side_dir / "run.log")
                    entry["triggers"] = {
                        k: trig.get(k, 0)
                        for k in (
                            "h2_candidate_cells",
                            "h2_rebuilt",
                            "pairswap_candidate",
                            "pairswap_rebuilt",
                            "branch_const_fold",
                            "branch_expr_const_fold",
                            "guard_aware",
                            "total_pmux",
                        )
                    }
            row[side] = entry
        rows.append(row)

        b, o = row["baseline"], row["optimized"]
        print(
            f"{name:28s} rc={b.get('rc')}/{o.get('rc')} "
            f"comb={b.get('comb')}->{o.get('comb')} "
            f"pmux(pre)={b.get('pre_pmux')} "
            f"trig={o.get('triggers', {})}"
        )

    # CSV 展开
    fields = [
        "case",
        "group",
        "top",
        "input_sha256",
        "expect_ref",
        "baseline_rc",
        "baseline_total",
        "baseline_comb",
        "baseline_dff",
        "baseline_pre_pmux",
        "baseline_pre_s_widths",
        "baseline_check_assert",
        "optimized_rc",
        "optimized_total",
        "optimized_comb",
        "optimized_dff",
        "optimized_pre_pmux",
        "optimized_post_pmux",
        "optimized_pre_s_widths",
        "optimized_check_assert",
        "h2_candidate",
        "h2_rebuilt",
        "pairswap_rebuilt",
        "branch_const_fold",
        "branch_expr_fold",
        "guard_aware",
    ]
    with open(out / "regression_summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            b, o = r["baseline"], r["optimized"]
            t = o.get("triggers", {})
            w.writerow(
                {
                    "case": r["case"],
                    "group": r["group"],
                    "top": r["top"],
                    "input_sha256": r["input_sha256"],
                    "expect_ref": r["expect_ref"],
                    "baseline_rc": b.get("rc"),
                    "baseline_total": b.get("total"),
                    "baseline_comb": b.get("comb"),
                    "baseline_dff": b.get("dff"),
                    "baseline_pre_pmux": b.get("pre_pmux"),
                    "baseline_pre_s_widths": b.get("pre_s_widths"),
                    "baseline_check_assert": b.get("check_assert"),
                    "optimized_rc": o.get("rc"),
                    "optimized_total": o.get("total"),
                    "optimized_comb": o.get("comb"),
                    "optimized_dff": o.get("dff"),
                    "optimized_pre_pmux": o.get("pre_pmux"),
                    "optimized_post_pmux": o.get("post_pmux"),
                    "optimized_pre_s_widths": o.get("pre_s_widths"),
                    "optimized_check_assert": o.get("check_assert"),
                    "h2_candidate": t.get("h2_candidate_cells"),
                    "h2_rebuilt": t.get("h2_rebuilt"),
                    "pairswap_rebuilt": t.get("pairswap_rebuilt"),
                    "branch_const_fold": t.get("branch_const_fold"),
                    "branch_expr_fold": t.get("branch_expr_const_fold"),
                    "guard_aware": t.get("guard_aware"),
                }
            )
    (out / "regression_summary.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n"
    )
    print(f"\n结果目录: {C.rel(out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
