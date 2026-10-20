"""Streaming projection of xperf bytes; numerical ASCII prefixes are unchanged."""
import argparse
import collections
import csv
import json
from pathlib import Path
import re
import shutil
import sys

HERE=Path(__file__).parent
sys.path.insert(0,str(HERE))
sys.path.insert(0,'D:/codex/0000_26qs/scripts/pmux_validation/runner')
import tools_v2 as T
import etw_reference as E

def pid(value):
    m=re.search(r'\(\s*(\d+)\s*\)',value)
    return int(m[1]) if m else None

def project(source,destination,target_pids):
    counts=collections.Counter();kept=collections.Counter();headers={}
    core={'P-Start','P-End','T-Start','T-End','CSwitch','DPC_ISR_CSWITCH_PCT','ReadyThread','I-Start','I-End'}
    with Path(source).open('rb') as sourcefile,Path(destination).open('w',encoding='utf-8',newline='') as out:
        for raw in sourcefile:
            name=raw.split(b',',1)[0].strip().decode('ascii',errors='replace');counts[name]+=1
            if raw.lstrip().startswith(b'OS Version:'):
                out.write(raw.decode('latin1'));kept[name]+=1;continue
            if name not in core and not any(k in name for k in ('Fault','FileIo','FileIO')):continue
            fields=next(csv.reader([raw.decode('latin1')],skipinitialspace=True))
            isheader=len(fields)>1 and fields[1].strip()=='TimeStamp'
            if isheader:headers[name]={v.strip():i for i,v in enumerate(fields)}
            keep=isheader or name in ('P-Start','P-End','T-Start','T-End')
            if not keep and len(fields)>2:
                if name=='CSwitch':keep=pid(fields[2]) in target_pids or (len(fields)>8 and pid(fields[8]) in target_pids)
                elif name=='DPC_ISR_CSWITCH_PCT':
                    index=headers.get(name,{}).get('OldPid')
                    keep=index is not None and fields[index].strip().isdigit() and int(fields[index]) in target_pids
                elif name=='ReadyThread':keep=len(fields)>4 and pid(fields[4]) in target_pids
                else:keep=pid(fields[2]) in target_pids
            if keep:out.write(raw.decode('latin1'));kept[name]+=1
    return dict(all_event_counts=dict(counts),projected_event_counts=dict(kept),decoder='latin1 1:1 byte mapping; only ASCII numerical/schema fields interpreted; non-ASCII tails are not asserted decoded text')

def detail(projection,target_pids):
    headers={};lifecycles=[];names={};ready={};waiting={};scheduling={};events=collections.defaultdict(collections.Counter)
    def state(p):return scheduling.setdefault(p,dict(ready_us=0,ready_intervals=0,waiting_us=0,waiting_intervals=0,switchins_without_ready=0,wait_reasons={}))
    with Path(projection).open(encoding='utf-8',newline='') as f:
        for line in f:
            row=next(csv.reader([line],skipinitialspace=True));name=row[0].strip()
            if len(row)>1 and row[1].strip()=='TimeStamp':headers[name]={v.strip():i for i,v in enumerate(row)};continue
            h=headers.get(name)
            if not h:continue
            def val(k):return row[h[k]].strip()
            if name=='P-Start':
                p=pid(val('Process Name ( PID)'))
                if p in target_pids:
                    entry=dict(pid=p,name=val('Process Name ( PID)'),parent=int(val('ParentPID')),start_us=int(val('TimeStamp')),raw_fields=dict(zip(h,row)))
                    lifecycles.append(entry);names[p]=entry['name']
            elif name=='CSwitch':
                t=int(val('TimeStamp'));old=pid(val('Old Process Name ( PID)'));new=pid(val('New Process Name ( PID)'))
                oldtid=int(val('Old TID'));newtid=int(val('New TID'));oldstate=val('OldState')
                if old in target_pids:
                    key=(old,oldtid)
                    if oldstate=='Waiting':waiting[key]=(t,val('Wait Reason'))
                    elif oldstate in ('Ready','Standby','DeferredReady'):ready[key]=t
                if new in target_pids:
                    key=(new,newtid);s=state(new)
                    if key in ready:
                        start=ready.pop(key)
                        if t>=start:s['ready_us']+=t-start;s['ready_intervals']+=1
                    else:s['switchins_without_ready']+=1
            elif name=='ReadyThread':
                p=pid(val('Rdy Process Name ( PID)'));tid=int(val('Rdy TID'));t=int(val('TimeStamp'))
                if p in target_pids:
                    key=(p,tid);s=state(p)
                    if key in waiting:
                        start,reason=waiting.pop(key)
                        if t>=start:s['waiting_us']+=t-start;s['waiting_intervals']+=1;s['wait_reasons'][reason]=s['wait_reasons'].get(reason,0)+t-start
                    ready[key]=t
            elif any(k in name for k in ('Fault','FileIo','FileIO','I-Start','I-End')) and 'Process Name ( PID)' in h:
                p=pid(val('Process Name ( PID)'))
                if p in target_pids:events[p][name]+=1
    return dict(process_lifecycles=lifecycles,process_names=names,scheduling_observed_intervals=scheduling,events_by_process=dict(events),
        limitation='Scheduling sums include only observed matching intervals; unmatched switches are counted, not zero-filled. Waiting and ready durations are thread sums, not CPU or necessarily process wall time.')

def run(root):
    root=Path(root);trace=root/'trace'
    for n in range(2,100):
        out=trace/f'analysis_reanalysis{n:02d}'
        if not out.exists():out.mkdir();break
    else:raise ValueError('analysis directory limit')
    samples=T.read(trace/'samples.json');target={p['pid'] for s in samples for p in s['native']['processes']}
    projection=out/'structured_projection_utf8.csv'
    projection_info=project(trace/'export/events.csv',projection,target)
    T.save(out/'projection.json',dict(**projection_info,source_sha256=T.sha(trace/'export/events.csv'),projection_sha256=T.sha(projection)))
    details=detail(projection,target);T.save(out/'lifecycle_scheduling_faults.json',details)
    reference=None;error=None
    try:
        reference=E.read_reference(projection,samples);T.save(out/'event_reference.json',reference)
    except Exception as exc:error=repr(exc);T.save(out/'event_reference_error.json',dict(error=error))
    sampled=[];hardfault=[]
    for filename,dest,process_col in (('sampled.csv',sampled,0),('hardfault.csv',hardfault,2)):
        with (trace/'export'/filename).open(encoding='latin1',newline='') as f:
            for row in csv.reader(f,skipinitialspace=True):
                if len(row)>process_col and pid(row[process_col]) in target:dest.append(row)
    T.save(out/'sampled_target_modules.json',sampled);T.save(out/'hardfault_target_rows.json',hardfault)
    T.save(out/'identity.json',dict(source_sha256=T.sha(__file__),target_runs_added=0,reference_valid=reference is not None,error=error))
    shutil.copy2(__file__,out/'analyze_trace_v2.py');T.seal(out)
    previous=T.read(trace/'status.json');T.save(out/'status_before_reanalysis.json',previous)
    previous.update(state='CAPTURED_AND_ANALYZED' if reference is not None else 'CAPTURED_ANALYSIS_PARTIAL',event_accounting_valid=reference is not None,
        error=error,analysis_directory=str(out),sampled_modules_exported=True,scheduling_faults_exported=True)
    T.save(trace/'status.json',previous)
    T.seal(out);T.seal(trace);T.seal(root)
    print(json.dumps(dict(reference_valid=reference is not None,error=error,samples=len(samples),sampled_rows=len(sampled),hardfault_rows=len(hardfault),path=str(out)),ensure_ascii=False))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--round',type=Path,required=True);args=ap.parse_args();run(args.round)
