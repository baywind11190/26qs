"""One conditional ETL and fixed 5 ordinary pairs. No official scoring."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import diagnose_v2 as D
import tools_v2 as T
import analysis_v2 as A
import etw_reference as E

def target_environment(cfg,work):
    env=D.P._build_env(cfg)
    env.update(TEMP=str(work),TMP=str(work),TMPDIR=str(work))
    return env

def run(root,retry_zero_startup=False):
    root=Path(root).resolve()
    if root.parent!=D.PROJECT/'results/官方口径评测' or 'CPU波动诊断_v2_6862831' not in root.name:raise ValueError('invalid diagnostic round path')
    state=T.read(root/'status.json');trace=root/'trace'
    if not state['complete']:raise ValueError('fixed diagnostic not complete; preserve and stop')
    if not T.read(root/'protected_verification.json')['unchanged']:raise ValueError('protected file verification failed; trace blocked')
    suffix=''
    if (trace/'collection').exists():
        previous=T.read(trace/'status.json')
        if not retry_zero_startup or previous.get('runs')!=0 or previous.get('etl') or previous.get('state')!='FAILED' or list(trace.rglob('*.etl')):
            raise FileExistsError('one actual trace only; startup retry requires failed zero-run evidence and explicit retry option')
        for n in range(2,100):
            candidate=f'_retry{n:02d}'
            if not (trace/('collection'+candidate)).exists():suffix=candidate;break
        else:raise ValueError('startup retry limit')
        shutil.copy2(trace/'status.json',trace/('status_before'+suffix+'.json'))
    D.guard();cfg,source,plan=D.preflight();context=T.read(root/'context.json');work=Path(context['work'])
    tools=T.read(root/'tools_ordinary.json');observer=work/'observer.exe'
    if T.sha(observer)!=T.read(root/'observer_identity.json')['exe_sha256']:raise ValueError('observer changed')
    for side in tools:
        if T.sha(tools[side]['yosys'])!=tools[side]['yosys_sha256'] or T.sha(tools[side]['abc'])!=tools[side]['abc_sha256']:raise ValueError('ordinary tools changed')
    env=target_environment(cfg,work);os.environ.update(env)
    code=trace/('code'+suffix);code.mkdir();shutil.copy2(__file__,code/'trace_v2.py')
    for name in ('cpu_diagnostic.wprp','cpu_etw_collector.ps1'):shutil.copy2(HERE/name,code/name)
    T.save(trace/('identity'+suffix+'.json'),dict(diagnostic_only=True,tools=tools,profile_sha256=T.sha(HERE/'cpu_diagnostic.wprp'),collector_sha256=T.sha(HERE/'cpu_etw_collector.ps1'),fixed_runs=10,symbols='Release MinGW; compatible WPA function symbols not assumed'))
    # Reuse the owned-session protocol, directing it to this independent script.
    E.__file__=str(HERE/'trace_v2.py')
    recorder=None;rows=[];error=None;etl=None;elapsed=state['runtime_seconds']
    if not suffix and (trace/'status.json').exists():shutil.copy2(trace/'status.json',trace/'status_before_collection.json')
    try:
        recorder=E.Recorder(trace/('collection'+suffix));recorder.start()
        for pair in range(1,6):
            for side in ('baseline','optimized') if pair%2 else ('optimized','baseline'):
                D.guard();out=trace/'samples'/f'{pair:02d}_{side}';out.mkdir(parents=True)
                flow=D.B.gen_builtin_synth_ys(work/'test4.v','test4');(out/'flow.ys').write_text(flow,encoding='utf-8')
                current={k:v for k,v in env.items() if not k.startswith(('PMUX_CPU_DIAG','PMUX_DIAG_V2'))}
                timeout_ms=A.trace_timeout_ms(elapsed)
                cmd=[str(observer),str(out/'native.json'),str(out/'run.log'),str(out),str(timeout_ms),tools[side]['yosys'],'-s','flow.ys','--runtime-json','runtime.json']
                T.save(out/'launch.json',dict(pair=pair,side=side,command=cmd,cwd=str(out),flow_sha256=T.sha(out/'flow.ys'),diagnostic_only=True))
                started=time.monotonic()
                try:result=subprocess.run(cmd,env=current,capture_output=True,text=True,timeout=timeout_ms/1000+15)
                finally:elapsed+=time.monotonic()-started
                native=T.read(out/'native.json');runtime=T.read(out/'runtime.json')
                if result.returncode or native['rc'] or not native['job_total_valid'] or not runtime['valid']:raise RuntimeError('trace target failed')
                rp=next(p for p in native['processes'] if p['pid']==native['root_pid'])
                rows.append(dict(pair=pair,side=side,main_pid=rp['pid'],process_create_filetime=rp['created'],process_exit_filetime=rp['ended'],job_total_processes=native['TotalProcesses'],runtime=runtime,native=native))
                T.save(trace/'samples.json',rows);print(f'TRACE {len(rows)}/10 {side}',flush=True)
        etl=recorder.stop('test4_diagnostic');print('TRACE_ETL='+str(etl),flush=True)
    except Exception as exc:
        import traceback
        error=repr(exc);T.save(trace/('exception'+suffix+'.json'),dict(error=error,traceback=traceback.format_exc()))
    finally:
        if recorder:
            try:recorder.close()
            except Exception as exc:error=(error or '')+' cleanup: '+repr(exc)
        T.save(trace/'status.json',dict(required=True,state='CAPTURED' if etl and len(rows)==10 and not error else 'FAILED',runs=len(rows),etl=str(etl) if etl else None,error=error,runtime_seconds_total=elapsed,diagnostic_only=True))
    if error:
        T.seal(trace);T.seal(root,preserve_previous=True)
        print('TRACE_ERROR='+error,flush=True);return 1
    xperf=shutil.which('xperf.exe') or 'D:/Windows Kits/10/Windows Performance Toolkit/xperf.exe'
    export=trace/'export'
    try:
        E.export_trace(etl,xperf,export,timeout_s=300)
        for name,args in {'sampled':['profile','-detail'],'hardfault':['hardfault']}.items():
            cmd=[xperf,'-i',str(etl),'-o',str(export/(name+'.csv')),'-a',*args]
            p=subprocess.run(cmd,capture_output=True,text=True,errors='replace',timeout=300)
            (export/(name+'.log')).write_text(p.stdout+p.stderr,encoding='utf-8')
            if p.returncode:raise RuntimeError('additional trace export failed: '+name)
        # Independent event totals are diagnostic; do not replace Job integers.
        reference=E.read_reference(export/'events.csv',rows)
        T.save(trace/'event_reference.json',reference)
        T.save(trace/'status.json',dict(required=True,state='CAPTURED_AND_ANALYZED',runs=10,etl=str(etl),event_accounting_valid=True,runtime_seconds_total=elapsed,diagnostic_only=True))
    except Exception as exc:
        T.save(trace/'analysis_error.json',dict(error=repr(exc),note='ETL preserved; do not infer zero or event qualification'))
        T.save(trace/'status.json',dict(required=True,state='CAPTURED_ANALYSIS_PARTIAL',runs=10,etl=str(etl),event_accounting_valid=False,error=repr(exc),runtime_seconds_total=elapsed,diagnostic_only=True))
    T.seal(trace);T.seal(root,preserve_previous=True)
    return 0

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--round',required=True,type=Path);ap.add_argument('--retry-zero-startup',action='store_true');args=ap.parse_args();sys.exit(run(args.round,args.retry_zero_startup))
