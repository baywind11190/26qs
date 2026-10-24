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


def gen_builtin_formal_ys(rtl, top):
    """Full synthesis with a post-ABC checkpoint before vendor cell mapping."""
    return (f"read_verilog -sv {rtl}\n"
            f"synth_intel -family {SYNTH_FAMILY} -top {top} -run begin:map_cells\n"
            "write_rtlil post_abc.il\n"
            "tee -o post_abc_stat.json stat -json\n"
            f"synth_intel -family {SYNTH_FAMILY} -top {top} -run map_cells:\n"
            "check -assert\nwrite_rtlil mapped.il\ntee -o stat.json stat -json\n")


def abc9_mapping_ok(log_text):
    names = [executing_name(d).split()[0] for d in extract_executing_sequence(log_text) if re.match(r'ABC9? pass\b', d)]
    return names.count('ABC9') == 1 and 'ABC' not in names


def compare_other_resources(base, opt):
    # Combinational logic and constants are not DFF/IO/memory/DSP resources.
    auxiliary = {'cycloneiv_lcell_comb', '$lut', '$not', '$_NOT_', 'VCC', 'GND'}
    kinds = sorted((set(base) | set(opt)) - auxiliary)
    counts = {k: {'baseline': base.get(k,0), 'optimized': opt.get(k,0)} for k in kinds}
    increases = [k for k in kinds if opt.get(k,0) > base.get(k,0)]
    return {'ok': not increases, 'counts': counts, 'increases': increases,
            'policy': 'per_cell_type_nonincrease; unclassified types retained conservatively'}


_IO_CELL_TYPES = {
    'cycloneiv_io', 'cycloneiv_io_ibuf', 'cycloneiv_io_obuf', 'cycloneiv_io_oe',
}
_CONSTANT_CELL_TYPES = {'VCC', 'GND'}


def _rtlil_cells(mapped_il: str, top: str):
    module = re.search(r'^module \\' + re.escape(top) + r'\n(.*?)^end$',
                       mapped_il, re.M | re.S)
    if not module:
        raise ValueError('mapped RTLIL top module missing: {}'.format(top))
    pattern = r'^\s*cell (\\?\S+) \S+\s*\n(.*?)^\s*end\s*$'
    for match in re.finditer(pattern, module.group(1), re.M | re.S):
        yield match.group(1).lstrip('\\'), match.group(2)


def parse_resource_counts(stat_data, mapped_il: str, top: str) -> dict:
    """Parse final Cyclone IV resources, counting vector inverters by output bits.

    ``comb`` remains a compatibility alias for LUT count. ``logic_units`` is the
    p6 headline metric: Cyclone IV LUTs plus independent inverter bits. Any cell
    type outside the explicitly understood set blocks the resource conclusion.
    """
    design = stat_data.get('design', stat_data)
    raw_types = design.get('num_cells_by_type') or {}
    cell_types = {str(k).lstrip('\\'): int(v) for k, v in raw_types.items()}

    cells = list(_rtlil_cells(mapped_il, top))
    inverters = {'$not': 0, '$_NOT_': 0}
    for kind, body in cells:
        if kind == '$not':
            widths = re.findall(r'^\s*parameter \\Y_WIDTH\s+(\d+)\s*$', body, re.M)
            if len(widths) != 1 or int(widths[0]) <= 0:
                raise ValueError('cannot determine $not output width for inverter count')
            inverters[kind] += int(widths[0])
        elif kind == '$_NOT_':
            inverters[kind] += 1

    for kind in ('$not', '$_NOT_'):
        mapped_instances = sum(1 for cell_kind, _ in cells if cell_kind == kind)
        if cell_types.get(kind, 0) != mapped_instances:
            raise ValueError('stat/mapped.il inverter instance mismatch for {}: {} != {}'
                             .format(kind, cell_types.get(kind, 0), mapped_instances))

    lut_count = cell_types.get('cycloneiv_lcell_comb', 0)
    inverter_count = sum(inverters.values())
    dff_types = {kind: count for kind, count in cell_types.items()
                 if re.search(r'(?:dff|latch)', kind, re.I)}
    dff_count = sum(dff_types.values())
    io_types = {kind: count for kind, count in cell_types.items()
                if kind in _IO_CELL_TYPES}
    other_types = {}
    unknown = []
    for kind, count in cell_types.items():
        if kind in ('cycloneiv_lcell_comb', '$not', '$_NOT_'):
            continue
        if kind in dff_types or kind in io_types:
            continue
        if kind in _CONSTANT_CELL_TYPES:
            other_types[kind] = count
            continue
        unknown.append(kind)
    if unknown:
        raise ValueError('unclassified mapped cell types: {}'.format(', '.join(sorted(unknown))))

    modules = stat_data.get('modules') or {}
    module_stats = modules.get('\\' + top) or modules.get(top) or design
    return {
        'lut_count': lut_count,
        'comb': lut_count,
        'inverter_count': inverter_count,
        'logic_units': lut_count + inverter_count,
        'dff_count': dff_count,
        'dff_cell_types': dff_types,
        'io_ports': int(module_stats.get('num_ports', design.get('num_ports', 0))),
        'io_bits': int(module_stats.get('num_port_bits', design.get('num_port_bits', 0))),
        'io_cell_types': io_types,
        'other_cell_types': other_types,
        'cell_types': dict(sorted(cell_types.items())),
    }
def compare_resource_counts(base: dict, opt: dict) -> dict:
    """Compute per-example logic reduction and check every nonlogic resource."""
    baseline_logic = int(base['logic_units'])
    optimized_logic = int(opt['logic_units'])
    logic_reduction_pct = ((baseline_logic - optimized_logic) / baseline_logic * 100.0
                           if baseline_logic else None)
    dff_nonincrease = int(opt['dff_count']) <= int(base['dff_count'])
    io_nonincrease = (int(opt['io_ports']) <= int(base['io_ports']) and
                      int(opt['io_bits']) <= int(base['io_bits']))
    io_keys = sorted(set(base.get('io_cell_types', {})) | set(opt.get('io_cell_types', {})))
    io_counts = {k: {'baseline': int(base.get('io_cell_types', {}).get(k, 0)),
                     'optimized': int(opt.get('io_cell_types', {}).get(k, 0))} for k in io_keys}
    io_increases = [k for k, v in io_counts.items() if v['optimized'] > v['baseline']]
    io_nonincrease = io_nonincrease and not io_increases
    other_keys = sorted(set(base['other_cell_types']) | set(opt['other_cell_types']))
    other_counts = {kind: {'baseline': int(base['other_cell_types'].get(kind, 0)),
                           'optimized': int(opt['other_cell_types'].get(kind, 0))}
                    for kind in other_keys}
    other_increases = [kind for kind, counts in other_counts.items()
                       if counts['optimized'] > counts['baseline']]
    return {
        'logic_reduction_pct': logic_reduction_pct,
        'dff_nonincrease': dff_nonincrease,
        'io_nonincrease': io_nonincrease,
        'io_resources': {'ok': not io_increases, 'counts': io_counts, 'increases': io_increases},
        'other_resources': {'ok': not other_increases, 'counts': other_counts,
                            'increases': other_increases},
        'resource_checks_ok': dff_nonincrease and io_nonincrease and not other_increases,
    }
