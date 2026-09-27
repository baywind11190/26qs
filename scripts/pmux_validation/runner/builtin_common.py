#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""内置四例共享的纯函数（不依赖轮次上下文，便于单元测试）。

- gen_builtin_synth_ys：内置外部综合脚本（两侧逐字节相同）；
- extract_executing_sequence / executing_name：日志 pass 序列解析；
- check_pmux_position：pmux_opt 位置/次数核对（fsm;opt 的 OPT 之后、WREDUCE 之前）；
- select_binaries：从 builtin 配置解析两侧二进制（缺失即报错，不回退）。
"""
from pathlib import Path
import re

SYNTH_FAMILY = "cycloneiv"


def gen_builtin_synth_ys(rtl, top: str) -> str:
    """内置四例外部综合脚本（两侧逐字节相同；输出相对 cwd）。

    优化版由 synth_intel.cc 内部在 fsm;opt 之后、wreduce 之前调用 pmux_opt；
    原版不含该调用。末尾 check -assert 为最终网表质量检查。
    """
    return (
        "# builtin external synthesis script (identical for both sides)\n"
        f"read_verilog -sv {rtl}\n"
        f"synth_intel -family {SYNTH_FAMILY} -top {top}\n"
        "check -assert\n"
        "write_rtlil mapped.il\n"
        "tee -o stat.json stat -json\n"
    )


def extract_executing_sequence(log_text: str) -> list:
    """提取日志中的 'Executing <desc>' 序列（含描述全文；编号可缺省）。"""
    return [m.group(1).strip() for m in re.finditer(
        r"^\s*(?:[\d.]+\s+)?Executing\s+(.+)$", log_text, re.M)]


def extract_executing_entries(log_text: str) -> list:
    """提取 (编号, 描述) 序列；无编号行编号为 None。"""
    entries = []
    for line in log_text.splitlines():
        m = re.match(r"^\s*([\d.]+)\s+Executing\s+(.+)$", line)
        if m:
            entries.append((m.group(1).rstrip("."), m.group(2).strip()))
            continue
        m2 = re.match(r"^\s*Executing\s+(.+)$", line)
        if m2:
            entries.append((None, m2.group(1).strip()))
    return entries


def executing_name(desc: str) -> str:
    """从 Executing 描述中提取 pass 名（'OPT pass (...)'. -> 'OPT'）。"""
    return re.split(r"\s+pass\b|:", desc, maxsplit=1)[0].strip().rstrip(".")


def check_pmux_position(entries) -> dict:
    """核对 PMUX_OPT 恰一次，且编号前兄弟为 OPT、后兄弟为 WREDUCE。

    entries: [(num, name) ...]，name 为归一化 pass 名（见 executing_name）。
    以编号结构判定（例 '2.16' 的前兄弟 '2.15'、后兄弟 '2.17'），而不是只看
    相邻文本行——opt 等 pass 会输出内部子 pass 行（'2.15.21' 等）。
    """
    result = {"count": 0, "before": None, "after": None,
              "after_opt": False, "before_wreduce": False, "by": "number"}
    hits = [e for e in entries if e[1] == "PMUX_OPT"]
    result["count"] = len(hits)
    if len(hits) != 1:
        return result
    num = hits[0][0]
    if not num or not num.split(".")[-1].isdigit():
        return result
    parts = num.split(".")
    prev_num = ".".join(parts[:-1] + [str(int(parts[-1]) - 1)])
    next_num = ".".join(parts[:-1] + [str(int(parts[-1]) + 1)])
    lookup = {n: name for n, name in entries if n}
    result["before"] = lookup.get(prev_num)
    result["after"] = lookup.get(next_num)
    result["after_opt"] = result["before"] == "OPT"
    result["before_wreduce"] = result["after"] == "WREDUCE"
    return result


def select_binaries(builtin_cfg) -> dict:
    """从 builtin 配置解析两侧内置二进制；缺失即抛错（不做静默回退）。"""
    out = {}
    for side in ("baseline", "optimized"):
        p = Path(((builtin_cfg or {}).get(side) or {}).get("path", ""))
        if not p.is_file():
            raise FileNotFoundError("{} 内置二进制缺失: {}".format(side, p))
        out[side] = p
    return out
