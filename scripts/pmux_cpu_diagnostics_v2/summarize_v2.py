"""Versioned same-data correction and attribution; never runs a target."""
import argparse
from pathlib import Path
import json
import statistics
import sys
import shutil
import collections
import re
sys.path.insert(0,'D:/codex/0000_26qs/scripts/pmux_validation/runner')
import analysis_v2 as A
import tools_v2 as T

def ms(v):return v/10000
def span(v,divisor=10000):
    vals=[x for x in v if x is not None]
    return '未取得' if not vals else f'{min(vals)/divisor:.6f}～{max(vals)/divisor:.6f}'

def run(root):
    root=Path(root).resolve();version=5
    while (root/f'{version:02d}_同数据复核_analysis_v2').exists():version+=1
    out=root/f'{version:02d}_同数据复核_analysis_v2';out.mkdir(exist_ok=False)
    rows=T.read(root/'timing_records.json');derived=[];procrows=[];differences=[]
    trace=T.read(root/'trace/status.json')
    for r in rows:
        n=r['native'];d=dict(index=r['index'],group=r['group'],pair=r['pair'],role=r['role'],cpu=r['cpu'],cpu_user=r['cpu_user'],cpu_kernel=r['cpu_kernel'],outer_cpu=n['user']+n['kernel'])
        diag=A.normalize_abc(r['diagnostic'],n) if r.get('diagnostic') else None
        d.update(A.classify_processes(n,diag['abc'] if diag else []))
        d['process_sum']=A.process_accounting(n['processes'],n['TotalProcesses'])['sum_ticks']
        d['outer_minus_process_ticks']=d['outer_cpu']-d['process_sum'] if d['process_sum'] is not None else None
        d['outer_minus_inner_ticks']=d['outer_cpu']-d['cpu']
        d['wall_ms']=r['wall_qpc']/r['qpc_frequency']*1000
        d['native_identity_errors']=[{'pid':p['pid'],'created':p['created'],'image':p['image'],'ppid':p['ppid'],'error':p['read_error']} for p in n['processes'] if not p['image'] or not p['ppid']]
        if diag:
            d['abc']=diag['abc'];d['stages']=A.partition(diag['marks']);first=diag['marks'][0];last=diag['marks'][-1]
            d['entry_already_accumulated_cpu']=first['root_user']+first['root_kernel']
            d['entry_job_already_accumulated_cpu']=first['job_user']+first['job_kernel']
            d['root_at_formal_final']=last['root_user']+last['root_kernel']
            d['abc_lifetime_cpu']=sum(p['user']+p['kernel'] for p in diag['abc'])
            d['abc_before_entry_cpu']=sum(p['entry_user']+p['entry_kernel'] for p in diag['abc'])
            d['abc_body_cpu']=sum(p['body_end_user']+p['body_end_kernel']-p['entry_user']-p['entry_kernel'] for p in diag['abc'])
            d['abc_exit_tail_cpu']=d['abc_lifetime_cpu']-d['abc_before_entry_cpu']-d['abc_body_cpu']
            d['pass_wall_ms']=r['pass_wall_qpc']/r['qpc_frequency']*1000
            d['pass_cpu_ticks']=r['pass_cpu_ticks']
            d['inner_minus_root_final_abc']=d['cpu']-d['root_at_formal_final']-d['abc_lifetime_cpu']
        derived.append(d)
        for p in n['processes']:
            procrows.append(dict(index=r['index'],group=r['group'],pair=r['pair'],role=r['role'],pid=p['pid'],created=p['created'],ppid=p['ppid'] or None,image=p['image'] or None,user=p['user'],kernel=p['kernel'],error=p['read_error']))
    capture_info=[]
    for capture in T.read(root/'captures.json'):
        for call,artifact in zip(capture['diagnostic']['abc'],capture['artifacts']):
            folder=Path(capture['cwd'])/'abc_artifacts'/f"call{call['id']:02d}"
            script=(folder/'abc.script').read_text(encoding='utf-8').replace('\\','/')
            normalized=script.replace(call['tempdir'].replace('\\','/'),'<ABC_TEMP>')
            import hashlib
            capture_info.append(dict(side=capture['side'],skip=capture['skip'],input_sha256=artifact['files'].get('input.xaig'),script_normalized_sha256=hashlib.sha256(normalized.encode()).hexdigest()))
    T.save(out/'abc_capture_comparison.json',capture_info)
    pp=A.pairs(derived);stats={}
    for group in A.GROUPS:
        stats[group]={role:{k:A.describe([r.get(k) for r in derived if r['group']==group and r['role']==role],allow_signed=k=='outer_minus_process_ticks') for k in ('cpu','cpu_user','cpu_kernel','root_cpu','abc_cpu','helper_cpu','unknown_cpu','outer_minus_process_ticks')} for role in ('A','B')}
        for pair in range(1,11):
            both={r['role']:r for r in derived if r['group']==group and r['pair']==pair}
            if set(both)!={'A','B'}:continue
            for key in ('cpu','root_cpu','abc_cpu','helper_cpu','unknown_cpu','outer_minus_process_ticks','entry_already_accumulated_cpu','abc_lifetime_cpu','abc_before_entry_cpu','abc_body_cpu','abc_exit_tail_cpu','inner_minus_root_final_abc'):
                a,b=both['A'].get(key),both['B'].get(key)
                differences.append(dict(group=group,pair=pair,component=key,A_ticks=a,B_ticks=b,delta_B_minus_A_ticks=b-a if a is not None and b is not None else None))
    T.save(out/'derived_rows.json',derived);T.save(out/'statistics.json',stats);T.save(out/'component_differences.json',differences);T.save(out/'paired_differences.json',pp)
    sys.path.insert(0,str(Path(__file__).parent));from diagnose_v2 import dump_csv
    dump_csv(out/'processes.csv',procrows);dump_csv(out/'component_differences.csv',differences);dump_csv(out/'paired_differences.csv',pp)
    lines=['# test4 CPU波动诊断：同数据复核与当前结论','',
        '已完成固定100次计时、3次工件捕获及3条原始RTL→ABC9后/map_cells前功能证明。正式单次规则及原失败结论保持原样。',
        '**结论：同程序波动已足以影响5%单次判定；pass自身CPU低于本批读数分辨能力。系统跟踪已完成，支持继续调查计数离散、启动/加载和系统活动；没有证据把大幅总差值主要归给pmux_opt。各类边界有重叠，不能强行精确分摊成100%。**',
        '', '## 1. 同程序是否也大幅波动','', '| 对照 | >+5% | <−5% | A范围(ms) | B范围(ms) |','|---|---:|---:|---|---|']
    for group in A.GROUPS:
        pair=[p for p in pp if p['group']==group]
        lines.append(f"| {group} | {sum(p['above_plus_5pct'] is True for p in pair)}/10 | {sum(p['below_minus_5pct'] is True for p in pair)}/10 | {span([r['cpu'] for r in derived if r['group']==group and r['role']=='A'])} | {span([r['cpu'] for r in derived if r['group']==group and r['role']=='B'])} |")
    lines+=['','| 对照 | 逐对变化范围 | A先：跨±5%/中位变化 | B先：跨±5%/中位变化 |','|---|---|---|---|']
    for group in A.GROUPS:
        pair=[p for p in pp if p['group']==group]
        cells=[]
        for first in ('A','B'):
            selected=[p for p in pair if p['first']==first]
            count=sum(p['above_plus_5pct'] or p['below_minus_5pct'] for p in selected)
            cells.append(f"{count}/5；{statistics.median(p['overhead_pct'] for p in selected):.3f}%")
        lines.append(f"| {group} | {min(p['overhead_pct'] for p in pair):.3f}%～{max(p['overhead_pct'] for p in pair):.3f}% | {' | '.join(cells)} |")
    lines+=['','先后顺序子组各仅5对，观察到的方向并不一致，尚不能据此断定固定的冷启动或先后因果效应；缓存冷热仍为未知。',
        'A/B是固定角色；奇数对A先、偶数对B先。stage_pass_on_off中A=调用，B=跳过。完整原始序列、均值、中位数、样本标准差、范围和逐对差值保留在原始轮次及本目录JSON/CSV，不剔除异常值。',
        '', '## 2. 原始整数是否离散','']
    for k in ('cpu_user','cpu_kernel','cpu'):
        s=A.describe([r[k] for r in derived]);lines.append(f"- {k}：公约步长 {s['observed_gcd_ticks']}，最小正差 {s['minimum_positive_gap_ticks']}，差值公约步长 {s['observed_gap_gcd_ticks']} 个100ns计数。")
    normal=[r['cpu'] for r in derived[:60]];quant=A.describe(normal)['observed_gap_gcd_ticks'];median=statistics.median(normal)
    lines+=['',f'普通60次总量范围 {span(normal)} ms；观测步长 {quant/10000:.3f} ms；中位数的5%为 {median/10000*0.05:.6f} ms。本批一个观测步长已超过这个5%尺度。',
        '这证明本批读数呈离散形态，不证明某一种操作系统内部更新机制；100ns只是单位，不是实际精度。',
        '', '## 3. 变化来自哪里','', '| 组/角色 | Yosys退出后自身CPU(ms) | 已识别ABC(ms) | 已识别辅助(ms) | 未识别进程(ms) |','|---|---|---|---|---|']
    for group in A.GROUPS:
        for role in ('A','B'):
            rr=[r for r in derived if r['group']==group and r['role']==role]
            lines.append('| '+group+'/'+role+' | '+' | '.join(span([r[k] for r in rr]) for k in ('root_cpu','abc_cpu','helper_cpu','unknown_cpu'))+' |')
    cp=sum(r['process_cpu_complete'] for r in derived);meta=sum(bool(r['process_metadata_complete']) for r in derived)
    lines+=['',f'CPU句柄计数覆盖完整 {cp}/100，映像及父PID元数据完整 {meta}/100。未识别项单列，不能偷偷归给辅助进程或把ABC缺读当零。',
        f"外部Job−完整逐进程CPU合计范围 {span([r['outer_minus_process_ticks'] for r in derived])} ms；外部Job−内部正式快照范围 {span([r['outer_minus_inner_ticks'] for r in derived])} ms。负残差原样保留。",
        '两种残差含不同边界、计数更新及可能的归属差异；现有证据不能把它们直接叫作漏计或算法错误。外部Job在退出后读，内部快照不含记录输出和系统退出尾段。',
        '', '| 阶段诊断组/角色 | 入口已累计CPU(ms) | ABC入口前已累计(ms) | ABC主体CPU(ms) | ABC退出尾段(ms) |','|---|---|---|---|---|']
    for group in A.GROUPS[3:]:
        for role in ('A','B'):
            rr=[r for r in derived if r['group']==group and r['role']==role]
            lines.append('| '+group+'/'+role+' | '+' | '.join(span([r.get(k) for r in rr]) for k in ('entry_already_accumulated_cpu','abc_before_entry_cpu','abc_body_cpu','abc_exit_tail_cpu'))+' |')
    lines+=['','入口读数包含进入探针前已累计的进程CPU及少量入口操作，不能单凭它区分DLL加载、运行库初始化或具体函数。内部Job入口值也有已累计CPU，正式公式没有减掉它。ABC主体、入口前和尾段只是同一ABC总量的拆分，不能再叠加到Job总量。',
        '每对分段CPU、墙钟差异见原 stage_differences.csv；进程及入口拆分见本目录 component_differences.csv。两套视角不能重复相加。',
        '', '## 4. test4 pass自身消耗','', '| 模式 | CPU整数序列 | 槽位墙钟范围(ms) |','|---|---|---|']
    for role,label in (('A','调用'),('B','跳过')):
        rr=[r for r in derived if r['group']=='stage_pass_on_off' and r['role']==role]
        lines.append(f"| {label} | {[r['pass_cpu_ticks'] for r in rr]} | {span([r['pass_wall_ms'] for r in rr],1)} |")
    lines+=['','CPU读数全部为零表示没有分辨出来，不能称零开销。墙钟覆盖pass槽位及两端探针，不能换算为正式CPU评分。调用/跳过的test4最终资源一致；两侧原始RTL证明均PASS。',
        f"三份捕获的ABC输入指纹一致={len({r['input_sha256'] for r in capture_info})==1}；仅替换临时目录后的脚本指纹一致={len({r['script_normalized_sha256'] for r in capture_info})==1}。原始与规范化指纹见 abc_capture_comparison.json，不据一次差值修改算法。",
        '', '## 5. 有证据支持的原因与最小建议','',
        '1. 已证实同程序A/A多次跨5%，且CPU整数观测步长大于本批5%的时间尺度。这是当前单次判定容易变化的直接证据，未证明全部波动都由计量粒度造成。',
        '2. Yosys入口累计、ABC入口前/主体和辅助/未识别进程均存在变化；尚无证据把总差值主要归给pmux_opt扫描。pass槽位墙钟很短，现有CPU读数不足以测出其自身成本。',
        '3. 本轮最小修改限于修正审计记录：未知进程单列、父PID标签、保护状态、累计上限和清单封存。暂无证据支持为此修改算法。若继续降低真实耗时，优先单独评估启动依赖、ABC命令外壳和临时目录清理；这些属于公共流程，不能悄悄只改优化侧或删掉正式综合步骤。不要更改优先级、系统计时器或关闭安全软件。',
        '4. 正式验收仍一次，诊断不能保证任意机器的一次测量绝不波动；本轮不重跑正式验收，也不把诊断均值拿去改判。',
        '', '## 系统跟踪与限制','']
    lines+=[f"状态 {trace['state']}，实际跟踪目标 {trace.get('runs',0)}/10，ETL={trace.get('etl')}。",str(trace.get('error') or ''),
        '首次助手启动超时，目标0次；用户明确允许重启后，在独立retry02目录取得唯一一份ETL及固定10次运行，未重跑100次诊断。编码错误和投影配对列错误均修正后重分析同一份数据，失败分析保留。',
        '跟踪的TEMP实际使用用户C盘临时目录，100次诊断使用D盘独立工作目录；跟踪两侧内部一致，但这一区别限制了跨阶段绝对值比较，不能将跟踪数值替代先前样本。后续入口已修复TEMP继承，本轮不为此重采。',
        'MinGW Release没有提供兼容WPA的函数符号，本轮采样只归因到模块，不能声称已经定位到具体加载函数或算法函数。',
        '', '## 同数据修正与证据边界','',
        '此目录仅重分析既有100个样本，没有新增综合。旧报告与每个原始JSON保留。原版记录中的helper_cpu可能包含未识别进程，分类以此目录为准。',
        '本轮冻结诊断构建ABC JSON中ppid字段实际为Yosys root PID；本目录已明确映射为root_pid，实际ppid按native相同PID+创建时间读取，缺失为null。该元数据标签问题不改变保留句柄所得ABC CPU。',
        '原始报告的“完整逐进程记录”仅代表CPU计数覆盖，不能理解为全部元数据完整。后续代码已增加独立覆盖字段。C++输出字段命名修正发生在退出计量快照后的JSON写出，未改变计时逻辑；未为元数据修正追加构建或重测，实验二进制对应冻结代码和原指纹。',
        '保护文件核对结果见 protected_verification.json；正式验证脚本、算法源码、旧诊断入口未修改。实际执行代码保存在 diagnostic_code，跟踪代码另冻结在 trace/code。','']
    if trace.get('event_accounting_valid'):
        analysis=Path(trace['analysis_directory']);refs=T.read(analysis/'event_reference.json');details=T.read(analysis/'lifecycle_scheduling_faults.json');names=details['process_names']
        commands={r['pid']:r['raw_fields'].get('Command Line','') for r in details['process_lifecycles']}
        def role(p):
            name=names.get(str(p),'').lower()
            if 'yosys-abc.exe' in name:return 'ABC'
            if 'yosys.exe' in name:return 'Yosys'
            if 'conhost.exe' in name:return 'conhost'
            if 'cmd.exe' in name:return 'cmd清理' if 'rmdir ' in commands.get(p,'') else 'cmd启动ABC'
            return '未知'
        ev=collections.defaultdict(list);api=collections.defaultdict(list);module=collections.defaultdict(collections.Counter);hard=collections.Counter();comparison=[]
        for r in refs:
            for p in r['reference_processes']:ev[role(p['pid'])].append(p['cpu_us']/1000)
            for p in r['native']['processes']:api[role(p['pid'])].append((p['user']+p['kernel'])/10000)
            comparison.append(dict(pair=r['pair'],side=r['side'],internal_ticks=r['runtime']['cpu_total_ticks'],outer_ticks=r['native']['user']+r['native']['kernel'],event_ticks=r['cpu_reference_ticks'],delta_outer_minus_event_ticks=r['native']['user']+r['native']['kernel']-r['cpu_reference_ticks']))
        for row in T.read(analysis/'sampled_target_modules.json'):
            p=int(re.search(r'\(\s*(\d+)\s*\)',row[0])[1]);module[role(p)][row[3].strip()]+=int(row[1])
        for row in T.read(analysis/'hardfault_target_rows.json'):
            p=int(re.search(r'\(\s*(\d+)\s*\)',row[2])[1]);hard[role(p)]+=int(row[0])
        lines+=['','## 跟踪的定量发现（仅这10次，不用于评分）','',
            '10次根进程实例、完整后代树、线程退出尾段及DPC/ISR配对均通过既有严格事件读取器；Events Lost=0，Buffers Lost=0。导出另有非目标事件的格式告警，原日志保留，不声称所有系统元数据均无告警。',
            '', '| 进程类别 | 事件CPU范围(ms) | 同次GetProcessTimes范围(ms) |','|---|---|---|']
        for k in ('Yosys','ABC','cmd启动ABC','cmd清理','conhost'):lines.append(f'| {k} | {span(ev[k],1)} | {span(api[k],1)} |')
        lines+=['','事件CPU是调度累计并扣除中断的诊断参考，不能把它与WinAPI字段视为完全相同口径或正式评分替代。相同生命周期下两者离散程度明显不同；本批外部Job减事件全树CPU的差为 '+span([r['delta_outer_minus_event_ticks'] for r in comparison])+' ms。',
            '20次cmd启动中，一半执行ABC命令，一半执行 rmdir /s /q 清理ABC临时目录。身份来自本份ETL，不反填先前100次的未知进程。',
            '', '| 类别 | 采样权重前三模块（ms，非精确CPU） | 硬缺页总数 |','|---|---|---:|']
        for k in ('Yosys','ABC','cmd启动ABC','cmd清理','conhost'):
            top='；'.join(f'{name} {weight/1000:.3f}' for name,weight in module[k].most_common(3));lines.append(f'| {k} | {top} | {hard[k]} |')
        rootweight=sum(module['Yosys'].values());sysdiag=module['Yosys'].get('sysdiag.sys',0)
        lines+=['',f'Yosys进程的采样还记录到sysdiag.sys权重 {sysdiag/1000:.3f} ms，约占其采样权重 {sysdiag/rootweight*100 if rootweight else 0:.2f}%。这只是该驱动模块在目标进程上下文中出现的证据，不足以认定驱动异常，更不建议关闭安全软件。',
            '调度就绪/等待、软硬缺页和加载事件详见 trace 分析JSON及原ETL。等待和就绪记录为线程区间合计，可超过进程墙钟，不能直接加到CPU上。',
            '综合判断：实际启动、系统活动、ABC和命令辅助进程各有成本；本轮并未测出pmux_opt自身CPU。应先按计量离散及启动/公共流程调查，不能把单次超5%都归给算法，也不能声称真实开销已经降低。','']
        T.save(out/'trace_counter_comparison.json',comparison);T.save(out/'trace_component_ranges.json',dict(event_cpu_ms=dict(ev),process_api_cpu_ms=dict(api),sampled_module_weights_us={k:dict(v) for k,v in module.items()},hardfaults=dict(hard)))
    (out/'00_当前诊断结论与最小建议.md').write_text('\n'.join(lines),encoding='utf-8')
    shutil.copy2(__file__,out/'summarize_v2.py');T.save(out/'analysis_identity.json',dict(source_sha256=T.sha(__file__),analysis_sha256=T.sha(Path(__file__).parent/'analysis_v2.py'),raw_timing_records_sha256=T.sha(root/'timing_records.json'),additional_target_runs=0))
    T.seal(out);T.seal(root,preserve_previous=True)
    print(out/'00_当前诊断结论与最小建议.md')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--round',required=True,type=Path);args=ap.parse_args();run(args.round)
