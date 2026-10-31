"""V8 report: 2N canonical samples supply every public-case result."""
import csv
import json
from pathlib import Path
import result_layout as L

from measure_v9 import H, SCHEME, METHOD, POLICY, evaluate_summary, sample_errors, sha, save, schedule, verify_run_evidence
import builtin_common as B
import integration_profiles as I
import official_suite as S


def load(path, default):
    try: return json.loads(Path(path).read_text(encoding='utf-8-sig'))
    except (OSError, ValueError): return default


def build_report(root, output_root=None, chain_attempt='run01', stages_override=None):
    from report import row_functional_ok, judge_area, judge_delivery
    root = Path(root); dest = Path(output_root) if output_root else root
    out = dest / L.SUMMARY; out.mkdir(parents=True, exist_ok=True)
    ctx = load(root / 'validation_context.json', {})
    if ctx.get('performance_scheme') != SCHEME or ctx.get('same_run_policy') != POLICY:
        raise ValueError('V9 report refuses non-V9 context')
    security = load(root / L.META / 'security_environment.json', {})
    try:
        security_details = json.loads(security.get('stdout', '{}'))
    except (ValueError, TypeError):
        security_details = {}
    realtime = (security_details.get('defender') or {}).get('RealTimeProtectionEnabled', '未核对')
    case_specs = S.context_cases(ctx)
    CASES = tuple(c['id'] for c in case_specs)
    specs_by = {c['id']: c for c in case_specs}
    n = len(CASES); expected_runs = 2 * n
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
    gates['V9身份与规则位置'] = (ctx.get('performance_scheme') == SCHEME
        and ctx.get('same_run_policy') == POLICY and bool((ctx.get('policy_source') or {}).get('path')))
    gates['首次综合完整且无替换'] = (set(samples) == expected and ledger.get('expected_runs') == expected_runs
        and ledger.get('attempted_runs') == ledger.get('started_runs') == ledger.get('completed_runs') == expected_runs
        and ledger.get('execution_complete') is True and len(ledger.get('attempts', [])) == expected_runs
        and ledger.get('schedule') == schedule(ctx)
        and len({r.get('sample_id') for r in samples.values()}) == expected_runs)
    measurement_evidence = verify_run_evidence(root, ctx)
    gates['预热首次复核账本与原始证据完整'] = measurement_evidence['ok']
    sample_issues = {c + '/' + s: sample_errors(row, require_outputs=True) for (c, s), row in samples.items()}
    gates['同进程时间内存与产物哈希完整'] = (len(samples) == expected_runs
        and all(not issues for issues in sample_issues.values())
        and all(row.get('case') == case and row.get('side') == side
                for (case, side), row in samples.items()))
    copied = {(r.get('case'), r.get('side')): r for p in perf for r in p.get('samples', [])}
    gates['性能摘要对应正式原始记录'] = (len(perf) == n and copied == samples
        and {p.get('case') for p in perf} == set(CASES)
        and sum(len(p.get('samples', [])) for p in perf) == expected_runs)
    attempts = {(a.get('case'), a.get('side')): a for a in ledger.get('attempts', [])}
    gates['调度账本对应正式记录'] = (len(ledger.get('attempts', [])) == expected_runs and set(attempts) == expected and all(
        attempts[k].get('sample_id') == samples[k].get('sample_id') for k in expected if k in samples))
    logs_ok = len(samples) == expected_runs
    external_ok = len(samples) == expected_runs
    for case in CASES:
        b, o = samples.get((case, 'baseline'), {}), samples.get((case, 'optimized'), {})
        external_ok = external_ok and bool(b.get('flow_sha256')) and b.get('flow_sha256') == o.get('flow_sha256')
        for side in ('baseline', 'optimized'):
            try:
                row = samples[(case, side)]
                folder = pub_path / case / side
                external_ok = external_ok and row.get('flow_sha256') == sha(folder / 'flow.ys')
                external_ok = external_ok and all(
                    Path(spec.get('path', '')).resolve() == (folder / name).resolve()
                    for name, spec in (row.get('artifacts') or {}).items())
                log = (pub_path / case / side / 'run.log').read_text(encoding='utf-8', errors='replace')
                good = B.abc9_mapping_ok(log) and 'Loading plugin' not in log
                good = good and (I.check_calls(log, I.identity(ctx), require_export=True)['ok']
                                 if side == 'optimized' else 'Executing PMUX_OPT' not in log)
                logs_ok = logs_ok and good
                frozen = S.case_path(root / L.ASSETS / 'tree', specs_by[case])
                external_ok = external_ok and row.get('input_sha256') == sha(frozen)
                spec = ctx.get('builtin', {}).get(side, {})
                external_ok = external_ok and row.get('executable_sha256') == spec.get('binary_sha256')
            except (OSError, KeyError, ValueError):
                logs_ok = False; external_ok = False
    gates['相同输入脚本与工具身份'] = external_ok
    gates['本次日志的ABC9与PMUX调用和导出阶段'] = logs_ok and fc.get('all_ok') is True and fc.get('analysis_only') is True
    evidence = load(root / (L.META + '/builtin_evidence.json'), {})
    gates['内置工具身份核验'] = evidence.get('ok') is True and ctx.get('suite_verified') is True
    resources = {}; comparisons = {}; rates = []
    resource_source_ok = (len(public) == n and {p.get('case') for p in public} == set(CASES))
    resource_nonincrease_ok = True
    public_by = {p.get('case'): p for p in public}
    for case in CASES:
        try:
            resources[case] = {}
            for side in ('baseline', 'optimized'):
                folder = pub_path / case / side
                stat = load(folder / 'stat.json', {})
                r = B.parse_resource_counts(stat, (folder / 'mapped.il').read_text(encoding='utf-8'), specs_by[case]['top'])
                r['total_cells'] = int(stat['design']['num_cells'])
                resources[case][side] = r
                resource_source_ok = resource_source_ok and public_by[case].get(side + '_sample_id') == samples[(case, side)]['sample_id']
                resource_source_ok = resource_source_ok and public_by[case].get(side + '_resources') == {k: v for k, v in r.items() if k != 'total_cells'}
            comparison = B.compare_resource_counts(resources[case]['baseline'], resources[case]['optimized'], allow_dff_increase=True)
            comparisons[case] = comparison
            rates.append(comparison['logic_reduction_pct'])
            resource_nonincrease_ok = resource_nonincrease_ok and comparison['resource_checks_ok']
        except (OSError, KeyError, TypeError, ValueError):
            resource_source_ok = False
    # An independently valid resource statistic does not depend on EQY success.
    # Resource growth is a separate failure, so its real reduction stays visible.
    resource_source_ok = resource_source_ok and all(gates[name] for name in (
        'V9身份与规则位置', '首次综合完整且无替换', '同进程时间内存与产物哈希完整', '预热首次复核账本与原始证据完整',
        '性能摘要对应正式原始记录', '调度账本对应正式记录', '相同输入脚本与工具身份',
        '本次日志的ABC9与PMUX调用和导出阶段', '内置工具身份核验'))
    resource_ok = resource_source_ok and resource_nonincrease_ok
    mean = sum(rates) / n if resource_source_ok and len(rates) == n and all(isinstance(v, (int, float)) for v in rates) else None
    area = judge_area(mean)
    gates['最终资源统计与同次来源完整'] = resource_ok
    gates['套件平均逻辑缩减达到10%'] = area['area_requirement_met']
    proof_pairs = {(c, chain) for c in CASES for chain in I.CHAINS}
    proof_by = {(r.get('case'), r.get('chain')): r for r in chains}
    eqy_archive = None
    eqy_evidence_errors = []
    if ctx.get('eqy_workspace_version'):
        import eqy_workspace as EW
        eqy_archive = EW.verify_archive(root)
        archive_status = load(root / (L.META + '/eqy_archive.json'), {})
        gates['EQY现场归档完整'] = eqy_archive.get('ok') is True and archive_status.get('ok') is True
    formal_ok = len(chains) == expected_runs and set(proof_by) == proof_pairs
    for case, chain in proof_pairs:
        proof = proof_by.get((case, chain), {})
        side = 'optimized' if chain == I.CHAINS[0] else 'baseline'
        sample = samples.get((case, side), {})
        bound = ((sample.get('artifacts') or {}).get('post_abc.il') or {}).get('sha256')
        formal_ok = formal_ok and row_functional_ok(proof) and proof.get('formal_netlist_stage') == 'post_abc' \
            and bool(bound) and proof.get('formal_netlist_sha256') == bound
        if ctx.get('eqy_workspace_version'):
            try:
                archived = EW.resolve_evidence(root, proof.get('formal_netlist_input', '__missing_input__'))
                if sha(archived) != bound:
                    raise ValueError('Archived EQY input differs from this-round post_abc')
            except (OSError, ValueError, KeyError) as exc:
                formal_ok = False
                eqy_evidence_errors.append(case + '/' + side + ': ' + str(exc))
    integration_errors = I.evidence_errors(root, ctx) if I.requires_evidence(I.identity(ctx)) else []
    gates['原始RTL功能证明与同次postABC哈希绑定'] = formal_ok and not integration_errors
    gates['墙钟与峰值完整并满足绝对限值'] = len(judgments) == n and {j['case'] for j in judgments} == set(CASES) and all(j['valid'] and j['limit_ok'] for j in judgments)
    gates['逐例墙钟与内存不超过5%'] = len(judgments) == n and {j['case'] for j in judgments} == set(CASES) and all(j['pass'] for j in judgments)
    if ctx.get('flow_revision') == 'v9-official1030-r1':
        gates['1030禁止后端LUT集成'] = not I.has_lut(I.identity(ctx))
    complete = all(gates.values())
    status = 'BUILTIN_SUITE_LOCAL_ACCEPTANCE_COMPLETE' if complete else 'NEEDS_REVIEW'
    formal_state = 'PASS' if formal_ok else 'NOT_RUN' if not chains else 'FAIL'
    category = {'formal': formal_state,
                'resources': 'PASS' if resource_ok and area['area_requirement_met'] else 'NOT_RUN' if not public else 'FAIL',
                'wall_time': 'NOT_RUN' if not perf else 'INVALID' if not all(j['valid'] for j in judgments) else 'PASS' if all(j['wall_5pct'] == 'PASS' for j in judgments) else 'FAIL',
                'memory': 'NOT_RUN' if not perf else 'INVALID' if not all(j['memory_valid'] for j in judgments) else 'PASS' if all(j['mem_ok'] for j in judgments) else 'FAIL'}
    delivery = judge_delivery(dest, ctx)
    manifest = dict(run_status=status, mode='builtin', performance_scheme=SCHEME,
        verification_verdict='PASS' if complete else 'FAIL', overall_verdict='PASS' if complete else 'FAIL',
        delivery_verdict=delivery['delivery_verdict'], project_readiness='NOT_READY', delivery=delivery,
        official_acceptance='NOT_CLAIMED', formal_synthesis_expected_runs=expected_runs,
        formal_synthesis_attempted_runs=ledger.get('attempted_runs', 0),
        formal_synthesis_started_runs=ledger.get('started_runs', 0),
        formal_synthesis_completed_runs=ledger.get('completed_runs', 0), same_run_metrics=True,
        independent_full_split_check='NOT_RUN', gates=gates,
        reasons=[k for k, passed in gates.items() if not passed], sample_errors=sample_issues,
        integration_evidence_errors=integration_errors, category_status=category,
        performance=judgments, mean_logic_reduction_pct=mean, **area,
        measurement_evidence=measurement_evidence, phase_ledger=ledger.get('phases', {}),
        security_environment=security, official_environment_compliance='NOT_CONFIRMED',
        public_runs_total=ledger.get('total_public_completed_runs', 0), recheck_cases=ledger.get('recheck_cases', []),
        resources=resources, resource_comparisons=comparisons, context=ctx, stages=stages,
        formal_input_binding_ok=formal_ok, wall_time_method=METHOD,
        eqy_archive=eqy_archive, eqy_evidence_errors=eqy_evidence_errors,
        stress_test_status='PROVIDED_OFFICIAL_SUITE', cpu_statistic='NOT_APPLICABLE')
    save(out / 'manifest.json', manifest)
    rows = []
    for case in CASES:
        judgment = next((j for j in judgments if j['case'] == case), {})
        data = {'case': case, 'initial_time_increase_pct': judgment.get('initial_wall_overhead_pct'),
                'time_decision_source': judgment.get('time_decision_source'), 'recheck_scope': judgment.get('recheck_scope'), 'baseline_time_ms': judgment.get('wall_base_ms'),
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
    lines = [f'# V9 九例预热、首次与条件时间复核报告', '',
             f'计量修订：{H.REVISION}；堆策略：{H.POLICY}；启动前关闭调试堆，启动断点只读核验。', '',
        f"工程套件验证：**{manifest['verification_verdict']}**；执行状态：`{status}`。",
        f"- 正式综合：预计{expected_runs}次，发起请求{ledger.get('attempted_runs', 0)}次，确认启动Yosys {ledger.get('started_runs', 0)}次，测量有效完成{ledger.get('completed_runs', 0)}次。",
        f"- 算法提交：`{ctx.get('target_commit')}`；算法源码 SHA-256：`{ctx.get('source_sha256')}`。",
        f"- 集成方式：`{ctx.get('integration_profile')}`；身份：`{I.identity(ctx)}`；算术探针：`{(ctx.get('builtin', {}).get('arith_probe') or {}).get('ok', 'NOT_APPLICABLE')}`。",
        f"- 优化侧逐例调用计数（arith/普通/LUT）：`{[(c.get('case'), [(c.get('sides', {}).get('optimized', {}).get('integration_calls') or {}).get(k) for k in ('arith_count', 'early_count', 'lut_count')]) for c in fc.get('cases', [])]}`。",
        f"- 规则原文：`{(ctx.get('policy_source') or {}).get('path')}`；SHA-256：`{(ctx.get('policy_source') or {}).get('sha256')}`。",
        f"- 已获得{n}例面积缩减率算术平均：{value(mean)}%；全部清单用例均纳入本轮。",
        '- 原版逐例预热10次；首次先原版全部后优化版全部；触发例另跑5组原版→优化版，仅相对时间取分侧均值。构建、自检和EQY另计。', '',
        '| 用例 | 墙钟ms 原/优 | 时间增幅 | 峰值MiB 原/优 | 内存增幅 | LUT 原/优 | NOT位 原/优 | 逻辑总数 原/优 | DFF 原/优 | IO端口/位 原/优 | 总cells 原/优 | 面积缩减 | Formal 原/优 |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---|']
    for r in rows:
        pair = lambda key: value(r.get('baseline_' + key)) + ' / ' + value(r.get('optimized_' + key))
        memory = ' / '.join(value(r.get(s + '_peak_bytes') / 1024**2 if r.get(s + '_peak_bytes') else None) for s in ('baseline', 'optimized'))
        io = ' / '.join(value(r.get(s + '_io_ports')) + '/' + value(r.get(s + '_io_bits')) for s in ('baseline', 'optimized'))
        lines.append(f"| {r['case']} | {pair('time_ms')} | {value(r['time_increase_pct'])}% | {memory} | {value(r['memory_increase_pct'])}% | {pair('lut_count')} | {pair('inverter_count')} | {pair('logic_units')} | {pair('dff_count')} | {io} | {pair('total_cells')} | {value(r['area_reduction_pct'])}% | {pair('formal')} |")
    lines += ['', '## 测量账本与时间复核', '',
        '| 阶段 | 计划 | 请求 | 启动 | 有效完成 |', '|---|---:|---:|---:|---:|']
    for phase, info in ledger.get('phases', {}).items():
        lines.append('| ' + phase + ' | ' + ' | '.join(str(info.get(k, 0)) for k in ('expected_runs','attempted_runs','started_runs','completed_runs')) + ' |')
    lines += ['', f"公开用例综合有效完成总计：{ledger.get('total_public_completed_runs',0)}；复核集合：{ledger.get('recheck_cases',[])}。",
        '', '| 用例 | 首次原/优ms | 首次增幅 | 复核原/优均值ms | 最终时间增幅 | 采用依据 | 复核口径 |', '|---|---:|---:|---:|---:|---|---|']
    for j in judgments:
        initial_ms = ' / '.join(value(j.get('initial_wall_'+side+'_ticks')/10000 if j.get('initial_wall_'+side+'_ticks') is not None else None) for side in ('base','opt'))
        reviewed = (' / '.join(value(j.get('wall_'+side+'_ms')) for side in ('base','opt'))
                    if j.get('time_decision_source') == 'RECHECK_MEAN' else '未完成' if j.get('recheck_required') else '-')
        lines.append(f"| {j['case']} | {initial_ms} | {value(j.get('initial_wall_overhead_pct'))}% | {reviewed} | {value(j.get('wall_overhead_pct'))}% | {j.get('time_decision_source')} | {j.get('recheck_scope') or '-'} |")
    review_rows=[]
    for j in judgments:
        for r in j.get('recheck_samples',[]):
            review_rows.append(dict(case=j['case'],repetition=r.get('repetition'),side=r.get('side'),sample_id=r.get('sample_id'),ticks=r.get('time_span_ticks'),milliseconds=r.get('total_milliseconds'),peak_bytes=r.get('yosys_peak_working_set_bytes'),evidence_dir=r.get('evidence_dir'),repeat_evidence_ok=r.get('repeat_evidence_ok')))
    save(out / 'recheck_samples.json',review_rows)
    lines += ['', '### 全部复核样本', '', '| 用例 | 组 | 侧别 | 原始Ticks | ms | 峰值字节（不改判） | 一致性 |', '|---|---:|---|---:|---:|---:|---|']
    for r in review_rows:
        lines.append('| ' + ' | '.join(str(r.get(k)) for k in ('case','repetition','side','ticks','milliseconds','peak_bytes','repeat_evidence_ok')) + ' |')
    if not review_rows: lines.append('本轮没有完成的复核样本。')
    lines += ['', '## 判定与限制', '',
        f'- 环境限制：Defender实时防护状态为 {realtime}；其他安全产品及后台进程见01_meta/security_environment.json。本流程没有关闭安全软件或终止后台程序，不声称已满足官方关闭杀软的建议条件。',
        f"- 每例时间及内存均不超过1.05倍：{gates['逐例墙钟与内存不超过5%']}。",
        f"- 正式结果存在超过1.15倍的时间或内存：{any(j.get('any_over_15pct') for j in judgments)}。",
        f'- 原始RTL的{expected_runs}条证明链全部通过且绑定本次网表：{formal_ok}。',
        f'- 取消的独立完整/分段资源对照为 NOT_RUN；采用脚本阶段边界及这{expected_runs}次日志核对，不把它写成独立对照PASS。',
        '- 时间为 Windows PowerShell 5.1 Measure-Command 的墙钟经过时间，保存原始 TimeSpan.Ticks 和 TotalMilliseconds；不是累计CPU时间。时间包含RTL读取、ABC9清理命名后的中间网表导出、厂商映射、最终网表/stat写出和退出收尾，也包含退出调试观测与本机请求/响应包装开销，未扣除。PowerShell及worker初始化、构建、EQY、事后分析不计入。',
        '- 内存为同一Yosys主进程在 EXIT_PROCESS_DEBUG_EVENT 中、ContinueDebugEvent 放行前读取的系统累计 PeakWorkingSetSize；原始单位字节，MiB=字节/1024²；不加ABC或进程树。调试可能影响运行与内存布局。',
        '- C147已明确1—10秒区间的复核；C148的预热一批90次按用户确定的解释执行。同工具同次时间与内存指标已确认；调试退出事件接口仍为本地实现。内存与60秒/2GiB绝对检查使用首次数据；2GiB沿用本地解释。5%～15%不推算分数。',
        '- C145涉及的官方基座dirty改动未公开，当前公开基座与该状态的一致性未核对。C149第一问未明确，不能据此宣称前端处理已获批准。',
        '- 原始测量先保存，功能证明完成后才作工程判定；FAIL、TIMEOUT、UNPROVEN等证明状态不记为PASS。',
        f'- 本报告覆盖当前清单{n}例；DFF仅记录，不作为数量不增门禁；逻辑、IO及其他硬件门禁保留。交付NOT_RUN，官方认可NOT_CLAIMED。', '', '## 检查项', '']
    lines += [f"- {'PASS' if passed else 'FAIL'}：{key}" for key, passed in gates.items()]
    lines += ['', '## 最终全部cell类型', '', '| 用例 | 原版 | 优化版 |', '|---|---|---|']
    for case in CASES:
        line = [json.dumps(resources.get(case, {}).get(s, {}).get('cell_types', {}), sort_keys=True) for s in ('baseline', 'optimized')]
        lines.append(f"| {case} | `{line[0]}` | `{line[1]}` |")
    lines += ['', '## 工具与证据', '',
        f"- 工具及构建身份：`01_meta/builtin_prepare.json`、`builtin_evidence.json`；完整配置见 `validation_context.json`。",
        f'- `05_public/round01/`：{expected_runs}次唯一正式运行的脚本、请求/响应、联合测量记录、日志、post_abc及最终网表/stat。',
        '- `09_performance/round01/`：调度账本与性能摘要，引用上述同次产物。',
        '- `04_flowcheck/`：只读日志分析；`10_selfcheck/chains/`：EQY配置、模型与完整证明日志。',
        '- `11_summary/official_summary.csv`：逐例汇总；`ALL_SHA256.txt`：证据哈希清单。', '']
    (dest / L.REPORT).write_text('\n'.join(lines), encoding='utf-8')
    return status
