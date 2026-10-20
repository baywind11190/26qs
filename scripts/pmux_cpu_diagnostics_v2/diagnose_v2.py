"""Fixed test4 diagnostics; no official evaluation or algorithm edits."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

HERE=Path(__file__).resolve().parent
PROJECT=Path('D:/codex/0000_26qs')
VALIDATION=PROJECT/'scripts/pmux_validation'
sys.path.insert(0,str(VALIDATION));sys.path.insert(0,str(VALIDATION/'runner'))
import validate as official
import prepare_builtin as P
import builtin_common as B
import function_common as F
import ast
import types
from formal_status import check_post_abc_model
from measure_v4 import resource_signature
from measure_v6 import runtime_errors
import analysis_v2 as A
import tools_v2 as T

# Reuse only pure proof helpers; importing the historical runner would read
# an official round context at import time. The original file stays unchanged.
def proof_helpers():
    path=VALIDATION/'runner/run_eqy_chains.py'
    wanted={'discover_modules','net_side_prelude_mapped','rtl_side_prelude','make_cfg','run_strategy','aggregate_partitions'}
    tree=ast.parse(path.read_text(encoding='utf-8'))
    body=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in wanted]
    if len(body)!=len(wanted):raise ValueError('proof helper interface changed')
    r=types.ModuleType('v2_pure_proof_helpers')
    r.__dict__.update(F=F,json=json,Path=Path,PARTITION_PROOF_TIMEOUT=600,PARTITION_PROBE_TIMEOUT=120,EQY_TAIL='\n[strategy simple]\nuse sat\ndepth 5\n')
    exec(compile(ast.Module(body=body,type_ignores=[]),str(path),'exec'),r.__dict__)
    return r

R=proof_helpers()

COMMIT='6862831899247fd0e8f5c1e590693b1291bfa71e'
SOURCE='37acf1672bd78cb463b96c8dfcb8d79f4b478a667b81d8377cec458743143fa7'
HEAVY=('yosys','yosys-abc','cmake','ninja','cc1plus','eqy','z3','sby','abc')

def ps(text):
    p=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',text],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=30)
    return dict(rc=p.returncode,stdout=p.stdout,stderr=p.stderr)

def busy():
    names=','.join("'"+s+"'" for s in HEAVY)
    r=ps("$ErrorActionPreference='SilentlyContinue'; @(Get-Process -Name "+names+" | Select-Object ProcessName,Id,CPU,StartTime) | ConvertTo-Json -Compress")
    if r['rc'] not in (0,1):raise RuntimeError('cannot inspect active tasks: '+str(r))
    if not r['stdout'].strip():return []
    value=json.loads(r['stdout']);return value if isinstance(value,list) else [value]

def guard():
    tasks=busy()
    if tasks:raise RuntimeError('concurrent build/Formal/evaluation active: '+str(tasks))

def environment():
    return dict(power=ps('powercfg.exe /getactivescheme'),
        machine=ps("[pscustomobject]@{OS=[Environment]::OSVersion.VersionString;CPU=$env:PROCESSOR_IDENTIFIER;LogicalProcessors=[Environment]::ProcessorCount;Time=[DateTime]::Now.ToString('o')} | ConvertTo-Json -Compress"),
        active_processes=ps('Get-Process | Select-Object ProcessName,Id,CPU,WorkingSet64 | ConvertTo-Json -Compress'),
        cache_state='UNKNOWN; no flush or dedicated warmup; manifest hashing/build/capture/proof history retained')

def preflight():
    cfg,source=official.preflight(COMMIT)
    if hashlib.sha256(source).hexdigest()!=SOURCE:raise ValueError('algorithm identity mismatch')
    plan=P.plan_builtin(cfg,SOURCE)
    return cfg,source,plan

def identity(binaries,abc_paths):
    return {side:dict(yosys=str(p),yosys_sha256=T.sha(p),abc=str(abc_paths[side]),abc_sha256=T.sha(abc_paths[side])) for side,p in binaries.items()}

def compile_observer(cfg,work):
    exe=work/'observer.exe'
    subprocess.run([cfg['tools']['compiler']['path'],'-O2','-std=c++17','-municode',str(HERE/'observer.cc'),'-o',str(exe)],env=P._build_env(cfg),stdout=(work/'observer_build.log').open('w'),stderr=subprocess.STDOUT,check=True,timeout=120)
    return exe

def dump_csv(path,rows):
    import csv
    if not rows:return
    with Path(path).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def collect_modules(native,env,cache):
    result={}
    for p in native['processes']:
        for name in [p['image']]+p['modules_observed_not_exhaustive']:
            if not name:continue
            if name not in cache:
                try:cache[name]=dict(sha256=T.sha(name),error=None)
                except OSError as exc:cache[name]=dict(sha256=None,error=str(exc))
            result[name]=cache[name]
    return result

def selfcheck(cfg,observer,work,env,root):
    folder=work/'selfcheck';folder.mkdir()
    original=(VALIDATION/'runner/runtime_cpu_probe.cc').read_text(encoding='utf-8')
    # A child that also starts a grandchild. Both are waited for, once.
    insert='''if (argc == 2) {
            char own[MAX_PATH];GetModuleFileNameA(NULL,own,MAX_PATH);
            std::string command=std::string("\\\"")+own+"\\\" child grandchild";
            STARTUPINFOA s={};s.cb=sizeof(s);PROCESS_INFORMATION p={};
            if(!CreateProcessA(NULL,&command[0],NULL,NULL,FALSE,CREATE_NO_WINDOW,NULL,NULL,&s,&p))return 20;
            if(WaitForSingleObject(p.hProcess,10000)!=WAIT_OBJECT_0)return 21;
            CloseHandle(p.hThread);CloseHandle(p.hProcess);
        }
        // Spend CPU'''
    text=original.replace('// Spend CPU',insert,1)
    (folder/'probe.cc').write_text(text,encoding='utf-8')
    exe=folder/'probe.exe'
    with (folder/'compile.log').open('w') as log:
        subprocess.run([cfg['tools']['compiler']['path'],'-O2','-I',str(VALIDATION/'runner'),str(folder/'probe.cc'),'-o',str(exe)],env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
    results=[]
    for n in (1,2):
        out=folder/f'run{n}';out.mkdir()
        cmd=[str(observer),str(out/'native.json'),str(out/'run.log'),str(out),'30000',str(exe)]
        p=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=40)
        T.save(out/'observer_launch.json',dict(command=cmd,rc=p.returncode,stdout=p.stdout,stderr=p.stderr))
        if not (out/'native.json').is_file():raise RuntimeError('observer did not produce JSON; rc='+str(p.returncode)+' '+p.stdout+' '+p.stderr)
        data=T.read(out/'native.json');r=T.read(out/'runtime.json')
        errs=runtime_errors(r,dict(main_pid=data['root_pid'],process_create_filetime=next(v['created'] for v in data['processes'] if v['pid']==data['root_pid'])))
        if p.returncode or data['rc'] or errs or not data['job_total_valid'] or data['TotalProcesses']<3:raise ValueError('native tree/selfcheck failed: '+str(errs))
        data['process_accounting']=A.process_accounting(data['processes'],data['TotalProcesses'])
        results.append(dict(native=data,internal=r,command=cmd))
    if (results[0]['internal']['main_pid'],results[0]['internal']['process_create_filetime'])==(results[1]['internal']['main_pid'],results[1]['internal']['process_create_filetime']):raise ValueError('selfcheck root instance reused')
    T.save(root/'selfcheck.json',dict(valid=True,runs=results,note='Fresh empty Jobs, exited child and grandchild; retained process snapshots. No equality asserted across different boundaries.'))
    shutil.copytree(folder,root/'01_计量自检_selfcheck')

def prove(cfg,rtl,net,work,out):
    check_post_abc_model(net,'test4')
    work.mkdir(parents=True);netcopy=work/'post_abc.il';shutil.copy2(net,netcopy)
    model=VALIDATION/'runner/form_cells_cycloneiv.v'
    config=R.make_cfg(R.rtl_side_prelude(rtl,'test4'),R.net_side_prelude_mapped(netcopy,'test4',model))
    configpath=work/'verify.eqy';configpath.write_text(config,encoding='utf-8')
    rc=F.setup_eqy(configpath,work/'work',work/'setup.log',yosys=cfg['tools']['yosys']['path'],abc=cfg['tools']['abc']['path'],eqy=cfg['tools']['eqy']['path'],timeout_s=600,jobs=1)
    summary=dict(state='TOOL_OR_CONFIG_ERROR',setup_rc=rc)
    if rc==0:
        dirs=sorted((work/'work/strategies').glob('*/*'))
        parts={str(d.relative_to(work/'work')):R.run_strategy(d,yosys=cfg['tools']['yosys']['path']) for d in dirs if d.is_dir()}
        summary=R.aggregate_partitions(parts);summary['parts']=parts
    T.save(work/'summary.json',summary);shutil.copytree(work,out)
    if summary['state']!='PASS':raise ValueError('RTL-to-post_abc proof '+summary['state'])
    return summary

def report(root,rows,error,captures,proofs):
    pairs=A.pairs(rows);T.save(root/'paired_differences.json',pairs);dump_csv(root/'paired_differences.csv',pairs)
    stats={}
    for group in A.GROUPS:
        stats[group]={}
        for role in ('A','B'):
            selected=[r for r in rows if r['group']==group and r['role']==role]
            stats[group][role]={key:A.describe([r.get(key) for r in selected]) for key in ('cpu','cpu_user','cpu_kernel','wall_qpc')}
    T.save(root/'statistics.json',stats)
    raw=[{k:r.get(k) for k in ('index','group','pair','role','side','skip','cpu_user','cpu_kernel','cpu','wall_qpc','qpc_frequency','process_complete','root_cpu','abc_cpu','helper_cpu','outer_minus_process_ticks','outer_minus_inner_ticks','pass_cpu_ticks','pass_wall_qpc')} for r in rows]
    dump_csv(root/'raw_sequence.csv',raw)
    lines=['# test4 CPU波动来源诊断','',f'算法：`{COMMIT}`。诊断已取得 {len(rows)}/100 个计时样本。',
        '状态：'+('固定计时完成' if len(rows)==100 and not error else '未完成：'+str(error)),
        '诊断均值、中位数和重复运行不用于正式评分；正式失败记录保持原样。','',
        '## 1. 同程序与版本对照','', '| 组 | 完整对数 | >+5% | <−5% | A CPU范围(ms) | B CPU范围(ms) |','|---|---:|---:|---:|---|---|']
    aa_cross=0
    for group in A.GROUPS:
        pp=[p for p in pairs if p['group']==group];s=stats[group];fmt=lambda v: '缺测' if not v['count'] else f"{v['minimum']/10000:.4f}～{v['maximum']/10000:.4f}"
        plus=sum(p['above_plus_5pct'] is True for p in pp);minus=sum(p['below_minus_5pct'] is True for p in pp)
        if group.endswith('_aa'):aa_cross+=plus+minus
        lines.append(f"| {group} | {len(pp)} | {plus} | {minus} | {fmt(s['A']['cpu'])} | {fmt(s['B']['cpu'])} |")
    lines+=['',f'同程序 A/A 跨 ±5% 共 {aa_cross} 对。'+('同程序波动已足以影响单次5%判定，不能把版本差值全部解释为算法成本。' if aa_cross else '本批尚未观察到同程序跨线；不保证任意机器或后续单次运行稳定。'),
        '逐对原始顺序、整数和差值见 raw_sequence.csv、paired_differences.csv；未剔除异常值。','',
        '## 2. 整数离散','', '| 组/侧 | 用户态公约步长 | 内核态公约步长 | 总量公约步长 | 总量最小正差 |','|---|---:|---:|---:|---:|']
    for group in A.GROUPS:
        for role in ('A','B'):
            s=stats[group][role];lines.append(f"| {group}/{role} | {s['cpu_user']['observed_gcd_ticks']} | {s['cpu_kernel']['observed_gcd_ticks']} | {s['cpu']['observed_gcd_ticks']} | {s['cpu']['minimum_positive_gap_ticks']} |")
    lines+=['','单位为原始100ns计数；公约步长及重复值是本批观测，不是计时精度保证。',
        '', '## 3. 进程与阶段归因','',
        f"逐进程CPU计数覆盖完整 {sum(r.get('process_complete',False) for r in rows)}/{len(rows)}；这不等于映像和父PID元数据完整。缺读保留null及错误，未知身份不归入辅助进程。", 
        '外部Job在全部退出后读，内部Job在正式退出前快照读；二者残差包括输出和退出尾段，不能强制归零。ABC已包含在Job中，只作分项。',
        '每个 record.json 保留 Yosys、各ABC、实际辅助进程CPU、父PID、创建时间、阶段CPU和墙钟。模块列表标为观察到的集合，不能假称穷尽全部DLL。',
        '阶段比较见 stage_differences.json；若读数为零或只有一个离散步长，表示未分辨，不表示没有工作。']
    stages=[]
    for group in A.GROUPS[3:]:
        for pair in range(1,11):
            rr={r['role']:r for r in rows if r['group']==group and r['pair']==pair}
            if set(rr)!={'A','B'}:continue
            for a,b in zip(rr['A']['stages'],rr['B']['stages']):
                stages.append(dict(group=group,pair=pair,stage=a['stage'],A_root_ticks=a['root_ticks'],B_root_ticks=b['root_ticks'],delta_root_ticks=b['root_ticks']-a['root_ticks'],A_wall_qpc=a['wall_qpc'],B_wall_qpc=b['wall_qpc']))
    T.save(root/'stage_differences.json',stages);dump_csv(root/'stage_differences.csv',stages)
    lines+=['','## 4. test4 pass自身开销','', '| 模式 | 原始CPU整数序列 | 范围(ms) |','|---|---|---|']
    for skip in (False,True):
        values=[r.get('pass_cpu_ticks') for r in rows if r['group']=='stage_pass_on_off' and r['skip']==skip];valid=[v for v in values if type(v)is int]
        lines.append(f"| {'跳过' if skip else '调用'} | {values} | "+(f'{min(valid)/10000:.4f}～{max(valid)/10000:.4f}' if valid else '缺测')+' |')
    lines+=['','调用/跳过还同时改变后续可能接收的网表，只有工件、资源和功能核对一致时，才能把差异解释为空pass成本。',
        '', '## 5. 原因与最小建议','',
        '先依据A/A跨线与整数步长判断分辨能力，再看逐进程及各阶段重复方向。机器环境、计量粒度和未解释残差不强行拼成100%。',
        '没有直接证据时保留“未归因”；不修改算法或降低日志级别来追求数字通过。',
        f'捕获综合 {len(captures)}/3；RTL到post_abc功能证明 {len(proofs)}/3。系统跟踪状态另见 trace/status.json。','']
    (root/'00_test4_CPU波动诊断报告.md').write_text('\n'.join(lines),encoding='utf-8')

def run():
    cfg,source,plan=preflight();guard()
    if plan.get('blocked'):raise ValueError(str(plan['blocked']))
    stamp=datetime.now().strftime('%Y-%m-%d_%H%M%S');root=PROJECT/'results/官方口径评测'/f'{stamp}_test4_CPU波动诊断_v2_6862831_第01轮';root.mkdir()
    print('DIAG_ROUND='+str(root),flush=True)
    protected=T.protected(PROJECT);T.save(root/'protected_before.json',protected)
    shutil.copytree(HERE,root/'diagnostic_code',ignore=shutil.ignore_patterns('__pycache__','*.exe'))
    work=PROJECT/'.tools/cpu-diag-v2-work'/uuid.uuid4().hex;work.mkdir(parents=True)
    env=P._build_env(cfg);env.update(TEMP=str(work),TMP=str(work),TMPDIR=str(work));os.environ.update(env)
    T.save(root/'environment.json',environment());T.save(root/'schedule.json',A.schedule())
    T.save(root/'context.json',dict(algorithm_commit=COMMIT,source_sha256=SOURCE,project_head=P._git(PROJECT,'rev-parse','HEAD'),work=str(work),diagnostic_only=True,plan=plan))
    rows=[];captures=[];proofs=[];error=None;elapsed=0.0;module_cache={};phase='prepare';tools={}
    try:
        # Existing matching tools are resolved without starting official run.
        ordinary=P.prepare_builtin(cfg,SOURCE,source_bytes=source)
        binaries={s:Path(ordinary['builtin'][s]['path']) for s in ('baseline','optimized')}
        abcpaths=ordinary['builtin']['abc'];tools['ordinary']=identity(binaries,abcpaths);T.save(root/'tools.json',tools);T.save(root/'tools_ordinary.json',tools['ordinary'])
        observer=compile_observer(cfg,work);T.save(root/'observer_identity.json',dict(source_sha256=T.sha(HERE/'observer.cc'),exe_sha256=T.sha(observer)))
        guard();selfcheck(cfg,observer,work,env,root)
        rtl=work/'test4.v';rtl.write_bytes((VALIDATION/'suite-official4/tree/pmux_case/competition_case/test4/test4.v').read_bytes())
        flow=B.gen_builtin_synth_ys(rtl,'test4');references={}
        def perform(item,exe,side,skip=False,capture=False):
            nonlocal elapsed
            guard()
            remaining=1800-elapsed
            if remaining<=0:raise TimeoutError('30 minute cumulative diagnostic runtime protection')
            name=(f"capture_{side}_{'off' if skip else 'on'}" if capture else f"{item['index']:03d}_{item['group']}_{item['pair']:02d}_{item['role']}")
            out=root/('03_捕获_capture' if capture else '02_原始样本_samples')/name;out.mkdir(parents=True)
            script=B.gen_builtin_formal_ys(rtl,'test4') if capture else flow
            (out/'flow.ys').write_text(script,encoding='utf-8')
            current=dict(env)
            for k in list(current):
                if k.startswith(('PMUX_CPU_DIAG','PMUX_DIAG_V2')):current.pop(k)
            isstage=bool(capture or item['group'].startswith('stage_'))
            if isstage:current.update(PMUX_DIAG_V2_JSON='diag.json',PMUX_DIAG_V2_SKIP_PASS='1' if skip else '0',PMUX_DIAG_V2_KEEP_ABC='1' if capture else '0')
            cmd=[str(observer),str(out/'native.json'),str(out/'run.log'),str(out),str(int(remaining*1000)),str(exe),'-s','flow.ys','--runtime-json','runtime.json']
            row=dict(item or {},side=side,skip=skip,capture=capture,exe=str(exe),command=cmd,target_command=cmd[5:],cwd=str(out),
                flow_sha256=T.sha(out/'flow.ys'),input_sha256=T.sha(rtl),tools_manifest=('tools_diagnostic.json' if isstage else 'tools_ordinary.json'),tools_manifest_sha256=T.sha(root/('tools_diagnostic.json' if isstage else 'tools_ordinary.json')),
                environment_overrides={k:v for k,v in current.items() if env.get(k)!=v},cache_state='UNKNOWN; prior operations in context and sequence; no dedicated warmup')
            T.save(out/'launch.json',row)
            t=time.monotonic()
            with (out/'observer.log').open('w') as log:
                p=subprocess.run(cmd,env=current,stdout=log,stderr=subprocess.STDOUT,timeout=remaining+15)
            elapsed+=time.monotonic()-t
            native=T.read(out/'native.json');row['native']=native
            row['module_fingerprints']=collect_modules(native,current,module_cache)
            if p.returncode or native['rc'] or not native['job_total_valid'] or native['timed_out']:raise ValueError('ordinary diagnostic launch invalid')
            rootproc=next(r for r in native['processes'] if r['pid']==native['root_pid'])
            r=T.read(out/'runtime.json');errors=runtime_errors(r,dict(main_pid=native['root_pid'],process_create_filetime=rootproc['created']))
            if errors:raise ValueError('internal CPU record invalid: '+str(errors))
            row['runtime']=r;row.update(cpu_user=r['cpu_user_ticks'],cpu_kernel=r['cpu_kernel_ticks'],cpu=r['cpu_total_ticks'],
                wall_qpc=native['job_empty_qpc']-native['resume_qpc'],qpc_frequency=native['qpc_frequency'])
            accounting=A.process_accounting(native['processes'],native['TotalProcesses']);row['process_accounting']=accounting
            row['process_complete']=accounting['complete'] and native['process_accounting_complete']
            row['root_cpu']=rootproc['user']+rootproc['kernel'] if rootproc['user'] is not None and rootproc['kernel'] is not None else None
            abc=[r for r in native['processes'] if Path(r['image']).name.lower() in ('yosys-abc.exe','abc.exe')]
            helper=[r for r in native['processes'] if r is not rootproc and r not in abc]
            row['abc_cpu']=sum(r['user']+r['kernel'] for r in abc) if abc and all(r['user'] is not None and r['kernel'] is not None for r in abc) else None
            row['helper_cpu']=sum(r['user']+r['kernel'] for r in helper) if row['process_complete'] else None
            row['outer_minus_process_ticks']=native['user']+native['kernel']-accounting['sum_ticks'] if accounting['complete'] else None
            row['outer_minus_inner_ticks']=native['user']+native['kernel']-row['cpu']
            sig=resource_signature(out/'stat.json');row['resource_signature']=sig
            refkey=side
            if refkey in references and references[refkey]!=sig:raise ValueError('test4 resources changed')
            references.setdefault(refkey,sig)
            text=(out/'run.log').read_text(encoding='utf-8',errors='replace')
            count=text.count('Executing PMUX_OPT')
            if count!=(1 if side=='optimized' and not skip else 0):raise ValueError('whole-pass execution/skip mismatch')
            if isstage:
                diag=T.read(out/'diag.json');row['diagnostic']=diag
                diag=A.normalize_abc(diag,native);row['diagnostic']=diag
                if not diag['valid'] or diag['skip_pass']!=skip:raise ValueError('stage diagnostics invalid')
                final=diag['marks'][-1]
                if final['job_user']!=row['cpu_user'] or final['job_kernel']!=row['cpu_kernel']:raise ValueError('stage/final formal CPU boundary mismatch')
                if not capture:
                    row['stages']=A.partition(diag['marks']);slot=next(r for r in row['stages'] if r['stage']=='整个pass槽位')
                    row['pass_cpu_ticks']=slot['root_ticks'];row['pass_wall_qpc']=slot['wall_qpc']
                if capture:
                    row['artifacts']=[]
                    for call in diag['abc']:
                        src=Path(call['tempdir']);dst=out/'abc_artifacts'/f"call{call['id']:02d}";shutil.copytree(src,dst)
                        row['artifacts'].append(dict(call_id=call['id'],files={p.relative_to(dst).as_posix():T.sha(p) for p in dst.rglob('*') if p.is_file()}))
            row.update(A.classify_processes(native,(row.get('diagnostic') or {}).get('abc',[])))
            T.save(out/'record.json',row);return row
        phase='ordinary_controls'
        for item in A.schedule()[:60]:
            side='baseline' if item['group']=='baseline_aa' or (item['group']=='baseline_optimized' and item['role']=='A') else 'optimized'
            row=perform(item,binaries[side],side);rows.append(row);T.save(root/'timing_records.json',rows)
            print(f"TIMING {len(rows)}/100 {item['group']} pair{item['pair']} {item['role']} cpu={row['cpu']} process_complete={row['process_complete']}",flush=True)
        phase='diagnostic_build';guard();diagtools=T.prepare(cfg,source,root);tools['diagnostic']=diagtools;T.save(root/'tools.json',tools);T.save(root/'tools_diagnostic.json',diagtools)
        phase='capture_and_proof'
        for side,skip in (('baseline',False),('optimized',False),('optimized',True)):
            capture=perform({},Path(diagtools[side]['yosys']),side,skip,capture=True);captures.append(capture);T.save(root/'captures.json',captures)
            out=Path(capture['cwd']);proof=prove(cfg,rtl,out/'post_abc.il',work/f'proof_{side}_{skip}',root/'04_功能证明_formal'/f'{side}_{skip}')
            proofs.append(proof);T.save(root/'proofs.json',proofs)
            print('CAPTURE_AND_PROOF '+side+' '+str(skip)+' PASS',flush=True)
        if captures[1]['resource_signature']!=captures[2]['resource_signature']:raise ValueError('pass on/off resource difference; cannot interpret as empty pass')
        phase='stage_timing';T.save(root/'stage_environment.json',environment())
        for item in A.schedule()[60:]:
            side='baseline' if item['group']=='stage_baseline_optimized' and item['role']=='A' else 'optimized'
            skip=item['group']=='stage_pass_on_off' and item['role']=='B'
            row=perform(item,Path(diagtools[side]['yosys']),side,skip);rows.append(row);T.save(root/'timing_records.json',rows)
            print(f"TIMING {len(rows)}/100 {item['group']} pair{item['pair']} {item['role']} cpu={row['cpu']} pass={row['pass_cpu_ticks']}",flush=True)
    except Exception as exc:
        import traceback
        error=repr(exc);T.save(root/'exception.json',dict(error=error,traceback=traceback.format_exc()));print('DIAG_ERROR='+error,flush=True)
    finally:
        after=T.protected(PROJECT);T.save(root/'protected_after.json',after)
        T.save(root/'protected_verification.json',dict(unchanged=protected==after,changed=[k for k in set(protected)|set(after) if protected.get(k)!=after.get(k)]))
        final=A.completion_status(len(rows),error,protected==after);error=final['error']
        T.save(root/'status.json',dict(diagnostic_only=True,phase=phase,timing_runs=len(rows),capture_runs=len(captures),proofs=len(proofs),runtime_seconds=elapsed,**final))
        report(root,rows,error,captures,proofs)
        needs_trace=bool(rows and (any(not r.get('process_complete') for r in rows) or any(r.get('outer_minus_process_ticks') not in (None,0) for r in rows) or len(rows)==100))
        T.save(root/'trace/status.json',dict(required=needs_trace,state='PENDING' if needs_trace else 'NOT_RUN',reason='unresolved process residuals/short stages; trace is attribution only'))
        T.seal(root)
        print('DIAG_REPORT='+str(root/'00_test4_CPU波动诊断报告.md'),flush=True)
    return 0 if not error and len(rows)==100 else 1

def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=('plan','run','analyze'));ap.add_argument('--round',type=Path);args=ap.parse_args()
    if args.action=='plan':
        cfg,source,plan=preflight();print(json.dumps(dict(commit=COMMIT,source_sha256=SOURCE,diagnostic_only=True,timing_runs=100,capture_runs=3,ordinary_plan=plan,active_tasks=busy()),ensure_ascii=False,indent=2));return 0
    if args.action=='analyze':
        if not args.round:ap.error('--round required')
        # Print only; sealed evidence is not overwritten by reanalysis.
        print(json.dumps(A.pairs(T.read(args.round/'timing_records.json')),ensure_ascii=False,indent=2));return 0
    return run()

if __name__=='__main__':sys.exit(main())
