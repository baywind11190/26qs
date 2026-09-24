#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""official4-p2 形式化自检（run_selfcheck）。

检查项由 assets/checks.json 驱动（少量、有针对性）：
- rtl_positive / rtl_negative：EQY 管道正/负例（既有素材，经新版 noDF 管道执行）；
- mac_init_ok / mac_init_conflict：初值一致（应通过）/ 初值冲突（应被检出）；
- mac_clr / mac_ena：v3 模型清零、使能路径（v2 会检出的最小复现；应通过）；
- mac_lut_ok / mac_lut_bad：LUT 模型正确性 / 映射层真实逻辑改错检出；
- maskreg_premise：未声明初值 FF 的“已发现矛盾前提”回归——noDF 前提必须 SAT；
  DF 前提应为 UNSAT（历史签名，仅记录不强制）。

所有检查均经与 chains 相同的 noDF 管道（EQY setup → 严格转换 → 本地执行 + 前提探针），
确保自检验证的就是正式功能路径本身。退出码 0=全部符合预期；1=存在不符合项。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p3_common as C
import function_common as F

PROOF_TIMEOUT = 300
PROBE_TIMEOUT = 120


def build_cfg(check, gold, gate, model, top):
    if check.get("kind") == "rtl":
        gold_lines = ["read_verilog -sv {}".format(gold), "prep -top {}".format(top)]
        gate_lines = ["read_verilog -sv {}".format(gate), "prep -top {}".format(top)]
    else:
        gold_lines = ["read_verilog -sv {}".format(gold),
                      "hierarchy -check -top {}".format(top),
                      "prep -top {}".format(top), "memory_collect", "memory_map"]
        gate_lines = ["read_verilog -sv {}".format(gate),
                      "hierarchy -top {}".format(top),
                      "read_verilog -sv {}".format(model),
                      "delete t:$specify2",
                      "hierarchy -check -top {}".format(top),
                      "prep -top {}".format(top), "memory_collect", "memory_map"]
    return ("[gold]\n" + "\n".join(gold_lines) + "\n\n[gate]\n" + "\n".join(gate_lines)
            + "\n\n[strategy simple]\nuse sat\ndepth 5\n")


def run_check(check, gold, gate, model, d):
    cfg = d / "config.eqy"
    cfg.write_text(build_cfg(check, gold, gate, model, check["top"]))
    rc = F.setup_eqy(cfg, d / "work", d / "setup.log",
                     yosys=C.TOOL_YOSYS, abc=C.EQY_ABC, eqy=C.TOOL_EQY)
    if rc != 0:
        return {"state": "TOOL_OR_CONFIG_ERROR", "error": "eqy -m rc={}".format(rc),
                "partitions": {}}
    parts = {}
    for sdir in sorted((d / "work" / "strategies").glob("*/simple")):
        pname = sdir.parent.name
        res = {}
        try:
            run_ys = sdir / "run.ys"
            orig = run_ys.read_text()
            new_text, info = F.transform_run_ys(orig)
        except F.TransformError as exc:
            return {"state": "TRANSFORM_ERROR", "error": "{}: {}".format(pname, exc),
                    "partitions": parts}
        (sdir / "run.ys.eqy-generated").write_text(orig)
        run_ys.write_text(new_text)
        (sdir / "transform.json").write_text(json.dumps(
            {"strategy_version": F.STRATEGY_VERSION,
             "orig_sha256": F.sha256_file(sdir / "run.ys.eqy-generated"),
             "new_sha256": F.sha256_file(run_ys), "info": info},
            ensure_ascii=False, indent=2) + "\n")
        prc = F.run_yosys_script(run_ys, sdir / "run_noDF.log", sdir,
                                 yosys=C.TOOL_YOSYS, timeout_s=PROOF_TIMEOUT)
        proof = F.classify_proof_text((sdir / "run_noDF.log").read_text(errors="replace"))
        proof["rc"] = prc
        if prc == 124:
            proof["state"] = "TIMEOUT"
        elif prc != 0 and proof["state"] in ("PASS", "INCOMPLETE"):
            proof["state"] = "TOOL_OR_CONFIG_ERROR"
        probes = {}
        for variant in ("noDF", "DF"):
            base = new_text if variant == "noDF" else orig
            pys = sdir / "probe_{}.ys".format(variant)
            pys.write_text(F.make_probe_ys(base, variant))
            xrc = F.run_yosys_script(pys, sdir / "probe_{}.log".format(variant), sdir,
                                     yosys=C.TOOL_YOSYS, timeout_s=PROBE_TIMEOUT)
            pv = F.classify_probe_text(
                (sdir / "probe_{}.log".format(variant)).read_text(errors="replace"))
            pv["rc"] = xrc
            probes[variant] = pv
        res = {"proof": proof, "probes": probes}
        (sdir / "status_noDF.json").write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n")
        parts[pname] = res
    return {"state": "RUN_DONE", "partitions": parts}


def judge(check, res):
    parts = res.get("partitions") or {}
    states = [p["proof"]["state"] for p in parts.values()]
    probes_noDF = [p["probes"]["noDF"]["verdict"] for p in parts.values()]
    probes_DF = [p["probes"]["DF"]["verdict"] for p in parts.values()]
    expect = check["expect"]
    detail = {"proof_states": states, "probe_noDF": probes_noDF, "probe_DF": probes_DF}
    if not parts:
        return False, "no partitions", detail
    if expect == "PASS":
        ok = all(s == "PASS" for s in states) and all(v == "PREMISES_SAT" for v in probes_noDF)
    elif expect == "REJECT":
        ok = any(s == "FAIL" for s in states)
    elif expect == "PREMISE_SAT":
        ok = all(v == "PREMISES_SAT" for v in probes_noDF)
        if check.get("df_probe_expect") and check.get("df_probe_enforce"):
            ok = ok and all(v == check["df_probe_expect"] for v in probes_DF)
    else:
        ok = False
    return ok, "" if ok else "expect={} not met".format(expect), detail


def main():
    base = C.ROUND_DIR / "10_验证工具自检_selfcheck" / "attempt01"
    C.refuse_overwrite(base)
    base.mkdir(parents=True)
    assets = C.ROUND_DIR / "10_验证工具自检_selfcheck" / "assets"

    checks = json.loads((assets / "checks.json").read_text())["checks"]
    model = C.stage_to_ascii_bridge(C.SCRIPT_DIR / "form_cells_cycloneiv.v",
                                    "selfcheck/form_cells_cycloneiv.v")
    summary = {"checks_version": json.loads((assets / "checks.json").read_text())
               .get("version"), "model_version": F.MODEL_VERSION,
               "strategy_version": F.STRATEGY_VERSION, "cases": []}
    hash_map = {}

    for check in checks:
        name = check["name"]
        gold_src = assets / check.get("gold", "mapped_model_gold.v")
        gate_src = assets / check.get("gate", "mapped_model_gate.v")
        gold = C.stage_to_ascii_bridge(gold_src, "selfcheck/{}_gold.v".format(name))
        gate = C.stage_to_ascii_bridge(gate_src, "selfcheck/{}_gate.v".format(name))
        for src, dst in ((gold_src, gold), (gate_src, gate)):
            hash_map[str(dst)] = {"source": C.rel(src), "sha256": C.sha256_file(src),
                                  "bridge_sha256": C.sha256_file(dst),
                                  "match": C.sha256_file(src) == C.sha256_file(dst)}
        d = base / name
        d.mkdir()
        try:
            res = run_check(check, gold, gate, model, d)
            ok, why, detail = judge(check, res)
        except Exception as exc:  # 保留现场，不掩盖
            res, ok, why, detail = {"state": "EXCEPTION", "error": str(exc)}, False, "exception", {}
        case = {"name": name, "expect": check["expect"], "ok": ok, "why": why,
                "state": res.get("state"), "error": res.get("error"),
                "detail": detail}
        summary["cases"].append(case)
        (d / "summary.json").write_text(json.dumps(case, ensure_ascii=False, indent=2) + "\n")
        print("{}: expect={} ok={}{}".format(name, check["expect"], ok,
                                             "" if not why else " ({})".format(why)))

    summary["selfcheck_ok"] = all(c["ok"] for c in summary["cases"])
    (base / "selfcheck_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    (C.ASCII_BRIDGE / "selfcheck" / "hash_manifest.json").write_text(
        json.dumps(hash_map, ensure_ascii=False, indent=2) + "\n")
    print("selfcheck_ok={}".format(summary["selfcheck_ok"]))
    return 0 if summary["selfcheck_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
