#!/usr/bin/env python3
"""One Linux development batch: wall time and same-run main-Yosys peak RSS.

Requires the diagnostic /proc/self/status VmHWM destructor library passed with --peak-preload.
This is not a Windows PeakWorkingSet acceptance result.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import statistics
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',required=True,type=Path)
    parser.add_argument('--candidate',required=True,type=Path)
    parser.add_argument('--peak-preload',required=True,type=Path)
    parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args()
    assert platform.system()=='Linux', 'Linux diagnostic only'
    out=args.out.resolve(); out.mkdir(parents=True,exist_ok=False)
    baseline,candidate,preload=[x.resolve() for x in (args.baseline,args.candidate,args.peak_preload)]
    assert all(x.is_file() for x in (baseline,candidate,preload))
    env=os.environ.copy(); env['LD_PRELOAD']=str(preload)
    cases=[(f'test{i}',ROOT/f'pmux_case/competition_case/test{i}/test{i}.v') for i in range(1,5)]
    cases += [(x.stem,x) for x in sorted((ROOT/'tests/official_new5').glob('*.v'))]
    assert len(cases)==9
    folders={}; scripts={}
    for top,rtl in cases:
        folder=out/top; folder.mkdir(); folders[top]=folder
        script=folder/'flow.ys'
        script.write_text(f'read_verilog -sv {rtl}\nsynth_intel -family cycloneiv -top {top}\ntee -o {folder}/stat.json stat -json\n')
        scripts[top]=script
    def file_hash(path):
        digest=hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda:stream.read(1024*1024), b''): digest.update(chunk)
        return digest.hexdigest()
    identity={'platform':platform.platform(), 'measurement':'wall clock; post-exec VmHWM main address-space peak RSS; same execution',
              'warmup_policy':'one initial phase, baseline test1 ten times; no per-case repeated warmup',
              'time_policy':'initial baseline then candidate; if >5% and both <10s, five paired repeats and ratio of means',
              'memory_policy':'first measurement only; no replacement by repeats',
              'binaries':{label:{'path':str(exe),'sha256':file_hash(exe)}
                          for label,exe in [('baseline',baseline),('candidate',candidate),('peak_preload',preload)]}}
    (out/'identity.json').write_text(json.dumps(identity,indent=2))

    def run(top,exe,label,trial):
        folder=folders[top]; dest=folder/f'{trial:02d}_{label}';dest.mkdir()
        with (dest/'run.log').open('w') as log:
            start=time.perf_counter()
            proc=subprocess.Popen([str(exe),'-Q','-s',str(scripts[top])],cwd=ROOT,env=env,
                                  stdout=log,stderr=subprocess.STDOUT)
            code=proc.wait()
            wall=(time.perf_counter()-start)*1000
        assert code==0,(top,label,trial,code)
        text=(dest/'run.log').read_text()
        peaks=[int(kib) for pid,kib in re.findall(r'MAIN_PEAK_SELF pid=(\d+) kib=(\d+)',text) if int(pid)==proc.pid]
        assert len(peaks)==1 and peaks[0]>0,(top,label,trial,peaks)
        raw=(folder/'stat.json').read_bytes();(dest/'stat.json').write_bytes(raw)
        cells=json.loads(raw)['modules']['\\'+top]['num_cells_by_type']
        return {'label':label,'trial':trial,'pid':proc.pid,'wall_ms':wall,'peak_kib':peaks[0],
                'logic':cells.get('cycloneiv_lcell_comb',0)+cells.get('$not',0),'dff':cells.get('dffeas',0)}

    warmup=[run('test1',baseline,'warmup_baseline',i) for i in range(10)]
    (out/'warmup.json').write_text(json.dumps(warmup,indent=2))
    results={}
    for top,_ in cases:
        b=run(top,baseline,'baseline',10);c=run(top,candidate,'candidate',10)
        raw=[b,c];initial_time=100*(c['wall_ms']/b['wall_ms']-1)
        memory=100*(c['peak_kib']/b['peak_kib']-1)
        recheck=initial_time>5 and max(b['wall_ms'],c['wall_ms'])<10000
        final_time=initial_time
        if recheck:
            pairs=[(run(top,baseline,'baseline',i),run(top,candidate,'candidate',i)) for i in range(11,16)]
            raw += [x for pair in pairs for x in pair]
            final_time=100*(statistics.mean(y['wall_ms'] for _,y in pairs)/statistics.mean(x['wall_ms'] for x,_ in pairs)-1)
        assert all(x['logic']==(b['logic'] if x['label']=='baseline' else c['logic']) for x in raw), (top,'resource instability')
        row={'raw':raw,'initial_time_percent':initial_time,'final_time_percent':final_time,
             'initial_memory_percent':memory,'five_pair_time_recheck':recheck,
             'area_reduction_percent':100*(1-c['logic']/b['logic']),
             'no_logic_increase':c['logic']<=b['logic'],'time_pass':final_time<=5,'memory_pass':memory<=5}
        results[top]=row;(out/'results.json').write_text(json.dumps(results,indent=2))
        print(top,json.dumps({k:v for k,v in row.items() if k!='raw'}),flush=True)
    summary={'average_area_reduction_percent':statistics.mean(r['area_reduction_percent'] for r in results.values()),
             'max_final_time_percent':max(r['final_time_percent'] for r in results.values()),
             'max_first_memory_percent':max(r['initial_memory_percent'] for r in results.values()),
             'all_cases_no_logic_increase':all(r['no_logic_increase'] for r in results.values()),
             'all_cases_time_pass':all(r['time_pass'] for r in results.values()),
             'all_cases_memory_pass':all(r['memory_pass'] for r in results.values()),
             'runs':len(warmup)+sum(len(r['raw']) for r in results.values()),'scope':'one Linux development batch'}
    summary['passed']=summary['average_area_reduction_percent']>20 and all(summary[k] for k in ['all_cases_no_logic_increase','all_cases_time_pass','all_cases_memory_pass'])
    (out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2),flush=True)
    assert summary['passed'], 'Development batch failed; preserve every original sample'


if __name__=='__main__':
    main()
