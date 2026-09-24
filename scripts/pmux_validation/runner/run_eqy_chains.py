#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""official4-p2 功能证明链运行器（chains）。

相对 official4-p1 的协议修正（版本化；详见 config.json / POLICY.md）：
- 模型：轮内 runner/form_cells_cycloneiv.v = 器件语义模型 v3（与已核对实验模型逐字节相同）；
- 策略：EQY setup（`eqy -m`，只生成分区与脚本、不执行证明）→ **严格转换**（仅删除
  恰一处 ` -set-def-formal`；任何格式不符立即停止）→ 本地执行 + 前提探针
  （noDF 必需 SAT；DF 仅记录历史签名对照）；
- 预检：映射网表跑前经 runner/precheck_supported_config.py 支持配置预检（未支持即阻断）；
- test3：链级证据 = 无切割整模块合并证明（两侧分别运行；覆盖全部输出与匹配点；
  模板与“该轮实际分区集合”核对，不特判结果），分区级结果保留为辅助记录；其余用例保留分区路径；
- --frozen-round：功能复核模式只读复用既有轮次的公开产物（对照该轮 ALL_SHA256 逐文件核对），
  不重新综合、不测性能；核对失败即停止，不回退全流程。

判定（联合，不允许只凭单一 SUCCESS 字样）：
  证明 PASS ⇔ 成功标记 + 基例数>=归纳长度 + 断言导入覆盖 + 全文无 ERROR（且进程未超时/非零退出的日志不得判 PASS）；
  链 PASS ⇔ 全部证据 PASS + noDF 前提探针全部 SAT + 覆盖/转换核验通过。
"""
import argparse
import csv
import io
import json
import sys
import contextlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p3_common as C
import function_common as F

CASES = ["test1", "test2", "test3", "test4"]
MAIN_CHAINS = ("c1_local", "c2_stage", "c4a_rtl_opt_mapped", "c4b_rtl_base_mapped")
FULL_CHAINS = ("c1_local", "c2_stage", "c3a_rtl_opt", "c3b_rtl_base",
               "c4a_rtl_opt_mapped", "c4b_rtl_base_mapped", "c5_mapped_pair")

PARTITION_PROOF_TIMEOUT = 600
PARTITION_PROBE_TIMEOUT = 120
MERGED_PROOF_TIMEOUT = 600
MERGED_PROBE_TIMEOUT = 120
WORKERS = 8

# test3 专用合并证明：模板 + 该用例全部输出/匹配点（按该轮实际分区集合核对覆盖）
MERGED = {
    "test3": {
        "template": "miter/test3_miter.sv",
        "port_of_partition": {"test3.rw": "__mp_rw", "test3.sr": "__mp_sr",
                              "test3.sr_out": "__po_sr_out", "test3.gpioout": "__po_gpioout"},
        "assert_suffixes": ["__mp_rw__assert.okay", "__mp_sr__assert.okay",
                            "__po_sr_out__assert.okay", "__po_gpioout__assert.okay"],
        "maxsteps": 16,
    }
}


# ---------------------------------------------------------------- EQY 配置生成
def discover_modules(il_path: Path):
    mods = []
    for line in Path(il_path).read_text(errors="replace").splitlines():
        if line.startswith("module "):
            mods.append(line.split()[1].lstrip("\\"))
    return mods


def net_side_prelude(il_path: Path, top: str) -> list:
    lines = [f"read_rtlil {il_path}"]
    others = [m for m in discover_modules(il_path) if m != top]
    lines.append(f"hierarchy -top {top}")
    if others:
        lines.append("delete " + " ".join("=" + m for m in others))
    lines.append(f"prep -top {top}")
    lines.append("memory_collect")
    lines.append("memory_map")
    return lines


def net_side_prelude_mapped(il_path: Path, top: str, form_model: Path) -> list:
    lines = [f"read_rtlil {il_path}"]
    others = [m for m in discover_modules(il_path) if m != top]
    lines.append(f"hierarchy -top {top}")
    if others:
        lines.append("delete " + " ".join("=" + m for m in others))
    from formal_status import check_mapped_model
    check_mapped_model(il_path, top)
    lines.append(f"read_verilog -sv {form_model}")
    lines.append("delete t:$specify2")
    lines.append(f"hierarchy -check -top {top}")
    lines.append(f"prep -top {top}")
    lines.append("memory_collect")
    lines.append("memory_map")
    return lines


def rtl_side_prelude(rtl_path: Path, top: str) -> list:
    return [
        f"read_verilog -sv {rtl_path}",
        f"hierarchy -check -top {top}",
        f"prep -top {top}",
        "memory_collect",
        "memory_map",
    ]


EQY_TAIL = """
[strategy simple]
use sat
depth 5
"""


def make_cfg(gold_lines: list, gate_lines: list) -> str:
    return ("[gold]\n" + "\n".join(gold_lines) + "\n\n[gate]\n" + "\n".join(gate_lines)
            + "\n" + EQY_TAIL)


# ---------------------------------------------------------------- 分区运行
def run_strategy(strategy_dir: Path, *, yosys: str) -> dict:
    run_ys = strategy_dir / "run.ys"
    orig = run_ys.read_text()
    try:
        new_text, info = F.transform_run_ys(orig)
    except F.TransformError as exc:
        raise F.TransformError("{}: {}".format(strategy_dir, exc))
    (strategy_dir / "run.ys.eqy-generated").write_text(orig)
    run_ys.write_text(new_text)
    (strategy_dir / "transform.json").write_text(json.dumps({
        "strategy_version": F.STRATEGY_VERSION,
        "orig_sha256": F.sha256_file(strategy_dir / "run.ys.eqy-generated"),
        "new_sha256": F.sha256_file(run_ys),
        "info": info,
    }, ensure_ascii=False, indent=2) + "\n")

    rc = F.run_yosys_script(run_ys, strategy_dir / "run_noDF.log", strategy_dir,
                            yosys=yosys, timeout_s=PARTITION_PROOF_TIMEOUT)
    proof = F.classify_proof_text((strategy_dir / "run_noDF.log").read_text(errors="replace"))
    proof["rc"] = rc
    if rc == 124:
        proof["state"] = "TIMEOUT"
    elif rc != 0 and proof["state"] in ("PASS", "INCOMPLETE"):
        proof["state"] = "TOOL_OR_CONFIG_ERROR"

    probes = {}
    for variant in ("noDF", "DF"):
        base = new_text if variant == "noDF" else orig
        probe_ys = strategy_dir / "probe_{}.ys".format(variant)
        probe_ys.write_text(F.make_probe_ys(base, variant))
        prc = F.run_yosys_script(probe_ys, strategy_dir / "probe_{}.log".format(variant),
                                 strategy_dir, yosys=yosys, timeout_s=PARTITION_PROBE_TIMEOUT)
        pv = F.classify_probe_text(
            (strategy_dir / "probe_{}.log".format(variant)).read_text(errors="replace"))
        pv["rc"] = prc
        probes[variant] = pv

    (strategy_dir / "status_noDF.json").write_text(json.dumps(
        {"proof": proof, "probes": probes}, ensure_ascii=False, indent=2) + "\n")
    return {"proof": proof, "probes": probes}


def run_partitions(work: Path, *, yosys: str) -> dict:
    sdirs = sorted(d for d in (work / "strategies").glob("*/*") if d.is_dir())
    results = {}
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {d.parent.name if d.name == "simple" else str(d): ex.submit(
            run_strategy, d, yosys=yosys) for d in sdirs}
        for d in sdirs:
            key = d.parent.name if d.name == "simple" else str(d)
            results[key] = futs[key].result()
    return results


def aggregate_partitions(parts: dict) -> dict:
    states = {p: r["proof"]["state"] for p, r in parts.items()}
    npass = sum(1 for s in states.values() if s == "PASS")
    probes_ok = bool(parts) and all(
        r["probes"]["noDF"]["verdict"] == "PREMISES_SAT" for r in parts.values())
    df_unsat = sum(1 for r in parts.values()
                   if r["probes"]["DF"]["verdict"] == "PREMISES_UNSAT")
    if not parts:
        state = "INCOMPLETE"
    elif not probes_ok:
        state = "PREMISES_NOT_SAT"
    elif npass == len(states):
        state = "PASS"
    elif any(s == "FAIL" for s in states.values()):
        state = "FAIL"
    elif any(s == "TIMEOUT" for s in states.values()):
        state = "TIMEOUT"
    elif any(s == "TOOL_OR_CONFIG_ERROR" for s in states.values()):
        state = "TOOL_OR_CONFIG_ERROR"
    elif any(s == "UNKNOWN" for s in states.values()):
        state = "UNKNOWN"
    else:
        state = "INCOMPLETE"
    return {"state": state, "partitions_total": len(states), "partitions_pass": npass,
            "partition_states": states, "probes_noDF_all_sat": probes_ok,
            "df_probes_unsat": df_unsat}


# ---------------------------------------------------------------- 合并证明（test3）
def run_merged(case: str, cdir: Path, *, yosys: str) -> dict:
    meta = MERGED[case]
    strat = sorted(d.name for d in (cdir / "work" / "strategies").iterdir() if d.is_dir())
    expected = sorted(meta["port_of_partition"])
    if strat != expected:
        return {"state": "METHOD_REVIEW_REQUIRED",
                "reason": "分区集合与模板覆盖不符: {} != {}".format(strat, expected)}
    tmpl_src = C.SCRIPT_DIR / meta["template"]
    tmpl = tmpl_src.read_text()
    missing = [pt for pt in (meta["port_of_partition"][p] for p in expected)
               if ("\\" + pt + "__gold") not in tmpl or ("\\" + pt + "__gate") not in tmpl]
    if missing:
        return {"state": "METHOD_REVIEW_REQUIRED",
                "reason": "模板未覆盖端口: " + ", ".join(missing)}
    src_il = cdir / "work" / "modules" / "{}.il".format(case)
    if not src_il.is_file():
        return {"state": "METHOD_REVIEW_REQUIRED",
                "reason": "缺少合并模块文件: {}".format(src_il)}
    mdir = cdir / "merged"
    mdir.mkdir(exist_ok=True)
    (mdir / "test3_miter.sv").write_text(tmpl)
    (mdir / "{}.merged.il".format(case)).write_text(src_il.read_text())

    head = ("verilog_defaults -add -D CHECK_OUTPUTS\n"
            "verilog_defaults -add -D CHECK_MATCH_POINTS\n"
            "read_verilog -sv test3_miter.sv\n"
            "read_rtlil {}.merged.il\n".format(case)
            + "hierarchy -top miter; proc; chformal -cover -remove\n"
            "async2sync\n"
            "formalff -clk2ff -ff2anyinit gate.{}\n".format(case)
            + "setundef -anyseq gate.{}\n".format(case)
            + "flatten -wb; dffunmap; opt_expr -keepdc -undriven; opt_clean\n")

    probe_ys = mdir / "probe_noDF.ys"
    probe_ys.write_text(head + "chformal -assert -remove\n"
                        "sat -seq 1 -set-init-undef -set-def-inputs -set-assumes miter\n")
    prc = F.run_yosys_script(probe_ys, mdir / "probe_noDF.log", mdir,
                             yosys=yosys, timeout_s=MERGED_PROBE_TIMEOUT)
    probe = F.classify_probe_text((mdir / "probe_noDF.log").read_text(errors="replace"))
    probe["rc"] = prc

    proof_ys = mdir / "proof_m{}.ys".format(meta["maxsteps"])
    proof_ys.write_text(head + "sat -tempinduct -set-init-undef -set-def-inputs "
                        "-maxsteps {} -set-assumes -prove-asserts miter\n".format(meta["maxsteps"]))
    rc = F.run_yosys_script(proof_ys, mdir / "proof_m{}.log".format(meta["maxsteps"]), mdir,
                            yosys=yosys, timeout_s=MERGED_PROOF_TIMEOUT)
    proof = F.classify_proof_text(
        (mdir / "proof_m{}.log".format(meta["maxsteps"])).read_text(errors="replace"))
    proof["rc"] = rc
    if rc == 124:
        proof["state"] = "TIMEOUT"
    elif rc != 0 and proof["state"] in ("PASS", "INCOMPLETE"):
        proof["state"] = "TOOL_OR_CONFIG_ERROR"
    cover_ok, cover_missing = F.verify_expected_asserts(meta["assert_suffixes"], proof["asserts"])

    if probe["verdict"] != "PREMISES_SAT":
        state = "PREMISES_NOT_SAT"
    elif proof["state"] != "PASS":
        state = proof["state"]
    elif not cover_ok:
        state = "INCOMPLETE"
    else:
        state = "PASS"
    res = {"state": state, "k": proof.get("induct_len"), "probe": probe["verdict"],
           "proof_state": proof["state"], "rc": rc, "probe_rc": prc,
           "asserts": proof["asserts"], "assert_cover_ok": cover_ok,
           "assert_cover_missing": cover_missing,
           "template_sha256": F.sha256_file(tmpl_src),
           "module_sha256": F.sha256_file(mdir / "{}.merged.il".format(case)),
           "maxsteps": meta["maxsteps"], "timeout_s": MERGED_PROOF_TIMEOUT}
    (mdir / "status.json").write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n")
    return res


# ---------------------------------------------------------------- 冻结轮次核对
def parse_all_sha256(path: Path):
    index = {}
    for line in path.read_text(errors="replace").splitlines():
        parts = line.split("  ", 1)
        if len(parts) == 2:
            index[parts[1].strip()] = parts[0].strip()
    return index


def verify_frozen(frozen: Path, used) -> (bool, list):
    index_path = frozen / "11_汇总与证据_summary" / "ALL_SHA256.txt"
    if not index_path.is_file():
        return False, [{"file": str(index_path), "status": "MANIFEST_MISSING"}]
    index = parse_all_sha256(index_path)
    ok, details = True, []
    for src, rel in used:
        if not src.is_file():
            ok = False
            details.append({"file": rel, "status": "SOURCE_MISSING"})
            continue
        sha = F.sha256_file(src)
        expected = index.get(rel)
        match = (expected == sha)
        ok = ok and match
        details.append({"file": rel, "sha256": sha, "manifest_sha256": expected, "match": match})
    return ok, details


# ---------------------------------------------------------------- 主流程
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--attempt", default="run01")
    ap.add_argument("--chains", choices=["main", "full"], default="main")
    ap.add_argument("--frozen-round", default=None,
                    help="功能复核：只读复用既有轮次 05_公开四例_public 产物（逐文件哈希核对）")
    args = ap.parse_args()
    if not __import__("re").fullmatch(r"run[0-9]+", args.attempt):
        ap.error("attempt must be runNN")
    selected = list(MAIN_CHAINS if args.chains == "main" else FULL_CHAINS)
    out = C.ROUND_DIR / "10_验证工具自检_selfcheck" / "chains" / args.attempt
    C.refuse_overwrite(out)
    out.mkdir(parents=True)

    pub = C.ROUND_DIR / "05_公开四例_public" / "round01"
    frozen = None
    if args.frozen_round:
        frozen = Path(args.frozen_round)
        if not frozen.is_absolute():
            frozen = C.REPO / frozen
        pub = frozen / "05_公开四例_public" / "round01"
        if not pub.is_dir():
            print("STOP：冻结轮次缺少 05_公开四例_public/round01：{}".format(pub))
            return 2

    bridge = C.ASCII_BRIDGE
    hash_map = {}
    used_frozen = []

    def stage(src: Path, rel: str, frozen_rel=None):
        dst = C.stage_to_ascii_bridge(src, rel)
        hash_map[str(dst)] = {"source": C.rel(src), "sha256": C.sha256_file(src)}
        if frozen_rel is not None:
            used_frozen.append((src, frozen_rel))
        return dst

    form_model = stage(C.SCRIPT_DIR / "form_cells_cycloneiv.v", "chains/form_cells_cycloneiv.v")
    inputs_dir = form_model.parent

    case_paths = {}
    for top in CASES:
        rtl = stage(C.TREE / "pmux_case" / "competition_case" / top / "{}.v".format(top),
                    "chains/{}.v".format(top))
        sides = {}
        for side in ("baseline", "optimized"):
            for kind in ("pre_p3", "post_p3", "coarse_done", "mapped"):
                src = pub / top / side / "{}_{}.il".format(side, kind)
                rel = "05_公开四例_public/round01/{}/{}/{}_{}.il".format(top, side, side, kind)
                sides[(side, kind)] = stage(src, "chains/{}_{}_{}.il".format(top, side, kind),
                                            frozen_rel=(rel if frozen else None))
        case_paths[top] = {"rtl": rtl, "sides": sides}

    if frozen:
        ok, details = verify_frozen(frozen, used_frozen)
        (out / "frozen_input_verification.json").write_text(json.dumps({
            "ok": ok, "frozen_round": str(frozen), "manifest": "11_汇总与证据_summary/ALL_SHA256.txt",
            "files": details}, ensure_ascii=False, indent=2) + "\n")
        if not ok:
            print("STOP：冻结输入哈希核对失败（{} 个文件）；不运行任何证明，不回退全流程。".format(
                sum(1 for d in details if not d.get("match", False))))
            return 2
        print("冻结输入哈希核对通过：{} 个文件".format(len(details)))

    # 跑前支持配置预检（边界：无输入/缺预期即失败；未支持配置阻断）
    from precheck_supported_config import main as precheck_main
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        prc = precheck_main(["--dir", str(inputs_dir),
                             "--expect", *["{}:{}".format(c, s) for c in CASES
                                           for s in ("baseline", "optimized")],
                             "--top-from-name", "--model", "form_cells_cycloneiv.v"])
    (out / "precheck_report.txt").write_text(buf.getvalue())
    print(buf.getvalue(), end="")
    if prc != 0:
        print("STOP：支持配置预检未通过（未启动证明）。")
        return 2

    rows = []
    try:
        for top in CASES:
            for cname in selected:
                cdir = out / top / cname
                cdir.mkdir(parents=True)
                sides = case_paths[top]["sides"]
                rtl = case_paths[top]["rtl"]
                if cname == "c1_local":
                    cfg_text = make_cfg(net_side_prelude(sides[("optimized", "pre_p3")], top),
                                        net_side_prelude(sides[("optimized", "post_p3")], top))
                elif cname == "c2_stage":
                    cfg_text = make_cfg(net_side_prelude(sides[("baseline", "coarse_done")], top),
                                        net_side_prelude(sides[("optimized", "coarse_done")], top))
                elif cname == "c3a_rtl_opt":
                    cfg_text = make_cfg(rtl_side_prelude(rtl, top),
                                        net_side_prelude(sides[("optimized", "coarse_done")], top))
                elif cname == "c3b_rtl_base":
                    cfg_text = make_cfg(rtl_side_prelude(rtl, top),
                                        net_side_prelude(sides[("baseline", "coarse_done")], top))
                elif cname == "c4a_rtl_opt_mapped":
                    cfg_text = make_cfg(rtl_side_prelude(rtl, top),
                                        net_side_prelude_mapped(sides[("optimized", "mapped")],
                                                                top, form_model))
                elif cname == "c4b_rtl_base_mapped":
                    cfg_text = make_cfg(rtl_side_prelude(rtl, top),
                                        net_side_prelude_mapped(sides[("baseline", "mapped")],
                                                                top, form_model))
                elif cname == "c5_mapped_pair":
                    cfg_text = make_cfg(net_side_prelude_mapped(sides[("baseline", "mapped")],
                                                                top, form_model),
                                        net_side_prelude_mapped(sides[("optimized", "mapped")],
                                                                top, form_model))
                else:
                    raise ValueError(cname)
                (cdir / "config.eqy").write_text(cfg_text)
                rc = F.setup_eqy(cdir / "config.eqy", cdir / "work", cdir / "setup.log",
                                 yosys=C.TOOL_YOSYS, abc=C.EQY_ABC, eqy=C.TOOL_EQY)
                if rc != 0:
                    row = {"case": top, "chain": cname, "rc": 2, "state": "TOOL_OR_CONFIG_ERROR",
                           "method": "partition", "error": "eqy -m rc={}".format(rc),
                           "strategy_version": F.STRATEGY_VERSION, "model_version": F.MODEL_VERSION,
                           "partitions_total": 0, "partitions_pass": 0, "partition_states": {},
                           "probes_noDF_all_sat": False, "df_probes_unsat": 0, "merged": None,
                           "verified": False, "frozen_round": (str(frozen) if frozen else None),
                           "evidence": C.rel(cdir)}
                    rows.append(row)
                    (cdir / "summary.json").write_text(json.dumps(row, ensure_ascii=False, indent=2) + "\n")
                    print("{} {}: setup FAILED rc={}".format(top, cname, rc))
                    continue
                parts = run_partitions(cdir / "work", yosys=C.TOOL_YOSYS)
                agg = aggregate_partitions(parts)
                merged = None
                if top in MERGED and cname in ("c4a_rtl_opt_mapped", "c4b_rtl_base_mapped"):
                    merged = run_merged(top, cdir, yosys=C.TOOL_YOSYS)
                    final_state = merged["state"]
                    method = "merged_miter"
                else:
                    final_state = agg["state"]
                    method = "partition"
                row = {"case": top, "chain": cname,
                       "rc": 0 if final_state == "PASS" else 2,
                       "state": final_state, "method": method,
                       "strategy_version": F.STRATEGY_VERSION, "model_version": F.MODEL_VERSION,
                       "partitions_total": agg["partitions_total"],
                       "partitions_pass": agg["partitions_pass"],
                       "partition_states": agg["partition_states"],
                       "probes_noDF_all_sat": agg["probes_noDF_all_sat"],
                       "df_probes_unsat": agg["df_probes_unsat"],
                       "merged": merged, "verified": final_state == "PASS",
                       "frozen_round": (str(frozen) if frozen else None),
                       "evidence": C.rel(cdir)}
                rows.append(row)
                (cdir / "summary.json").write_text(json.dumps(row, ensure_ascii=False, indent=2) + "\n")
                extra = ""
                if merged:
                    extra = " merged={}@k{} probe={}".format(
                        merged["state"], merged.get("k"), merged.get("probe"))
                elif agg["partition_states"]:
                    detail = ", ".join("{}={}".format(k, v) for k, v in
                                       sorted(agg["partition_states"].items())[:6])
                    extra = " partitions: " + detail
                print("{} {}: {} ({} / {}){}".format(
                    top, cname, final_state, agg["partitions_pass"], agg["partitions_total"], extra),
                    flush=True)
    except F.TransformError as exc:
        (out / "transform_blocked.json").write_text(json.dumps(
            {"strategy_version": F.STRATEGY_VERSION, "error": str(exc)},
            ensure_ascii=False, indent=2) + "\n")
        print("STOP：EQY 生成脚本转换核验失败（已停止本次 chains）：{}".format(exc))
        return 2

    with open(out / "chains_summary.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["case", "chain", "method", "state", "rc", "partitions_total",
                    "partitions_pass", "probes_noDF_all_sat", "df_probes_unsat",
                    "merged_state", "merged_k", "probe_noDF", "verified",
                    "frozen_round", "evidence"])
        for r in rows:
            w.writerow([r["case"], r["chain"], r["method"], r["state"], r["rc"],
                        r["partitions_total"], r["partitions_pass"],
                        r["probes_noDF_all_sat"], r["df_probes_unsat"],
                        (r["merged"] or {}).get("state", ""),
                        (r["merged"] or {}).get("k", ""),
                        (r["merged"] or {}).get("probe", ""),
                        r["verified"], r["frozen_round"] or "", r["evidence"]])
    (out / "chains_summary.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    (out / "chains_set.json").write_text(json.dumps(
        {"chain_set": args.chains, "chains": sorted(selected),
         "strategy_version": F.STRATEGY_VERSION, "model_version": F.MODEL_VERSION},
        ensure_ascii=False, indent=2) + "\n")
    (out / "hash_manifest.json").write_text(json.dumps(hash_map, ensure_ascii=False, indent=2) + "\n")
    (bridge / "chains" / "hash_manifest.json").write_text(
        json.dumps(hash_map, ensure_ascii=False, indent=2) + "\n")
    print("结果目录: {}".format(C.rel(out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
