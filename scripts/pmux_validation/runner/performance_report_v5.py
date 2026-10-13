"""Recompute v5 scores from ETW samples; intervals are diagnostic only."""
import json
import statistics
from cpu_statistics_v5 import SCHEME,METHOD,POLICY,analyse_cpu_runs,judge_cpu
from cpu_statistics import aa_is_healthy
from cpu_selfcheck_v5 import certificate_valid
from measure_v4 import memory_errors

def judge_case(summ,certificate_cache=None):
    cpu=summ.get('cpu_runs') or [];memory=summ.get('memory_runs') or []
    stats=analyse_cpu_runs(cpu);aa=analyse_cpu_runs(summ.get('aa_runs') or [],pairs_per_block=5)
    if summ.get('cpu_policy')!=POLICY or summ.get('performance_scheme')!=SCHEME:
        stats['valid']=False;stats['errors'].append('v5 policy or scheme mismatch')
    cert=summ.get('method_selfcheck') or {};fp=summ.get('selfcheck_fingerprint')
    key=json.dumps([cert,fp],sort_keys=True)
    cache=certificate_cache if certificate_cache is not None else {}
    if key not in cache:cache[key]=certificate_valid(cert,fp)
    qualified,qual_reason=cache[key]
    cpu_valid=stats['valid'] and aa['valid'] and qualified and summ.get('execution_complete') is True
    decision=judge_cpu(stats)
    if not cpu_valid:decision.update(cpu_verdict='INVALID',cpu_point_requirement_met=False)
    issues=[dict(index=i+1,side=r.get('side'),reasons=memory_errors(r)) for i,r in enumerate(memory) if memory_errors(r)]
    expected={(s,p) for s in ('baseline','optimized') for p in range(1,16)}
    mem_valid=len(memory)==30 and {(r.get('side'),r.get('pair')) for r in memory}==expected and not issues
    if any(r.get('performance_scheme')!=SCHEME for r in memory):mem_valid=False
    mb=mo=None
    if mem_valid:
        mb=statistics.median(r['yosys_peak_working_set_bytes'] for r in memory if r['side']=='baseline')
        mo=statistics.median(r['yosys_peak_working_set_bytes'] for r in memory if r['side']=='optimized')
    mem_over=(mo-mb)/mb*100 if mem_valid else None
    mem_ok=mem_valid and (mo-mb)*100<=mb*5
    b,o=stats['baseline_mean_s'],stats['optimized_mean_s'];valid=cpu_valid and mem_valid
    bits=dict(cpu_exempt_upstream_over_limit=b is not None and b>60,
              rss_exempt_upstream_over_limit=mb is not None and mb>2*1024**3,
              memory_metric='yosys_peak_working_set_bytes',memory_limit=2*1024**3)
    limit_ok=bool(valid and (o<=60 or bits['cpu_exempt_upstream_over_limit']) and (mo<=2*1024**3 or bits['rss_exempt_upstream_over_limit']))
    reasons=[];warnings=[]
    if not stats['valid']:reasons.append('事件CPU证据无效：'+'; '.join(stats['errors'][:8]))
    if not aa['valid']:reasons.append('A/A运行或事件证据无效；不使用部分样本')
    elif not aa_is_healthy(aa):warnings.append('A/A区间不含0：测量质量提示，不改变均值评分')
    if stats['valid'] and stats['ci95_pct'][0]<=5<stats['ci95_pct'][1]:warnings.append('CPU区间跨5%：波动提示，仍按均值评分')
    if not qualified:reasons.append('v5技术自检证据无效：'+str(qual_reason))
    if summ.get('execution_complete') is not True:reasons.append('2720次性能阶段未完整完成')
    if decision['cpu_verdict']=='FAIL':reasons.append('事件CPU平均相对开销超过5%')
    if not mem_valid:reasons.append('退出事件内存样本不完整或无效')
    elif not mem_ok:reasons.append('内存相对开销超过5%')
    if valid and not limit_ok:reasons.append('超出60s/2GB且原版未超限')
    return dict(decision,case=summ.get('case'),valid=valid,invalid_samples=issues,cpu_statistics=stats,
        aa_statistics=aa,quality_warnings=warnings,cpu_method_selfcheck_valid=qualified,
        cpu_ok=decision['cpu_verdict']=='PASS',mem_ok=mem_ok,mem_overhead_pct=mem_over,memory_valid=mem_valid,
        limit_ok=limit_ok,limit_bits=bits,base_cpu_s=b,opt_cpu_s=o,base_rss_kb=None,opt_rss_kb=None,
        base_memory_bytes=mb,opt_memory_bytes=mo,base_memory_mib=mb/1024**2 if mb is not None else None,
        opt_memory_mib=mo/1024**2 if mo is not None else None,
        **{'pass':bool(valid and decision['cpu_verdict']=='PASS' and mem_ok and limit_ok)},reasons=reasons)

def report_lines(judgments,selfcheck):
    lines=['## 事件CPU计分与辅助记录','',
           '每例事件CPU完整样本算术平均直接与5%比较；统计区间、A/A差异和墙钟时间只提示，不评分。Job计数原样保留为辅助记录，不作事件缺失时的回退。',
           '| 用例 | 事件CPU近似95%区间（提示） | Job均值前→后(s) | 墙钟均值前→后(s) | 测量质量提示 |',
           '|---|---|---|---|---|']
    for j in judgments:
        s=j['cpu_statistics'];lines.append('| {} | {} | {}→{} | {}→{} | {} |'.format(j['case'],s.get('ci95_pct'),
            s.get('baseline_job_mean_s'),s.get('optimized_job_mean_s'),s.get('baseline_wall_mean_s'),s.get('optimized_wall_mean_s'),
            '; '.join(j['quality_warnings']) or '无'))
    lines+=['','v5技术自检只核对事件完整性、身份和软件计算，不是±1个百分点精度保证；已有test2采集CPU影响证据不等同于四例完全无干扰。',
            '自检详情见10_验证工具自检_selfcheck/cpu_etw_v5及01_来源与环境_meta/cpu_etw_selfcheck.json。','']
    return lines
