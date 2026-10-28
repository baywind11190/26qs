#!/usr/bin/env python3
"""Exercise decoded-PMUX reconstruction and conservative rejection boundaries."""
import argparse,copy,json,re,subprocess
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--yosys',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);ns=ap.parse_args();out=ns.out.resolve();out.mkdir(parents=True,exist_ok=True)
def run(text,folder,name):
    folder.mkdir(parents=True,exist_ok=True);script=folder/(name+'.ys');script.write_text(text)
    with (folder/(name+'.log')).open('w') as f:subprocess.run([str(ns.yosys),'-Q','-s',str(script)],stdout=f,stderr=subprocess.STDOUT,check=True)
    return (folder/(name+'.log')).read_text()
rtl=out/'fixture.v';rtl.write_text('module top(input [1:0] s, input [11:0] d, output reg [2:0] y); always @* case(s) 0:y=d[2:0]; 1:y=d[5:3]; 2:y=d[8:6]; default:y=d[11:9]; endcase endmodule\n')
run(f'read_verilog {rtl}\nproc\nopt\nwrite_json {out}/input.json\n',out,'prepare')
original=json.loads((out/'input.json').read_text());top=original['modules']['top'];name=next(n for n,c in top['cells'].items() if c['type']=='$pmux')
def driver(design,typ):return next(c for c in design['modules']['top']['cells'].values() if c['type']==typ)
variants=['positive','positive_3bit','dependent_selector','keep_cell','keep_module','keep_output','init_output','duplicate_selector','unknown_default','signed_compare','decoder_keep','multiple_driver','unknown_cell_touching_output','output_is_input','partial_unselected']
results={}
for label in variants:
    d=copy.deepcopy(original);m=d['modules']['top'];c=m['cells'][name]
    if label=='positive_3bit':
        fresh=1+max(b for cell in m['cells'].values() for bits in cell['connections'].values() for b in bits if isinstance(b,int))
        m['ports']['s']['bits'].append(fresh);m['netnames']['s']['bits'].append(fresh)
        for decode in m['cells'].values():
            if decode['type'] in ('$eq','$logic_not'):
                decode['connections']['A'].append(fresh);decode['parameters']['A_WIDTH']=format(3,'032b')
                if decode['type']=='$eq':decode['connections']['B'].append('0');decode['parameters']['B_WIDTH']=format(3,'032b')
    if label=='dependent_selector':
        pred=copy.deepcopy(c);fresh=1+max(b for cell in m['cells'].values() for bits in cell['connections'].values() for b in bits if isinstance(b,int))
        pred['parameters']['WIDTH']=format(1,'032b');pred['connections']['A']=pred['connections']['A'][:1];pred['connections']['B']=[pred['connections']['B'][i] for i in (0,3,6)];pred['connections']['Y']=[fresh]
        m['cells']['predecessor_pmux']=pred;c['connections']['S'][0]=fresh
    if label=='keep_cell':c['attributes']['keep']='1'
    if label=='keep_module':m['attributes']['keep']='1'
    if label in ('keep_output','init_output'):m['netnames']['y']['attributes']['keep' if label=='keep_output' else 'init']='1' if label=='keep_output' else '000'
    if label=='duplicate_selector':c['connections']['S'][1]=c['connections']['S'][0]
    if label=='unknown_default':c['connections']['A'][0]='x'
    if label=='signed_compare':driver(d,'$eq')['parameters'].update({'A_SIGNED':format(1,'032b'),'B_SIGNED':format(1,'032b')})
    if label=='decoder_keep':driver(d,'$eq')['attributes']['keep']='1'
    if label=='multiple_driver':
        extra=copy.deepcopy(driver(d,'$eq'));extra['connections']['Y']=[c['connections']['S'][0]];m['cells']['extra_driver']=extra
    if label=='unknown_cell_touching_output':m['cells']['unknown_driver']={'hide_name':0,'type':'unknown_external','parameters':{},'attributes':{},'port_directions':{'Y':'output'},'connections':{'Y':c['connections']['Y']}}
    if label=='output_is_input':m['ports']['y']['direction']='input'
    source=out/(label+'.json');source.write_text(json.dumps(d));dest=out/label
    selection='select top/t:$eq\n' if label=='partial_unselected' else ''
    log=run(f'read_json {source}\n{selection}pmux_opt\nselect -clear\nwrite_json {dest}/after.json\n',dest,'run')
    after=json.loads((dest/'after.json').read_text())['modules']['top'];removed=name not in after['cells']
    expected=label in ('positive','positive_3bit');assert removed==expected,(label,'PMUX removal',removed,expected)
    assert ('8.1 DECODED PMUX REBUILT' in log)==(expected or label=='dependent_selector'),(label,'missing/unexpected 8.1 log')
    results[label]='PASS'
# Compare every data/control combination symbolically for the accepted fixture.
for label in ('positive','positive_3bit'):
 f=out/label;run(f'read_json {out}/{label}.json\nrename top gold\nread_json {f}/after.json\nrename top gate\nequiv_make gold gate equiv\nhierarchy -top equiv\nequiv_simple\nequiv_status -assert\n',f,'equiv')
results['positive_all_inputs_equivalence']='PASS'
(out/'results.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
