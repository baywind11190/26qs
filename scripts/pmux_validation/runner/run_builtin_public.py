#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""内置四例两侧综合运行器（run_builtin_public）。

对每个用例、两侧内置二进制分别运行**逐字节相同**的外部综合脚本：

    read_verilog -sv <rtl>
    synth_intel -family cycloneiv -top <top>
    check -assert
    write_rtlil mapped.il
    tee -o stat.json stat -json

优化版由 synth_intel.cc 内部在 fsm;opt 之后、wreduce 之前自动调用
pmux_opt（原版不含该调用）；两侧独立目录、独立进程运行同一脚本，
输出路径差异由各自工作目录处理（相对输出名）。

输出：05_公开四例_public/round01/<case>/<side>/（flow.ys、run.log、
mapped.il、stat.json、triggers.json、cell_types.json）
汇总：summary.json（cases 行；含 Comb/DFF 缩减与 DFF 不增检查）
"""
import csv
import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p3_common as C
import builtin_common as B


def run_case(top: str, out_root: Path) -> dict:
    rtl = C.TREE / "pmux_case" / "competition_case" / top / "{}.v".format(top)
    case_dir = out_root / top
    case_dir.mkdir(parents=True, exist_ok=False)
    builtin = C.CONTEXT.get("builtin") or {}
    binaries = B.select_binaries(builtin)

    script = C.gen_builtin_synth_ys(rtl, top)
    script_sha = hashlib.sha256(script.encode()).hexdigest()
    result = {"case": top, "input": C.rel(rtl), "input_sha256": C.sha256_file(rtl),
              "script_sha256": script_sha}

    for side, binary in binaries.items():
        side_dir = case_dir / side
        side_dir.mkdir()
        (side_dir / "flow.ys").write_text(script)
        (side_dir / "binary.txt").write_text(str(binary) + "\n" + C.sha256_file(binary) + "\n")
        t0 = time.perf_counter()
        rc = C.run_binary(binary, script, side_dir / "run.log", cwd=side_dir)
        wall = time.perf_counter() - t0
        if rc != 0:
            raise RuntimeError("{} {} synthesis rc={}; see run.log".format(top, side, rc))
        stat = C.parse_stat_json(side_dir / "stat.json")
        ca_ok = C.check_assert_ok(side_dir / "run.log")
        log_text = (side_dir / "run.log").read_text(errors="replace")
        triggers = (C.extract_triggers(side_dir / "run.log") if side == "optimized"
                    else {"plugin_ran": False})
        if side == "optimized" and "Executing PMUX_OPT" not in log_text:
            raise RuntimeError("{} optimized 缺少内置 pmux_opt 执行证据".format(top))
        if side == "baseline" and "Executing PMUX_OPT" in log_text:
            raise RuntimeError("{} baseline 出现 PMUX_OPT 执行痕迹".format(top))

        result.update({
            "{}_rc".format(side): rc,
            "{}_wall_s".format(side): round(wall, 3),
            "{}_total".format(side): stat["total_cells"],
            "{}_comb".format(side): stat["comb"],
            "{}_dff".format(side): stat["dffeas"],
            "{}_check_assert".format(side): ca_ok,
            "{}_mapped_sha256".format(side): C.sha256_file(side_dir / "mapped.il"),
        })
        (side_dir / "cell_types.json").write_text(
            json.dumps(stat["cell_types"], ensure_ascii=False, indent=2) + "\n")
        (side_dir / "triggers.json").write_text(
            json.dumps(triggers, ensure_ascii=False, indent=2) + "\n")

    def red(b, o):
        return (b - o) / b * 100.0 if b else None

    result["total_reduction_pct"] = red(result["baseline_total"], result["optimized_total"])
    result["comb_reduction_pct"] = red(result["baseline_comb"], result["optimized_comb"])
    result["dff_nonincrease"] = result["optimized_dff"] <= result["baseline_dff"]
    trig = json.loads((case_dir / "optimized" / "triggers.json").read_text())
    result["h2_candidate"] = trig.get("h2_candidate_cells", 0)
    result["h2_rebuilt"] = trig.get("h2_rebuilt", 0)
    result["pairswap_rebuilt"] = trig.get("pairswap_rebuilt", 0)
    result["total_pmux_seen"] = trig.get("total_pmux", 0)
    return result


def main():
    out = C.ROUND_DIR / "05_公开四例_public" / "round01"
    C.refuse_overwrite(out)
    out.mkdir(parents=True)

    rows = []
    for i in range(1, 5):
        row = run_case("test{}".format(i), out)
        rows.append(row)
        print("test{}: total {}->{} comb {}->{} dff {}->{} script={}".format(
            i, row["baseline_total"], row["optimized_total"],
            row["baseline_comb"], row["optimized_comb"],
            row["baseline_dff"], row["optimized_dff"], row["script_sha256"][:12]))

    comb_reds = [r["comb_reduction_pct"] for r in rows]
    total_reds = [r["total_reduction_pct"] for r in rows]
    mean_comb = sum(comb_reds) / 4 if len(comb_reds) == 4 and None not in comb_reds else None
    mean_total = (sum(total_reds) / 4 if len(total_reds) == 4 and None not in total_reds
                  else None)

    with open(out / "summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if v is None else v) for k, v in r.items()})

    summary = {
        "round": C.ROUND_DIR.name,
        "flow": ("builtin synth_intel (pmux_opt inside synth_intel.cc between fsm;opt "
                 "and wreduce); external script identical for both sides"),
        "cases": rows,
        "public_mean_comb_reduction_pct": mean_comb,
        "public_mean_total_reduction_pct": mean_total,
    }
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print("\n内置公开均值: comb {}%  total {}%".format(mean_comb, mean_total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
