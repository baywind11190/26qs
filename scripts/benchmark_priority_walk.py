from pathlib import Path
import argparse,json,statistics,subprocess
ap=argparse.ArgumentParser(description="Compare priority-chain rejection cost; diagnostic only.");ap.add_argument('--baseline',required=True);ap.add_argument('--candidate',required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--require-improvement',action='store_true');a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
depth=900;cells={};previous=902
for k in range(depth):
 y=903+k;cells[f'm{k:04}']={'hide_name':0,'type':'$mux','parameters':{'WIDTH':format(1,'032b')},'attributes':{},'port_directions':{'A':'input','B':'input','S':'input','Y':'output'},'connections':{'A':[previous],'B':[901],'S':[1+k],'Y':[y]}};previous=y
m={'attributes':{},'ports':{'s':{'direction':'input','bits':list(range(1,901))},'d':{'direction':'input','bits':[901]},'base':{'direction':'input','bits':[902]},'y':{'direction':'output','bits':[previous]}},'cells':cells,'netnames':{}}
for name,p in m['ports'].items():m['netnames'][name]={'hide_name':0,'bits':p['bits'],'attributes':{}}
fixture=a.out/'chain.json';fixture.write_text(json.dumps({'modules':{'top':m}}));rows={'baseline':[],'candidate':[]}
for trial in range(5):
 for label,exe in [('baseline',a.baseline),('candidate',a.candidate)]:
  prefix=a.out/f'{trial}_{label}';ys=prefix.with_suffix('.ys');perf=prefix.with_suffix('.perf.json');dest=prefix.with_suffix('.out.json')
  ys.write_text(f'read_json {fixture}\nwrite_json {prefix}.before.json\n'+('pmux_opt\n'*100)+f'write_json {dest}\n')
  with prefix.with_suffix('.log').open('w') as log:subprocess.run([exe,'-Q','--perffile',str(perf),'-s',str(ys)],stdout=log,stderr=subprocess.STDOUT,check=True)
  after=json.loads(dest.read_text())['modules']['top']['cells'];before=json.loads(Path(str(prefix)+'.before.json').read_text())['modules']['top']['cells'];assert after==before,'Rejected dynamic-default chain must remain unchanged'
  rows[label].append(json.loads(perf.read_text())['passes']['pmux_opt']['runtime_ns']/1e6)
ratio=statistics.median(rows['candidate'])/statistics.median(rows['baseline']);result={'raw_ms':rows,'ratio':ratio,'unchanged_900_cells':True};(a.out/'summary.json').write_text(json.dumps(result,indent=2));print(result,flush=True)
if a.require_improvement:assert ratio<0.85,'Require at least 15% lower chain-analysis median'
