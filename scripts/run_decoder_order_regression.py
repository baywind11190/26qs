#!/usr/bin/env python3
"""Require redundant PMUX branches to use the smaller decoded selector tree."""
import argparse, json, subprocess
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--yosys',required=True,type=Path)
parser.add_argument('--out',required=True,type=Path)
args=parser.parse_args()
args.out.mkdir(parents=True,exist_ok=False)
rtl=args.out/'fixture.v'
rtl.write_text("module top(input [1:0] s,input [2:0] a,b,c,output reg [2:0] y); always @* case(s) 2'd2:y=b; 2'd3:y=c; default:y=a; endcase endmodule\n")
flow=args.out/'flow.ys'
flow.write_text(f'read_verilog {rtl}\nproc\nopt\nwrite_rtlil {args.out}/before.il\npmux_opt\nwrite_json {args.out}/after.json\nwrite_rtlil {args.out}/after.il\n')
with (args.out/'run.log').open('w') as log:
    subprocess.run([str(args.yosys.resolve()),'-Q','-s',str(flow)],stdout=log,stderr=subprocess.STDOUT,check=True)
cells=json.loads((args.out/'after.json').read_text())['modules']['top']['cells']
count=sum(c['type']=='$mux' for c in cells.values())
assert count==2, f'Expected two vector muxes for shared default branches, got {count}'
proof=args.out/'proof.ys'
proof.write_text(f'read_rtlil {args.out}/before.il\nrename top gold\nread_rtlil {args.out}/after.il\nrename top gate\nequiv_make gold gate equiv\nhierarchy -top equiv\nequiv_simple\nequiv_status -assert\n')
with (args.out/'proof.log').open('w') as log:
    subprocess.run([str(args.yosys.resolve()),'-Q','-s',str(proof)],stdout=log,stderr=subprocess.STDOUT,check=True)
(args.out/'summary.json').write_text(json.dumps({'vector_muxes':count,'all_inputs_equivalent':True},indent=2))
print('PASS: two vector muxes and all-input equivalence')
