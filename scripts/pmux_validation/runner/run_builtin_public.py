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
pmux_opt（原版不含该调用）；p3-local-lut 还在 map_luts 末尾执行 pmux_opt -lut，
post_abc.il 在局部 LUT 优化完成后导出。两侧独立目录、独立进程运行同一脚本，
输出路径差异由各自工作目录处理（相对输出名）。

输出：05_公开四例_public/round01/<case>/<side>/（flow.ys、run.log、
post_abc.il、mapped.il、stat.json、triggers.json、cell_types.json）
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
import integration_profiles as I


def run_case(top: str, out_root: Path) -> dict:
    rtl_source = C.TREE / "pmux_case" / "competition_case" / top / "{}.v".format(top)
    rtl = C.stage_to_ascii_bridge(rtl_source, "builtin_inputs/{}.v".format(top))
    joint = C.CONTEXT.get('performance_scheme') == 'pmux-perf-single-powershell-same-run-exitpeak-v8'
    case_dir = out_root / top
    case_dir.mkdir(parents=True, exist_ok=joint)
    builtin = C.CONTEXT.get("builtin") or {}
    binaries = B.select_binaries(builtin)

    script = B.gen_builtin_formal_ys(rtl, top)
    script_sha = hashlib.sha256(script.encode()).hexdigest()
    result = {"case": top, "input": C.rel(rtl_source),
              "input_sha256": C.sha256_file(rtl_source),
              "staged_input": str(rtl), "staged_input_sha256": C.sha256_file(rtl),
              "script_sha256": script_sha}

    for side, binary in binaries.items():
        side_dir = case_dir / side
        side_dir.mkdir(exist_ok=joint)
        if joint:
            if (side_dir / 'flow.ys').read_text(encoding='utf-8') != script:
                raise RuntimeError('same-run script mismatch')
        else:
            (side_dir / "flow.ys").write_text(script)
        (side_dir / "binary.txt").write_text(str(binary) + "\n" + C.sha256_file(binary) + "\n")
        t0 = time.perf_counter()
        if joint:
            from measure_v8 import sample_errors
            sample = json.loads((side_dir / 'measure_result.json').read_text(encoding='utf-8'))
            errors = sample_errors(sample, require_outputs=True)
            if errors: raise RuntimeError('; '.join(errors))
            rc = sample['rc']; wall = sample['total_milliseconds'] / 1000
            result[side + '_sample_id'] = sample['sample_id']
        else:
            rc = C.run_binary(binary, script, side_dir / "run.log", cwd=side_dir)
            wall = time.perf_counter() - t0
        if rc != 0:
            raise RuntimeError("{} {} synthesis rc={}; see run.log".format(top, side, rc))
        stat = C.parse_stat_json(side_dir / "stat.json")
        resource = B.parse_resource_counts(
            json.loads((side_dir / "stat.json").read_text(encoding="utf-8")),
            (side_dir / "mapped.il").read_text(encoding="utf-8", errors="replace"),
            top,
        )
        from formal_status import check_post_abc_model
        stage_info = check_post_abc_model(side_dir / "post_abc.il", top)
        full_stat_path = C.ROUND_DIR / "04_流程一致性_flowcheck" / "builtin_run01" / top / side / "stat.json"
        full_stat = C.parse_stat_json(full_stat_path) if not joint else None
        if not joint and stat["cell_types"] != full_stat["cell_types"]:
            raise RuntimeError(f"{top} {side}: split/full synthesis resource mismatch")
        ca_ok = C.check_assert_ok(side_dir / "run.log")
        log_text = (side_dir / "run.log").read_text(errors="replace")
        if not B.abc9_mapping_ok(log_text):
            raise RuntimeError(f"{top} {side}: expected ABC9 mapping, no ABC substitution")
        triggers = (C.extract_triggers(side_dir / "run.log") if side == "optimized"
                    else {"plugin_ran": False})
        if side == "optimized" and "Executing PMUX_OPT" not in log_text:
            raise RuntimeError("{} optimized 缺少内置 pmux_opt 执行证据".format(top))
        if side == "baseline" and "Executing PMUX_OPT" in log_text:
            raise RuntimeError("{} baseline 出现 PMUX_OPT 执行痕迹".format(top))
        if side == 'optimized':
            calls = I.check_calls(log_text, I.identity(C.CONTEXT), require_export=True)
            if not calls['ok']:
                raise RuntimeError(f'{top}: integration calls/export position invalid: {calls}')
            result['optimized_integration_calls'] = calls
        result[side + '_formal_netlist_description'] = (
            'after ABC9 and 7.1 local LUT, before map_cells'
            if side == 'optimized' and I.identity(C.CONTEXT) == I.LOCAL_ID
            else 'after ABC9, before map_cells')

        result.update({
            "{}_split_full_resources_match".format(side): None if joint else True,
            "{}_mapping_complete".format(side): bool(ca_ok and B.abc9_mapping_ok(log_text)),
            "{}_independent_full_split_check".format(side): "NOT_RUN" if joint else "PASS",
            "{}_post_abc_lut".format(side): stage_info["lut_cells"],
            "{}_post_abc_sha256".format(side): C.sha256_file(side_dir / "post_abc.il"),
            "{}_formal_netlist_stage".format(side): "post_abc",
            "{}_abc9_ok".format(side): True,
            "{}_rc".format(side): rc,
            "{}_wall_s".format(side): round(wall, 3),
            "{}_total".format(side): stat["total_cells"],
            "{}_comb".format(side): resource["comb"],
            "{}_lut_count".format(side): resource["lut_count"],
            "{}_inverter_count".format(side): resource["inverter_count"],
            "{}_logic_units".format(side): resource["logic_units"],
            "{}_dff".format(side): resource["dff_count"],
            "{}_io_ports".format(side): resource["io_ports"],
            "{}_io_bits".format(side): resource["io_bits"],
            "{}_other_cell_types".format(side): resource["other_cell_types"],
            "{}_resources".format(side): resource,
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
    resource_comparison = B.compare_resource_counts(
        result["baseline_resources"], result["optimized_resources"])
    result["logic_reduction_pct"] = resource_comparison["logic_reduction_pct"]
    result["dff_nonincrease"] = resource_comparison["dff_nonincrease"]
    result["io_nonincrease"] = resource_comparison["io_nonincrease"]
    result["io_resources"] = resource_comparison["io_resources"]
    result["other_resources"] = resource_comparison["other_resources"]
    result["other_resources_nonincrease"] = result["other_resources"]["ok"]
    result["resource_checks_ok"] = resource_comparison["resource_checks_ok"]
    trig = json.loads((case_dir / "optimized" / "triggers.json").read_text())
    result["h2_candidate"] = trig.get("h2_candidate_cells", 0)
    result["h2_rebuilt"] = trig.get("h2_rebuilt", 0)
    result["pairswap_rebuilt"] = trig.get("pairswap_rebuilt", 0)
    result["total_pmux_seen"] = trig.get("total_pmux", 0)
    return result


def main():
    out = C.ROUND_DIR / "05_公开四例_public" / "round01"
    joint = C.CONTEXT.get('performance_scheme') == 'pmux-perf-single-powershell-same-run-exitpeak-v8'
    C.refuse_overwrite(out / 'summary.json' if joint else out)
    out.mkdir(parents=True, exist_ok=joint)

    rows = []
    for i in range(1, 5):
        row = run_case("test{}".format(i), out)
        rows.append(row)
        print("test{}: total {}->{} comb {}->{} dff {}->{} script={}".format(
            i, row["baseline_total"], row["optimized_total"],
            row["baseline_comb"], row["optimized_comb"],
            row["baseline_dff"], row["optimized_dff"], row["script_sha256"][:12]))

    comb_reds = [r["comb_reduction_pct"] for r in rows]
    logic_reds = [r["logic_reduction_pct"] for r in rows]
    total_reds = [r["total_reduction_pct"] for r in rows]
    mean_comb = sum(comb_reds) / 4 if len(comb_reds) == 4 and None not in comb_reds else None
    mean_logic = sum(logic_reds) / 4 if len(logic_reds) == 4 and None not in logic_reds else None
    mean_total = (sum(total_reds) / 4 if len(total_reds) == 4 and None not in total_reds
                  else None)

    with open(out / "summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if v is None else v) for k, v in r.items()})

    summary = {
        "round": C.ROUND_DIR.name,
        'integration_id': I.identity(C.CONTEXT),
        "flow": ("builtin synth_intel (pmux_opt inside synth_intel.cc between fsm;opt "
                 "and wreduce; optional registered local LUT after ABC9); external script identical for both sides"),
        "cases": rows,
        "resource_metric": "cycloneiv_lcell_comb + independent inverter bits",
        "public_mean_logic_reduction_pct": mean_logic,
        "public_mean_comb_reduction_pct": mean_comb,
        "public_mean_total_reduction_pct": mean_total,
    }
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print("\n内置公开均值: logic_units {}%  LUT {}%  total {}%".format(
        mean_logic, mean_comb, mean_total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
