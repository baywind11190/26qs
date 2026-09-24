#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P3 v1 validation runner; adapted from the preserved 2026-09-22 round.
See ../POLICY.md for scope, provenance and limitations.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import json
SCRIPT_DIR = Path(__file__).resolve().parent
ROUND_DIR = SCRIPT_DIR.parent
CONTEXT = json.loads((ROUND_DIR / "validation_context.json").read_text())
REPO = Path(CONTEXT["repo"])
RESULTS_DIR = REPO / "results"
EVAL_DIR = ROUND_DIR.parent
TREE = ROUND_DIR / "02_冻结源码与输入_assets" / "tree"
PLUGIN_SO = SCRIPT_DIR / "pmux_opt.so"
ASCII_BRIDGE = Path(CONTEXT["ascii_bridge"])
TOOL_YOSYS = Path(CONTEXT["tools"]["yosys"]["path"])
TOOL_YOSYS_CONFIG = Path(CONTEXT["tools"]["yosys_config"]["path"])
TOOL_EQY = Path(CONTEXT["tools"]["eqy"]["path"])
TOOL_Z3 = Path(CONTEXT["tools"]["z3"]["path"])
EQY_YOSYS = TOOL_YOSYS
EQY_ABC = Path(CONTEXT["tools"]["abc"]["path"])
TARGET_COMMIT = CONTEXT["target_commit"]
TARGET_BRANCH = None
SOURCE_SHA256 = CONTEXT["source_sha256"]
YOSYS_SRC_COMMIT = CONTEXT["yosys_src_commit"]

# ---------------------------------------------------------------- 流程
SYNTH_FAMILY = "cycloneiv"

# synth_intel.cc (9f75ca1f9) coarse 阶段手工展开（P3 前）。
# 对应源码行：run("proc") ... run("opt")（fsm 之后、wreduce 之前为 P3）。
COARSE_EARLY = [
    "proc",
    "check",
    "flatten",
    "tribuf -logic",
    "deminout",
    "opt_expr",
    "opt_clean",
    "check",
    "opt -nodffe -nosdff",
    "fsm",
    "opt",
]

# P3 之后继续的 coarse 阶段（wreduce → opt_clean）。
COARSE_LATE = [
    "wreduce",
    "peepopt",
    "opt_clean",
    "techmap -map +/cmp2lut.v -D LUT_WIDTH=4",
    "opt_expr",
    "opt_clean",
    "alumacc",
    "opt",
    "memory -nomap",
    "opt_clean",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def stage_to_ascii_bridge(src: Path, rel_name: str) -> Path:
    dst = (ASCII_BRIDGE / rel_name).resolve()
    dst.relative_to(ASCII_BRIDGE.resolve())
    dst.parent.mkdir(parents=True, exist_ok=True)
    digest = sha256_file(src)
    if dst.exists():
        if sha256_file(dst) != digest:
            raise RuntimeError(f"Bridge collision: {dst}")
    else:
        shutil.copyfile(src, dst)
    with (ROUND_DIR / "01_来源与环境_meta" / "bridge.jsonl").open("a") as f:
        f.write(json.dumps({"source": str(src), "bridge": str(dst), "sha256": digest}) + "\n")
    return dst



def refuse_overwrite(path: Path):
    """拒绝覆盖：确保目标不存在。"""
    if path.exists():
        raise SystemExit(f"REFUSING to overwrite existing path: {path}")


def mkdir_new(path: Path):
    """以拒绝覆盖的方式创建目录。"""
    if path.exists():
        raise SystemExit(f"REFUSING to reuse existing directory: {path}")
    path.mkdir(parents=True)


def gen_split_flow_ys(
    rtl: Path,
    top: str,
    *,
    optimized: bool,
    dump_dir: Path,
    tag: str,
    stat_json: Path | None = None,
    extra_final: list[str] | None = None,
) -> str:
    """生成拆分流程 .ys 脚本文本。

    dump 文件（两侧对称）：
      <tag>_pre_p3.il     —— check -assert 之后、P3 之前
      <tag>_post_p3.il    —— P3（optimized）或同位置（baseline）之后
      <tag>_coarse_done.il—— coarse 阶段全部完成、映射前（通用网表）
      <tag>_mapped.il     —— 完整映射后
    """
    d = dump_dir
    lines = []
    lines.append(f"# split-flow (P3) for {tag}, optimized={optimized}")
    lines.append(f"read_verilog -sv {rtl}")
    lines.append(
        f"synth_intel -family {SYNTH_FAMILY} -top {top} -run begin:coarse"
    )
    lines += COARSE_EARLY
    lines.append("check -assert")
    lines.append(f"write_rtlil {d / (tag + '_pre_p3.il')}")
    if optimized:
        lines.append("pmux_opt")
    lines.append(f"write_rtlil {d / (tag + '_post_p3.il')}")
    lines += COARSE_LATE
    lines.append(f"write_rtlil {d / (tag + '_coarse_done.il')}")
    lines.append(
        f"synth_intel -family {SYNTH_FAMILY} -top {top} -run map_bram:"
    )
    lines.append(f"write_rtlil {d / (tag + '_mapped.il')}")
    if stat_json is not None:
        lines.append(f"tee -o {stat_json} stat -json")
    if extra_final:
        lines += extra_final
    return "\n".join(lines) + "\n"


def gen_native_flow_ys(
    rtl: Path,
    top: str,
    *,
    out_il: Path,
    stat_json: Path | None = None,
) -> str:
    """原生完整 synth_intel 流程（用于流程一致性对照）。"""
    lines = [
        f"# native synth_intel for {top}",
        f"read_verilog -sv {rtl}",
        f"synth_intel -family {SYNTH_FAMILY} -top {top}",
        f"write_rtlil {out_il}",
    ]
    if stat_json is not None:
        lines.append(f"tee -o {stat_json} stat -json")
    return "\n".join(lines) + "\n"


def run_yosys(
    ys_script: str,
    log_path: Path,
    *,
    plugin: bool = False,
    timeout: int = 900,
) -> int:
    """运行 yosys（可选加载本轮插件），保存完整日志。

    返回进程退出码；超时返回 124（由调用方判定）。
    """
    cmd = [str(TOOL_YOSYS)]
    if plugin:
        cmd += ["-m", str(PLUGIN_SO)]
    cmd += ["-s", "-"]  # 从 stdin 读脚本
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w") as logf:
        p = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=logf,
            stderr=subprocess.STDOUT,
            cwd=str(REPO),
            start_new_session=True,
        )
        try:
            p.communicate(ys_script.encode(), timeout=timeout)
            return p.returncode
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, 9)
            p.wait()
            return 124


def parse_stat_json(path: Path) -> dict:
    """解析 `stat -json` 输出（取 design 级统计）。"""
    data = json.loads(path.read_text())
    design = data["design"]
    types = design.get("num_cells_by_type", {})
    return {
        "total_cells": int(design["num_cells"]),
        "comb": int(types.get("cycloneiv_lcell_comb", 0)),
        "dffeas": int(types.get("dffeas", 0)),
        "cell_types": {k: int(v) for k, v in sorted(types.items())},
    }


def extract_pmux_stats_from_il(il_path: Path) -> dict:
    """从 RTLIL 网表统计 $pmux 数量（P3 前后结构快照）。"""
    n_pmux = 0
    s_widths = []
    for line in il_path.read_text(errors="replace").splitlines():
        line = line.strip()
        if line.startswith("cell $pmux"):
            n_pmux += 1
        elif line.startswith("parameter \\S_WIDTH"):
            try:
                s_widths.append(int(line.split()[2]))
            except (IndexError, ValueError):
                pass
    return {"pmux_cells": n_pmux, "s_widths": sorted(s_widths)}


def extract_triggers(log_path: Path) -> dict:
    """从插件运行日志提取 H1/H2 与 Pattern A/B/C/D 触发证据。

    日志前缀（冻结源码）：
      H2 ROTATION CANDIDATE / H2 ROTATION REBUILT
      PAIR-SWAP CANDIDATE / PAIR-SWAP REBUILT
      BRANCH-CONST FOLD / BRANCH-EXPR CONST FOLD
      Pattern D candidates / GUARD-AWARE
    """
    text = log_path.read_text(errors="replace")
    if "Executing PMUX_OPT" not in text:
        return {"plugin_ran": False}
    seg = text.split("Executing PMUX_OPT", 1)[1]
    # 截到统计汇总（"Total $pmux cells:" 段）为止
    total_idx = seg.find("Total $pmux cells:")
    if total_idx >= 0:
        seg_total = seg[total_idx:]
        seg = seg[:total_idx]
    else:
        seg_total = ""
    result = {
        "plugin_ran": True,
        "h2_candidate_cells": seg.count("H2 ROTATION CANDIDATE"),
        "h2_rebuilt": seg.count("H2 ROTATION REBUILT"),
        "pairswap_candidate": seg.count("PAIR-SWAP CANDIDATE"),
        "pairswap_rebuilt": seg.count("PAIR-SWAP REBUILT"),
        "branch_const_fold": seg.count("BRANCH-CONST FOLD"),
        "branch_expr_const_fold": seg.count("BRANCH-EXPR CONST FOLD"),
        "guard_aware": seg.count("GUARD-AWARE"),
        "shared_selector_groups": 0,
        "total_pmux": 0,
        "total_rebuilt": 0,
    }
    for line in seg_total.splitlines():
        line = line.strip()
        if line.startswith("Total $pmux cells:"):
            result["total_pmux"] = int(line.split(":")[1])
        elif line.startswith("Total shared-selector groups:"):
            result["shared_selector_groups"] = int(line.split(":")[1])
        elif line.startswith("Total pair-swap rebuilt:"):
            result["total_rebuilt"] = int(line.split(":")[1])
    # H2 REBUILT 段落里的 bank/lane 信息（用于证据表）
    h2_details = []
    for marker in ["H2 ROTATION REBUILT", "H2 ROTATION CANDIDATE"]:
        pos = 0
        while True:
            idx = seg.find(marker, pos)
            if idx < 0:
                break
            h2_details.append(seg[idx : idx + 360])
            pos = idx + len(marker)
    result["h2_log_excerpts"] = h2_details
    return result


def check_assert_ok(log_path: Path) -> bool:
    import re
    text = log_path.read_text(errors="replace")
    sections = re.findall(r"Executing CHECK pass[^\n]*\n(.*?)(?=\n\d+(?:\.\d+)*\. Executing|\Z)", text, re.S)
    return bool(sections) and "ERROR:" not in text and all("Found and reported 0 problems." in s and "Warning:" not in s for s in sections)



def write_manifest(path: Path, obj: dict):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def git_rev_parse(ref: str) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", ref], cwd=str(REPO), text=True
    ).strip()


def tool_provenance() -> dict:
    """采集工具身份（路径/版本/哈希）。"""
    yosys_v = subprocess.check_output([str(TOOL_YOSYS), "-V"], text=True).strip()
    settings = {
        "yosys": {
            "path": str(TOOL_YOSYS),
            "version": yosys_v,
            "sha256": sha256_file(TOOL_YOSYS),
            "src_commit": YOSYS_SRC_COMMIT,
        },
        "yosys_config": {
            "path": str(TOOL_YOSYS_CONFIG),
            "sha256": sha256_file(TOOL_YOSYS_CONFIG),
        },
        "abc": {
            "path": str(EQY_ABC),
            "sha256": sha256_file(EQY_ABC),
        },
        "eqy": {
            "path": str(TOOL_EQY),
            "sha256": sha256_file(TOOL_EQY),
        },
        "z3": {"path": str(TOOL_Z3)},
        "plugin": {
            "path": str(PLUGIN_SO),
            "sha256": sha256_file(PLUGIN_SO),
        },
        "target_commit": TARGET_COMMIT,
        "source_sha256": SOURCE_SHA256,
        "source_sha256_actual": sha256_file(
            TREE / "src" / "pmux_opt.cc"
        ),
    }
    return settings


def rel(path: Path) -> str:
    """相对 repo 根的可读路径（用于报告）。"""
    try:
        return str(Path(path).resolve().relative_to(REPO))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    # 自检：打印冻结身份
    prov = tool_provenance()
    print(json.dumps(prov, ensure_ascii=False, indent=2))
