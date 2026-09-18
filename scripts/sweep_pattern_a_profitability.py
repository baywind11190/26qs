#!/usr/bin/env python3

import csv
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "pmux_opt.so"
OUTDIR = ROOT / "results" / "pattern_a_profitability"
CASEDIR = OUTDIR / "cases"

OUTDIR.mkdir(parents=True, exist_ok=True)
CASEDIR.mkdir(parents=True, exist_ok=True)

CTRL_WIDTHS = [3, 4, 5]
DATA_WIDTHS = [1, 2, 4, 8, 12, 16]
SPECIAL_MODES = [0, 1]


def run(cmd):
    p = subprocess.run(
        cmd,
        shell=True,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return p.returncode, p.stdout


def get_lcells(text):
    matches = re.findall(
        r'^\s*(\d+)\s+cycloneiv_lcell_comb\s*$',
        text,
        re.MULTILINE
    )
    if not matches:
        return None
    return int(matches[-1])


def generate_case(ctrl_width, width, special):
    choices = 1 << ctrl_width
    pair_count = choices // 2

    name = f"pa_c{ctrl_width}_w{width}_s{special}"
    path = CASEDIR / f"{name}.v"

    ports = [f"input [{ctrl_width-1}:0] control"]

    for p in range(pair_count):
        ports.append(f"input [{width-1}:0] d{p}")
        ports.append(f"input [{width-1}:0] e{p}")

    if special:
        ports += [
            f"input [{width-1}:0] special_a",
            f"input [{width-1}:0] special_b",
            f"input [{width-1}:0] special_c",
            f"input [{width-1}:0] special_d",
        ]

    ports += [
        f"output reg [{width-1}:0] x",
        f"output reg [{width-1}:0] y",
    ]

    lines = []
    lines.append(f"module {name}(")
    lines.append("    " + ",\n    ".join(ports))
    lines.append(");")
    lines.append("")
    lines.append("always @* begin")
    lines.append(f"    x = {width}'b0;")
    lines.append(f"    y = {width}'b0;")
    lines.append("    case (control)")

    for p in range(pair_count):
        base = 2 * p
        mate = base + 1

        if special and p == 0:
            lines.append(
                f"        {ctrl_width}'d{base}: "
                "begin x = special_a; y = special_b; end"
            )
            lines.append(
                f"        {ctrl_width}'d{mate}: "
                "begin x = special_c; y = special_d; end"
            )
        else:
            lines.append(
                f"        {ctrl_width}'d{base}: "
                f"begin x = d{p}; y = e{p}; end"
            )
            lines.append(
                f"        {ctrl_width}'d{mate}: "
                f"begin x = e{p}; y = d{p}; end"
            )

    lines.append("    endcase")
    lines.append("end")
    lines.append("")
    lines.append("endmodule")
    lines.append("")

    path.write_text("\n".join(lines))
    return name, path, pair_count


# 先编译插件
rc, build_log = run(
    "yosys-config --build pmux_opt.so src/pmux_opt.cc"
)

if rc != 0:
    print(build_log)
    raise SystemExit("插件编译失败")


rows = []

print(
    f"{'CASE':24} "
    f"{'PAIR':>4} "
    f"{'SPEC':>4} "
    f"{'TRIG':>5} "
    f"{'BEFORE':>7} "
    f"{'AFTER':>7} "
    f"{'DELTA':>7} "
    f"{'CHANGE':>8}"
)

print("-" * 78)

for ctrl_width in CTRL_WIDTHS:
    for width in DATA_WIDTHS:
        for special in SPECIAL_MODES:

            name, src, pair_count = generate_case(
                ctrl_width,
                width,
                special
            )

            before_cmd = f"""
yosys -p '
read_verilog {src}
hierarchy -check -top {name}
proc
opt
synth_intel -family cycloneiv -top {name}
stat
'
"""

            rc_before, before_log = run(before_cmd)
            before = get_lcells(before_log)

            after_cmd = f"""
yosys -m {PLUGIN} -p '
read_verilog {src}
hierarchy -check -top {name}
proc
opt
pmux_opt
opt
synth_intel -family cycloneiv -top {name}
stat
'
"""

            rc_after, after_log = run(after_cmd)
            after = get_lcells(after_log)

            triggered = (
                "PAIR-SWAP REBUILT" in after_log
            )

            if (
                rc_before != 0 or
                rc_after != 0 or
                before is None or
                after is None
            ):
                print(f"{name:24} ERROR")
                continue

            delta = after - before
            change = 100.0 * delta / before if before else 0.0

            print(
                f"{name:24} "
                f"{pair_count:4d} "
                f"{special:4d} "
                f"{'YES' if triggered else 'NO':>5} "
                f"{before:7d} "
                f"{after:7d} "
                f"{delta:7d} "
                f"{change:7.2f}%"
            )

            rows.append({
                "case": name,
                "ctrl_width": ctrl_width,
                "data_width": width,
                "pair_count": pair_count,
                "special_pairs": special,
                "triggered": int(triggered),
                "before": before,
                "after": after,
                "delta": delta,
                "change_percent": round(change, 3),
            })


csv_path = OUTDIR / "profitability.csv"

with csv_path.open("w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "case",
            "ctrl_width",
            "data_width",
            "pair_count",
            "special_pairs",
            "triggered",
            "before",
            "after",
            "delta",
            "change_percent",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)

print()
print(f"CSV: {csv_path}")
