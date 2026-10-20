#!/usr/bin/env python3
"""Validate built-in local LUT optimization; optional Linux timing is diagnostic."""
import argparse,importlib.util,json,subprocess,time,statistics,sys,random,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser()
ap.add_argument('--baseline',required=True,type=Path)
ap.add_argument('--candidate',required=True,type=Path)
ap.add_argument('--out',required=True,type=Path)
ap.add_argument('--timing',action='store_true')
ns=ap.parse_args();OUT=ns.out.resolve();OUT.mkdir(parents=True,exist_ok=True)
executables={'baseline':str(ns.baseline.resolve()),'candidate':str(ns.candidate.resolve())}
negative_model=OUT/'negative_dffeas.v'
negative_model.write_text((ROOT/'tests/local_lut/dffeas_model.v').read_text().replace('q <= d;','q <= ~d;'))
fixtures=OUT/'fixtures';fixtures.mkdir(exist_ok=True)
original=(ROOT/'pmux_case/competition_case/test4/test4.v').read_text()
for seed in range(16):
    rng=random.Random(20261010+seed)
    text=re.sub(r"(5'd\d+:\s*\{[^}]+\}\s*<=\s*\{6'b)([01]{6})(,1'b)",lambda m:m[1]+format(rng.getrandbits(6),'06b')+m[3],original)
    (fixtures/f'variant_{seed}.v').write_text(text)
s=importlib.util.spec_from_file_location('h',ROOT/'scripts/run_enable_feedback_regression.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
def run_case(name,rtl,top):
    stats={}
    for label in ('baseline','candidate'):
        folder=OUT/'integrated'/name/label;folder.mkdir(parents=True,exist_ok=True)
        ys=f'read_verilog -sv {rtl}\nsynth_intel -family cycloneiv -top {top} -run begin:map_cells\nselect {top}\nwrite_rtlil -selected {folder}/post_abc.il\nwrite_json {folder}/post_abc.json\nselect -clear\nsynth_intel -family cycloneiv -top {top} -run map_cells:\ntee -o {folder}/stat.json stat -json\n'
        (folder/'run.ys').write_text(ys);h.run([executables[label],'-s',str(folder/'run.ys')],folder/'run.log')
        cells=json.loads((folder/'stat.json').read_text())['modules']['\\'+top]['num_cells_by_type'];stats[label]={'cells':cells,'logic':cells.get('cycloneiv_lcell_comb',0)+cells.get('$not',0)}
    folder=OUT/'integrated'/name/'candidate'
    m=json.loads((folder/'post_abc.json').read_text())['modules'][top]
    for c in m['cells'].values():
        assert c['type'] in ('$lut','dffeas'),c['type']
        if c['type']=='dffeas':
            for port,value in [('prn','1'),('asdata','0'),('aload','0'),('sclr','0'),('sload','0')]:assert c['connections'][port]==[value],(name,port,c)
            assert c['connections']['clk']==m['ports']['clock' if top=='test1' else 'clk']['bits']
            assert c['parameters']['power_up']=='low'
    h.prove(rtl,top,folder/'post_abc.il',folder/'formal',model=ROOT/'tests/local_lut/dffeas_model.v')
    if name=='test1':
        wrong_init=OUT/'negative_init.v'
        wrong_init.write_text((ROOT/'tests/local_lut/dffeas_model.v').read_text().replace("q = 1'b0;","q = 1'b1;"))
        h.prove(rtl,top,folder/'post_abc.il',folder/'formal_negative_init',negative=True,model=wrong_init)
    if name=='test4':h.prove(rtl,top,folder/'post_abc.il',folder/'formal_negative',negative=True,model=negative_model)
    assert stats['candidate']['logic']<=stats['baseline']['logic'],stats
    assert stats['candidate']['cells'].get('dffeas',0)==stats['baseline']['cells'].get('dffeas',0),stats
    stats['formal']='RTL PASS';print(name,stats,flush=True);return stats
results={}
for i in range(1,5):results[f'test{i}']=run_case(f'test{i}',ROOT/f'pmux_case/competition_case/test{i}/test{i}.v',f'test{i}')
for seed in range(16):results[f'variant_{seed}']=run_case(f'variant_{seed}',fixtures/f'variant_{seed}.v','test4')
(OUT/'integrated_results.json').write_text(json.dumps(results,indent=2)+'\n')
if not ns.timing:sys.exit(0)
timing={}
for i in range(1,5):
    rtl=ROOT/f'pmux_case/competition_case/test{i}/test{i}.v';ys=f'read_verilog -sv {rtl}\nsynth_intel -family cycloneiv -top test{i}\n'
    path=OUT/f'timing_test{i}.ys';path.write_text(ys);values={'baseline':[],'candidate':[]}
    for trial in range(9):
        for label in (('baseline','candidate') if trial%2==0 else ('candidate','baseline')):
            # Blocking waitpid: timeout-based Popen.wait polls on POSIX and can
            # add 50ms observation delays to these short measurements.
            start=time.perf_counter();subprocess.run([executables[label],'-Q','-T','-s',str(path)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True);values[label].append(time.perf_counter()-start)
    timing[f'test{i}']={'raw_wall_seconds':values,'median_baseline':statistics.median(values['baseline']),'median_candidate':statistics.median(values['candidate'])}
    print('Linux diagnostic timing',f'test{i}',timing[f'test{i}'],flush=True)
(OUT/'linux_diagnostic_timing.json').write_text(json.dumps(timing,indent=2)+'\n')
