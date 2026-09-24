#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P3 v1 validation runner; adapted from the preserved 2026-09-22 round.
See ../POLICY.md for scope, provenance and limitations.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p3_common as C
from run_eqy_chains import make_cfg, net_side_prelude, summarize_eqy


from formal_status import run_eqy


def gen_ref_model(name: str, ctrl_w: int, lane_w: int) -> str:
    """独立参考模型：用移位运算符表达与拼接表达不同的实现。"""
    width = lane_w * 4
    banks = (1 << ctrl_w) // 4
    bank_bits = ctrl_w - 2
    lines = [
        f"// 独立参考模型（移位表达）: phase=ctrl[1:0], bank=ctrl[{ctrl_w-1}:2]",
        f"// 模块名与用例相同（EQY 要求 gold/gate 顶层同名）",
        f"module {name} (",
        f"    input  wire [{ctrl_w-1}:0] ctrl,",
        f"    input  wire [{banks*width-1}:0] d,",
        f"    output wire [{width-1}:0] y",
        ");",
    ]
    # bank 选择（先选 bank 再旋转，直观语义）
    if banks == 1:
        lines.append(f"    wire [{width-1}:0] pre = d;")
    else:
        lo_hi = []
        for b in range(banks):
            lo = b * width
            cond = f"ctrl[{ctrl_w-1}:2] == {bank_bits}'d{b}" if bank_bits > 1 else f"ctrl[{ctrl_w-1}:2] == 1'b{b}"
            lo_hi.append(f"({cond}) ? d[{lo+width-1}:{lo}]")
        lines.append(
            f"    wire [{width-1}:0] pre = "
            + " : ".join(lo_hi)
            + f" : {width}'b0;"
        )
    lines += [
        "    wire [1:0] phase = ctrl[1:0];",
        f"    wire [{width-1}:0] s_amt = phase * {lane_w};  // 移位量（bit）",
        f"    wire [{width-1}:0] rot_r = pre >> s_amt;",
        f"    wire [{width-1}:0] rot_l = pre << ({width} - s_amt);",
        "    assign y = (phase == 2'd0) ? pre",
        "                          : (rot_r | rot_l);",
        "endmodule",
    ]
    return "\n".join(lines) + "\n"


def main():
    root = C.ROUND_DIR / "07_负例与边界_negative" / "h2_cases_run01"
    meta = json.loads((root / "cases.json").read_text())
    cases = meta["cases"]
    rtl_dir = root / "rtl"
    flows = root / "flows"
    C.refuse_overwrite(flows)
    flows.mkdir(parents=True)
    bridge = C.ASCII_BRIDGE

    results = []
    for case in cases:
        name = case["name"]
        rtl = rtl_dir / f"{name}.v"
        d = flows / name
        d.mkdir()
        res = dict(case)
        res["ref_check_state"] = "NOT_APPLICABLE" if case["kind"] != "positive" else "NOT_RUN"
        res["rtl_sha256"] = C.sha256_file(rtl)

        # 1) 流程两侧
        for side, optimized in (("baseline", False), ("optimized", True)):
            sd = d / side
            sd.mkdir()
            ys = C.gen_split_flow_ys(
                rtl, name, optimized=optimized, dump_dir=sd, tag=side,
                stat_json=sd / "stat.json",
            )
            (sd / "flow.ys").write_text(ys)
            rc = C.run_yosys(ys, sd / "run.log", plugin=optimized, timeout=300)
            res[f"{side}_rc"] = rc
            if rc == 0 and (sd / "stat.json").exists():
                stat = C.parse_stat_json(sd / "stat.json")
                pre = C.extract_pmux_stats_from_il(sd / f"{side}_pre_p3.il")
                res[f"{side}_total"] = stat["total_cells"]
                res[f"{side}_comb"] = stat["comb"]
                res[f"{side}_dff"] = stat["dffeas"]
                res[f"{side}_pre_pmux"] = pre["pmux_cells"]
                res[f"{side}_pre_s_widths"] = pre["s_widths"]
                res[f"{side}_check"] = C.check_assert_ok(sd / "run.log")
                if optimized:
                    trig = C.extract_triggers(sd / "run.log")
                    res["plugin_ran"] = trig.get("plugin_ran", False)
                    res["triggers"] = {
                        k: trig.get(k, 0)
                        for k in (
                            "h2_candidate_cells", "h2_rebuilt",
                            "pairswap_candidate", "pairswap_rebuilt",
                            "branch_const_fold", "branch_expr_const_fold",
                            "guard_aware",
                        )
                    }
            else:
                res[f"{side}_check"] = False

        # 2) 期望判定
        if not res.get("plugin_ran"):
            raise RuntimeError(f"Missing plugin execution evidence: {name}")
        t = res.get("triggers", {})
        if case["kind"] == "positive":
            res["expect_verdict"] = (
                "OK"
                if t.get("h2_rebuilt", 0) >= 1 and res.get("optimized_rc") == 0
                else "MISMATCH"
            )
        else:
            res["expect_verdict"] = (
                "OK"
                if t.get("h2_rebuilt", 0) == 0 and t.get("h2_candidate_cells", 0) == 0
                and res.get("optimized_rc") == 0
                else "MISMATCH"
            )

        # 3) 独立参考模型（仅正例；用移位表达）
        if case["kind"] == "positive":
            ref_text = gen_ref_model(name, case["ctrl_width"], case["lane_width"])
            ref = rtl_dir / f"{name}_ref.v"
            if not ref.exists():
                ref.write_text(ref_text)
            # EQY: ref (gold) vs rtl (gate) —— 组合等价
            rtl_b = C.stage_to_ascii_bridge(rtl, f"h2/{name}/{name}.v")
            ref_b = C.stage_to_ascii_bridge(ref, f"h2/{name}/{name}_ref.v")
            cfg_text = (
                "[gold]\n"
                f"read_verilog -sv {ref_b}\n"
                f"hierarchy -check -top {name}\n"
                f"prep -top {name}\n\n[gate]\n"
                f"read_verilog -sv {rtl_b}\n"
                f"hierarchy -check -top {name}\n"
                f"prep -top {name}\n\n[strategy simple]\nuse sat\ndepth 3\n"
            )
            cd = d / "ref_check"
            cd.mkdir()
            cfg = cd / "config.eqy"
            cfg.write_text(cfg_text)
            rc = run_eqy(cfg, cd / "work", cd / "verify.log", timeout_s=300)
            res["ref_check_rc"] = rc
            summ = summarize_eqy(cd / "verify.log", cd / "work")
            res["ref_check_state"] = summ["state"]

        # 4) EQY c1 / c2
        rtl_b = C.stage_to_ascii_bridge(rtl, f"h2/{name}/{name}.v")
        for chain, ((g_side, g_kind), (a_side, a_kind)) in {
            "c1_local": (("optimized", "pre_p3"), ("optimized", "post_p3")),
            "c2_stage": (("baseline", "coarse_done"), ("optimized", "coarse_done")),
        }.items():
            g = flows / name / g_side / f"{g_side}_{g_kind}.il"
            a = flows / name / a_side / f"{a_side}_{a_kind}.il"
            if not (g.exists() and a.exists()):
                res[f"{chain}_state"] = "NOT_RUN"
                continue
            gb = C.stage_to_ascii_bridge(g, f"h2/{name}/{g_side}_{g_kind}.il")
            ab = C.stage_to_ascii_bridge(a, f"h2/{name}/{a_side}_{a_kind}.il")
            cfg_text = make_cfg(
                net_side_prelude(gb, name), net_side_prelude(ab, name)
            )
            cd = d / chain
            cd.mkdir()
            cfg = cd / "config.eqy"
            cfg.write_text(cfg_text)
            rc = run_eqy(cfg, cd / "work", cd / "verify.log", timeout_s=600)
            summ = summarize_eqy(cd / "verify.log", cd / "work")
            res[f"{chain}_rc"] = rc
            res[f"{chain}_state"] = summ["state"]
            res[f"{chain}_proved"] = f"{summ['proved']}/{summ['total']}"

        results.append(res)
        print(
            f"{name:24s} kind={case['kind'][:4]} rc={res.get('baseline_rc')}/"
            f"{res.get('optimized_rc')} comb={res.get('baseline_comb')}->"
            f"{res.get('optimized_comb')} h2r={t.get('h2_rebuilt')} "
            f"verdict={res['expect_verdict']} "
            f"ref={res.get('ref_check_state')} c1={res.get('c1_local_state')}"
        )

    (root / "h2_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n"
    )
    print(f"\n结果: {C.rel(root / 'h2_results.json')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
