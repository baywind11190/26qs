"""Minimal nested-Job/terminated-child check and both Yosys entry points."""
import json
from pathlib import Path
import subprocess
import shutil
from measure_v6 import read_runtime
from win_measure import run_cpu_measured,run_measured

def run(context,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    here=Path(__file__).parent
    compiler=context['tools']['compiler']['path']
    work=Path(context['ascii_bridge'])/'v6-selfcheck'
    work.mkdir(parents=True,exist_ok=True)
    for name in ('runtime_cpu_probe.cc','runtime_cpu_windows.inc'):
        shutil.copy2(here/name,work/name)
    exe=work/'runtime_cpu_probe.exe'
    with (out/'compile.log').open('w') as log:
        subprocess.run([compiler,'-O2',str(work/'runtime_cpu_probe.cc'),'-o',str(exe)],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
    records={};checks=[]
    r=run_cpu_measured([str(exe)],cwd=out,log_path=out/'probe.log',timeout_s=30)
    records['probe']=r
    runtime=read_runtime(out/'runtime.json',r)
    records['probe']['runtime']=runtime
    checks.append(r['rc']==0 and runtime['cpu_total_ticks']>=2500000 and runtime['total_processes']==2)
    # Both public entry points must write an identity-bound record under the external Job.
    for side in ('baseline','optimized'):
        folder=out/side;folder.mkdir(exist_ok=True)
        execute=run_cpu_measured if side=='baseline' else run_measured
        r=execute([context['builtin'][side]['path'],'-p','help','--runtime-json','runtime.json'],cwd=folder,log_path=folder/'run.log',timeout_s=60)
        r['runtime']=read_runtime(folder/'runtime.json',r);records[side]=r
        checks.append(r['rc']==0 and r['metrics_valid'])
        if side=='optimized':checks.append(r['memory_capture_complete'] and r['memory_exit_event_observed'])
    result=dict(selftest_ok=all(checks),checks=checks,records=records,
                note='Nested Job and terminated-child accounting; not a precision guarantee or performance sample.')
    (out/'selftest_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return 0 if result['selftest_ok'] else 1
