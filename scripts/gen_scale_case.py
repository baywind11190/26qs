#!/usr/bin/env python3

import argparse
import json
import subprocess
import tempfile
from pathlib import Path


def split_units(units, mode):
    if mode == "pattern_a":
        return units, 0, 0

    if mode == "expr":
        return 0, units, 0

    if mode == "negative":
        return 0, 0, units

    if units == 1:
        return 1, 0, 0

    if units == 2:
        return 1, 1, 0

    a = max(1, units // 2)
    c = max(1, (units * 3) // 10)
    n = units - a - c

    if n < 1:
        n = 1
        a = units - c - n

    return a, c, n


def render_verilog(units, mode):
    a_count, c_count, n_count = split_units(units, mode)

    ports = []

    if a_count:
        ports += [
            f"input [{2*a_count-1}:0] a_ctrl",
            f"input [{16*a_count-1}:0] a_data",
            f"output [{8*a_count-1}:0] a_out",
        ]

    if c_count:
        ports += [
            f"input [{4*c_count-1}:0] c_ctrl",
            f"output [{4*c_count-1}:0] c_out",
        ]

    if n_count:
        ports += [
            f"input [{2*n_count-1}:0] n_ctrl",
            f"input [{16*n_count-1}:0] n_data",
            f"output [{4*n_count-1}:0] n_out",
        ]

    lines = []
    lines.append("module stress_top(")
    lines.append("    " + ",\n    ".join(ports))
    lines.append(");")
    lines.append("")

    for i in range(a_count):
        lines += [
            f"wire [1:0] a_ctrl_{i} = a_ctrl[{2*i} +: 2];",
            f"wire [15:0] a_data_{i} = a_data[{16*i} +: 16];",
            f"reg [3:0] a_x_{i};",
            f"reg [3:0] a_y_{i};",
            "",
            "always @* begin",
            f"    a_x_{i} = 4'b0;",
            f"    a_y_{i} = 4'b0;",
            f"    case (a_ctrl_{i})",
            f"        2'd0: begin a_x_{i} = a_data_{i}[3:0];   a_y_{i} = a_data_{i}[11:8];  end",
            f"        2'd1: begin a_x_{i} = a_data_{i}[11:8];  a_y_{i} = a_data_{i}[3:0];   end",
            f"        2'd2: begin a_x_{i} = a_data_{i}[7:4];   a_y_{i} = a_data_{i}[15:12]; end",
            f"        2'd3: begin a_x_{i} = a_data_{i}[15:12]; a_y_{i} = a_data_{i}[7:4];   end",
            "    endcase",
            "end",
            f"assign a_out[{8*i} +: 4] = a_x_{i};",
            f"assign a_out[{8*i+4} +: 4] = a_y_{i};",
            "",
        ]

    for i in range(c_count):
        lines += [
            f"wire [3:0] c_ctrl_{i} = c_ctrl[{4*i} +: 4];",
            f"reg [3:0] c_y_{i};",
            "",
            "always @* begin",
            f"    c_y_{i} = 4'b0000;",
            f"    case (c_ctrl_{i})",
            "        4'd3:",
            f"            c_y_{i} = {{",
            f"                ~c_ctrl_{i}[0],",
            f"                c_ctrl_{i}[1] ^ c_ctrl_{i}[2],",
            f"                c_ctrl_{i}[3] & c_ctrl_{i}[0],",
            f"                |c_ctrl_{i}",
            "            };",
            "        4'd12:",
            f"            c_y_{i} = {{",
            f"                ~c_ctrl_{i}[3],",
            f"                c_ctrl_{i}[2] ^ c_ctrl_{i}[1],",
            f"                c_ctrl_{i}[0] & c_ctrl_{i}[3],",
            f"                &c_ctrl_{i}",
            "            };",
            "    endcase",
            "end",
            f"assign c_out[{4*i} +: 4] = c_y_{i};",
            "",
        ]

    for i in range(n_count):
        lines += [
            f"wire [1:0] n_ctrl_{i} = n_ctrl[{2*i} +: 2];",
            f"wire [15:0] n_data_{i} = n_data[{16*i} +: 16];",
            f"reg [3:0] n_y_{i};",
            "",
            "always @* begin",
            f"    n_y_{i} = n_data_{i}[3:0];",
            f"    case (n_ctrl_{i})",
            f"        2'd0: n_y_{i} = n_data_{i}[3:0];",
            f"        2'd1: n_y_{i} = n_data_{i}[7:4];",
            f"        2'd2: n_y_{i} = n_data_{i}[11:8];",
            f"        2'd3: n_y_{i} = n_data_{i}[15:12];",
            "    endcase",
            "end",
            f"assign n_out[{4*i} +: 4] = n_y_{i};",
            "",
        ]

    lines.append("endmodule")
    lines.append("")

    return "\n".join(lines), (a_count, c_count, n_count)


def count_nodes(text):
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        src = td / "candidate.v"
        stat = td / "stat.json"

        src.write_text(text)

        cmd = [
            "yosys",
            "-p",
            (
                f"read_verilog {src}; "
                "hierarchy -check -top stress_top; "
                "proc; opt; "
                f"tee -o {stat} stat -json"
            ),
        ]

        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )

        data = json.loads(stat.read_text())
        modules = data["modules"]

        mod = modules.get("\\stress_top")
        if mod is None:
            mod = modules.get("stress_top")

        return int(mod["num_cells"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, required=True)
    ap.add_argument(
        "--mode",
        choices=["mixed", "pattern_a", "expr", "negative"],
        required=True,
    )
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    target = args.target

    low = 1
    high = 1

    while True:
        text, _ = render_verilog(high, args.mode)
        nodes = count_nodes(text)

        if nodes > target:
            break

        low = high
        high *= 2

    best_units = low
    best_nodes = -1

    left = 1
    right = high

    while left <= right:
        mid = (left + right) // 2

        text, _ = render_verilog(mid, args.mode)
        nodes = count_nodes(text)

        if nodes <= target:
            if nodes > best_nodes:
                best_nodes = nodes
                best_units = mid
            left = mid + 1
        else:
            right = mid - 1

    start = max(1, best_units - 4)
    stop = best_units + 5

    for units in range(start, stop):
        text, _ = render_verilog(units, args.mode)
        nodes = count_nodes(text)

        if nodes <= target and nodes > best_nodes:
            best_nodes = nodes
            best_units = units

    final_text, counts = render_verilog(best_units, args.mode)
    final_nodes = count_nodes(final_text)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(final_text)

    meta = {
        "target_nodes": target,
        "actual_nodes": final_nodes,
        "mode": args.mode,
        "units": best_units,
        "pattern_a_units": counts[0],
        "expr_units": counts[1],
        "negative_units": counts[2],
    }

    Path(str(out) + ".json").write_text(
        json.dumps(meta, indent=2)
    )

    print(
        f"{args.mode}: target={target}, "
        f"actual={final_nodes}, "
        f"units={best_units}, "
        f"A={counts[0]}, C={counts[1]}, N={counts[2]}"
    )


if __name__ == "__main__":
    main()
