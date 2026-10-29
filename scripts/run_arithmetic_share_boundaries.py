#!/usr/bin/env python3
"""Check sharing with and without an independently observed arithmetic result."""

import argparse
import importlib.util
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--yosys', required=True, type=Path)
parser.add_argument('--out', required=True, type=Path)
args = parser.parse_args()
out = args.out.resolve()
out.mkdir(parents=True, exist_ok=False)

spec = importlib.util.spec_from_file_location('formal_helper', ROOT / 'scripts/run_enable_feedback_regression.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)

common = '''module top(input [1:0] sel,
    input [3:0] a, b, c, d,
    output reg [3:0] result%s);
wire [3:0] add_result = a + b;
wire [3:0] sub_result = c - d;
always @* case (sel)
    2'd0: result = add_result;
    2'd1: result = sub_result;
    default: result = 4'd0;
endcase
%s
endmodule
'''

results = {}
for label, port, statement, expected in (
    ('shareable', '', '', 1),
    ('observed', ', output [3:0] observe', 'assign observe = add_result;', 0),
):
    folder = out / label
    folder.mkdir()
    rtl = folder / 'fixture.v'
    rtl.write_text(common % (port, statement))
    script = folder / 'flow.ys'
    script.write_text(
        f'read_verilog -sv {rtl}\n'
        f'synth_intel -family cycloneiv -top top -run begin:map_cells\n'
        f'select top\nwrite_rtlil -selected {folder}/post_abc.il\n'
        f'select -clear\nsynth_intel -family cycloneiv -top top -run map_cells:\n'
        f'tee -o {folder}/stat.json stat -json\n'
    )
    with (folder / 'run.log').open('w') as stream:
        subprocess.run([str(args.yosys.resolve()), '-Q', '-s', str(script)],
                       cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=True)
    log = (folder / 'run.log').read_text()
    matches = re.findall(r'ARITH_SHARE total=(\d+) all=1', log)
    assert len(matches) == 1 and int(matches[0]) == expected, (label, matches)
    helper.prove(rtl, 'top', folder / 'post_abc.il', folder / 'formal')
    results[label] = {'shares': expected, 'formal': 'PASS actual induction'}
    print(label, results[label], flush=True)

(out / 'summary.json').write_text(json.dumps(results, indent=2))
