#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P3 v1 validation runner; adapted from the preserved 2026-09-22 round.
See ../POLICY.md for scope, provenance and limitations.
"""

import csv
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p3_common as C

FORM_MODEL_SRC = C.SCRIPT_DIR / "form_cells_cycloneiv.v"

CASES = ["test1", "test2", "test3", "test4"]

# 默认链集合（main）：主路径 c4a（原始 RTL ↔ 优化版最终映射网表）+ baseline 对照 c4b
# + 范围受限定位 c1（P3 局部）/ c2（同阶段）。full：全部链（含 c3a/c3b/c5，供扩展
# 诊断；不作为每轮必跑链路）。
MAIN_CHAINS = ("c1_local", "c2_stage", "c4a_rtl_opt_mapped", "c4b_rtl_base_mapped")
FULL_CHAINS = ("c1_local", "c2_stage", "c3a_rtl_opt", "c3b_rtl_base",
               "c4a_rtl_opt_mapped", "c4b_rtl_base_mapped", "c5_mapped_pair")


def discover_modules(il_path: Path):
    """解析 RTLIL 网表的全部模块名。

    模块行形如 `module \\test1` 或 `module $__ABC9_DELAY`（$ 开头的内部
    模块不带反斜杠前缀）。返回去转义后的名字。
    """
    mods = []
    for line in il_path.read_text(errors="replace").splitlines():
        if line.startswith("module "):
            name = line.split()[1]
            mods.append(name.lstrip("\\"))
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
    return (
        "[gold]\n"
        + "\n".join(gold_lines)
        + "\n\n[gate]\n"
        + "\n".join(gate_lines)
        + "\n"
        + EQY_TAIL
    )


from formal_status import run_eqy


from formal_status import summarize_eqy


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--attempt', default='run01')
    ap.add_argument('--chains', choices=['main', 'full'], default='main',
                    help='main=主路径+对照+定位（c1/c2/c4a/c4b）；full=全部链（含 c3a/c3b/c5）')
    args = ap.parse_args()
    if not re.fullmatch(r'run[0-9]+', args.attempt):
        ap.error('attempt must be runNN')
    selected = set(MAIN_CHAINS if args.chains == 'main' else FULL_CHAINS)
    out = C.ROUND_DIR / "10_验证工具自检_selfcheck" / "chains" / args.attempt
    C.refuse_overwrite(out)
    out.mkdir(parents=True)
    pub = C.ROUND_DIR / "05_公开四例_public" / "round01"
    bridge = C.ASCII_BRIDGE
    hash_map = {}

    form_model = C.stage_to_ascii_bridge(
        FORM_MODEL_SRC, "form/form_cells_cycloneiv.v"
    )
    hash_map[str(form_model)] = {
        "source": C.rel(FORM_MODEL_SRC),
        "sha256": C.sha256_file(FORM_MODEL_SRC),
    }

    rows = []
    for top in CASES:
        rtl_src = C.TREE / "pmux_case" / "competition_case" / top / f"{top}.v"
        rtl = C.stage_to_ascii_bridge(rtl_src, f"chains/{top}/{top}.v")
        hash_map[str(rtl)] = {
            "source": C.rel(rtl_src),
            "sha256": C.sha256_file(rtl_src),
        }
        side_files = {}
        for side in ("baseline", "optimized"):
            for kind in ("pre_p3", "post_p3", "coarse_done", "mapped"):
                src = pub / top / side / f"{side}_{kind}.il"
                dst = C.stage_to_ascii_bridge(
                    src, f"chains/{top}/{side}_{kind}.il"
                )
                side_files[(side, kind)] = dst
                hash_map[str(dst)] = {
                    "source": C.rel(src),
                    "sha256": C.sha256_file(src),
                }

        case_dir = out / top
        case_dir.mkdir()

        try:
            chains = {
                "c1_local": make_cfg(
                    net_side_prelude(side_files[("optimized", "pre_p3")], top),
                    net_side_prelude(side_files[("optimized", "post_p3")], top),
                ),
                "c2_stage": make_cfg(
                    net_side_prelude(side_files[("baseline", "coarse_done")], top),
                    net_side_prelude(side_files[("optimized", "coarse_done")], top),
                ),
                "c3a_rtl_opt": make_cfg(
                    rtl_side_prelude(rtl, top),
                    net_side_prelude(side_files[("optimized", "coarse_done")], top),
                ),
                "c3b_rtl_base": make_cfg(
                    rtl_side_prelude(rtl, top),
                    net_side_prelude(side_files[("baseline", "coarse_done")], top),
                ),
                "c4a_rtl_opt_mapped": make_cfg(
                    rtl_side_prelude(rtl, top),
                    net_side_prelude_mapped(
                        side_files[("optimized", "mapped")], top, form_model
                    ),
                ),
                "c4b_rtl_base_mapped": make_cfg(
                    rtl_side_prelude(rtl, top),
                    net_side_prelude_mapped(
                        side_files[("baseline", "mapped")], top, form_model
                    ),
                ),
                "c5_mapped_pair": make_cfg(
                    net_side_prelude_mapped(
                        side_files[("baseline", "mapped")], top, form_model
                    ),
                    net_side_prelude_mapped(
                        side_files[("optimized", "mapped")], top, form_model
                    ),
                ),
            }
            chains = {name: text for name, text in chains.items() if name in selected}
        except ValueError as exc:
            chains = {
                "c1_local": make_cfg(net_side_prelude(side_files[("optimized", "pre_p3")], top), net_side_prelude(side_files[("optimized", "post_p3")], top)),
                "c2_stage": make_cfg(net_side_prelude(side_files[("baseline", "coarse_done")], top), net_side_prelude(side_files[("optimized", "coarse_done")], top)),
                "c3a_rtl_opt": make_cfg(rtl_side_prelude(rtl, top), net_side_prelude(side_files[("optimized", "coarse_done")], top)),
                "c3b_rtl_base": make_cfg(rtl_side_prelude(rtl, top), net_side_prelude(side_files[("baseline", "coarse_done")], top)),
            }
            for cname in ("c4a_rtl_opt_mapped", "c4b_rtl_base_mapped", "c5_mapped_pair"):
                if cname in selected:
                    rows.append({"case": top, "chain": cname, "rc": None, "state": "MODEL_UNSUPPORTED", "proved": 0, "total": 0, "failed": 0, "failed_partitions": [], "error": str(exc)})

        for cname, cfg_text in chains.items():
            cdir = case_dir / cname
            cdir.mkdir()
            cfg = cdir / "config.eqy"
            cfg.write_text(cfg_text)
            rc = run_eqy(cfg, cdir / "work", cdir / "verify.log")
            summ = summarize_eqy(cdir / "verify.log", cdir / "work")
            summ.update({"case": top, "chain": cname, "rc": rc})
            (cdir / "summary.json").write_text(
                json.dumps(summ, ensure_ascii=False, indent=2) + "\n"
            )
            rows.append(summ)
            detail = [
                f"{f['name']}:{f['status']}" for f in summ["failed_partitions"]
            ]
            print(
                f"{top} {cname}: rc={rc} state={summ['state']} "
                f"proved={summ['proved']}/{summ['total']} fail={detail[:6]}"
                + (f" err={summ.get('error')}" if summ.get("error") else "")
            )

    with open(out / "chains_summary.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "case",
                "chain",
                "rc",
                "state",
                "proved",
                "total",
                "failed",
                "failed_detail",
                "error",
            ]
        )
        for r in rows:
            w.writerow(
                [
                    r["case"],
                    r["chain"],
                    r["rc"],
                    r["state"],
                    r["proved"],
                    r["total"],
                    r["failed"],
                    "; ".join(
                        f"{p['name']}={p['status']}"
                        for p in r["failed_partitions"]
                    ),
                    (r.get("error") or "")[:120],
                ]
            )
    (out / "chains_summary.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n"
    )
    (out / "chains_set.json").write_text(
        json.dumps({"chain_set": args.chains, "chains": sorted(selected)},
                   ensure_ascii=False, indent=2) + "\n"
    )
    (bridge / "chains" / "hash_manifest.json").write_text(
        json.dumps(hash_map, ensure_ascii=False, indent=2) + "\n"
    )
    print(f"\n结果目录: {C.rel(out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
