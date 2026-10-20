"""Windows-only, fixed 8 capture + 40 stage runs; never grades official results."""
import argparse
import csv
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
PROJECT=HERE.parents[1]
VALIDATION=PROJECT/'scripts/pmux_validation'
sys.path.insert(0,str(VALIDATION));sys.path.insert(0,str(VALIDATION/'runner'))
import validate as official
import prepare_builtin as P
import builtin_common as B
from measure_v4 import resource_signature
import analysis as A
import build
import launcher

COMMIT='b87e3ab3ad475ef581a1fc09ebd365c0e2d0e59a'
CASES=('test1','test2','test3','test4')
REFERENCES=[PROJECT/f'results/官方口径评测/2026-10-13_{t}_Windows单次内部计时_v6_b87e3ab_第01轮' for t in ('1730','1750','1814')]

def save(path,data):build.save(path,data)
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))

def preflight(commit):
    if commit!=COMMIT:raise ValueError('this diagnostic is pinned to '+COMMIT)
    cfg,source=official.preflight(commit)
    refs=[];identities=[];reference_flows=[];reference_resources=[]
    for root in REFERENCES:
        c=read(root/'validation_context.json');m=read(root/'11_汇总与证据_summary/manifest.json')
        if c['target_commit']!=commit or c['source_sha256']!=hashlib.sha256(source).hexdigest():raise ValueError('reference algorithm mismatch')
        for side in ('baseline','optimized'):
            if build.sha(c['builtin'][side]['path'])!=c['builtin'][side]['binary_sha256']:raise ValueError('reference binary changed')
        ident=[c['builtin'][s]['binary_sha256'] for s in ('baseline','optimized')]+[c['suite_manifest_sha256']]
        identities.append(ident)
        flows={};resources={}
        for case in CASES:
            frozen=VALIDATION/f'suite-official4/tree/pmux_case/competition_case/{case}/{case}.v'
            for side in ('baseline','optimized'):
                folder=root/f'09_时间内存开销_performance/round01/{case}/cpu/{side}'
                flow=(folder/'flow.ys').read_text(encoding='utf-8')
                line=next(v for v in flow.splitlines() if v.startswith('read_verilog -sv '))
                input_path=Path(line[len('read_verilog -sv '):].strip().strip('"'))
                if official.digest_package_file(input_path)!=official.digest_package_file(frozen):raise ValueError('reference actual input mismatch')
                flows[case+':'+side]=flow.replace('\\','/').replace(c['ascii_bridge'].replace('\\','/'),'<BRIDGE>')
                resources[case+':'+side]=resource_signature(folder/'stat.json')
                if resources[case+':'+side]!=resource_signature(root/f'05_公开四例_public/round01/{case}/{side}/stat.json'):
                    raise ValueError('reference performance/public resource mismatch')
        reference_flows.append(flows);reference_resources.append(resources)
        refs.append(dict(root=str(root),algorithm_commit=c['target_commit'],source_sha256=c['source_sha256'],
                         binary_identity=ident,verification_verdict=m['verification_verdict'],
                         performance=[{k:r[k] for k in ('case','base_cpu_s','opt_cpu_s','cpu_overhead_pct')} for r in m['performance']]))
    if any(i!=identities[0] for i in identities):raise ValueError('three reference identities differ')
    if any(v!=reference_flows[0] for v in reference_flows) or any(v!=reference_resources[0] for v in reference_resources):
        raise ValueError('three reference actual flows/resources differ')
    for ref in refs:ref.update(actual_inputs_checked=True,actual_flows_match=True,actual_resources_match=True)
    return cfg,source,refs

def selfcheck(cfg,tool,root,env):
    out=root/'01_selfcheck';out.mkdir()
    cache=Path(tool['cache']);exe=cache/'nested_probe.exe'
    with (out/'compile.log').open('w') as log:
        subprocess.run([cfg['tools']['compiler']['path'],'-O2',str(HERE/'nested_probe.cc'),'-o',str(exe)],
                       env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
    execute=launcher.load(PROJECT)
    native=execute([str(exe)],cwd=out,log_path=out/'probe.log',timeout_s=30,env=env)
    save(out/'native.json',native)
    data=read(out/'probe.json')
    if native['rc'] or not native['metrics_valid'] or data['valid'] is not True:raise ValueError('nested/shared-memory selfcheck failed')
    if data['pid']!=native['main_pid'] or data['created']!=native['process_create_filetime']:raise ValueError('selfcheck root identity mismatch')
    children=data['children']
    if len(children)!=2 or {r['call_id'] for r in children}!={1,2} or any(r['ready']!=2 or r['shared_total_ticks']>r['after_exit_total_ticks'] for r in children):raise ValueError('selfcheck child CPU records invalid')
    unique={(data['pid'],data['created'])}|{(r['pid'],r['created']) for r in children}
    if len(unique)!=3:raise ValueError('selfcheck explicit process identity count invalid')
    data.update(native=native,unique_process_instances=len(unique),
                nested_count_difference=native['job_total_processes']-data['final_inner_processes'],
                note='Three explicitly created instances; live snapshots identify possible helpers. Root assigned outer then inner; do not equate Job total count with explicit creates.')
    save(out/'selfcheck.json',data)
    return data

def report(root,rows,captures,selftest,complete,error):
    q=A.observed_quantum(rows) if rows else None
    lines=['# CPU阶段归因诊断结果','',
        '诊断不用于正式评分。'+('固定8次捕获、40次计时完成。' if complete else '诊断未完成：'+str(error)),
        '算法提交：`'+COMMIT+'`。既有正式v6及三轮结论保持原样。',
        f'观测到的计数公约步长：{q/10000 if q else "未取得"} ms；这不是绝对精度保证。',
        '所有差值为优化版−原版，毫秒；不平均、不取中位数、不计算统计区间。ABC是ABC9的子项，不重复加入全流程总和。',
        'main_entry是在主函数入口读取进程已累计CPU；读取前的少量诊断调用也在该边界前。最终CPU快照不含JSON输出及OS最后退出尾段。',
        '', '## 计量自检','',
        f'受控程序显式创建根进程及两个顺序子进程，共{selftest.get("unique_process_instances")}个不同实例；内部Job {selftest.get("final_inner_processes")}，外部Job {(selftest.get("native") or {}).get("job_total_processes")}。',
        '受控自检保存创建后实际进程清单、映像路径和根进程归属操作；额外计数需结合辅助进程及嵌套归属解释，不能只按显式创建次数判无效。CPU残差仍独立记录，不据进程数修正CPU。',
        '', '## 八次捕获与资源核对','',
        '| 用例 | 侧 | ABC调用数 | 资源匹配 | 输入SHA-256 | 规范化脚本SHA-256 |','|---|---|---:|---|---|---|']
    for r in captures:
        artifacts=r.get('artifacts') or []
        lines.append('| {} | {} | {} | {} | {} | {} |'.format(r['case'],r['side'],len(r['diagnostic']['abc']),r['resource_match'],
            ', '.join(v['input_sha256'][:16] for v in artifacts),', '.join(v['script_normalized_sha256'][:16] for v in artifacts)))
    clues=[];differences=[]
    for case in CASES:
        pairs=[]
        for pair in range(1,6):
            both={r['side']:r for r in rows if r['case']==case and r['pair']==pair}
            if set(both)!= {'baseline','optimized'}:continue
            b,o=both['baseline']['accounting'],both['optimized']['accounting']
            delta=[o['pre_main_root_ticks']-b['pre_main_root_ticks']]
            delta+=[x['root_ticks']-y['root_ticks'] for x,y in zip(o['stages'],b['stages'])]
            delta+=[o['abc_process_ticks']-b['abc_process_ticks'],o['abc_pre_entry_ticks']-b['abc_pre_entry_ticks'],o['abc_main_body_ticks']-b['abc_main_body_ticks'],o['job_final_ticks']-b['job_final_ticks']]
            names=('主函数入口前',)+A.STAGE_NAMES+('ABC进程自身','ABC主算法前','ABC主函数体','内部Job总量')
            base=[b['pre_main_root_ticks']]+[v['root_ticks'] for v in b['stages']]+[b['abc_process_ticks'],b['abc_pre_entry_ticks'],b['abc_main_body_ticks'],b['job_final_ticks']]
            opt=[o['pre_main_root_ticks']]+[v['root_ticks'] for v in o['stages']]+[o['abc_process_ticks'],o['abc_pre_entry_ticks'],o['abc_main_body_ticks'],o['job_final_ticks']]
            for name,bt,ot in zip(names,base,opt):
                differences.append(dict(case=case,pair=pair,stage=name,baseline_ticks=bt,optimized_ticks=ot,
                                        delta_ms=(ot-bt)/10000,overhead_pct=(ot-bt)/bt*100 if bt>0 else None))
            pairs.append((pair,delta,b,o))
        lines+=['',f'## {case} 五对绝对差值','',
            '| 对 | 主函数入口前 | 启动读取 | 前段综合 | 边界间隔 | PMUX槽位 | ABC前准备 | ABC9主进程 | 剩余收尾 | ABC进程自身 | ABC主算法前 | ABC主函数体 | 内部Job总量 |',
            '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
        for pair,delta,b,o in pairs:lines.append('| '+str(pair)+' | '+' | '.join(f'{v/10000:.4f}' for v in delta)+' |')
        lines+=['','| 阶段 | 差值范围(ms) | 正/零/负对数 | 解释 |','|---|---|---|---|']
        names=('主函数入口前',)+A.STAGE_NAMES+('ABC进程自身','ABC主算法前','ABC主函数体','内部Job总量')
        for i,name in enumerate(names):
            values=[d[i] for _,d,_,_ in pairs]
            if not values:continue
            pos=sum(v>0 for v in values);neg=sum(v<0 for v in values);zeros=len(values)-pos-neg
            # Direction alone is not proof: a one-quantum effect remains unresolved.
            observed=[v for v in differences if v['case']==case and v['stage']==name]
            bs=[v['baseline_ticks'] for v in observed];os_=[v['optimized_ticks'] for v in observed]
            hint=A.directional_clue(values,bs,os_,q)
            reason=('至少4对同向，但范围重叠，尚未证实稳定' if hint['overlap'] else '至少4对同向，仅作调查线索') if hint['clue'] else '分辨能力不足（单步/零值/范围重叠）' if hint['small'] or zeros>=3 or hint['overlap'] else '方向不稳定'
            lines.append(f'| {name} | {min(values)/10000:.4f}～{max(values)/10000:.4f} | {pos}/{zeros}/{neg} | {reason} |')
            if i<len(names)-1 and hint['clue']:clues.append(dict(case=case,stage=name,direction=hint['direction'],overlap=hint['overlap'],confirmed=False))
        lines+=['','| 对 | 原版外部−内部Job(ms) | 优化版外部−内部Job(ms) | 原版内部−主进程−ABC(ms) | 优化版内部−主进程−ABC(ms) |','|---|---:|---:|---:|---:|']
        for pair,delta,b,o in pairs:
            lines.append('| {} | {:.4f} | {:.4f} | {:.4f} | {:.4f} |'.format(pair,b['outer_minus_inner_ticks']/10000,o['outer_minus_inner_ticks']/10000,b['inner_minus_root_abc_ticks']/10000,o['inner_minus_root_abc_ticks']/10000))
    lines+=['','## 结论与限制','',
        ('已发现重复方向的调查线索，但未确证持续增耗。' if clues else '现有CPU读数不足以确证哪个阶段持续增加开销。')+'调查线索：'+('；'.join(c['case']+' '+c['stage']+' '+c['direction']+('（范围重叠）' if c['overlap'] else '') for c in clues) if clues else '没有满足重复方向及非单步差值的阶段。'),
        '阶段为零只说明未分辨出CPU时间，不代表阶段没有工作。主进程阶段、ABC进程和Job采用不同读取边界；残差可能包含命令解释器、进入主函数前CPU、ABC/根进程输出及退出尾段和计量粒度，不强制归零。',
        '至少4对同向只提示调查顺序；两侧范围重叠或读数离散时不能认定稳定增耗。未增加样本，未修改算法。',
        '下一步仅根据上述线索选择具体对象；没有明确线索时保留尚不能定位，不自动启动高频跟踪或循环放大。','']
    lines+=['各阶段相对差见paired_differences.csv/JSON；基线为0时不计算百分比。',
            'ABC主算法前是进入Abc_RealMain之前的累计CPU，包括加载、运行库初始化及少量诊断共享连接；ABC主函数体为入口至正常返回前差值。两者只拆分ABC自身总量，不再加入主进程阶段总和。',
            'main_entry的Job值0表示此时尚未建立该Job；归属后可带入此前累计CPU，因此Job−主进程的阶段差值不等于精确子进程CPU。',
            '根进程退出后CPU与最终内部快照的差值保存在accounting.root_exit_tail_ticks；它包含诊断JSON写入及根进程退出尾段。']
    save(root/'paired_differences.json',differences)
    if differences:
        with (root/'paired_differences.csv').open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(differences[0]));writer.writeheader();writer.writerows(differences)
    (root/'00_CPU阶段诊断结论.md').write_text('\n'.join(lines),encoding='utf-8')
    save(root/'analysis.json',dict(complete=complete,error=error,diagnostic_only=True,observed_quantum_ticks=q,clues=clues,
                                  conclusion='已取得调查线索，尚未确证持续增耗阶段' if clues else '现有CPU读数不足以确证持续增耗阶段',timing_runs=len(rows),capture_runs=len(captures)))

def run(cfg,source,refs):
    tool=build.prepare(cfg,source)
    parent=PROJECT/'results/官方口径评测';stamp=datetime.now().strftime('%Y-%m-%d_%H%M')
    for i in range(1,100):
        root=parent/f'{stamp}_CPU阶段归因诊断_v1_b87e3ab_第{i:02d}轮'
        try:root.mkdir();break
        except FileExistsError:continue
    else:raise ValueError('cannot create new diagnostic round')
    print('DIAG_ROUND='+str(root),flush=True)
    work=PROJECT/'.tools/cpu-diag-work'/uuid.uuid4().hex;work.mkdir(parents=True)
    inputs=work/'inputs';inputs.mkdir();tmp=work/'tmp';tmp.mkdir()
    env=P._build_env(cfg)
    for name in ('TEMP','TMP','TMPDIR'):env[name]=str(tmp).replace('\\','/')
    for name in ('PMUX_CPU_DIAG_JSON','PMUX_CPU_DIAG_KEEP_ABC','PMUX_CPU_DIAG_MAPPING'):env.pop(name,None)
    save(root/'references.json',refs);save(root/'tools.json',tool)
    code=root/'diagnostic_code';shutil.copytree(HERE,code,ignore=shutil.ignore_patterns('__pycache__'))
    input_identity={};flows={}
    for case in CASES:
        original=VALIDATION/f'suite-official4/tree/pmux_case/competition_case/{case}/{case}.v'
        target=inputs/(case+'.v');target.write_bytes(original.read_bytes().replace(b'\r\n',b'\n'))
        input_identity[case]=build.sha(target);flows[case]=B.gen_builtin_synth_ys(target,case)
    save(root/'context.json',dict(algorithm_commit=COMMIT,source_sha256=hashlib.sha256(source).hexdigest(),inputs=input_identity,
                                work=str(work),policy=dict(capture_runs=8,timing_runs=40,pairs=5,timeout_s=600),diagnostic_only=True))
    execute=launcher.load(PROJECT);rows=[];captures=[];selftest={};error=None;phase='selfcheck'
    def perform(case,side,pair,capture,timeout):
        out=root/('02_capture' if capture else '03_timing')/case/(side if capture else f'pair{pair:02d}_{side}')
        out.mkdir(parents=True);(out/'flow.ys').write_text(flows[case],encoding='utf-8')
        current=dict(env,PMUX_CPU_DIAG_JSON='diag.json',PMUX_CPU_DIAG_KEEP_ABC='1' if capture else '0')
        native=execute([tool[side]['yosys'],'-s','flow.ys'],cwd=out,log_path=out/'run.log',timeout_s=timeout,env=current)
        row=dict(case=case,side=side,pair=pair,capture=capture,native=native,evidence=str(out))
        save(out/'native.json',native)
        if native['rc'] or native['timed_out'] or not native['metrics_valid'] or native['root_debugged']:raise ValueError('ordinary diagnostic execution failed')
        data=read(out/'diag.json');row['diagnostic']=data;row['accounting']=A.validate(data,native)
        if data['keep_abc'] is not capture:raise ValueError('capture/timing mode mismatch')
        expected=resource_signature(REFERENCES[-1]/f'05_公开四例_public/round01/{case}/{side}/stat.json')
        row['resource_match']=resource_signature(out/'stat.json')==expected
        if not row['resource_match']:raise ValueError('diagnostic resources differ from official reference')
        if capture:
            artifacts=[]
            for call in data['abc']:
                temp=Path(call['tempdir']);dest=out/'abc_artifacts'/f'call{call["call_id"]:02d}'
                if not temp.is_dir():raise ValueError('ABC capture directory missing')
                shutil.copytree(temp,dest)
                files={p.relative_to(dest).as_posix():build.sha(p) for p in dest.rglob('*') if p.is_file()}
                script=(dest/'abc.script').read_text(encoding='utf-8').replace(call['tempdir'],'<ABC_TEMP>')
                artifacts.append(dict(call_id=call['call_id'],original_directory=str(temp),files=files,
                    input_sha256=files['input.xaig'],script_normalized_sha256=hashlib.sha256(script.encode()).hexdigest()))
            row['artifacts']=artifacts
        save(out/'record.json',row);return row
    try:
        selftest=selfcheck(cfg,tool,root,env)
        phase='capture'
        for case in CASES:
            for side in ('baseline','optimized'):
                captures.append(perform(case,side,0,True,120));print(f'CAPTURE {len(captures)}/8 {case} {side}',flush=True)
                save(root/'capture_records.json',captures)
        phase='timing';start=time.monotonic()
        for pair,case,side in A.schedule():
            remaining=600-(time.monotonic()-start)
            if remaining<=0:raise TimeoutError('ten minute diagnostic protection limit')
            rows.append(perform(case,side,pair,False,remaining));print(f'TIMING {len(rows)}/40 pair{pair} {case} {side}',flush=True)
            save(root/'timing_records.json',rows)
        if time.monotonic()-start>=600:raise TimeoutError('ten minute diagnostic protection limit')
    except Exception as exc:error=str(exc);print('DIAG_ERROR='+error,flush=True)
    complete=error is None and len(captures)==8 and len(rows)==40
    save(root/'status.json',dict(complete=complete,error=error,phase=phase,capture_runs=len(captures),timing_runs=len(rows),diagnostic_only=True))
    report(root,rows,captures,selftest,complete,error)
    files={p.relative_to(root).as_posix():build.sha(p) for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    save(root/'SHA256.json',files)
    print('DIAG_REPORT='+str(root/'00_CPU阶段诊断结论.md'),flush=True)
    return 0 if complete else 3

def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('plan','build','run'));parser.add_argument('commit')
    args=parser.parse_args();cfg,source,refs=preflight(args.commit)
    if args.action=='plan':
        hit=build.load(cfg,source)
        print(json.dumps(dict(commit=args.commit,diagnostic_only=True,build_required=hit is None,cache=hit['cache'] if hit else str(build.directory(cfg,source)),capture_runs=8,timing_runs=40,blocked=[]),ensure_ascii=False,indent=2));return 0
    if args.action=='build':build.prepare(cfg,source);return 0
    return run(cfg,source,refs)

if __name__=='__main__':sys.exit(main())
