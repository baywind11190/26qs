"""Owned administrator recorder; ordinary caller runs targets and analyses ETLs."""
import csv
import json
import os
from pathlib import Path
import subprocess
import re
import time
import uuid


def save(path,value):
    temp=path.with_suffix('.writing')
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8');os.replace(temp,path)


class Recorder:
    def __init__(self,root):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=False)
        self.instance='PMUX_CPU_'+uuid.uuid4().hex;self.sequence=0;self.owned=False
        script=Path(__file__).parent/'cpu_etw_collector.ps1'
        # Literal PowerShell strings, with no command interpolation from external data.
        quote=lambda x:"'"+str(x).replace("'","''")+"'"
        arguments=['-NoProfile','-ExecutionPolicy','Bypass','-File',str(script),'-Root',str(self.root),'-Instance',self.instance,'-ParentPid',str(os.getpid())]
        cmd="Start-Process -FilePath 'powershell.exe' -Verb RunAs -WindowStyle Hidden -ArgumentList @("+','.join(quote(x) for x in arguments)+")"
        save(self.root/'collector_identity.json',dict(instance=self.instance,parent_pid=os.getpid(),script=str(script),
                                                     purpose='independent administrator event collector; targets remain ordinary'))
        try:
            process=subprocess.run(['powershell.exe','-NoProfile','-Command',cmd],capture_output=True,text=True,errors='replace',timeout=120)
        except Exception as exc:
            save(self.root/'collector_launch_error.json',dict(type=type(exc).__name__,error=str(exc),instance=self.instance,
                                                             target_started=False))
            output=getattr(exc,'stdout',None) or '';stderr=getattr(exc,'stderr',None) or ''
            if isinstance(output,bytes):output=output.decode('utf-8',errors='replace')
            if isinstance(stderr,bytes):stderr=stderr.decode('utf-8',errors='replace')
            (self.root/'elevation.log').write_text(str(output)+str(stderr)+'\n'+str(exc),encoding='utf-8')
            raise
        (self.root/'elevation.log').write_text(process.stdout+process.stderr,encoding='utf-8')
        if process.returncode:raise RuntimeError('independent collector elevation failed; see elevation.log')
        ready=self.wait(self.root/'collector_ready.json',120)
        if not ready.get('administrator') or ready.get('instance')!=self.instance:
            raise RuntimeError('independent collector not elevated or identity mismatch')

    @staticmethod
    def wait(path,timeout):
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            if path.is_file():
                try:return json.loads(path.read_text(encoding='utf-8-sig'))
                except (ValueError,OSError):pass
            time.sleep(.1)
        raise TimeoutError('collector response unavailable: '+str(path))

    def request(self,action,name=None):
        self.sequence+=1
        save(self.root/'collector_request.json',dict(instance=self.instance,sequence=self.sequence,action=action,name=name))
        result=self.wait(self.root/f'collector_response_{self.sequence}.json',min(120,max(.001,self.deadline-time.monotonic())) if getattr(self,'deadline',None) is not None else 120)
        if result.get('instance')!=self.instance or result.get('rc')!=0:
            raise RuntimeError('collector '+action+' failed: '+str(result))
        self.owned=bool(result['owned']);return result

    def start(self):return self.request('start')
    def stop(self,name):self.request('stop',name);return self.root/(name+'.etl')
    def close(self):
        # Server ownership is authoritative even if a start acknowledgement was lost.
        self.request('abort','abort_preserved_'+str(self.sequence+1))
        self.request('finish')


def export_trace(etl,xperf,out,timeout_s=300):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    commands={'events':['dumper','-exc_dpcisr','-add_fieldnames'], 'cpu':['cswitch','-process','-thread','-exc_dpcisr'],
              'trace_stats':['tracestats','-detail']}
    for name,args in commands.items():
        cmd=[str(xperf),'-i',str(etl),'-o',str(out/(name+'.csv')),'-a',*args]
        limit=min(300,timeout_s()) if callable(timeout_s) else timeout_s
        result=subprocess.run(cmd,capture_output=True,text=True,errors='replace',timeout=limit)
        (out/(name+'.log')).write_text(result.stdout+result.stderr,encoding='utf-8')
        if result.returncode:raise RuntimeError('xperf export failed: '+name)
    return out


def _pid(value):
    match=re.search(r'\(\s*(\d+)\s*\)\s*$',value)
    if not match:raise ValueError('unrecognized xperf process identity: '+value)
    return int(match[1])


def _records(stream):
    """Read xperf physical event records; never let command-tail quotes join events.

    CPU analysis uses structured prefixes, not arbitrary command-line tails.
    A dangling quote in those tails is emitted by xperf without RFC CSV escaping.
    Per-line CSV parsing preserves every following event and the fixed fields.
    """
    kinds={'P-Start','P-End','T-Start','T-End','CSwitch','DPC_ISR_CSWITCH_PCT'}
    for line in stream:
        kind=line.split(',',1)[0].strip()
        if kind in kinds or kind.startswith('OS Version:'):
            yield next(csv.reader([line],skipinitialspace=True))
        else:yield []


def read_reference(events_csv,samples,deadline_check=None):
    """Subtract xperf's paired DPC_ISR_CSWITCH_PCT from InSwitchTime (us).

    No process-name aggregation, no polling, no elapsed-wall substitution. Kernel
    teardown can be scheduled after T-End/P-End. Require its final Terminated
    switch and an unreused global thread incarnation, rather than dropping CPU
    after an arbitrary elapsed delay. Root FILETIME matching remains bounded.
    """
    csv.field_size_limit(32*1024*1024)
    headers={};processes=[];active={};threads={};global_threads={};trace_start=None;lost=None
    pending=None;last_interrupt=None
    root_pids={sample['main_pid'] for sample in samples}
    with Path(events_csv).open(encoding='utf-8-sig',errors='strict',newline='') as f:
        for event_index,fields in enumerate(_records(f)):
            if deadline_check is not None and event_index%1024==0:deadline_check()
            if not fields:continue
            name=fields[0].strip()
            if name.startswith('OS Version:') and any('Events Lost:' in cell for cell in fields):
                line=','.join(fields)
                m=re.search(r'Events Lost:\s*(\d+).*Buffers lost:\s*(\d+).*Trace Start:\s*(\d+)',line)
                if not m:raise ValueError('trace completeness header unavailable')
                lost=(int(m[1]),int(m[2]));trace_start=int(m[3])
                if lost!=(0,0):raise ValueError('ETW events/buffers lost: '+str(lost))
                continue
            if len(fields)>1 and fields[1].strip()=='TimeStamp':
                headers[name]={v.strip():i for i,v in enumerate(fields)};continue
            if name not in ('P-Start','P-End','T-Start','T-End','CSwitch','DPC_ISR_CSWITCH_PCT'):continue
            if name not in headers:raise ValueError('event schema header missing: '+name)
            h=headers[name]
            def val(key):return fields[h[key]].strip()
            if name=='DPC_ISR_CSWITCH_PCT':
                identity=(int(val('TimeStamp')),int(val('OldPid')),int(val('OldTid')),int(val('CPU')))
                if pending is not None:
                    proc,expected,duration=pending
                    if identity!=expected:raise ValueError('DPC/ISR report identity mismatch')
                    interrupt=int(val('IsrDpc'))
                    if not 0<=interrupt<=duration:raise ValueError('DPC/ISR duration outside CPU interval')
                    proc['cpu_us']-=interrupt
                    pending=None;last_interrupt=identity
                elif identity==last_interrupt:raise ValueError('duplicate DPC/ISR report')
                continue
            if name=='CSwitch':
                if pending is not None:raise ValueError('DPC/ISR report missing for CPU switch')
                pid=_pid(val('Old Process Name ( PID)'));proc=active.get(pid)
                if not proc or not proc['candidate']:continue
            stamp=int(val('TimeStamp'))
            if name=='P-Start':
                pid=_pid(val('Process Name ( PID)'))
                parent=int(val('ParentPID'))
                candidate=pid in root_pids or (active.get(parent) or {}).get('candidate',False)
                proc=dict(pid=pid,parent=parent,key=val('UniqueKey'),start=stamp,end=None,cpu_us=0,used_threads=[],candidate=candidate)
                processes.append(proc);active[pid]=proc
            elif name=='P-End':
                pid=_pid(val('Process Name ( PID)'));proc=active.get(pid)
                if proc and proc['key']==val('UniqueKey'):proc['end']=stamp
            elif name in ('T-Start','T-End'):
                pid=_pid(val('Process Name ( PID)'));tid=int(val('ThreadID'))
                entries=threads.setdefault((pid,tid),[])
                if name=='T-Start':
                    entries.append([stamp,None]);global_threads.setdefault(tid,[]).append((stamp,pid))
                elif entries and entries[-1][1] is None:entries[-1][1]=stamp
            elif name=='CSwitch':
                pid=_pid(val('Old Process Name ( PID)'));proc=active.get(pid)
                if not proc:continue
                if stamp<proc['start']:continue
                duration=int(val('InSwitchTime'))
                if duration<0:raise ValueError('negative xperf CPU duration')
                proc['cpu_us']+=duration
                pending=(proc,(stamp,pid,int(val('Old TID')),int(val('CPU'))),duration)
                if 'OldState' not in h:raise ValueError('CSwitch terminal-state schema missing')
                proc['used_threads'].append((int(val('Old TID')),stamp,val('OldState')))
    if pending is not None:raise ValueError('DPC/ISR report missing for final CPU switch')
    if trace_start is None or lost is None:raise ValueError('missing ETW completeness metadata')
    results=[];used_roots=set()
    for sample in samples:
        if deadline_check is not None:deadline_check()
        pid=sample['main_pid'];creation=sample.get('process_create_filetime');exit_time=sample.get('process_exit_filetime')
        if type(creation) is not int or type(exit_time) is not int:raise ValueError('root creation/exit FILETIME missing')
        candidates=[p for p in processes if p['pid']==pid and p['end'] is not None
                    and abs(trace_start+p['start']*10-creation)<=50_000
                    and abs(trace_start+p['end']*10-exit_time)<=50_000]
        if len(candidates)!=1:raise ValueError('root FILETIME identity missing/ambiguous (5ms maximum tolerance): '+str(pid))
        root=candidates[0];identity=(pid,root['key'],root['start'])
        if identity in used_roots:raise ValueError('ETW root reused by multiple samples')
        used_roots.add(identity)
        tree=[root]
        for proc in sorted(processes,key=lambda p:p['start']):
            if deadline_check is not None:deadline_check()
            if proc is root:continue
            parent=[p for p in tree if p['pid']==proc['parent'] and p['start']<=proc['start'] and p['end'] is not None and proc['start']<=p['end']]
            if len(parent)>1:raise ValueError('ambiguous parent lifetime')
            if parent:tree.append(proc)
        if len(tree)!=sample.get('job_total_processes'):raise ValueError('Job/ETW descendant count mismatch: {} / {}'.format(sample.get('job_total_processes'),len(tree)))
        for proc in tree:
            if proc['end'] is None or proc['cpu_us']<=0:raise ValueError('process lifecycle/CPU incomplete')
            incarnations={}
            for thread_index,(tid,stamp,state) in enumerate(proc['used_threads']):
                if deadline_check is not None and thread_index%256==0:deadline_check()
                intervals=[(start,end) for start,end in threads.get((proc['pid'],tid),[]) if start<=stamp]
                latest=max(intervals,key=lambda x:x[0]) if intervals else (None,None)
                start,end=latest
                global_latest=max((x for x in global_threads.get(tid,[]) if x[0]<=stamp),default=(None,None))
                if start is None or end is None or start<proc['start'] or start>proc['end'] or global_latest!=(start,proc['pid']):
                    raise ValueError('thread lifecycle incomplete: '+str((proc['pid'],tid)))
                incarnations.setdefault((tid,start,end),[]).append((stamp,state))
            for (tid,start,end),switches in incarnations.items():
                switches.sort()
                terminal=[stamp for stamp,state in switches if state=='Terminated']
                if len(terminal)!=1 or terminal[0]!=switches[-1][0] or switches[-1][1]!='Terminated':
                    raise ValueError('thread teardown terminal switch missing/ambiguous: '+str((proc['pid'],tid)))
        result=dict(sample,cpu_reference_ticks=sum(p['cpu_us'] for p in tree)*10,
            reference_processes=[{k:v for k,v in p.items() if k not in ('used_threads','candidate')} for p in tree],
            reference_events_lost=0,reference_buffers_lost=0,reference_method='xperf-cswitch-paired-interrupt-subtraction-terminal-thread-v3')
        results.append(result)
    return results
