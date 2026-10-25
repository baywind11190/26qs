"""V8 report: eight canonical samples supply every public-case result."""
import csv
import json
from pathlib import Path
import result_layout as L

from measure_v8 import CASES, SCHEME, METHOD, POLICY, evaluate_summary, sample_errors, sha, save
import builtin_common as B
import integration_profiles as I


def load(path, default):
    try: return json.loads(Path(path).read_text(encoding='utf-8-sig'))
    except (OSError, ValueError): return default


def build_report(root, output_root=None, chain_attempt='run01', stages_override=None):
    from report import row_functional_ok, judge_area, judge_delivery
    root = Path(root); dest = Path(output_root) if output_root else root
    out = dest / L.SUMMARY; out.mkdir(parents=True, exist_ok=True)
    ctx = load(root / 'validation_context.json', {})
    stages = stages_override if stages_override is not None else load(root / (L.META + '/stages.json'), [])
    pub_path = root / (L.PUBLIC + '/round01')
    public = load(pub_path / 'summary.json', {}).get('cases', [])
    fc = load(root / (L.FLOWCHECK + '/builtin_run01/builtin_flowcheck.json'), {})
    perf_path = root / (L.PERFORMANCE + '/round01')
    perf = load(perf_path / 'performance_summary.json', [])
    ledger = load(perf_path / 'synthesis_ledger.json', {})
    chains = load(root / f'{L.SELFCHECK}/chains/{chain_attempt}/chains_summary.json', [])
    samples = {}
    for case in CASES:
        for side in ('baseline', 'optimized'):
            row = load(pub_path / case / side / 'measure_result.json', None)
            if row is not None: samples[(case, side)] = row
    judgments = [evaluate_summary(p) for p in perf]
    gates = {}
    expected = {(c, s) for c in CASES for s in ('baseline', 'optimized')}
    expected_stages = {'build', 'formal_selfcheck', 'measurement_selfcheck', 'performance', 'flowcheck', 'public', 'chains'}
    stages_by = {s.get('name'): s for s in stages}
    gates['执行阶段完整'] = set(stages_by) == expected_stages and all(
        s.get('rc') == 0 and s.get('state') in ('COMPLETED', 'REUSED') for s in stages_by.values())
    gates['V8身份与规则位置'] = (ctx.get('performance_scheme') == SCHEME
        and ctx.get('same_run_policy') == POLICY and bool((ctx.get('policy_source') or {}).get('path')))
    gates['八次正式综合无补跑'] = (set(samples) == expected and ledger.get('expected_runs') == 8
        and ledger.get('attempted_runs') == ledger.get('started_runs') == ledger.get('completed_runs') == 8
        and ledger.get('execution_complete') is True and len(ledger.get('attempts', [])) == 8
        and len({r.get('sample_id') for r in samples.values()}) == 8)
    sample_issues = {c + '/' + s: sample_errors(row, require_outputs=True) for (c, s), row in samples.items()}
    gates['同进程时间内存与产物哈希完整'] = len(samples) == 8 and all(not issues for issues in sample_issues.values())
    copied = {(r.get('case'), r.get('side')): r for p in perf for r in p.get('samples', [])}
    gates['性能摘要对应正式原始记录'] = (len(perf) == 4 and copied == samples
        and {p.get('case') for p in perf} == set(CASES))
    attempts = {(a.get('case'), a.get('side')): a for a in ledger.get('attempts', [])}
    gates['调度账本对应正式记录'] = (set(attempts) == expected and all(
        attempts[k].get('sample_id') == samples[k].get('sample_id') for k in expected if k in samples))
    logs_ok = len(samples) == 8
    external_ok = len(samples) == 8
    for case in CASES:
        b, o = samples.get((case, 'baseline'), {}), samples.get((case, 'optimized'), {})
        external_ok = external_ok and bool(b.get('flow_sha256')) and b.get('flow_sha256') == o.get('flow_sha256')
        for side in ('baseline', 'optimized'):
            try:
                row = samples[(case, side)]
                log = (pub_path / case / side / 'run.log').read_text(encoding='utf-8', errors='replace')
                good = B.abc9_mapping_ok(log) and 'Loading plugin' not in log
                good = good and (I.check_calls(log, I.identity(ctx), require_export=True)['ok']
                                 if side == 'optimized' else 'Executing PMUX_OPT' not in log)
                logs_ok = logs_ok and good
                frozen = root / f'{L.ASSETS}/tree/pmux_case/competition_case/{case}/{case}.v'
                external_ok = external_ok and row.get('input_sha256') == sha(frozen)
                spec = ctx.get('builtin', {}).get(side, {})
                external_ok = external_ok and row.get('executable_sha256') == spec.get('binary_sha256')
            except (OSError, KeyError, ValueError):
                logs_ok = False; external_ok = False
    gates['相同输入脚本与工具身份'] = external_ok
    gates['本次日志的ABC9与PMUX调用和导出阶段'] = logs_ok and fc.get('all_ok') is True and fc.get('analysis_only') is True
    evidence = load(root / (L.META + '/builtin_evidence.json'), {})
    gates['内置工具身份核验'] = evidence.get('ok') is True and ctx.get('suite_verified') is True
    resources = {}; comparisons = {}; rates = []; resource_ok = len(public) == 4
    public_by = {p.get('case'): p for p in public}
    for case in CASES:
        try:
            resources[case] = {}
            for side in ('baseline', 'optimized'):
                folder = pub_path / case / side
                stat = load(folder / 'stat.json', {})
                r = B.parse_resource_counts(stat, (folder / 'mapped.il').read_text(encoding='utf-8'), case)
                r['total_cells'] = int(stat['design']['num_cells'])
                resources[case][side] = r
                resource_ok = resource_ok and public_by[case].get(side + '_sample_id') == samples[(case, side)]['sample_id']
                resource_ok = resource_ok and public_by[case].get(side + '_resources') == {k: v for k, v in r.items() if k != 'total_cells'}
            comparison = B.compare_resource_counts(resources[case]['baseline'], resources[case]['optimized'])
            comparisons[case] = comparison
            rates.append(comparison['logic_reduction_pct'])
            resource_ok = resource_ok and comparison['resource_checks_ok']
        except (OSError, KeyError, TypeError, ValueError):
            resource_ok = False
    mean = sum(rates) / 4 if len(rates) == 4 and all(isinstance(v, (int, float)) for v in rates) else None
    area = judge_area(mean)
    gates['最终资源统计与同次来源完整'] = resource_ok
    gates['四例平均逻辑缩减达到10%'] = area['area_requirement_met']
    proof_pairs = {(c, chain) for c in CASES for chain in I.CHAINS}
    proof_by = {(r.get('case'), r.get('chain')): r for r in chains}
    formal_ok = len(chains) == 8 and set(proof_by) == proof_pairs
    for case, chain in proof_pairs:
        proof = proof_by.get((case, chain), {})
        side = 'optimized' if chain == I.CHAINS[0] else 'baseline'
        sample = samples.get((case, side), {})
        bound = ((sample.get('artifacts') or {}).get('post_abc.il') or {}).get('sha256')
        formal_ok = formal_ok and row_functional_ok(proof) and proof.get('formal_netlist_stage') == 'post_abc' \
            and bool(bound) and proof.get('formal_netlist_sha256') == bound
    integration_errors = I.evidence_errors(root, ctx) if I.identity(ctx) == I.LOCAL_ID else []
    gates['原始RTL功能证明与同次postABC哈希绑定'] = formal_ok and not integration_errors
    gates['墙钟与峰值完整并满足绝对限值'] = len(judgments) == 4 and all(j['valid'] and j['limit_ok'] for j in judgments)
    gates['逐例墙钟与内存不超过5%'] = len(judgments) == 4 and all(j['pass'] for j in judgments)
    complete = all(gates.values())
    status = 'BUILTIN_FOUR_CASE_LOCAL_ACCEPTANCE_COMPLETE' if complete else 'NEEDS_REVIEW'
    formal_state = 'PASS' if formal_ok else 'NOT_RUN' if not chains else 'FAIL'
    category = {'formal': formal_state,
                'resources': 'PASS' if resource_ok and area['area_requirement_met'] else 'NOT_RUN' if not public else 'FAIL',
                'wall_time': 'NOT_RUN' if not perf else 'INVALID' if not all(j['valid'] for j in judgments) else 'PASS' if all(j['wall_5pct'] == 'PASS' for j in judgments) else 'FAIL',
                'memory': 'NOT_RUN' if not perf else 'INVALID' if not all(j['valid'] for j in judgments) else 'PASS' if all(j['mem_ok'] for j in judgments) else 'FAIL'}
    delivery = judge_delivery(dest, ctx)
    manifest = dict(run_status=status, mode='builtin', performance_scheme=SCHEME,
        verification_verdict='PASS' if complete else 'FAIL', overall_verdict='PASS' if complete else 'FAIL',
        delivery_verdict=delivery['delivery_verdict'], project_readiness='NOT_READY', delivery=delivery,
        official_acceptance='NOT_CLAIMED', formal_synthesis_expected_runs=8,
        formal_synthesis_attempted_runs=ledger.get('attempted_runs', 0),
        formal_synthesis_started_runs=ledger.get('started_runs', 0),
        formal_synthesis_completed_runs=ledger.get('completed_runs', 0), same_run_metrics=True,
        independent_full_split_check='NOT_RUN', gates=gates,
        reasons=[k for k, passed in gates.items() if not passed], sample_errors=sample_issues,
        integration_evidence_errors=integration_errors, category_status=category,
        performance=judgments, mean_logic_reduction_pct=mean, **area,
        resources=resources, resource_comparisons=comparisons, context=ctx, stages=stages,
        formal_input_binding_ok=formal_ok, wall_time_method=METHOD,
        stress_test_status='WAITING_OFFICIAL_CASES', cpu_statistic='NOT_APPLICABLE')
    save(out / 'manifest.json', manifest)
    rows = []
    for case in CASES:
        judgment = next((j for j in judgments if j['case'] == case), {})
        data = {'case': case, 'baseline_time_ms': judgment.get('wall_base_ms'),
                'optimized_time_ms': judgment.get('wall_opt_ms'), 'time_increase_pct': judgment.get('wall_overhead_pct'),
                'baseline_peak_bytes': judgment.get('base_memory_bytes'), 'optimized_peak_bytes': judgment.get('opt_memory_bytes'),
                'memory_increase_pct': judgment.get('mem_overhead_pct'),
                'area_reduction_pct': comparisons.get(case, {}).get('logic_reduction_pct')}
        for side in ('baseline', 'optimized'):
            r = resources.get(case, {}).get(side, {})
            for key in ('lut_count', 'inverter_count', 'logic_units', 'dff_count', 'io_ports', 'io_bits', 'total_cells'):
                data[side + '_' + key] = r.get(key)
            data[side + '_formal'] = proof_by.get((case, I.CHAINS[0] if side == 'optimized' else I.CHAINS[1]), {}).get('state', 'NOT_RUN')
        rows.append(data)
    with (out / 'official_summary.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    def value(v): return '-' if v is None else f'{v:.3f}' if isinstance(v, float) else str(v)
    lines = ['# V8 同次采集八次正式综合报告', '',
        f"工程四例验证：**{manifest['verification_verdict']}**；执行状态：`{status}`。",
        f"- 正式综合：预计8次，发起请求{ledger.get('attempted_runs', 0)}次，确认启动Yosys {ledger.get('started_runs', 0)}次，测量有效完成{ledger.get('completed_runs', 0)}次。",
        f"- 算法提交：`{ctx.get('target_commit')}`；算法源码 SHA-256：`{ctx.get('source_sha256')}`。",
        f"- 规则原文：`{(ctx.get('policy_source') or {}).get('path')}`；SHA-256：`{(ctx.get('policy_source') or {}).get('sha256')}`。",
        f"- 已获得四例面积缩减率算术平均：{value(mean)}%；官方新增效率用例：`WAITING_OFFICIAL_CASES`。",
        '- 工具构建、专用探针和EQY单独记录；没有额外的公开四例流程对照或资源综合，没有自动稳定性重复测量。', '',
        '| 用例 | 墙钟ms 原/优 | 时间增幅 | 峰值MiB 原/优 | 内存增幅 | LUT 原/优 | NOT位 原/优 | 逻辑总数 原/优 | DFF 原/优 | IO端口/位 原/优 | 总cells 原/优 | 面积缩减 | Formal 原/优 |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---|']
    for r in rows:
        pair = lambda key: value(r.get('baseline_' + key)) + ' / ' + value(r.get('optimized_' + key))
        memory = ' / '.join(value(r.get(s + '_peak_bytes') / 1024**2 if r.get(s + '_peak_bytes') else None) for s in ('baseline', 'optimized'))
        io = ' / '.join(value(r.get(s + '_io_ports')) + '/' + value(r.get(s + '_io_bits')) for s in ('baseline', 'optimized'))
        lines.append(f"| {r['case']} | {pair('time_ms')} | {value(r['time_increase_pct'])}% | {memory} | {value(r['memory_increase_pct'])}% | {pair('lut_count')} | {pair('inverter_count')} | {pair('logic_units')} | {pair('dff_count')} | {io} | {pair('total_cells')} | {value(r['area_reduction_pct'])}% | {pair('formal')} |")
    lines += ['', '## 判定与限制', '',
        f"- 每例时间及内存均不超过1.05倍：{gates['逐例墙钟与内存不超过5%']}。",
        f"- 正式结果存在超过1.15倍的时间或内存：{any(j.get('any_over_15pct') for j in judgments)}。",
        f'- 原始RTL的八条证明链全部通过且绑定本次网表：{formal_ok}。',
        '- 取消的独立完整/分段资源对照为 NOT_RUN；采用脚本阶段边界及这8次日志核对，不把它写成独立对照PASS。',
        '- 时间为 Windows PowerShell 5.1 Measure-Command 的墙钟经过时间，保存原始 TimeSpan.Ticks 和 TotalMilliseconds；不是累计CPU时间。时间包含RTL读取、ABC9、7.1后的中间网表导出、厂商映射、最终网表/stat写出和退出收尾，也包含退出调试观测与本机请求/响应包装开销，未扣除。PowerShell及worker初始化、构建、EQY、事后分析不计入。',
        '- 内存为同一Yosys主进程在 EXIT_PROCESS_DEBUG_EVENT 中、ContinueDebugEvent 放行前读取的系统累计 PeakWorkingSetSize；原始单位字节，MiB=字节/1024²；不加ABC或进程树。调试可能影响运行与内存布局。',
        '- 同次采集是用户确认的本地规则；官方答疑规定单次计时及峰值工作内存只看yosys.exe，未指定此调试采集实现。题目写2GB，本地绝对阈值按2GiB记录，原始字节保留。5%～15%之间不推算分数。',
        '- 原始测量先保存，功能证明完成后才作工程判定；FAIL、TIMEOUT、UNPROVEN等证明状态不记为PASS。',
        '- 本报告仅覆盖当前四例；交付包未重新执行，官方认可不作声称。', '', '## 检查项', '']
    lines += [f"- {'PASS' if passed else 'FAIL'}：{key}" for key, passed in gates.items()]
    lines += ['', '## 最终全部cell类型', '', '| 用例 | 原版 | 优化版 |', '|---|---|---|']
    for case in CASES:
        line = [json.dumps(resources.get(case, {}).get(s, {}).get('cell_types', {}), sort_keys=True) for s in ('baseline', 'optimized')]
        lines.append(f"| {case} | `{line[0]}` | `{line[1]}` |")
    lines += ['', '## 工具与证据', '',
        f"- 工具及构建身份：`01_meta/builtin_prepare.json`、`builtin_evidence.json`；完整配置见 `validation_context.json`。",
        '- `05_public/round01/`：8次唯一正式运行的脚本、请求/响应、联合测量记录、日志、post_abc及最终网表/stat。',
        '- `09_performance/round01/`：调度账本与性能摘要，引用上述同次产物。',
        '- `04_flowcheck/`：只读日志分析；`10_selfcheck/chains/`：EQY配置、模型与完整证明日志。',
        '- `11_summary/official_summary.csv`：逐例汇总；`ALL_SHA256.txt`：证据哈希清单。', '']
    (dest / L.REPORT).write_text('\n'.join(lines), encoding='utf-8')
    return status
