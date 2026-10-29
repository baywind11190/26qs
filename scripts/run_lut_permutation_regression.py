"""Verify LUT input permutation normalization and exact combinational behavior."""
from pathlib import Path
import argparse,itertools,json,random,subprocess
ap=argparse.ArgumentParser();ap.add_argument('--yosys',required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
def canonical(w,t):
 return min(sum(((t>>sum(((address>>j)&1)<<p[j] for j in range(w)))&1)<<address for address in range(1<<w)) for p in itertools.permutations(range(w)))
rng=random.Random(20261029);functions=[(3,t) for t in range(256)]+[(4,rng.getrandbits(16)) for _ in range(64)];cells={}
for i,(w,t) in enumerate(functions):cells[f'n{i:03}']={'hide_name':0,'type':'$lut','parameters':{'WIDTH':format(w,'032b'),'LUT':format(t,f'0{1<<w}b')},'attributes':{},'port_directions':{'A':'input','Y':'output'},'connections':{'A':list(range(2,2+w)),'Y':[6+i]}}
ports={'a':{'direction':'input','bits':[2,3,4,5]},'y':{'direction':'output','bits':list(range(6,6+len(cells)))}};m={'attributes':{},'ports':ports,'cells':cells,'netnames':{n:{'hide_name':0,'bits':p['bits'],'attributes':{}} for n,p in ports.items()}}
source=a.out/'input.json';source.write_text(json.dumps({'modules':{'top':m}}))
def run(text,name):
 ys=a.out/(name+'.ys');ys.write_text(text)
 with (a.out/(name+'.log')).open('w') as log:subprocess.run([a.yosys,'-Q','-s',str(ys)],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
first=a.out/'first.json';second=a.out/'second.json'
run(f'read_json {source}\npmux_opt -lut\nwrite_json {first}\npmux_opt -lut\nwrite_json {second}\n','run')
after=json.loads(first.read_text())['modules']['top']['cells'];assert len(after)==len(cells)
bad=[]
for n,c in after.items():
 w=int(c['parameters']['WIDTH'],2);t=int(c['parameters']['LUT'],2)
 if t!=canonical(w,t):bad.append(n)
assert not bad,('Noncanonical LUT functions',len(bad),bad[:5])
assert after==json.loads(second.read_text())['modules']['top']['cells'],'Normalization must be idempotent'
run(f'read_json {source}\nrename top gold\nread_json {first}\nrename top gate\nmiter -equiv -flatten gold gate miter\nhierarchy -top miter\nopt_clean\nsat -verify -prove trigger 0 -show-inputs -show-outputs\n','formal')
result={'checked_functions':len(cells),'all_three_input_functions':256,'random_four_input_functions':64,'formal':'PASS','idempotent':True};(a.out/'summary.json').write_text(json.dumps(result,indent=2));print(result,flush=True)
