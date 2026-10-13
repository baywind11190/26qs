"""One ordinary internal CPU run and one exit-event memory run per side/case."""
import json
from pathlib import Path
import time
from runtime_patch import SCHEME, METHOD
from measure_v4 import memory_errors, resource_signature, save, CASES

POLICY=dict(cpu_runs_per_side=1,memory_runs_per_side=1,stage_timeout_s=1800)

def schedule():
    for purpose in ('cpu','memory'):
        for case in CASES:
            for side in ('baseline','optimized'):
                yield dict(purpose=purpose,case=case,side=side)

def compare(base,opt):
    valid=all(type(v) is int and v>0 for v in (base,opt))
    return dict(verdict=('PASS' if (opt-base)*100<=base*5 else 'FAIL') if valid else 'INVALID',
                overhead_pct=(opt-base)/base*100 if valid else None)

def read_runtime(path,native):
    try: r=json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError,ValueError) as exc: raise ValueError('runtime JSON missing/invalid') from exc
    errors=runtime_errors(r,native)
    if errors: raise ValueError('; '.join(errors))
    return r

def runtime_errors(r,native):
    errors=[]
    if not isinstance(r,dict):return ['runtime object missing']
    if r.get('schema')!=1 or r.get('method')!=METHOD or r.get('valid') is not True or r.get('error') is not None:
        errors.append('runtime method/status invalid')
    for key in ('main_pid','process_create_filetime'):
        if type(r.get(key)) is not int or r[key]<=0 or r[key]!=native.get(key): errors.append(key+' mismatch')
    counts=[r.get(k) for k in ('cpu_user_ticks','cpu_kernel_ticks','cpu_total_ticks')]
    if not all(type(v) is int and v>=0 for v in counts) or counts[2]<=0 or counts[0]+counts[1]!=counts[2]:
        errors.append('CPU counts invalid')
    if type(r.get('total_processes')) is not int or r['total_processes']<1 or r.get('active_processes')!=1:
        errors.append('process accounting incomplete')
    return errors

def cpu_errors(row):
    issues=runtime_errors(row.get('runtime'),row)
    for k in ('metrics_valid','stat_exists','resource_match','flow_match'):
        if row.get(k) is not True:issues.append(k+' missing/false')
    if row.get('rc')!=0 or row.get('timed_out') is not False or row.get('root_debugged') is not False:
        issues.append('ordinary execution failed/debugged')
    if row.get('measurement_error') not in (None,''):issues.append('wrapper failed')
    if row.get('performance_scheme')!=SCHEME:issues.append('scheme mismatch')
    if isinstance(row.get('runtime'),dict) and row['runtime'].get('total_processes',0)<2:
        issues.append('no synthesis child process accounted')
    return issues

def judge_case(summ,certificate_cache=None):
    cpu=summ.get('cpu_runs') or [];mem=summ.get('memory_runs') or []
    cv=len(cpu)==2 and {r.get('side') for r in cpu}=={'baseline','optimized'} and all(not cpu_errors(r) for r in cpu)
    mv=len(mem)==2 and {r.get('side') for r in mem}=={'baseline','optimized'} and all(not memory_errors(r) and r.get('performance_scheme')==SCHEME for r in mem)
    complete=summ.get('execution_complete') is True and summ.get('performance_scheme')==SCHEME and summ.get('cpu_policy')==POLICY
    cv=cv and complete;mv=mv and complete
    def val(rows,side,key):return next(r[key] for r in rows if r['side']==side)
    b=val(cpu,'baseline','runtime')['cpu_total_ticks'] if cv else None
    o=val(cpu,'optimized','runtime')['cpu_total_ticks'] if cv else None
    mb=val(mem,'baseline','yosys_peak_working_set_bytes') if mv else None
    mo=val(mem,'optimized','yosys_peak_working_set_bytes') if mv else None
    cj=compare(b,o);mj=compare(mb,mo);valid=cv and mv
    bits=dict(cpu_exempt_upstream_over_limit=b is not None and b>600000000,
              rss_exempt_upstream_over_limit=mb is not None and mb>2*1024**3,
              memory_metric='yosys_peak_working_set_bytes',memory_limit=2*1024**3)
    limit_ok=bool(valid and (o<=600000000 or bits['cpu_exempt_upstream_over_limit']) and (mo<=2*1024**3 or bits['rss_exempt_upstream_over_limit']))
    reasons=[]
    if not cv:reasons.append('单次内部CPU记录缺失、无效或16次阶段未完成')
    elif cj['verdict']=='FAIL':reasons.append('单次CPU总时间相对开销超过5%')
    if not mv:reasons.append('单次退出事件内存记录缺失或无效')
    elif mj['verdict']=='FAIL':reasons.append('单次内存相对开销超过5%')
    if valid and not limit_ok:reasons.append('超过60秒/2GB且原版未超限')
    return dict(case=summ.get('case'),valid=valid,cpu_verdict=cj['verdict'],cpu_ok=cj['verdict']=='PASS',
                mem_ok=mj['verdict']=='PASS',memory_valid=mv,cpu_overhead_pct=cj['overhead_pct'],
                mem_overhead_pct=mj['overhead_pct'],base_cpu_s=b/1e7 if b else None,opt_cpu_s=o/1e7 if o else None,
                base_cpu_ticks=b,opt_cpu_ticks=o,base_memory_bytes=mb,opt_memory_bytes=mo,
                base_memory_mib=mb/1024**2 if mb else None,opt_memory_mib=mo/1024**2 if mo else None,
                base_rss_kb=None,opt_rss_kb=None,limit_bits=bits,limit_ok=limit_ok,reasons=reasons,
                **{'pass':valid and cj['verdict']=='PASS' and mj['verdict']=='PASS' and limit_ok})

def run(context,round_dir,binaries,flows,*,cpu_execute=None,memory_execute=None):
    from win_measure import run_cpu_measured,run_measured
    if context.get('performance_scheme')!=SCHEME or context.get('cpu_policy')!=POLICY:raise ValueError('v6 fixed policy mismatch')
    root=Path(round_dir);out=root/'09_时间内存开销_performance/round01';out.mkdir(parents=True,exist_ok=False)
    cpu_execute=cpu_execute or run_cpu_measured;memory_execute=memory_execute or run_measured
    summaries={c:dict(case=c,performance_scheme=SCHEME,cpu_policy=POLICY,cpu_primary_method=METHOD,
                 memory_metric='yosys_peak_working_set_bytes',cpu_runs=[],memory_runs=[]) for c in CASES}
    start=time.monotonic();error=None;completed=0
    try:
        expected={(c,s):resource_signature(root/f'05_公开四例_public/round01/{c}/{s}/stat.json') for c in CASES for s in binaries}
        for item in schedule():
            case,side,purpose=item['case'],item['side'],item['purpose']
            folder=out/case/purpose/side;folder.mkdir(parents=True,exist_ok=False)
            flow=flows[case];(folder/'flow.ys').write_text(flow,encoding='utf-8')
            remaining=POLICY['stage_timeout_s']-(time.monotonic()-start)
            if remaining<=0:raise TimeoutError('30 minute performance protection limit')
            cmd=[str(binaries[side]),'-s','flow.ys']
            if purpose=='cpu':cmd+=['--runtime-json','runtime.json']
            execute=cpu_execute if purpose=='cpu' else memory_execute
            r=execute(cmd,cwd=folder,log_path=folder/'run.log',timeout_s=remaining)
            r.update(item,performance_scheme=SCHEME,execution_kind='synthesis',evidence_dir=str(folder),
                     stat_exists=(folder/'stat.json').is_file(),flow_match=(folder/'flow.ys').read_text(encoding='utf-8')==flow)
            try:r['resource_match']=resource_signature(folder/'stat.json')==expected[case,side]
            except (OSError,ValueError,KeyError):r['resource_match']=False
            if purpose=='cpu':
                try:r['runtime']=read_runtime(folder/'runtime.json',r)
                except ValueError as exc:r['runtime']=None;r['runtime_error']=str(exc)
                issues=cpu_errors(r)
            else:r['cpu_role']='not_scored_debug_run';issues=memory_errors(r)
            summaries[case][purpose+'_runs'].append(r)
            r['validation_errors']=issues;save(folder/'metrics.json',r);completed+=1
            print(f'v6 {completed}/16 {case} {purpose} {side}',flush=True)
            if issues:raise ValueError('invalid sample: '+str(issues))
        if time.monotonic()-start>=POLICY['stage_timeout_s']:raise TimeoutError('30 minute performance protection limit')
    except Exception as exc:error=str(exc)
    complete=error is None and completed==16
    for s in summaries.values():
        s.update(execution_complete=complete,execution_error=error)
        (out/s['case']).mkdir(exist_ok=True);save(out/s['case']/'summary.json',s)
    save(out/'performance_summary.json',list(summaries.values()))
    save(out/'execution_status.json',dict(complete=complete,completed=completed,planned=16,error=error,elapsed_s=time.monotonic()-start))
    return 0 if complete else 1
