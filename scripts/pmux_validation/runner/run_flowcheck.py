#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P3 v1 validation runner; adapted from the preserved 2026-09-22 round.
See ../POLICY.md for scope, provenance and limitations.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p3_common as C


def extract_pass_sequence(log_path: Path):
    """从 yosys 日志提取 'N. Executing <PASS> ...' 的命令名序列。"""
    seq = []
    pat = re.compile(r"^\s*[\d.]+\s+Executing\s+(.+)$")
    for line in log_path.read_text(errors="replace").splitlines():
        m = pat.match(line)
        if not m:
            continue
        desc = m.group(1).strip()
        # 归一化：取第一个 " pass" 或 ":" 或行尾之前的名字
        name = re.split(r"\s+pass\b|:", desc, maxsplit=1)[0].strip().rstrip(".")
        seq.append(name)
    return seq


def main():
    out = C.ROUND_DIR / "04_流程一致性_flowcheck" / "formal_run01"
    C.refuse_overwrite(out)
    out.mkdir(parents=True)

    rows = []
    report_lines = [
        "# 04 流程一致性检查（原生 vs 拆分 baseline）",
        "",
        f"- 工具: {C.TOOL_YOSYS}（Yosys 0.69 / 源码提交 {C.YOSYS_SRC_COMMIT}）",
        f"- 输入树: {C.rel(C.TREE)}",
        "- 拆分流程: `synth_intel -run begin:coarse` + 手工展开 coarse 21 条命令 + `synth_intel -run map_bram:`",
        "- 两侧命令均与 techlibs/intel/synth_intel.cc (9f75ca1f9) 源码逐条一致；baseline 侧无 pmux_opt。",
        "",
        "| case | native rc | split rc | netlist | nl_sha_equal | stat_total | stat_comb | stat_dff | check_assert(split) |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    for i in range(1, 5):
        top = f"test{i}"
        rtl = C.TREE / "pmux_case" / "competition_case" / top / f"{top}.v"
        case_dir = out / top
        case_dir.mkdir()

        # ---- 原生流程 ----
        nat_ys = C.gen_native_flow_ys(
            rtl,
            top,
            out_il=case_dir / "native_mapped.il",
            stat_json=case_dir / "native_stat.json",
        )
        (case_dir / "native.ys").write_text(nat_ys)
        rc_nat = C.run_yosys(nat_ys, case_dir / "native.log")

        # ---- 拆分 baseline 流程 ----
        spl_ys = C.gen_split_flow_ys(
            rtl,
            top,
            optimized=False,
            dump_dir=case_dir,
            tag="split",
            stat_json=case_dir / "split_stat.json",
        )
        (case_dir / "split.ys").write_text(spl_ys)
        rc_spl = C.run_yosys(spl_ys, case_dir / "split.log")

        # ---- 对比 ----
        nat_il = case_dir / "native_mapped.il"
        spl_il = case_dir / "split_mapped.il"
        nat_sha = C.sha256_file(nat_il)
        spl_sha = C.sha256_file(spl_il)
        netlist_equal = nat_sha == spl_sha

        nat_stat = C.parse_stat_json(case_dir / "native_stat.json")
        spl_stat = C.parse_stat_json(case_dir / "split_stat.json")
        stat_equal = nat_stat == spl_stat

        ca_ok = C.check_assert_ok(case_dir / "split.log")

        # 命令序列对照（供人工审阅）
        seq_nat = extract_pass_sequence(case_dir / "native.log")
        seq_spl = extract_pass_sequence(case_dir / "split.log")
        (case_dir / "command_sequence_native.txt").write_text(
            "\n".join(seq_nat) + "\n"
        )
        (case_dir / "command_sequence_split.txt").write_text(
            "\n".join(seq_spl) + "\n"
        )

        rows.append(
            {
                "case": top,
                "native_rc": rc_nat,
                "split_rc": rc_spl,
                "native_mapped_sha256": nat_sha,
                "split_mapped_sha256": spl_sha,
                "netlist_equal": netlist_equal,
                "stat_equal": stat_equal,
                "native_total": nat_stat["total_cells"],
                "native_comb": nat_stat["comb"],
                "native_dff": nat_stat["dffeas"],
                "split_total": spl_stat["total_cells"],
                "split_comb": spl_stat["comb"],
                "split_dff": spl_stat["dffeas"],
                "check_assert_split": ca_ok,
            }
        )
        report_lines.append(
            "| {case} | {native_rc} | {split_rc} | {nl} | {eq} | {t} | {c} | {d} | {ca} |".format(
                case=top,
                native_rc=rc_nat,
                split_rc=rc_spl,
                nl="逐字节相等" if netlist_equal else "**不一致**",
                eq=netlist_equal,
                t=spl_stat["total_cells"],
                c=spl_stat["comb"],
                d=spl_stat["dffeas"],
                ca=ca_ok,
            )
        )

    # CSV
    import csv

    with open(out / "consistency_summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    all_ok = all(
        r["netlist_equal"] and r["stat_equal"] and r["native_rc"] == 0
        and r["split_rc"] == 0 and r["check_assert_split"]
        for r in rows
    )
    report_lines += [
        "",
        f"## 结论",
        "",
        f"- 逐例网表、资源和检查结果见上表；全部满足：{all_ok}。",
        f"- **流程一致性: {'PASS' if all_ok else 'FAIL'}**",
        "",
        "说明：拆分侧日志中的 `synth_intel` 启动次数为 3 次（原生 1 次）、并额外包含对称的 `check -assert` 与 `write_rtlil` dump 命令；",
        "coarse 阶段的 21 条命令与原生源码逐条一致（见 command_sequence_*.txt）。",
    ]
    (out / "REPORT.md").write_text("\n".join(report_lines) + "\n")

    print(json.dumps({"all_ok": all_ok, "rows": rows}, ensure_ascii=False, indent=2))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
