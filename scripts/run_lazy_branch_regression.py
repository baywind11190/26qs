#!/usr/bin/env python3
"""Check 2.2 lazy construction and constant-branch bypass against 7ebbff9."""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = '7ebbff92defc0224d753ff8621991de0eccd9963'
spec = importlib.util.spec_from_file_location('feedback', ROOT/'scripts/run_enable_feedback_regression.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)

def instrument(source):
    # Only generated test copies carry counters; production has no extra logs.
    token = 'init.set(&sigmap, module);'
    assert source.count(token) == 1
    source = source.replace(token, 'log("FEEDBACK INIT\\n"); '+token)
    token = 'SigMap sigmap(module);'
    assert source.count(token) == 1
    source = source.replace(token, token + '''
int test_builds=0, test_evals=0;
auto test_report=std::shared_ptr<void>(nullptr,[&](void*) {
log("BRANCH WORK builds=%d evals=%d\\n",test_builds,test_evals);
});
''')
    eager = 'ConstEval branch_consteval(\n                module,\n                RTLIL::State::Sx);'
    lazies = ['branch_consteval.reset(new ConstEval(module, RTLIL::State::Sx));',
              'branch_consteval.reset(new ConstEval(module));']
    assert int(eager in source) + sum(lazy in source for lazy in lazies) == 1
    if eager in source: source = source.replace(eager,'++test_builds;\n'+eager)
    else:
        for lazy in lazies:
            source = source.replace(lazy,'{ ++test_builds; '+lazy+' }')
    token = 'bool eval_ok ='
    assert source.count(token) == 1
    return source.replace(token,'++test_evals;\n'+token)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--baseline',default=BASE)
    ap.add_argument('--check-feedback-entry',action='store_true')
    ns=ap.parse_args()
    out=ns.out.resolve()
    out.mkdir(parents=True,exist_ok=False)
    plugins={}
    for label in ['baseline','candidate']:
        source=(subprocess.check_output(['git','show',ns.baseline+':src/pmux_opt.cc'],cwd=ROOT).decode()
                if label=='baseline' else (ROOT/'src/pmux_opt.cc').read_text())
        cc=out/(label+'.cc')
        cc.write_text(instrument(source))
        plugins[label]=out/(label+'.so')
        helper.run(['yosys-config','--build',str(plugins[label]),str(cc)],out/(label+'_build.log'))
    fixture=out/'mixed.v'
    fixture.write_text('''module top(input [1:0] c, input [3:0] d, output reg [3:0] y);
always @* case(c)
0: y=4'b1010;
1: y=~{c,c};
2: y=d;
default: y=4'b0000;
endcase
endmodule
''')
    cases=[(f'test{i}',ROOT/f'pmux_case/competition_case/test{i}/test{i}.v',f'test{i}') for i in range(1,5)]
    cases.append(('mixed',fixture,'top'))
    constants=out/'constant_xz.v'
    constants.write_text('''module top(input [1:0] c, output reg [3:0] y);
always @* case(c)
0: y=4'b10xz;
1: y=4'b01zx;
2: y=4'b0011;
default: y=4'b1100;
endcase
endmodule
''')
    cases.append(('constant_xz',constants,'top'))
    rows={}
    for name,rtl,top in cases:
        row={}
        for label,plugin in plugins.items():
            dest=out/name/label
            dest.mkdir(parents=True)
            ys=dest/'run.ys'
            ys.write_text(helper.flow(rtl,top,dest))
            helper.run(['yosys','-m',str(plugin),'-s',str(ys)],dest/'run.log')
            text=(dest/'run.log').read_text()
            work=re.search(r'BRANCH WORK builds=(\d+) evals=(\d+)',text)
            row[label]={'cells':json.loads((dest/'stat.json').read_text())['modules']['\\'+top]['num_cells_by_type'],
                        'work':[int(v) for v in work.groups()] if work else [0,0],
                        'feedback_init':text.count('FEEDBACK INIT')}
        assert row['baseline']['cells']==row['candidate']['cells'],(name,row)
        if name=='test1': assert row['candidate']['work']==[1,33],row
        if name=='test3': assert row['candidate']['work']==[0,0],row
        if name=='constant_xz':
            assert row['candidate']['work']==[0,0],row
            if ns.baseline==BASE: assert row['baseline']['work'][0]==1,row
        if name=='mixed': assert row['candidate']['work'][0]==1 and row['candidate']['work'][1]>0,row
        if ns.check_feedback_entry:
            if name=='test1': assert row['baseline']['feedback_init']==1 and row['candidate']['feedback_init']==0,row
            if name=='test3':
                assert row['candidate']['feedback_init']==1,row
                assert 'Total enable-feedback rebuilt: 1' in (out/name/'candidate/run.log').read_text()
        ys=out/name/'equiv.ys'
        ys.write_text(f'''read_rtlil {out}/{name}/baseline/rebuilt.il
rename {top} gold
read_rtlil {out}/{name}/candidate/rebuilt.il
rename {top} gate
memory_map
async2sync
equiv_make gold gate equiv
hierarchy -top equiv
opt_clean
equiv_simple
equiv_induct -seq 6
equiv_status -assert
''')
        helper.run(['yosys','-s',str(ys)],out/name/'equiv.log')
        row['old_new_equivalence']='PASS'
        rows[name]=row
        print(name,row,flush=True)
    (out/'summary.json').write_text(json.dumps(rows,indent=2)+'\n')
    print('All lazy branch checks passed:',out)

if __name__=='__main__': main()
