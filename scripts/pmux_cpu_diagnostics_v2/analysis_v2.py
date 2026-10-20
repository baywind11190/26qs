"""Exact integer diagnostics. No official verdicts or sample selection."""
import math
import statistics
from pathlib import Path
import copy

GROUPS=('baseline_aa','optimized_aa','baseline_optimized','stage_baseline_optimized','stage_pass_on_off')
MARKS=('main_entry','design_read_end','fsm_opt_end','pmux_begin','pmux_end','abc9_begin','abc9_end','final')
NAMES=('启动读取','综合至fsm_opt','边界间隔','整个pass槽位','ABC前综合','ABC9主进程区间','综合及输出收尾')

def completion_status(count,error,protected_unchanged):
    if not protected_unchanged:error=(error or '')+' protected files changed'
    return dict(complete=count==100 and not error, error=error, protected_unchanged=protected_unchanged)

def trace_timeout_ms(elapsed):
    remaining=1800-elapsed
    if remaining<0.001:raise TimeoutError('30 minute cumulative diagnostic protection')
    return max(1,int(min(60,remaining)*1000))

def normalize_abc(diag,native):
    result=copy.deepcopy(diag)
    for call in result['abc']:
        if 'root_pid' not in call:call['root_pid']=call.pop('ppid',native['root_pid'])
        proc=next((p for p in native['processes'] if (p['pid'],p['created'])==(call['pid'],call['created'])),None)
        call['ppid']=proc['ppid'] if proc and proc.get('ppid') else None
        call['parent_source']='native observed process instance' if call['ppid'] else 'UNKNOWN'
    return result

def classify_processes(native,abc_records=()):
    abcids={(r['pid'],r['created']) for r in abc_records}
    buckets={k:[] for k in ('root','abc','helper','unknown')}
    for p in native['processes']:
        if p['pid']==native['root_pid']:kind='root'
        elif (p['pid'],p['created']) in abcids or Path(p.get('image','')).name.lower() in ('yosys-abc.exe','abc.exe'):kind='abc'
        elif p.get('image'):kind='helper'
        else:kind='unknown'
        buckets[kind].append(p)
    r={}
    for k,values in buckets.items():
        valid=all(type(p.get(n))is int and p[n]>=0 for p in values for n in ('user','kernel'))
        r[k+'_cpu']=sum(p['user']+p['kernel'] for p in values) if valid else None
        r[k+'_instances']=[(p['pid'],p['created']) for p in values]
    if not buckets['abc']:r['abc_cpu']=None
    r['process_cpu_complete']=process_accounting(native['processes'],native['TotalProcesses'])['complete'] and native.get('process_accounting_complete',True)
    r['process_metadata_complete']=bool(native['processes']) and all(p.get('image') and p.get('ppid') for p in native['processes'])
    r['process_roles_complete']=not buckets['unknown']
    return r

def schedule():
    rows=[]
    for group in GROUPS:
        for pair in range(1,11):
            for role in ('A','B') if pair%2 else ('B','A'):
                rows.append(dict(index=len(rows)+1,group=group,pair=pair,role=role))
    return rows

def describe(raw,allow_signed=False):
    vals=[v for v in raw if type(v) is int]
    if not allow_signed and any(v<0 for v in vals):raise ValueError('negative cumulative time')
    unique=sorted(set(vals));gaps=[b-a for a,b in zip(unique,unique[1:])]
    return dict(raw=raw,count=len(vals),missing=len(raw)-len(vals),minimum=min(vals) if vals else None,
                maximum=max(vals) if vals else None,range_ticks=max(vals)-min(vals) if vals else None,
                mean=statistics.mean(vals) if vals else None,median=statistics.median(vals) if vals else None,
                sample_stddev=statistics.stdev(vals) if len(vals)>1 else None,
                repeated_values={str(v):vals.count(v) for v in unique if vals.count(v)>1},
                minimum_positive_gap_ticks=min(gaps) if gaps else None,
                observed_gap_gcd_ticks=math.gcd(*gaps) if gaps else None,
                observed_gcd_ticks=math.gcd(*vals) if vals else None)

def pairs(rows):
    result=[]
    for group in GROUPS:
        for pair in sorted({r['pair'] for r in rows if r['group']==group}):
            selected=[r for r in rows if r['group']==group and r['pair']==pair]
            a=[r for r in selected if r['role']=='A'];b=[r for r in selected if r['role']=='B']
            if len(a)!=1 or len(b)!=1:continue
            av,bv=a[0].get('cpu'),b[0].get('cpu')
            ok=type(av) is int and type(bv) is int and av>0 and bv>0
            delta=bv-av if ok else None
            result.append(dict(group=group,pair=pair,first=selected[0]['role'],A_ticks=av,B_ticks=bv,
                delta_ticks=delta,overhead_pct=delta/av*100 if ok else None,
                above_plus_5pct=(delta*100>av*5) if ok else None,
                below_minus_5pct=(-delta*100>av*5) if ok else None))
    return result

def process_accounting(rows,total_processes):
    ids=[(r.get('pid'),r.get('created')) for r in rows]
    if len(set(ids))!=len(ids):raise ValueError('duplicate process instance')
    valid=all(type(r.get(k)) is int and r[k]>=0 for r in rows for k in ('user','kernel'))
    complete=valid and all(p and c for p,c in ids) and len(rows)==total_processes
    return dict(complete=bool(complete),known_processes=len(rows),job_processes=total_processes,
        sum_ticks=sum(r['user']+r['kernel'] for r in rows) if complete else None)

def partition(marks):
    core=[m for m in marks if m['label'] in MARKS]
    if [m['label'] for m in core]!=list(MARKS):raise ValueError('missing/duplicate/out of order checkpoint')
    result=[]
    for name,left,right in zip(NAMES,core,core[1:]):
        values={}
        for prefix in ('root','job'):
            for m in (left,right):
                if not all(type(m.get(prefix+'_'+k)) is int and m[prefix+'_'+k]>=0 for k in ('user','kernel')):
                    raise ValueError('invalid stage counter')
            values[prefix+'_ticks']=sum(right[prefix+'_'+k]-left[prefix+'_'+k] for k in ('user','kernel'))
        values['wall_qpc']=right['qpc']-left['qpc']
        if min(values.values())<0:raise ValueError('nonmonotonic stage')
        result.append(dict(stage=name,**values))
    return result
