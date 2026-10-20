#!/usr/bin/env python3
"""Generic LUT DAG equivalence and preservation boundary checks."""
import argparse,copy,importlib.util,json,random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('h',ROOT/'scripts/run_enable_feedback_regression.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
def cell(ins,out,mask):
    return {'hide_name':0,'type':'$lut','parameters':{'WIDTH':format(len(ins),'032b'),'LUT':format(mask,f'0{1<<len(ins)}b')},'attributes':{},'port_directions':{'A':'input','Y':'output'},'connections':{'A':ins,'Y':[out]}}
def design(seed,count=24):
    rng=random.Random(seed);signals=list(range(2,10));cells={};fresh=10
    for i in range(count):
        width=rng.randrange(1,5);ins=rng.sample(signals,width);cells[f'n{i:02}']=cell(ins,fresh,rng.getrandbits(1<<width));signals.append(fresh);fresh+=1
    return {'modules':{'top':{'attributes':{},'ports':{'a':{'direction':'input','bits':list(range(2,10))},'y':{'direction':'output','bits':signals[-3:]}},'cells':cells,'netnames':{f'w{b}':{'hide_name':0,'bits':[b],'attributes':{}} for b in signals}}}}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--plugin',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);ns=ap.parse_args();out=ns.out.resolve();out.mkdir(parents=True,exist_ok=True)
    results={}
    fixtures=[(f'random_{i}',design(20261020+i),'',False) for i in range(24)]
    fixtures.append(('stress_1000',design(20261020,1000),'',False))
    base=design(31)
    for name in ('module_keep','cell_keep','wire_keep','shared_outputs','partial_selection'):
        d=copy.deepcopy(base);m=d['modules']['top'];sel=''
        if name=='module_keep':m['attributes']['keep']='1'
        if name=='cell_keep':
            for c in m['cells'].values():c['attributes']['keep']='1'
        if name=='wire_keep':
            for net in m['netnames'].values():net['attributes']['keep']='1'
        if name=='shared_outputs':m['ports']['observe']={'direction':'output','bits':[c['connections']['Y'][0] for c in m['cells'].values()]}
        if name=='partial_selection':sel='top/n23'
        fixtures.append((name,d,sel,True))
    # Unsupported or invalid cones must remain intact, not be evaluated as don't-cares.
    for name in ('multidriver','x_input','x_truth','cycle'):
        m={'attributes':{},'ports':{'a':{'direction':'input','bits':[2]},'y':{'direction':'output','bits':[5]}},'netnames':{},'cells':{'n0':cell([2],3,2),'n1':cell([3],4,2),'n2':cell([4],5,2)}}
        if name=='multidriver':m['cells']['duplicate']=cell([2],3,1)
        if name=='x_input':m['cells']['n0']['connections']['A']=['x']
        if name=='x_truth':m['cells']['n0']['parameters']['LUT']='x0'
        if name=='cycle':m['cells']['n0']['connections']['A']=[4]
        fixtures.append((name,{'modules':{'top':m}},'',False))
    for name,d,selection,identity in fixtures:
        folder=out/name;folder.mkdir(exist_ok=True);(folder/'input.json').write_text(json.dumps(d))
        ys=f'read_json {folder}/input.json\nwrite_json {folder}/canonical.json\npmux_opt -lut {selection}\nwrite_json {folder}/output.json\n'
        (folder/'run.ys').write_text(ys);h.run(['yosys','-m',str(ns.plugin.resolve()),'-s',str(folder/'run.ys')],folder/'run.log')
        transformed=json.loads((folder/'output.json').read_text())['modules']['top'];original=json.loads((folder/'canonical.json').read_text())['modules']['top']
        if identity:assert transformed['cells']==original['cells'],name
        if name in ('multidriver','x_input','x_truth','cycle'):
            assert transformed['cells']['n0']==original['cells']['n0'],name
            if name=='multidriver':assert transformed['cells']['duplicate']==original['cells']['duplicate']
            results[name]='protected boundary PASS';continue
        # Compare observable outputs; deliberately deleted private wires are not
        # part of the equivalence boundary.
        prove=f'read_json {folder}/input.json\nrename top gold\nread_json {folder}/output.json\nrename top gate\nmiter -equiv -flatten gold gate miter\nhierarchy -top miter\nopt_clean\nsat -verify -prove trigger 0 -show-inputs -show-outputs\n'
        (folder/'prove.ys').write_text(prove);h.run(['yosys','-s',str(folder/'prove.ys')],folder/'prove.log');results[name]='PASS'
        print(name,results[name],flush=True)
    (out/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
if __name__=='__main__':main()
