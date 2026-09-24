#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P3 v1 validation runner; adapted from the preserved 2026-09-22 round.
See ../POLICY.md for scope, provenance and limitations.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p3_common as C

EQY_TEMPLATE = """[gold]
read_verilog -sv {gold}
prep -top {top}

[gate]
read_verilog -sv {gate}
prep -top {top}

[strategy simple]
use sat
depth 5
"""


from formal_status import run_eqy


def main():
    base = C.ROUND_DIR / "10_验证工具自检_selfcheck" / "attempt01"
    C.refuse_overwrite(base)
    base.mkdir(parents=True)
    assets = C.ROUND_DIR / "10_验证工具自检_selfcheck" / "assets"

    summary = {"cases": [], "ascii_bridge": str(C.ASCII_BRIDGE)}
    hash_map = {}

    for name, top, expect in (
        ("positive", "selfcheck_pos", "PASS"),
        ("negative", "selfcheck_neg", "REJECT"),
    ):
        src_gold = assets / f"{name}_gold.v"
        src_gate = assets / f"{name}_gate.v"
        # 1) 暂存到 ASCII 桥（哈希对照）
        gold = C.stage_to_ascii_bridge(src_gold, f"selfcheck/{name}_gold.v")
        gate = C.stage_to_ascii_bridge(src_gate, f"selfcheck/{name}_gate.v")
        for src, dst in ((src_gold, gold), (src_gate, gate)):
            hash_map[str(dst)] = {
                "source": C.rel(src),
                "source_sha256": C.sha256_file(src),
                "bridge_sha256": C.sha256_file(dst),
                "match": C.sha256_file(src) == C.sha256_file(dst),
            }
        # 2) 配置放 ASCII 桥
        cfg = C.ASCII_BRIDGE / f"selfcheck/{name}.eqy"
        cfg.parent.mkdir(parents=True, exist_ok=True)
        cfg.write_text(EQY_TEMPLATE.format(gold=gold, gate=gate, top=top))

        # 3) 运行（work 与 log 分离，二者均在本轮目录内）
        d = base / name
        d.mkdir()
        rc = run_eqy(cfg, d / "work", d / "verify.log")
        log_text = (d / "verify.log").read_text(errors="replace")
        from formal_status import summarize_eqy
        proof = summarize_eqy(d / "verify.log", d / "work")
        status = "PASS" if proof["state"] == "PASS" else ("REJECTED" if proof["state"] == "COUNTEREXAMPLE_REQUIRES_REVIEW" else proof["state"])
        case = {
            "name": name,
            "rc": rc,
            "status": status,
            "expect": expect,
            "gold_bridge": str(gold),
            "gate_bridge": str(gate),
            "gold_sha256": C.sha256_file(src_gold),
            "gate_sha256": C.sha256_file(src_gate),
        }
        if name == "negative":
            lines = log_text.splitlines()
            diff_lines = [
                l
                for l in lines
                if "Differing" in l or "ERROR" in l or "is not" in l
            ]
            case["counterexample_lines"] = diff_lines[:20]
            case["log_tail"] = lines[-14:]
        summary["cases"].append(case)
        print(f"{name}: rc={rc} -> {status}")

    ok = (
        summary["cases"][0]["status"] == "PASS"
        and summary["cases"][1]["status"] == "REJECTED"
    )
    summary["selfcheck_ok"] = ok
    (base / "selfcheck_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    )
    (C.ASCII_BRIDGE / "selfcheck" / "hash_manifest.json").write_text(
        json.dumps(hash_map, ensure_ascii=False, indent=2) + "\n"
    )
    print(f"selfcheck_ok={ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
