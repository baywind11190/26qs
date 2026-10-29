from pathlib import Path
import argparse, copy, json, subprocess, importlib.util, re
ap=argparse.ArgumentParser(); ap.add_argument('--candidate',required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
a.out.mkdir(parents=True,exist_ok=False)
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('formal',root/'scripts/run_enable_feedback_regression.py'); f=importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
rtl=a.out/'chain.v'
rtl.write_text("module top(input [2:0] s,input [11:0] d,output [3:0] y); wire [3:0] low,mid; assign low=s[0]?d[3:0]:4'b0; assign mid=s[1]?d[7:4]:low; assign y=s[2]?d[11:8]:mid; endmodule\n")
def run(text,p):
 ys=p.with_suffix('.ys');ys.write_text(text)
 with p.with_suffix('.log').open('w') as log: subprocess.run([a.candidate,'-Q','-s',str(ys)],stdout=log,stderr=subprocess.STDOUT,check=True)
run(f'read_verilog {rtl}\nproc\nwrite_json {a.out}/base.json\n',a.out/'prepare')
base=json.loads((a.out/'base.json').read_text()); results={}; failures=[]
for name in ['plain','keep_module','keep_cell','keep_wire','init_wire','partial_selection','shared_output','alias_keep','repeat_selector','cycle']:
 des=copy.deepcopy(base); m=des['modules']['top']; sel=''
 bottom=next(c for c in m['cells'].values() if c['connections']['A']==['0']*4)
 if name=='repeat_selector':bottom['connections']['S']=m['ports']['s']['bits'][2:3]
 if name=='cycle':bottom['connections']['A']=m['netnames']['mid']['bits']
 if name=='keep_module':m['attributes']['keep']='1'
 if name=='keep_cell':bottom['attributes']['keep']='1'
 if name in ['keep_wire','init_wire']:m['netnames']['low']['attributes']['keep' if name=='keep_wire' else 'init']='1' if name=='keep_wire' else '0000'
 if name=='alias_keep':m['netnames']['alias']={'hide_name':0,'bits':m['netnames']['low']['bits'],'attributes':{'keep':'1'}}
 if name=='partial_selection':sel='select top/w:y\n'
 if name=='shared_output':m['ports']['tap']={'direction':'output','bits':m['netnames']['low']['bits'][:1]}
 folder=a.out/name;folder.mkdir();(folder/'in.json').write_text(json.dumps(des))
 run(f'read_json {folder}/in.json\n{sel}pmux_opt\nselect -clear\nwrite_json {folder}/out.json\nwrite_rtlil {folder}/out.il\n',folder/'run')
 out=json.loads((folder/'out.json').read_text())['modules']['top']; hits=int(re.search(r'Total H3 rebuilt: (\d+)',(folder/'run.log').read_text())[1]);expected=int(name=='plain')
 results[name]={'pmux':hits,'expected':expected}
 if hits!=expected:failures.append(name)
 print(name,results[name],flush=True)
 if name in ['plain','keep_cell','keep_wire','alias_keep','keep_module','partial_selection']:
  f.prove(rtl,'top',folder/'out.il',folder/'formal')
(a.out/'results.json').write_text(json.dumps(results,indent=2));assert not failures,failures
