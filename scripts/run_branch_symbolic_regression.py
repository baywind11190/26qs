#!/usr/bin/env python3
"""Reproduce 2.2 unknown-input misfolding and prove the conservative fix."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
BASE='0146fedacfc8cf568f9ac28ff2e5a6ca0021a162'
spec=importlib.util.spec_from_file_location('helper',ROOT/'scripts/run_enable_feedback_regression.py')
helper=importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)

def prove_after_abc(rtl,top,dest):
    ys=dest/'extract.ys'
    ys.write_text(f'read_rtlil {dest}/post_abc.il\nselect {top}\nwrite_rtlil -selected {dest}/abc_top.il\nwrite_json {dest}/abc.json\n')
    helper.run(['yosys','-s',str(ys)],dest/'extract.log')
    module=json.loads((dest/'abc.json').read_text())['modules'][top]
    model=None
    for cell in module['cells'].values():
        assert cell['type'] in ('$lut','dffeas'),cell['type']
        if cell['type']=='dffeas':
            for port,value in [('clrn','1'),('prn','1'),('asdata','0'),('aload','0'),('sclr','0'),('sload','0')]:
                assert cell['connections'][port]==[value],(port,cell)
            assert cell['connections']['clk']==module['ports']['clk']['bits']
            assert cell['parameters']['power_up']=='low'
            model=dest/'dffeas.v'
    if model:
        model.write_text('''module dffeas(output reg q,input d,clk,clrn,prn,ena,asdata,aload,sclr,sload);
parameter power_up="low", is_wysiwyg="false";
always @(posedge clk or negedge clrn)
if(!clrn) q<=0; else if(ena) q<=d;
endmodule
''')
    helper.prove(rtl,top,dest/'abc_top.il',dest/'formal_abc',model=model)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out',type=Path,required=True)
    ns=ap.parse_args()
    out=ns.out.resolve()
    out.mkdir(parents=True,exist_ok=False)
    plugins={}
    for label in ['baseline','candidate']:
        source=(subprocess.check_output(['git','show',BASE+':src/pmux_opt.cc'],cwd=ROOT)
                if label=='baseline' else (ROOT/'src/pmux_opt.cc').read_bytes())
        cc=out/(label+'.cc')
        cc.write_bytes(source)
        plugins[label]=out/(label+'.so')
        helper.run(['yosys-config','--build',str(plugins[label]),str(cc)],out/(label+'_build.log'))
    fixtures=out/'fixtures'
    fixtures.mkdir()
    spec=importlib.util.spec_from_file_location('fixtures',ROOT/'tests/enable_feedback/generate.py')
    gen=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    generated=gen.generate(ROOT,fixtures)
    cases=[('external_case_equality',next(r for n,r,t,h in generated if n=='external_case_equality'),'test3',True)]
    for name,expr,broken in [('case_eq','p === q',True),('case_ne','p !== q',True),
                             ('ordinary_eq','p == q',False)]:
        rtl=fixtures/(name+'.v')
        rtl.write_text(f'''module top(input [1:0] c, input p,q, output reg y);
always @* case(c)
0: y=0;
1: y=({expr});
2: y=1;
default:y=0;
endcase
endmodule
''')
        cases.append((name,rtl,'top',broken))
    mixed=fixtures/'mixed.v'
    mixed.write_text('''module top(input [1:0] c,input [3:0] d,output reg [7:0] y);
always @* case(c)
0:y={d,~c,c};
1:y={d,c,~c};
2:y=8'b10xz01zx;
default:y=0;
endcase
endmodule
''')
    cases.append(('mixed',mixed,'top',False))
    results={}
    for name,rtl,top,broken in cases:
        row={}
        for label,plugin in plugins.items():
            dest=out/name/label
            dest.mkdir(parents=True)
            ys=dest/'run.ys'
            ys.write_text(helper.flow(rtl,top,dest))
            helper.run(['yosys','-m',str(plugin),'-s',str(ys)],dest/'run.log')
            helper.prove(rtl,top,dest/'rebuilt.il',dest/'formal',negative=broken and label=='baseline')
            row[label]='COUNTEREXAMPLE (expected)' if broken and label=='baseline' else 'PASS'
        results[name]=row
        prove_after_abc(rtl,top,out/name/'candidate')
        row['candidate_abc']='PASS'
        print(name,row,flush=True)
    # The candidate must preserve public resources and the existing transforms.
    for i in range(1,5):
        name=f'test{i}'
        row={}
        for label,plugin in plugins.items():
            dest=out/name/label
            dest.mkdir(parents=True)
            ys=dest/'run.ys'
            ys.write_text(helper.flow(ROOT/f'pmux_case/competition_case/{name}/{name}.v',name,dest))
            helper.run(['yosys','-m',str(plugin),'-s',str(ys)],dest/'run.log')
            row[label]=json.loads((dest/'stat.json').read_text())['modules']['\\'+name]['num_cells_by_type']
        assert row['baseline']==row['candidate'],(name,row)
        ys=out/name/'equiv.ys'
        ys.write_text(f'''read_rtlil {out}/{name}/baseline/rebuilt.il
rename {name} gold
read_rtlil {out}/{name}/candidate/rebuilt.il
rename {name} gate
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
        results[name]=row
        print(name,row,flush=True)
    (out/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
    print('All symbolic branch checks passed:',out)

if __name__=='__main__':main()
