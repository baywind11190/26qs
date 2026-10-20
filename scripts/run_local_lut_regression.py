#!/usr/bin/env python3
"""Check bounded post-ABC LUT rewriting and its actual Intel resource count."""
import argparse,importlib.util,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('helper',ROOT/'scripts/run_enable_feedback_regression.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--plugin',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);ns=ap.parse_args()
    out=ns.out.resolve();out.mkdir(parents=True,exist_ok=True)
    rtl=ROOT/'pmux_case/competition_case/test4/test4.v'
    # Build a fresh baseline in the ordinary, diagnostic-free mapping flow.
    base=out/'baseline';base.mkdir(exist_ok=True)
    (base/'run.ys').write_text(h.flow(rtl,'test4',base));h.run(['yosys','-m',str(ns.plugin.resolve()),'-s',str(base/'run.ys')],base/'run.log')
    dest=out/'candidate';dest.mkdir(exist_ok=True)
    ys=f'read_verilog {rtl}\nsynth_intel -family cycloneiv -top test4 -run begin:coarse\ndelete test4\nread_rtlil {base}/post_abc.il\npmux_opt -lut\ncheck -assert\nselect test4\nwrite_rtlil -selected {dest}/rebuilt.il\nselect -clear\nsynth_intel -family cycloneiv -top test4 -run map_cells:\ntee -o {dest}/stat.json stat -json\n'
    (dest/'run.ys').write_text(ys)
    h.run(['yosys','-m',str(ns.plugin.resolve()),'-s',str(dest/'run.ys')],dest/'run.log')
    before=json.loads((base/'stat.json').read_text())['modules']['\\test4']['num_cells_by_type'];after=json.loads((dest/'stat.json').read_text())['modules']['\\test4']['num_cells_by_type']
    area=lambda c:c.get('cycloneiv_lcell_comb',0)+c.get('$not',0)
    assert area(after)<area(before),(before,after)
    assert before.get('dffeas')==after.get('dffeas')==10
    h.prove(rtl,'test4',dest/'rebuilt.il',dest/'formal',model=ROOT/'tests/local_lut/dffeas_model.v')
    row={'before':before,'after':after,'formal':'PASS'};(out/'summary.json').write_text(json.dumps(row,indent=2)+'\n');print(row)
if __name__=='__main__':main()
