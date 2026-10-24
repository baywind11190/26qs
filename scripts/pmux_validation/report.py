"""官方四例判定与中文报告；缺失证据永不算通过。

判定规则（详见 POLICY.md，来源为官方答疑 Sheet1 C21~C26、C34、C37、C41）：
- 逻辑单元（cycloneiv_lcell_comb）逐例缩减率算术平均；DFF 单独检查、不应增加；
- 逐例比较 CPU/内存相对开销与 5%（边界值按不超过处理；不跨例平均、不使用舍入值）；
- 60s/2GB 以原版为对照，原版超限时允许优化版也超限，不自行发明扣分计算；
- 插件预检永远不能得出内置验收完成；缺功能证明、工具错误、无效样本不输出通过。
"""
import json
import math
import hashlib
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'runner'))
from measure_format import sample_errors, finite_positive, EXIT_PEAK_SCHEME
from cpu_statistics import SCHEME as MEAN_CPU_SCHEME, POLICY as CPU_POLICY
from cpu_statistics_v5 import SCHEME as ETW_CPU_SCHEME, METHOD as ETW_CPU_METHOD
from runtime_patch import SCHEME as SINGLE_CPU_SCHEME, METHOD as SINGLE_CPU_METHOD
from measure_v7 import SCHEME as SINGLE_WALL_SCHEME, METHOD as SINGLE_WALL_METHOD

OVERHEAD_LIMIT_PCT = 5.0
# 判定使用未舍入值；仅容忍 1e-9 个百分点量级的浮点表示误差（不等于四舍五入后的显示值比较）。
OVERHEAD_EPS_PCT = 1e-9
CPU_LIMIT_S = 60.0
RSS_LIMIT_KB = 2 * 1024 * 1024
MEMORY_LIMIT_BYTES = 2 * 1024 * 1024 * 1024
CASES = ("test1", "test2", "test3", "test4")
MAIN_CHAINS = ("c1_local", "c2_stage", "c4a_rtl_opt_mapped", "c4b_rtl_base_mapped")
FULL_CHAINS = ("c1_local", "c2_stage", "c3a_rtl_opt", "c3b_rtl_base",
               "c4a_rtl_opt_mapped", "c4b_rtl_base_mapped", "c5_mapped_pair")
FUNCTION_ONLY_EXEC = ("build", "formal_selfcheck", "chains")
FUNCTION_ONLY_SKIPPED = ("flowcheck", "measurement_selfcheck", "public", "performance")
EXPECTED_PLUGIN_STAGES = {"build", "flowcheck", "formal_selfcheck", "measurement_selfcheck",
                          "public", "chains", "performance"}
# 内置四例验收：执行阶段、主证明链与完成状态词。
BUILTIN_EXPECTED_STAGES = {"build", "flowcheck", "formal_selfcheck", "measurement_selfcheck",
                           "public", "chains", "performance"}
BUILTIN_MAIN_CHAINS = ("c4a_rtl_opt_mapped", "c4b_rtl_base_mapped")
BUILTIN_COMPLETE_STATUS = "BUILTIN_FOUR_CASE_LOCAL_ACCEPTANCE_COMPLETE"
BUILTIN_FOLLOW_UP = (
    "1) 修复失败原因后重新运行：`validate.py run <提交>`（默认内置，自动准备工具，不退回插件）。",
    "2) 工具准备：baseline 按登记核对复用；optimized 按缓存键（算法源码哈希、基础提交、"
    "集成模板、关键构建参数、编译器、ABC 身份）在 cache_dir/registry 查找，未命中时从本地"
    "基础提交自动构建（隔离源码树 + 幂等集成 + 冒烟验证）并登记为 READY；构建失败保留 "
    "FAILED 诊断、不发布完成标记、不被复用。",
    "3) 内置外部脚本、插入位点与判定方法见 POLICY.md“内置四例验收”节；"
    "插件预检（--mode plugin）不能替代内置验收。",
)


def overhead_pct(base, opt):
    """未舍入相对开销（%）。基线为零或缺失时不可计算。"""
    if base is None or opt is None or base == 0:
        return None
    return (opt - base) / base * 100.0


def judge_area(mean):
    valid = type(mean) in (int, float) and math.isfinite(mean)
    return {'area_requirement_met': bool(valid and mean + OVERHEAD_EPS_PCT >= 10.0),
            'area_20pct_band_met': bool(valid and mean + OVERHEAD_EPS_PCT >= 20.0),
            'area_mean_pct': mean if valid else None}


def judge_delivery(root, ctx):
    """Delivery is independent of four-case verification and bound to ZIP identity."""
    local_evidence = Path(root) / 'delivery_evidence.json'
    registered = ctx.get('delivery_evidence') or {}
    if local_evidence.is_file():
        evidence = _read_json(local_evidence, {})
    else:
        registered_path = Path(registered.get('path') or '__missing_delivery__')
        evidence = (_read_json(registered_path, {}) if registered_path.is_file()
                    and sha_file(registered_path) == registered.get('sha256') else {})
    reasons = []
    identity_ok = bool(evidence) and all(evidence.get(k) == ctx.get(k) and ctx.get(k)
                                      for k in ('target_commit', 'source_sha256'))
    artifact = Path(evidence.get('package_path') or '__missing_package__')
    if not artifact.is_file():
        identity_ok = False
        reasons.append('交付包缺失')
    elif hashlib.sha256(artifact.read_bytes()).hexdigest() != evidence.get('package_sha256'):
        identity_ok = False
        reasons.append('交付包 SHA-256 与验收身份不符')
    if not identity_ok:
        reasons.append('交付证据缺失或算法/包身份不匹配')
    checks = {}
    for name in ('c55', 'eqy_portable'):
        spec = (evidence.get('checks') or {}).get(name) or {}
        state = spec.get('state', 'NOT_RUN')
        if state == 'PASS':
            proof_path = Path(spec.get('evidence_path') or '__missing_check__')
            proof_ok = proof_path.is_file() and sha_file(proof_path) == spec.get('evidence_sha256')
            proof = _read_json(proof_path, {}) if proof_ok else {}
            proof_ok = (proof_ok and proof.get(name) == 'PASS'
                        and proof.get('package_sha256') == evidence.get('package_sha256'))
            if not identity_ok or not proof_ok:
                state = 'NOT_RUN'
                reasons.append(name + ' 验收记录缺失/变化/不匹配当前包')
        checks[name] = dict(spec, state=state)
    states = [v['state'] for v in checks.values()]
    verdict = ('PASS' if all(s == 'PASS' for s in states) else
               'FAIL' if 'FAIL' in states else 'PAUSED' if 'PAUSED' in states else 'NOT_RUN')
    return {'delivery_verdict': verdict, 'checks': checks, 'reasons': reasons,
            'identity_ok': bool(identity_ok), 'evidence': evidence}


def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def judge_case_performance(summ, pairs=5, *, certificate_cache=None):
    if summ.get('performance_scheme') == 'pmux-perf-single-powershell-same-run-exitpeak-v8':
        from measure_v8 import evaluate_summary
        return evaluate_summary(summ)
    """逐例性能判定。无效样本不判通过；5% 边界按不超过处理；不做跨例平均。"""
    if summ.get('performance_scheme') == SINGLE_WALL_SCHEME:
        from measure_v7 import judge_case
        return judge_case(summ)
    if summ.get('performance_scheme') == SINGLE_CPU_SCHEME:
        from measure_v6 import judge_case
        return judge_case(summ)
    if summ.get('performance_scheme') == ETW_CPU_SCHEME:
        from performance_report_v5 import judge_case
        return judge_case(summ,certificate_cache)
    if summ.get('performance_scheme') == MEAN_CPU_SCHEME:
        return judge_case_performance_v4(summ)
    runs = summ.get("runs") or []
    memory_metric = summ.get("memory_metric")
    windows_memory = memory_metric == "yosys_peak_working_set_bytes"
    main_memory = memory_metric == "yosys_main_rss_peak_kb"
    mem_key = ("yosys_peak_working_set_bytes" if windows_memory else
               "yosys_main_rss_peak_kb" if main_memory else "tree_rss_peak_kb")
    mem_summary = ("yosys_peak_working_set_bytes" if windows_memory else
                   "yosys_main_rss_peak" if main_memory else "tree_rss_peak")
    memory_limit = MEMORY_LIMIT_BYTES if windows_memory else RSS_LIMIT_KB
    reasons = []

    def count(side):
        return sum(1 for r in runs if r.get("side") == side)

    sample_failures = [dict(index=i + 1, side=r.get('side'), reasons=sample_errors(
        dict(r, memory_metric=memory_metric) if not windows_memory else r, windows=windows_memory))
        for i, r in enumerate(runs)]
    sample_failures = [r for r in sample_failures if r['reasons']]
    if summ.get('performance_scheme') not in (None,'','pmux-perf-15p-mainrss-v2','pmux-perf-5p-mainrss-v1',EXIT_PEAK_SCHEME):
        sample_failures.append(dict(index=0,side='policy',reasons=['unknown performance scheme; no median fallback']))
    if summ.get('performance_scheme') == EXIT_PEAK_SCHEME:
        for i, r in enumerate(runs):
            if r.get('performance_scheme') != EXIT_PEAK_SCHEME:
                sample_failures.append(dict(index=i + 1, side=r.get('side'),
                                            reasons=['required exit-event scheme missing/mismatch']))
    valid = (
        len(runs) == pairs * 2
        and count("baseline") == pairs and count("optimized") == pairs
        and not sample_failures
    )
    base_cpu = summ.get("baseline_cpu_total_median")
    opt_cpu = summ.get("optimized_cpu_total_median")
    base_memory = summ.get("baseline_" + mem_summary + "_median")
    opt_memory = summ.get("optimized_" + mem_summary + "_median")
    valid = valid and all(finite_positive(v) for v in (base_cpu, opt_cpu, base_memory, opt_memory))
    cpu_over = overhead_pct(base_cpu, opt_cpu) if valid else None
    mem_over = overhead_pct(base_memory, opt_memory) if valid else None
    cpu_ok = valid and cpu_over is not None and cpu_over <= OVERHEAD_LIMIT_PCT + OVERHEAD_EPS_PCT
    mem_ok = valid and mem_over is not None and mem_over <= OVERHEAD_LIMIT_PCT + OVERHEAD_EPS_PCT
    limit_ok, limit_bits = False, {}
    if valid and opt_cpu is not None and opt_memory is not None:
        cpu_exempt = base_cpu is not None and base_cpu > CPU_LIMIT_S
        rss_exempt = base_memory is not None and base_memory > memory_limit
        limit_bits = {"cpu_exempt_upstream_over_limit": cpu_exempt,
                      "rss_exempt_upstream_over_limit": rss_exempt,
                      "memory_metric": memory_metric or "tree_rss_peak_kb",
                      "memory_limit": memory_limit}
        limit_ok = (opt_cpu <= CPU_LIMIT_S or cpu_exempt) and \
            (opt_memory <= memory_limit or rss_exempt)
    if not valid:
        reasons.append("样本不完整或存在无效样本，不判定通过")
        reasons.extend('样本 {index} ({side}): {reasons}'.format(**r) for r in sample_failures)
    elif not cpu_ok:
        reasons.append("CPU 相对开销超过 5%")
    if valid and not mem_ok:
        reasons.append("内存相对开销超过 5%")
    if valid and not limit_ok:
        reasons.append("超出 60s/2GB 且原版未超限")
    return {
        "case": summ.get("case"), "valid": valid,
        "invalid_samples": sample_failures,
        "cpu_overhead_pct": cpu_over, "mem_overhead_pct": mem_over,
        "cpu_ok": cpu_ok, "mem_ok": mem_ok, "limit_ok": limit_ok, "limit_bits": limit_bits,
        "base_cpu_s": base_cpu, "opt_cpu_s": opt_cpu,
        "base_rss_kb": base_memory if not windows_memory else None,
        "opt_rss_kb": opt_memory if not windows_memory else None,
        "base_memory_bytes": base_memory if windows_memory else None,
        "opt_memory_bytes": opt_memory if windows_memory else None,
        "base_memory_mib": (base_memory / (1024 * 1024)
                            if windows_memory and finite_positive(base_memory) else None),
        "opt_memory_mib": (opt_memory / (1024 * 1024)
                           if windows_memory and finite_positive(opt_memory) else None),
        "pass": bool(valid and cpu_ok and mem_ok and limit_ok),
        "reasons": reasons,
    }


def v4_non_cpu_performance_ok(judgments):
    return (len(judgments)==4 and {j.get('case') for j in judgments}==set(CASES)
            and all(j.get('valid') is True and j.get('limit_ok') is True for j in judgments))


def verification_verdict_v4(categories,structural_ok):
    if not structural_ok or any(v in ('FAIL','INVALID','NOT_RUN') for v in categories.values()):return 'FAIL'
    if any(v=='INCONCLUSIVE' for v in categories.values()):return 'INCONCLUSIVE'
    return 'PASS' if all(v=='PASS' for v in categories.values()) else 'FAIL'


def judge_case_performance_v4(summ):
    from cpu_statistics import analyse_cpu_runs,judge_cpu,aa_is_healthy
    from cpu_qualification import certificate_valid
    from measure_v4 import memory_errors
    import statistics
    cpu=summ.get('cpu_runs') or [];memory=summ.get('memory_runs') or []
    stats=analyse_cpu_runs(cpu)
    if summ.get('cpu_policy')!=CPU_POLICY or any(r.get('execution_kind')!='synthesis' or r.get('performance_scheme')!=MEAN_CPU_SCHEME for r in cpu):
        stats.update(valid=False,baseline_mean_s=None,optimized_mean_s=None,overhead_pct=None,ci95_pct=None)
        stats['errors'].append('v4 CPU policy or sample scheme mismatch')
    aa=analyse_cpu_runs(summ.get('aa_runs') or [],pairs_per_block=5)
    cert=summ.get('method_certificate') or {}
    qualified,qual_reason=certificate_valid(cert,summ.get('qualification_fingerprint'))
    decision=judge_cpu(stats,qualified=qualified,guard_pct=cert.get('guard_pct'),aa_ok=aa_is_healthy(aa))
    expected={(s,p) for s in ('baseline','optimized') for p in range(1,16)}
    mem_errors=[dict(index=i+1,side=r.get('side'),reasons=memory_errors(r)) for i,r in enumerate(memory) if memory_errors(r)]
    mem_valid=len(memory)==30 and {(r.get('side'),r.get('pair')) for r in memory}==expected and not mem_errors
    mb=mo=None
    if mem_valid:
        mb=statistics.median(r['yosys_peak_working_set_bytes'] for r in memory if r['side']=='baseline')
        mo=statistics.median(r['yosys_peak_working_set_bytes'] for r in memory if r['side']=='optimized')
    mem_over=overhead_pct(mb,mo) if mem_valid else None
    mem_ok=mem_valid and mem_over<=5+OVERHEAD_EPS_PCT
    b,o=stats['baseline_mean_s'],stats['optimized_mean_s']
    valid=stats['valid'] and mem_valid
    bits=dict(cpu_exempt_upstream_over_limit=finite_positive(b) and b>CPU_LIMIT_S,
              rss_exempt_upstream_over_limit=finite_positive(mb) and mb>MEMORY_LIMIT_BYTES,
              memory_metric='yosys_peak_working_set_bytes',memory_limit=MEMORY_LIMIT_BYTES)
    limit_ok=bool(valid and (o<=CPU_LIMIT_S or bits['cpu_exempt_upstream_over_limit']) and
                  (mo<=MEMORY_LIMIT_BYTES or bits['rss_exempt_upstream_over_limit']))
    reasons=[]
    if not stats['valid']:reasons.append('CPU 样本不完整或无效：'+'; '.join(stats['errors'][:8]))
    if not qualified:reasons.append('CPU 方法资格无效：'+str(qual_reason))
    if not aa_is_healthy(aa):reasons.append('A/A控制未通过或未完成，不能确认CPU开销')
    if decision['cpu_verdict']=='INCONCLUSIVE':reasons.append('CPU 暂不能判断；均值点估计和扩展区间分别报告')
    elif decision['cpu_verdict']=='FAIL':reasons.append('CPU 扩展区间下限超过5%，支持超限')
    if not mem_valid:reasons.append('内存样本不完整或无效')
    elif not mem_ok:reasons.append('内存相对开销超过5%')
    if valid and not limit_ok:reasons.append('超出60s/2GB且原版未超限')
    return dict(decision,case=summ.get('case'),valid=valid,invalid_samples=mem_errors,
        cpu_statistics=stats,aa_statistics=aa,qualification_reason=qual_reason,
        cpu_ok=decision['cpu_verdict']=='PASS',mem_ok=mem_ok,mem_overhead_pct=mem_over,
        memory_valid=mem_valid,limit_ok=limit_ok,limit_bits=bits,base_cpu_s=b,opt_cpu_s=o,
        base_rss_kb=None,opt_rss_kb=None,base_memory_bytes=mb,opt_memory_bytes=mo,
        base_memory_mib=mb/1024**2 if mb is not None else None,opt_memory_mib=mo/1024**2 if mo is not None else None,
        **{'pass':valid and decision['cpu_verdict']=='PASS' and mem_ok and limit_ok},reasons=reasons)


def _read_json(path, default):
    path = Path(path)
    return json.loads(path.read_text()) if path.exists() else default


def _fmt_pct(value):
    return f"{value:.3f}%" if value is not None else "不可计算"


def row_functional_ok(r):
    """功能证据行的联合判定（不能只看单一字段/单一 SUCCESS 字样）。

    要求：state=PASS 且 rc=0 且 verified=True；分区方法需 noDF 前提探针全 SAT；
    合并证明方法需合并探针 SAT 且断言覆盖成立。
    """
    if r.get("state") != "PASS" or r.get("rc") != 0 or r.get("verified") is not True:
        return False
    if r.get("method") == "merged_miter":
        merged = r.get("merged") or {}
        return merged.get("probe") == "PREMISES_SAT" and merged.get("assert_cover_ok") is True
    return r.get("probes_noDF_all_sat") is True


def per_side_function_lines(chains):
    """每例两侧功能状态（两侧分别独立运行；不使用“两链同结果”推断）。"""
    def find(case, chain):
        return next((r for r in chains if r.get("case") == case and r.get("chain") == chain), None)

    lines = []
    for case in CASES:
        chunks = []
        for label, chain in (("c4a", "c4a_rtl_opt_mapped"), ("c4b", "c4b_rtl_base_mapped")):
            r = find(case, chain)
            if not r:
                chunks.append(f"{label} 未运行")
            elif r.get("method") == "merged_miter":
                m = r.get("merged") or {}
                chunks.append("{} 合并证明 state={} k={}（探针 {}；全部输出覆盖 {}）".format(
                    label, m.get("state"), m.get("k"), m.get("probe"), m.get("assert_cover_ok")))
            else:
                chunks.append("{} 分区 {}/{}（探针全 SAT={}）".format(
                    label, r.get("partitions_pass"), r.get("partitions_total"),
                    r.get("probes_noDF_all_sat")))
        lines.append("{}：{}。".format(case, "；".join(chunks)))
    return lines


def build_report(root, output_root=None, chain_attempt="run01", stages_override=None, mode=None):
    root = Path(root)
    output_root = Path(output_root) if output_root else root
    output_root.mkdir(parents=True, exist_ok=True)
    ctx = _read_json(root / "validation_context.json", {})
    if mode is None:
        mode = ctx.get("mode", "plugin")
    if ctx.get("function_only"):
        return build_function_recheck_report(root, output_root=output_root,
                                             chain_attempt=chain_attempt, ctx=ctx)
    stages = stages_override if stages_override is not None else _read_json(
        root / "01_来源与环境_meta/stages.json", [])
    pub = _read_json(root / "05_公开四例_public/round01/summary.json", {}).get("cases", [])
    chains = _read_json(root / f"10_验证工具自检_selfcheck/chains/{chain_attempt}/chains_summary.json", [])
    perf = _read_json(root / "09_时间内存开销_performance/round01/performance_summary.json", [])
    pairs = ctx.get("performance_pairs", 5)

    gates, reasons = {}, []

    def gate(name, passed):
        gates[name] = bool(passed)
        if not passed:
            reasons.append(name)

    stage_by = {s.get("name"): s for s in stages}

    def stage_ok(name):
        s = stage_by.get(name)
        if not s:
            return False
        return s.get("rc") == 0 and s.get("state") in ("COMPLETED", "REUSED")

    gate("执行阶段完整", {s.get("name") for s in stages} == EXPECTED_PLUGIN_STAGES
         and all(stage_ok(n) for n in EXPECTED_PLUGIN_STAGES))
    iso = ctx.get("isolation") or {}
    gate("插件构建与隔离", stage_ok("build")
         and iso.get("baseline_no_pmux") is True and iso.get("plugin_has_pmux") is True)
    gate("四例综合与检查", len(pub) == 4 and {p.get("case") for p in pub} == set(CASES)
         and all(p.get("baseline_rc") == 0 and p.get("optimized_rc") == 0
                 and p.get("baseline_check_assert") and p.get("optimized_check_assert")
                 for p in pub))
    gate("DFF逐例不增加", len(pub) == 4 and all(p.get("dff_nonincrease") is True for p in pub))
    expected_pairs = {(c, ch) for c in CASES for ch in MAIN_CHAINS}
    have_pairs = {(r.get("case"), r.get("chain")) for r in chains}
    default_pass = expected_pairs <= have_pairs and all(
        row_functional_ok(r) for r in chains
        if (r.get("case"), r.get("chain")) in expected_pairs)
    gate("功能证明（默认链集合）", default_pass)
    certificate_cache={}
    judgments = [judge_case_performance(p, pairs=pairs,certificate_cache=certificate_cache) for p in perf]
    gate("四例性能逐例判定", len(perf) == 4 and {p.get("case") for p in perf} == set(CASES)
         and all(j["pass"] for j in judgments))
    gate("四例输入指纹已核验", ctx.get("suite_verified") is True)

    unresolved = [r for r in chains if r.get("state") != "PASS"]
    status = "FOUR_CASE_PLUGIN_CHECKS_COMPLETE" if all(gates.values()) else "NEEDS_REVIEW"
    out = output_root / "11_汇总与证据_summary"
    out.mkdir(exist_ok=True)
    manifest = {
        "run_status": status, "mode": mode, "marking": "四例插件预检",
        "official_acceptance": "NOT_CLAIMED", "final_builtin_acceptance": "NOT_RUN",
        "full_rtl_mapping_proof": "PASS" if default_pass else "NOT_CLOSED",
        "gates": gates, "reasons": reasons,
        "chains_mode": ctx.get("chains_mode"), "chains_run": sorted(
            f"{c}/{ch}" for c, ch in sorted(have_pairs)),
        "unresolved_chains": unresolved,
        "performance": judgments,
        "context": ctx, "stages": stages, "evidence_root": str(root),
        "chain_attempt": chain_attempt,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    lines = [
        "# 官方四例插件预检", "",
        f"执行状态：**{status}**。",
        "形态：四例插件预检（显式 `--mode plugin`）；**最终内置四例验收：NOT_RUN**——插件结果不构成内置验收。", "",
        f"证据根目录：`{root}`；功能证明链采用 `{chain_attempt}`。", "",
        f"- 算法提交：`{ctx.get('target_commit')}`",
        f"- 项目 HEAD：`{ctx.get('project_head')}`",
        f"- 源码 SHA-256：`{ctx.get('source_sha256')}`",
        f"- 插件 SHA-256：`{ctx.get('plugin_sha256', 'NOT_BUILT')}`",
        f"- 流程 / 套件：{ctx.get('flow_version')} / {ctx.get('suite_version')}",
        f"- 链集合：{ctx.get('chains_mode', 'main')}（main=主路径+对照+定位；full=全部链）", "",
        "## 检查结果", "", "| 项目 | 结果 |", "|---|---|",
    ]
    lines += [f"| {name} | {'满足' if ok else '未满足或缺证据'} |" for name, ok in gates.items()]
    lines += ["", "## 四例资源与缩减率", "",
              "| 用例 | Comb 前→后 | DFF 前→后 | Comb 缩减率 |", "|---|---|---|---|"]
    rates = []
    for p in pub:
        b, o = p.get("baseline_comb"), p.get("optimized_comb")
        rate = (b - o) / b * 100 if b else None
        rates.append(rate)
        lines.append(f"| {p.get('case')} | {b}→{o} | {p.get('baseline_dff')}→{p.get('optimized_dff')} | {_fmt_pct(rate)} |")
    average = sum(rates) / 4 if len(rates) == 4 and None not in rates else None
    lines += ["", f"四例 Comb 缩减率算术平均：{average if average is not None else '不可计算（缺测不缩分母）'}%。",
              "逻辑单元口径为 `cycloneiv_lcell_comb`；DFF 独立检查、不应增加；Total 仅辅助。", "",
              "## 功能证明状态", "",
              "默认链集合说明：`c4a_rtl_opt_mapped`（原始 RTL ↔ 优化版最终映射网表）为主路径；"
              "`c4b_rtl_base_mapped` 为 baseline 对照；`c1_local`（P3 局部）与 `c2_stage`（同阶段）"
              "是范围受限证据与失败定位，不能单独支撑全链声明。",
              f"完整公开证明链：{'PASS' if default_pass else 'NOT_CLOSED'}。",
              "",
              "每例两侧功能状态（两侧分别独立运行；不使用“两链同结果”推断）："]
    lines += ["- " + s for s in per_side_function_lines(chains)]
    if unresolved:
        lines += [f"- {r.get('case')} / {r.get('chain')}：{r.get('state')}，rc={r.get('rc')}" for r in unresolved]
    else:
        lines += ["- 默认链集合全部通过。"]
    if ctx.get("chains_mode", "main") == "main":
        lines += ["- 未运行链：c3a/c3b/c5（`--chains full` 可单独运行；默认不作为每轮必跑）。"]
    lines += ["- COUNTEREXAMPLE_REQUIRES_REVIEW 表示工具报告分区不等价，需复核配置、假设和反例，"
              "不自动断言算法错误；MODEL_UNSUPPORTED 表示映射模型适用条件不满足，保留条件、不强行证明。", "",
              "## 四例性能（逐例判定）", "",
              "| 用例 | CPU 中位数前→后(s) | CPU 开销 | CPU 5% | RSS 前→后(KiB) | 内存开销 | 内存 5% | 60s/2GB | 样本有效 |",
              "|---|---|---|---|---|---|---|---|---|"]
    for j in judgments:
        cpu = f"{j['base_cpu_s']}→{j['opt_cpu_s']}"
        rss = f"{j['base_rss_kb']}→{j['opt_rss_kb']}"
        limit_disp = "通过" if j["limit_ok"] else "超限"
        if j["limit_bits"].get("cpu_exempt_upstream_over_limit") or \
           j["limit_bits"].get("rss_exempt_upstream_over_limit"):
            limit_disp += "（原版超限例外）"
        lines.append(
            f"| {j['case']} | {cpu} | {_fmt_pct(j['cpu_overhead_pct'])} | "
            f"{'满足' if j['cpu_ok'] else '未满足'} | {rss} | {_fmt_pct(j['mem_overhead_pct'])} | "
            f"{'满足' if j['mem_ok'] else '未满足'} | {limit_disp} | {j['valid']} |")
    lines += ["",
              f"每侧 {pairs} 次交错运行、取中位数；相对开销 =（优化版-原版）/原版，逐例与 5% 比较"
              "（边界值按不超过处理；不跨例平均、不使用舍入后的显示值）。",
              "CPU 时间为 wait4 采集并覆盖子进程树（含 ABC 子进程）；测量自检含孙进程 CPU 累计检查。",
              ("内存为 Yosys 主进程 Linux VmHWM（5ms 轮询），不含 ABC 与包装器；"
               if all(p.get("memory_metric") == "yosys_main_rss_peak_kb" for p in perf) else
               "历史内存为进程组 RSS 求和采样；可能漏峰和重复计共享页；"),
              "不是精确官方内存计量。",
              "60s/2GB 以原版为对照；原版超限时允许优化版也超限；不自行发明扣分计算。",
              "无效样本（含工具失败、超时、缺失）不判定通过；原始样本全部保留、不自动剔除。", "",
              "## 证据", "",
              "- `validation_context.json`：工具、提交、四例输入套件、代码指纹与隔离检查结果。",
              "- `01_来源与环境_meta/stages.json`：本阶段状态；自检阶段带 `REUSED` 标记时表示按指纹复用。",
              f"- 本报告清单：`{out / 'manifest.json'}`。",
              f"- 全量证据哈希：`{out / 'ALL_SHA256.txt'}`（与报告同轮生成或更新）。", "",
              "执行状态与缺证据/需复核一致；阶段完成不等于功能或性能通过；没有擅自补充官方分数。"]
    (output_root / "00_本轮验证结论.md").write_text("\n".join(lines) + "\n")
    return status


def build_builtin_block_report(root, status, missing, evidence, cfg):
    """内置四例验收的未就绪阻断记录（不执行任何验收进程）。"""
    root = Path(root)
    out = root / "11_汇总与证据_summary"
    out.mkdir(parents=True, exist_ok=True)
    context = {k: cfg.get(k) for k in ("flow_version", "suite_version", "target_commit",
                                       "source_sha256", "project_head", "suite_verified")}
    manifest = {
        "run_status": status, "mode": "builtin", "marking": "官方四例内置验收（未就绪阻断）",
        "official_acceptance": "NOT_CLAIMED", "builtin_execution": "NOT_READY",
        "missing_items": missing, "follow_up": list(BUILTIN_FOLLOW_UP),
        "evidence": evidence, "context": context, "evidence_root": str(root),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    lines = [
        "# 官方四例内置验收 —— 未就绪阻断", "",
        f"状态：**{status}**。", "",
        "本次未运行任何综合/EQY/性能实验，未加载插件；不会自动退回插件方案，"
        "也不以空实现冒充内置验收。", "",
        f"- 算法提交：`{cfg.get('target_commit')}`",
        f"- 项目 HEAD：`{cfg.get('project_head')}`",
        f"- 源码 SHA-256：`{cfg.get('source_sha256')}`",
        f"- 流程 / 套件：{cfg.get('flow_version')} / {cfg.get('suite_version')}", "",
    ]
    if missing:
        lines += ["## 缺项清单", ""] + [f"- {m}" for m in missing] + [""]
    else:
        lines += ["## 说明", "",
                  "内置证据预检未通过；本次未启动验收进程，不退回插件。", ""]
    lines += ["## 后续动作", ""] + [f"- {item}" for item in BUILTIN_FOLLOW_UP] + [""]
    lines += [
        "## 内置四例验收要求（契约）", "",
        "- 原版与优化版均为 Yosys 0.69 的可追溯构建；记录基础源码提交、构建信息、二进制指纹、"
        "ABC、实际数据文件和插入调用证据。",
        "- 优化版在 `synth_intel.cc` 中调用 `pmux_opt`（C24/C37）；外部综合脚本两侧内容相同、"
        "直接调用 `synth_intel`。",
        "- 路径参数分别指向两份工具，不要求二进制哈希相同。",
        "- 插件预检（`--mode plugin`）不能替代内置验收。", "",
        "## 证据", "",
        f"- 内置证据检查：`{root / '01_来源与环境_meta/builtin_evidence.json'}`",
        f"- 清单：`{out / 'manifest.json'}`",
    ]
    (root / "00_本轮验证结论.md").write_text("\n".join(lines) + "\n")
    return status


def build_builtin_build_failed_report(root, error, cfg, build_dir=None, logs=None):
    """内置工具准备失败记录（构建失败/环境不满足）；不启动验收进程、不退回插件。"""
    root = Path(root)
    out = root / "11_汇总与证据_summary"
    out.mkdir(parents=True, exist_ok=True)
    context = {k: cfg.get(k) for k in ("flow_version", "suite_version", "target_commit",
                                       "source_sha256", "project_head", "suite_verified")}
    manifest = {
        "run_status": "BUILTIN_BUILD_FAILED", "mode": "builtin",
        "marking": "官方四例内置验收（工具准备失败）",
        "official_acceptance": "NOT_CLAIMED", "builtin_execution": "BUILD_FAILED",
        "error": error, "build_dir": build_dir, "logs": logs or {},
        "context": context, "evidence_root": str(root),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    lines = [
        "# 官方四例内置验收 —— 工具准备失败", "",
        "状态：**BUILTIN_BUILD_FAILED**。",
        "本次在自动准备内置工具（复用查找或构建）时失败；未启动任何验收阶段、"
        "未加载插件、不退回插件方案、不自动重试。", "",
        f"- 算法提交：`{cfg.get('target_commit')}`",
        f"- 源码 SHA-256：`{cfg.get('source_sha256')}`",
        f"- 流程 / 套件：{cfg.get('flow_version')} / {cfg.get('suite_version')}", "",
        "## 失败原因", "",
        f"- {error}", "",
    ]
    if build_dir:
        lines.append(f"- 构建目录（保留诊断）：`{build_dir}`")
    if logs:
        lines.append(f"- 日志：`{logs}`")
    lines += ["", "## 后续动作", "",
              "- 按日志检查失败原因（编译错误 / 依赖缺失 / 锚点上下文不符 / 构建锁残留等）；"
              "修复后重新运行 `validate.py run <提交>`。",
              "- 既有历史构建与缓存不受影响（不删除、不覆盖）；缓存中 FAILED 条目不会被复用。", "",
              "## 证据", "",
              f"- 工具准备记录：`{root / '01_来源与环境_meta/builtin_prepare.json'}`",
              f"- 阶段记录：`{root / '01_来源与环境_meta/stages.json'}`",
              f"- 清单：`{out / 'manifest.json'}`",
              ]
    (root / "00_本轮验证结论.md").write_text("\n".join(lines) + "\n")
    return "BUILTIN_BUILD_FAILED"


def build_builtin_report(root, output_root=None, chain_attempt="run01", stages_override=None):
    """官方四例内置验收（本地）判定与中文报告；缺失证据永不算通过。

    与插件预检的区别：交付形态为两份内置 Yosys（外部脚本直接调用 synth_intel；
    优化版由 synth_intel.cc 在 fsm;opt 之后、wreduce 之前自动调用 pmux_opt）；
    p5/p6 功能证明主链为 c4a/c4b（原始 RTL ↔ 两侧 ABC9 后 post_abc.il；test3 为无切割合并
    证明）；c1/c2 依赖 P3 中间网表，内置模式不适用（NOT_APPLICABLE，不虚构）。
    完成状态 BUILTIN_FOUR_CASE_LOCAL_ACCEPTANCE_COMPLETE 仅在全部门通过时给出；
    本地验收不代表主办方认可。
    """
    root = Path(root)
    output_root = Path(output_root) if output_root else root
    output_root.mkdir(parents=True, exist_ok=True)
    ctx = _read_json(root / "validation_context.json", {})
    if ctx.get('performance_scheme') == 'pmux-perf-single-powershell-same-run-exitpeak-v8':
        from report_v8 import build_report
        return build_report(root, output_root=output_root, chain_attempt=chain_attempt,
                            stages_override=stages_override)
    stages = stages_override if stages_override is not None else _read_json(
        root / "01_来源与环境_meta/stages.json", [])
    evidence = _read_json(root / "01_来源与环境_meta/builtin_evidence.json", {})
    fc = _read_json(root / "04_流程一致性_flowcheck/builtin_run01/builtin_flowcheck.json", {})
    pub_summary = _read_json(root / "05_公开四例_public/round01/summary.json", {})
    pub = pub_summary.get("cases", [])
    chains = _read_json(
        root / f"10_验证工具自检_selfcheck/chains/{chain_attempt}/chains_summary.json", [])
    perf = _read_json(root / "09_时间内存开销_performance/round01/performance_summary.json", [])
    pairs = ctx.get("performance_pairs", 5)
    prep = ctx.get("builtin_prepare") or {}
    scheme = ctx.get("performance_scheme") or ""
    p6_windows = ctx.get("flow_version") == "official4-p6-windows"
    single_wall = p6_windows and scheme == SINGLE_WALL_SCHEME
    import integration_profiles as I
    local_lut = I.identity(ctx) == I.LOCAL_ID
    single_cpu = p6_windows and scheme == SINGLE_CPU_SCHEME
    etw_cpu = p6_windows and scheme == ETW_CPU_SCHEME
    mean_cpu = p6_windows and scheme in (MEAN_CPU_SCHEME,ETW_CPU_SCHEME)
    if mean_cpu:pairs=300
    if single_wall:pairs=1
    exit_peak = p6_windows and scheme in (EXIT_PEAK_SCHEME,MEAN_CPU_SCHEME,ETW_CPU_SCHEME,SINGLE_CPU_SCHEME,SINGLE_WALL_SCHEME)
    area = judge_area(None)
    io_comparisons = {}

    gates, reasons = {}, []

    def gate(name, passed):
        gates[name] = bool(passed)
        if not passed:
            reasons.append(name)

    stage_by = {s.get("name"): s for s in stages}

    def stage_ok(name):
        s = stage_by.get(name)
        return bool(s) and s.get("rc") == 0 and s.get("state") in ("COMPLETED", "REUSED")

    expected_stages=BUILTIN_EXPECTED_STAGES | ({'cpu_etw_selfcheck'} if etw_cpu else {'cpu_method_qualification'} if mean_cpu else set())
    gate("执行阶段完整（内置）", {s.get("name") for s in stages} == expected_stages
         and all(stage_ok(n) for n in expected_stages))
    fc_ok = (evidence.get("ok") is True and fc.get("all_ok") is True
             and len(fc.get("cases") or []) == 4)
    gate("内置构建与调用证据", fc_ok)
    integration_errors = I.evidence_errors(root, ctx) if local_lut else []
    if local_lut:
        gate('7.1调用与证明网表来源一致', not integration_errors)
        reasons.extend(integration_errors)
    gate("四例综合与检查", len(pub) == 4 and {p.get("case") for p in pub} == set(CASES)
         and all(p.get("baseline_rc") == 0 and p.get("optimized_rc") == 0
                 and p.get("baseline_check_assert") and p.get("optimized_check_assert")
                 for p in pub))
    gate("DFF逐例不增加", len(pub) == 4 and all(p.get("dff_nonincrease") is True for p in pub))
    if p6_windows:
        resource_complete = len(pub) == 4 and {p.get("case") for p in pub} == set(CASES)
        resource_rows_ok = resource_complete
        computed_rates = []
        for p in pub:
            for side in ("baseline", "optimized"):
                lut = p.get(side + "_lut_count")
                inv = p.get(side + "_inverter_count")
                logic = p.get(side + "_logic_units")
                if not all(isinstance(v, (int, float)) for v in (lut, inv, logic)):
                    resource_rows_ok = False
                    continue
                resource_rows_ok = resource_rows_ok and logic == lut + inv
                resource_rows_ok = resource_rows_ok and p.get(side + "_comb") == lut
            base_logic, opt_logic = p.get("baseline_logic_units"), p.get("optimized_logic_units")
            rate = p.get("logic_reduction_pct")
            if not all(isinstance(v, (int, float)) for v in (base_logic, opt_logic, rate)):
                resource_rows_ok = False
            elif base_logic <= 0 or not math.isclose(
                    rate, (base_logic - opt_logic) / base_logic * 100.0,
                    rel_tol=0.0, abs_tol=1e-9):
                resource_rows_ok = False
            else:
                computed_rates.append(rate)
        expected_mean = sum(computed_rates) / 4 if len(computed_rates) == 4 else None
        reported_mean = pub_summary.get("public_mean_logic_reduction_pct")
        if expected_mean is None or not isinstance(reported_mean, (int, float)) or not math.isclose(
                expected_mean, reported_mean, rel_tol=0.0, abs_tol=1e-9):
            resource_rows_ok = False
        gate("资源统计完整且取反位计入逻辑单元", resource_rows_ok)
        area = judge_area(expected_mean if resource_rows_ok else None)
        gate("四例平均面积缩减达到10%", area['area_requirement_met'])
        from builtin_common import compare_resource_counts
        for p in pub:
            try:
                io_comparisons[p['case']] = compare_resource_counts(
                    p['baseline_resources'], p['optimized_resources'])
            except (KeyError, TypeError, ValueError):
                io_comparisons[p.get('case')] = {'resource_checks_ok': False,
                                                'io_resources': {'error': '缺少逐类资源计数'}}
        gate("DFF、IO及其他硬件资源逐例不增加", len(pub) == 4 and all(
            p.get("resource_checks_ok") is True and p.get("dff_nonincrease") is True
            and p.get("io_nonincrease") is True
            and io_comparisons[p.get('case')].get('resource_checks_ok') is True
            and p.get("other_resources_nonincrease") is True for p in pub))
    if ctx.get("flow_version") in ("official4-p5", "official4-p6-windows"):
        gate("其他硬件单元逐类不增加", len(pub) == 4 and all(p.get("other_resources_nonincrease") is True for p in pub))
        gate("ABC9与功能输入阶段", len(pub) == 4 and all(
            p.get(side + "_abc9_ok") is True and p.get(side + "_formal_netlist_stage") == "post_abc" and p.get(side + "_split_full_resources_match") is True
            for p in pub for side in ("baseline", "optimized")))
        expected_memory_metric = ("yosys_peak_working_set_bytes" if p6_windows
                                  else "yosys_main_rss_peak_kb")
        gate("主进程内存口径", len(perf) == 4 and all(
            p.get("memory_metric") == expected_memory_metric for p in perf))
        if exit_peak:
            gate(('PowerShell墙钟与退出事件内存方案身份一致' if single_wall
                  else '普通CPU与退出事件内存方案身份一致'), len(perf) == 4 and all(
                      p.get('performance_scheme') == scheme for p in perf))
    expected_pairs = {(c, ch) for c in CASES for ch in BUILTIN_MAIN_CHAINS}
    have_pairs = {(r.get("case"), r.get("chain")) for r in chains}
    func_ok = expected_pairs <= have_pairs and all(
        row_functional_ok(r) for r in chains
        if (r.get("case"), r.get("chain")) in expected_pairs)
    if ctx.get("flow_version") in ("official4-p5", "official4-p6-windows"):
        func_ok = func_ok and all(r.get("formal_netlist_stage") == "post_abc"
                                  for r in chains if (r.get("case"), r.get("chain")) in expected_pairs)
    gate("功能证明（内置主链 c4a/c4b）", func_ok)
    certificate_cache={}
    judgments = [judge_case_performance(p, pairs=pairs,certificate_cache=certificate_cache) for p in perf]
    if mean_cpu or single_cpu:gate('四例性能完整性与绝对限值',v4_non_cpu_performance_ok(judgments))
    if single_wall:
        gate("墙钟与峰值内存完整且绝对限值有效", v4_non_cpu_performance_ok(judgments))
        gate("PowerShell墙钟相对开销逐例不超过5%", len(judgments) == 4
             and all(j.get("wall_valid") is True and j.get("wall_5pct") == "PASS"
                     for j in judgments))
        gate("Yosys峰值工作内存逐例不超过5%", len(judgments) == 4
             and all(j.get("memory_valid") is True and j.get("mem_ok") is True
                     for j in judgments))
    elif p6_windows:
        gate("CPU相对开销逐例判定", len(judgments) == 4
             and all(j.get("cpu_ok") is True for j in judgments))
        gate("Yosys峰值工作内存逐例判定", len(judgments) == 4
             and all(j.get("mem_ok") is True for j in judgments))
    gate("四例性能逐例判定", len(perf) == 4 and {p.get("case") for p in perf} == set(CASES)
         and all(j["pass"] for j in judgments))
    gate("四例输入指纹已核验", ctx.get("suite_verified") is True)

    complete = all(gates.values())
    status = BUILTIN_COMPLETE_STATUS if complete else "NEEDS_REVIEW"
    unresolved = [r for r in chains if r.get("state") != "PASS"]
    category_status = {
        "formal": "PASS" if func_ok else "FAIL",
        "resources": "PASS" if p6_windows and gates.get("资源统计完整且取反位计入逻辑单元", False)
        and gates.get("DFF、IO及其他硬件资源逐例不增加", False)
        and area['area_requirement_met'] else "FAIL",
        "cpu": "PASS" if judgments and len(judgments) == 4
        and all(j.get("cpu_ok") is True for j in judgments) else "FAIL",
        "memory": "PASS" if judgments and len(judgments) == 4
        and all(j.get("mem_ok") is True for j in judgments) else "FAIL",
    }
    if single_wall:
        category_status.pop("cpu", None)
        walls = [j.get("wall_5pct", "INVALID") for j in judgments]
        category_status["wall_time"] = (
            "NOT_RUN" if not perf else "INVALID" if len(judgments) != 4 or "INVALID" in walls
            else "FAIL" if "FAIL" in walls else "PASS")
        category_status["memory"] = (
            "NOT_RUN" if not perf else "INVALID" if len(judgments) != 4
            or any(not j.get("memory_valid") for j in judgments)
            else "FAIL" if any(not j.get("mem_ok") for j in judgments) else "PASS")
    elif mean_cpu or single_cpu:
        verdicts=[j.get('cpu_verdict','INVALID') for j in judgments]
        category_status['cpu']=('NOT_RUN' if not perf else 'INVALID' if len(verdicts)!=4 or 'INVALID' in verdicts else
                                'FAIL' if 'FAIL' in verdicts else 'INCONCLUSIVE' if 'INCONCLUSIVE' in verdicts else 'PASS')
        if not perf:category_status['memory']='NOT_RUN'
        elif single_cpu and (len(judgments)!=4 or any(not j.get('memory_valid') for j in judgments)): category_status['memory']='INVALID'
    out = output_root / "11_汇总与证据_summary"
    out.mkdir(exist_ok=True)
    ev_all = evidence.get("evidence") or {}
    opt_ev = ev_all.get("optimized") or {}
    base_ev = ev_all.get("baseline") or {}
    alg_ev = ev_all.get("optimized_algorithm_source") or {}
    delivery = judge_delivery(output_root, ctx)
    verification_verdict = 'PASS' if complete else 'FAIL'
    if single_wall:
        non_performance_gates = {k: v for k, v in gates.items()
                                 if k not in ('墙钟与峰值内存完整且绝对限值有效',
                                              'PowerShell墙钟相对开销逐例不超过5%',
                                              'Yosys峰值工作内存逐例不超过5%',
                                              '四例性能逐例判定')}
        verification_verdict = verification_verdict_v4(
            category_status, all(non_performance_gates.values()))
    elif mean_cpu or single_cpu:
        non_cpu_gates={k:v for k,v in gates.items() if k not in ('CPU相对开销逐例判定','四例性能逐例判定')}
        verification_verdict=verification_verdict_v4(category_status,all(non_cpu_gates.values()))
    readiness = 'READY' if complete and delivery['delivery_verdict'] == 'PASS' and not (single_cpu or single_wall) else 'NOT_READY'
    manifest = {
        "run_status": status, "mode": "builtin",
        'integration_id': I.identity(ctx),
        'integration_profile': ctx.get('integration_profile', 'p3'),
        'integration_patch_sha256': (ctx.get('integration_patch') or {}).get('sha256'),
        'integration_evidence_errors': integration_errors,
        "overall_verdict": verification_verdict,
        "overall_verdict_scope": "工程内四例验证；交付及整体就绪分别见独立字段",
        "verification_verdict": verification_verdict,
        "delivery_verdict": delivery['delivery_verdict'],
        "project_readiness": readiness,
        "project_readiness_scope": "当前四例验证与C55/EQY包检查；不包含答辩材料审查或官方认可",
        "delivery": delivery,
        **area,
        "io_resources": {k: v.get('io_resources') for k, v in io_comparisons.items()},
        "marking": "官方四例内置验收（本地）",
        "official_acceptance": "NOT_CLAIMED",
        "builtin_execution": "COMPLETE" if complete else "NEEDS_REVIEW",
        "builtin_local_acceptance": "COMPLETE" if complete else "NOT_CLOSED",
        "gates": gates, "reasons": reasons,
        "chains_mode": "builtin main (c4a/c4b)",
        "chains_run": sorted(f"{c}/{ch}" for c, ch in sorted(have_pairs)),
        "unresolved_chains": unresolved,
        "performance": judgments,
        "category_status": category_status,
        "builtin_prepare": prep,
        "performance_scheme": scheme,
        'cpu_statistic':'NOT_APPLICABLE' if single_wall else 'single' if single_cpu else 'arithmetic_mean' if mean_cpu else 'median',
        'wall_time_method':SINGLE_WALL_METHOD if single_wall else None,
        'wall_time_statistic':'single' if single_wall else None,
        'wall_time_unit':'milliseconds (TimeSpan.TotalMilliseconds)' if single_wall else None,
        'wall_time_measurement':'Windows PowerShell 5.1 Microsoft.PowerShell.Utility\\Measure-Command elapsed wall time' if single_wall else None,
        'stress_test_status':'WAITING_OFFICIAL_CASES' if single_cpu or single_wall else 'NOT_IN_SCOPE',
        'cpu_method_qualification':(_read_json(root/'10_验证工具自检_selfcheck/cpu_method_qualification/qualification_result.json',{})
                                   or _read_json(root/'01_来源与环境_meta/cpu_qualification.json',{})) if mean_cpu and not etw_cpu else None,
        'cpu_primary_method':None if single_wall else SINGLE_CPU_METHOD if single_cpu else ETW_CPU_METHOD if etw_cpu else None,
        'cpu_etw_selfcheck':_read_json(root/'01_来源与环境_meta/cpu_etw_selfcheck.json',{}) if etw_cpu else None,
        "resource_metric": ("cycloneiv_lcell_comb + independent inverter bits"
                            if p6_windows else "cycloneiv_lcell_comb"),
        "mean_logic_reduction_pct": (
            sum(p.get("logic_reduction_pct") for p in pub) / 4
            if p6_windows and len(pub) == 4 and all(
                isinstance(p.get("logic_reduction_pct"), (int, float)) for p in pub)
            else None),
        "builtin_evidence": evidence,
        "context": ctx, "stages": stages, "evidence_root": str(root),
        "chain_attempt": chain_attempt,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    lines = [
        "# 官方四例内置验收（本地）", "",
        f"执行状态：**{status}**。",
        f"工程内四例验证：**{verification_verdict}**；交付：**{delivery['delivery_verdict']}**；当前流程就绪：**{readiness}**。",
        "兼容字段 overall_verdict 仅覆盖工程内四例验证；项目就绪另含 C55 与本地 EQY 包检查，不覆盖答辩材料或主办方认可。",
        f"形态：**内置四例验收（本地，自动内置准备 + 每例 "
        f"{'一次墙钟、一次独立内存' if single_wall else str(pairs) + ' 对性能'}）**——"
        "原版/优化版两份 Yosys 0.69 隔离构建（复用或按目标源码构建，见“工具准备”）；"
        "外部综合脚本两侧逐字节相同、直接调用 `synth_intel`；优化版由 "
        "`synth_intel.cc` 在 `fsm;opt` 之后、`wreduce` 之前自动调用 `pmux_opt`。"
        "本结论为本地验收，不代表主办方认可；正式评测以官方环境为准。", "",
        f"证据根目录：`{root}`；功能证明链采用 `{chain_attempt}`。", "",
        f"- 算法提交：`{ctx.get('target_commit')}`",
        f"- 项目 HEAD：`{ctx.get('project_head')}`",
        f"- 源码 SHA-256：`{ctx.get('source_sha256')}`",
        f"- 集成身份：`{I.identity(ctx)}`；补丁 SHA-256：`{(ctx.get('integration_patch') or {}).get('sha256', '不适用')}`",
        ('- 7.1：ABC9、清理及命名之后、map_cells 前再调用一次 `pmux_opt -lut`；优化侧 post_abc.il 在该调用之后导出，EQY 实际输入哈希单独核对。' if local_lut else '- P3：仅早期 pmux_opt 调用，保持历史集成。'),
        f"- 优化版构建绑定算法源码：`{alg_ev.get('sha256', 'NOT_RECORDED')}`",
        f"- 原版 Yosys：`{base_ev.get('path', '-')}`（sha256 `{(base_ev.get('sha256') or '')[:16]}…`）",
        f"- 优化版 Yosys：`{opt_ev.get('path', '-')}`（sha256 `{(opt_ev.get('sha256') or '')[:16]}…`）",
        f"- 流程 / 套件：{ctx.get('flow_version')} / {ctx.get('suite_version')}", "",
        "## 工具准备", "",
    ]
    bp = prep.get("baseline") or {}
    op = prep.get("optimized") or {}
    lines += [
        f"- 原版（baseline）：{bp.get('action', '未记录')}" +
        (f"——`{bp.get('path')}`" if bp.get("path") else "") +
        (f"（{bp.get('reason')}）" if bp.get("reason") else ""),
        f"- 优化版（optimized）：{op.get('action', '未记录')}" +
        (f"——`{op.get('path')}`" if op.get("path") else "") +
        (f"（{op.get('reason')}）" if op.get("reason") else ""),
    ]
    if op.get("build_dir"):
        lines.append(f"- 本次构建目录（保留）：`{op.get('build_dir')}`；构建日志："
                     f"`{(op.get('logs') or {}).get('dir', '-')}`")
    lines += [
        f"- 缓存命名空间：`{prep.get('cache_dir', '-')}`；登记条目：`{prep.get('registry_entry', '-')}`",
        (f"- 性能方案：`{scheme or '未标记'}`（墙钟按每例 `testN→baseline→optimized`，"
         "用例顺序为 test1 至 test4；全部墙钟运行后再做独立内存运行）"
         if single_wall else
         f"- 性能方案：`{scheme or '未标记'}`（每例 {pairs} 对、两侧交错；pair 奇 baseline→optimized、"
         "偶 optimized→baseline）"),
        "", "## 检查结果", "", "| 项目 | 结果 |", "|---|---|",
    ]
    lines += [f"| {name} | {'满足' if ok else '未满足或缺证据'} |" for name, ok in gates.items()]
    lines += ['', '## 交付状态', '', '| 检查 | 状态 | 证据 |', '|---|---|---|']
    for name, check in delivery['checks'].items():
        lines.append(f"| {name} | {check['state']} | {check.get('evidence_path', '未提供当前包验收证据')} |")
    lines += ['- ' + reason for reason in delivery['reasons']]
    lines += ['', f"面积10%技术指标：{area['area_requirement_met']}；20%数值档：{area['area_20pct_band_met']}。",
              '按未舍入四例平均判断，20%不是基本通过门槛；不推算10%～20%分数，实际评分由主办方决定。',
              'IO 器件逐类对照：' + json.dumps(manifest['io_resources'], ensure_ascii=False), '']
    if p6_windows:
        lines += ["", "## 分类结论", "",
                  "| 项目 | 结论 |", "|---|---|",
                  f"| Formal（功能等价证明） | {category_status['formal']} |",
                  f"| 资源与逐例缩减率 | {category_status['resources']} |",
                  (f"| PowerShell Measure-Command 墙钟相对开销 | {category_status['wall_time']} |"
                   if single_wall else f"| CPU 相对开销 | {category_status['cpu']} |"),
                  f"| Yosys 主进程峰值内存 | {category_status['memory']} |", ""]
    lines += ["", "## 四例资源与缩减率", ""]
    if p6_windows:
        lines += ["| 用例 | LUT 前→后 | 取反位 前→后 | 逻辑单元 前→后 | 逐例缩减率 | DFF 前→后 | IO 端口 前→后 | IO 位 前→后 |",
                  "|---|---|---|---|---|---|---|---|"]
        rates = []
        for p in pub:
            b, o = p.get("baseline_logic_units"), p.get("optimized_logic_units")
            rate = ((b - o) / b * 100.0) if isinstance(b, (int, float)) and b > 0 \
                and isinstance(o, (int, float)) else None
            rates.append(rate)
            lines.append(
                f"| {p.get('case')} | {p.get('baseline_lut_count')}→{p.get('optimized_lut_count')} "
                f"| {p.get('baseline_inverter_count')}→{p.get('optimized_inverter_count')} "
                f"| {b}→{o} | {_fmt_pct(rate)} "
                f"| {p.get('baseline_dff')}→{p.get('optimized_dff')} "
                f"| {p.get('baseline_io_ports')}→{p.get('optimized_io_ports')} "
                f"| {p.get('baseline_io_bits')}→{p.get('optimized_io_bits')} |")
        average = sum(rates) / 4 if len(rates) == 4 and None not in rates else None
        lines += ["", f"四例逐例缩减率算术平均：{average if average is not None else '不可计算（缺测不缩分母）'}%。",
                  "逻辑单元 = `cycloneiv_lcell_comb` LUT 数 + 独立取反单元输出位数；ABC 后 `$lut` 不加入映射后资源合计。",
                  "DFF、IO 与其他单元另列并逐例检查不增加；Total cells 仅作辅助。", ""]
    else:
        lines += ["| 用例 | Comb 前→后 | DFF 前→后 | Comb 缩减率 |", "|---|---|---|---|"]
        rates = []
        for p in pub:
            b, o = p.get("baseline_comb"), p.get("optimized_comb")
            rate = (b - o) / b * 100 if b else None
            rates.append(rate)
            lines.append(f"| {p.get('case')} | {b}→{o} | {p.get('baseline_dff')}→{p.get('optimized_dff')} | {_fmt_pct(rate)} |")
        average = sum(rates) / 4 if len(rates) == 4 and None not in rates else None
        lines += ["", f"四例 Comb 缩减率算术平均：{average if average is not None else '不可计算（缺测不缩分母）'}%。",
                  "逻辑单元口径为 `cycloneiv_lcell_comb`；DFF 独立检查、不应增加；Total 仅辅助。", ""]
    lines += ["## 功能证明状态", "",
              "内置主链：`c4a_rtl_opt_mapped`（原始 RTL ↔ 优化版功能网表（阶段见下））与 "
              "`c4b_rtl_base_mapped`（原始 RTL ↔ 原版功能网表（阶段见下））；两侧分别独立运行；"
              "test3 保存分区证明；分区未证明时同时保存整设计合并证明日志和结果。插件轮的 `c1_local`/`c2_stage` 依赖 P3 中间网表，"
              "内置流程（synth_intel 内部调用）不产生该中间产物，故本模式不适用（NOT_APPLICABLE，不虚构）。",
              f"内置完整公开证明链：{'PASS' if func_ok else 'NOT_CLOSED'}。", "",
              "每例两侧功能状态（两侧分别独立运行；不使用“两链同结果”推断）："]
    lines += ["- " + s for s in per_side_function_lines(chains)]
    if unresolved:
        lines += [f"- {r.get('case')} / {r.get('chain')}：{r.get('state')}，rc={r.get('rc')}" for r in unresolved]
    else:
        lines += ["- 内置主链全部通过。"]
    memory_header = ("PeakWorkingSet 前→后(MiB)" if p6_windows else "RSS 前→后(KiB)")
    lines += ["- COUNTEREXAMPLE_REQUIRES_REVIEW 表示工具报告分区不等价，需复核配置、假设和反例，"
              "不自动断言算法错误；MODEL_UNSUPPORTED 表示映射模型适用条件不满足，保留条件、不强行证明。", "",
              "## 四例性能（逐例判定）", ""]
    if single_wall:
        lines += ["计时类别：**PowerShell Measure-Command 墙钟时间**。时间单位为秒；原始证据同时保存 TimeSpan.Ticks 与 TotalMilliseconds。",
                  "| 用例 | Measure-Command 墙钟前→后(s) | 墙钟开销 | 5%本地目标 | 15%门槛 | 官方评分状态 | " + memory_header + " | 内存开销 | 内存5% | 60s/2GB | 样本有效 |",
                  "|---|---:|---:|---|---|---|---:|---:|---|---|---|"]
    else:
        lines += ["| 用例 | CPU " + ("单次总时间" if single_cpu else "平均值" if mean_cpu else "中位数") + "前→后(s) | CPU 开销（点估计） | CPU 5% | " + memory_header + " | 内存开销 | 内存 5% | 60s/2GB | 样本有效 |",
                  "|---|---|---|---|---|---|---|---|---|"]
    for j in judgments:
        if single_wall:
            wall = (f"{j['wall_base_ms'] / 1000:.6f}→{j['wall_opt_ms'] / 1000:.6f}"
                    if j.get('wall_base_ms') is not None and j.get('wall_opt_ms') is not None
                    else "不可用")
            midband = j.get("official_midband_score")
            official_score = ("5%门槛内，官方认可未声明" if midband == "UP_TO_5_THRESHOLD"
                              else "5%～15%规则尚未明确" if midband == "NOT_DETERMINED"
                              else "超过15%门槛，无效率分" if midband == "ABOVE_15_THRESHOLD"
                              else "不可判定")
            memory = (f"{j['base_memory_mib']:.2f}→{j['opt_memory_mib']:.2f}"
                      if j.get("base_memory_mib") is not None and j.get("opt_memory_mib") is not None
                      else "不可用")
            limit_disp = "不可判断" if not j['valid'] else "满足" if j["limit_ok"] else "超限"
            if j["limit_bits"].get("wall_exempt_upstream_over_60s") or \
               j["limit_bits"].get("memory_exempt_upstream_over_2gib"):
                limit_disp += "（原版超限例外）"
            lines.append(
                f"| {j['case']} | {wall} | {_fmt_pct(j.get('wall_overhead_pct'))} | "
                f"{j.get('wall_5pct')} | {j.get('wall_15pct')} | {official_score} | {memory} | "
                f"{_fmt_pct(j.get('mem_overhead_pct'))} | "
                f"{'满足' if j.get('mem_ok') else '未满足'} | {limit_disp} | {j['valid']} |")
            lines += ['- ' + j['case'] + '：' + reason for reason in j['reasons']]
            continue
        cpu = f"{j['base_cpu_s']}→{j['opt_cpu_s']}"
        rss = (f"{j['base_memory_mib']:.2f}→{j['opt_memory_mib']:.2f}"
               if p6_windows and j.get("base_memory_mib") is not None
               and j.get("opt_memory_mib") is not None else
               f"{j['base_rss_kb']}→{j['opt_rss_kb']}")
        limit_disp = "不可判断" if not j['valid'] else "通过" if j["limit_ok"] else "超限"
        if j["limit_bits"].get("cpu_exempt_upstream_over_limit") or \
           j["limit_bits"].get("rss_exempt_upstream_over_limit"):
            limit_disp += "（原版超限例外）"
        lines.append(
            f"| {j['case']} | {cpu} | {_fmt_pct(j['cpu_overhead_pct'])} | "
            f"{j.get('cpu_verdict') if mean_cpu else '满足' if j['cpu_ok'] else '未满足'} | {rss} | {_fmt_pct(j['mem_overhead_pct'])} | "
            f"{'满足' if j['mem_ok'] else '未满足'} | {limit_disp} | {j['valid']} |")
        lines += ['- ' + j['case'] + '：' + reason for reason in j['reasons']]
    lines += ["",
              ("V7每例每侧一次 Measure-Command 墙钟运行，8次墙钟完成后另做8次独立内存运行；不预热、不平均、不取中位数、不自动补跑。墙钟相对开销按（优化版−原版）/原版，使用原始 TimeSpan.Ticks 对5%和15%门槛比较。墙钟是经过时间，不标记为CPU时间；Ticks是表示单位，不代表100ns实际精度。官方允许 Measure-Command，但墙钟与早期CPU术语的评分对应关系尚未明确。" if single_wall else
               "每例每侧一次普通CPU、一次独立内存，共16次；不预热、不平均、不取中位数、不自动补跑。原始整数逐例比较5%。" if single_cpu else "事件CPU每侧300次，原始整数计数取算术平均；平均开销≤5%为PASS，>5%为FAIL。统计区间和A/A差异仅提示，不叠加Job一致性裕量。内存每侧15次中位数。" if etw_cpu else "CPU每侧300次完整普通运行，20批×15对，全部原始整数计数取算术平均。每批5对原版A/A单独统计。配对整批Bootstrap 20000次、种子20261011、近似95%分位区间，加资格裕量为扩展区间；它不是严格95%总误差保证。均值≤5%的点估计与PASS/FAIL/INCONCLUSIVE分开；内存仍每侧15次取中位数。" if mean_cpu else
               f"每侧 {pairs} 次交错运行、取中位数；相对开销 =（优化版-原版）/原版，逐例与 5% 比较（边界值按不超过处理；不跨例平均、不使用舍入后的显示值）。"),
              ("V7在 Windows PowerShell 5.1 中用 Microsoft.PowerShell.Utility\\Measure-Command 包裹直接启动 yosys.exe、并发收集 stdout/stderr、等待退出并排空输出流；PowerShell启动、工具构建、EQY、结果检查和报告生成不计入墙钟。" if single_wall else
               "CPU由Yosys主函数中的私有Job累计用户态与内核态时间，包含已退出ABC及其子进程。入口建立计量至退出前读取；不含计量文件写入和操作系统最后退出尾段。100ns是计数单位，不是精度保证。外部Job及墙钟仅诊断，调试运行CPU不评分。" if single_cpu else "CPU来自ETW线程切换事件，包含Yosys和全部子进程含ABC；扣除DPC/ISR，完整生命周期核验，无事件或资源证据不回退Job。每批独立采集，全部CPU分析后再测退出事件内存；调试CPU不计分。" if etw_cpu else "CPU与A/A全部完成后，再测根进程退出事件内存；两侧相同外部脚本，各次资源统计与对应正式综合一致。CPU来自未调试的Job Object，包含ABC；调试CPU不得评分。首轮、慢样本和原始计数保留，不预热、不扣启动，不追加采样。" if mean_cpu else
               "CPU用独立的普通Job Object运行，包含ABC子进程；内存另用同输入同脚本的根进程退出调试事件运行，只计Yosys。每侧15个CPU样本和15个内存样本各取中位数，两次运行的日志、统计和退出状态全部保留。调试运行CPU不用于CPU评分。"
               if exit_peak else
               "CPU 使用 Windows Job Object 累计用户态与内核态时间，包含 ABC 子进程；内存每 5 ms 读取存活中的 Yosys 主进程 PeakWorkingSetSize 累计峰值字段，"
               "以字节记录，不含 ABC；无有效采样的样本判无效。"
               if p6_windows else
               "CPU 时间为 wait4 采集并覆盖子进程树（含 ABC 子进程）；测量自检含孙进程 CPU 累计检查。"),
              ("在匹配根PID的EXIT_PROCESS_DEBUG_EVENT中，读取系统累计PeakWorkingSetSize后再ContinueDebugEvent放行最后清理。末段不依赖轮询；完整退出事件、读数和正常放行缺一即样本无效，不回退旧采样。调试可能影响内存布局，本值对应事件观测运行；不得声称等于未调试运行内存。该具体方法官方认可尚未确认。"
               if exit_peak else
               "Windows 在运行期间读取系统维护的 PeakWorkingSetSize 累计峰值；退出前最后一个成功采样间隔可能漏峰。5 ms 为目标间隔，实际调度可延迟，不保证误差上界；官方对该具体测量方法的认可尚未确认。"
               if p6_windows else
               ("p5 内存仅计 Yosys 主进程 Linux VmHWM，5ms 轮询；不含 ABC 和计时包装器；短进程可能缺测。"
                if ctx.get("flow_version") == "official4-p5" else
                "历史内存为 5ms 间隔进程组 RSS 求和采样；可能漏峰、重复计共享页或含包装器。")),
              ("内存计数口径与 Windows 系统峰值工作集字段一致。" if p6_windows else
               "不是精确官方内存计量。"),
              "60s/2GB 以原版为对照；原版超限时允许优化版也超限；不自行发明扣分计算。",
              "无效样本（含工具失败、超时、缺失）不判定通过；原始样本全部保留、不自动剔除。", "",
              "## 证据", "",
              "- `01_来源与环境_meta/builtin_evidence.json`：两侧二进制/源码/ABC/数据文件与指纹绑定。",
              "- `04_流程一致性_flowcheck/builtin_run01/`：优化版自动调用 pmux_opt 的位置与次数证据。",
              "- `05_公开四例_public/round01/`：功能 post_abc.il（ABC9 后、map_cells 前）；资源 mapped.il 与 stat；性能运行完整综合。",
              "- `01_来源与环境_meta/工具链与构建证据/`：Yosys、ABC、EQY、编译器版本，MSYS2 依赖包指纹及两侧构建日志。",
              "功能输入阶段：" + ("ABC9 后 $lut + 受支持 dffeas" if ctx.get("flow_version") in ("official4-p5", "official4-p6-windows") else "历史最终映射网表"),
              "其他硬件资源对照：" + json.dumps({p.get("case"): p.get("other_resources") for p in pub}, ensure_ascii=False),
              f"- `10_验证工具自检_selfcheck/chains/{chain_attempt}/`：功能证明（含支持配置预检与逐分区证据）。",
              f"- 本报告清单：`{out / 'manifest.json'}`。",
              f"- 全量证据哈希：`{out / 'ALL_SHA256.txt'}`（与报告同轮生成或更新）。", "",
              "阶段完成不等于功能或性能通过；缺失证据与需复核项保持原样记录；没有擅自补充官方分数。"]
    if single_wall:
        lines += ['', 'V7仅覆盖当前本地公开用例 test1～test4，不能代表全部官方效率测试；新增官方效率用例尚待提供。',
                  '5%～15%之间的官方评分规则尚未明确；>15%按最新答疑“不计效率分”的门槛单列。官方允许PowerShell Measure-Command，不等于主办方已认可本地具体实现或墙钟与CPU术语的评分对应。',
                  'V7复用退出事件内存法（只计Yosys主进程，不含ABC）；V7没有交付包复核证据，交付为NOT_RUN、当前就绪为NOT_READY。']
    if single_cpu:
        lines += ['', '千节点压力测试：WAITING_OFFICIAL_CASES，等待官方统一用例；四例结果不外推。',
                  '依据最新答疑C87，CPU和内存相对开销不得超过5%；不推算未明确的扣分公式。',
                  '原版无PMUX优化，两侧包含同一公共计量补丁。交付包未在本次重建，不继承旧包通过状态。']
    if etw_cpu:
        from performance_report_v5 import report_lines
        pos=lines.index('## 证据');lines[pos:pos]=report_lines(judgments,manifest['cpu_etw_selfcheck'])
    elif mean_cpu:
        interval_lines=['## CPU稳定性与方法资格','',
            '点估计满足5%只描述均值，不等于已证明满足。统计区间与扩展区间分别列示；扩展区间不是严格95%总误差保证。',
            '| 用例 | 均值点估计满足5% | 近似95%统计区间 | 资格裕量(百分点) | 扩展区间 | A/A正常 |',
            '|---|---|---|---|---|---|']
        for j in judgments:
            interval_lines.append('| {} | {} | {} | {} | {} | {} |'.format(j['case'],j.get('cpu_point_requirement_met'),
                j.get('cpu_ci95_pct'),j.get('guard_pct'),j.get('cpu_expanded_interval_pct'),j.get('aa_ok')))
        q=manifest['cpu_method_qualification'] or {}
        q_summary={k:q.get(k) for k in ('ok','qualified','required','guard_pct','actual_samples') if k in q}
        q_error=q.get('error') or q.get('reason')
        if q_error:q_summary['原因摘要']=str(q_error)[:500]
        interval_lines += ['', 'CPU方法资格记录：'+json.dumps(q_summary,ensure_ascii=False),
                           '完整资格指纹、错误及原始证据见10_验证工具自检_selfcheck/cpu_method_qualification与01_来源与环境_meta/cpu_qualification.json。',
                           '资格校验失败、样本未完成或A/A异常时，不能宣布CPU目标通过；原始失败记录保留。','']
        pos=lines.index('## 证据');lines[pos:pos]=interval_lines
    (output_root / "00_本轮验证结论.md").write_text("\n".join(lines) + "\n")
    return status


def build_function_recheck_report(root, output_root=None, chain_attempt="run01", ctx=None):
    """插件版功能补充复核（冻结网表；不重新综合、不重测性能）。"""
    root = Path(root)
    output_root = Path(output_root) if output_root else root
    output_root.mkdir(parents=True, exist_ok=True)
    ctx = ctx or _read_json(root / "validation_context.json", {})
    stages = _read_json(root / "01_来源与环境_meta/stages.json", [])
    chains = _read_json(
        root / f"10_验证工具自检_selfcheck/chains/{chain_attempt}/chains_summary.json", [])
    frozen = _read_json(
        root / f"10_验证工具自检_selfcheck/chains/{chain_attempt}/frozen_input_verification.json", {})

    gates, reasons = {}, []

    def gate(name, passed):
        gates[name] = bool(passed)
        if not passed:
            reasons.append(name)

    stage_by = {s.get("name"): s for s in stages}
    names = {s.get("name") for s in stages}
    exec_ok = all(
        (stage_by.get(n) or {}).get("rc") == 0
        and (stage_by.get(n) or {}).get("state") in ("COMPLETED", "REUSED")
        for n in FUNCTION_ONLY_EXEC)
    skipped_ok = all(
        (stage_by.get(n) or {}).get("state") == "NOT_RUN" for n in FUNCTION_ONLY_SKIPPED)
    gate("执行阶段（功能复核）",
         names == set(FUNCTION_ONLY_EXEC) | set(FUNCTION_ONLY_SKIPPED) and exec_ok and skipped_ok)
    iso = ctx.get("isolation") or {}
    gate("插件构建与隔离", (stage_by.get("build") or {}).get("rc") == 0
         and (stage_by.get("build") or {}).get("state") in ("COMPLETED", "REUSED")
         and iso.get("baseline_no_pmux") is True and iso.get("plugin_has_pmux") is True)
    gate("冻结输入来源核验", frozen.get("ok") is True and bool(frozen.get("files")))
    precheck = root / f"10_验证工具自检_selfcheck/chains/{chain_attempt}/precheck_report.txt"
    precheck_text = precheck.read_text(errors="replace") if precheck.exists() else ""
    gate("支持配置预检", precheck_text.startswith("[通过]"))
    expected_pairs = {(c, ch) for c in CASES for ch in MAIN_CHAINS}
    have_pairs = {(r.get("case"), r.get("chain")) for r in chains}
    func_ok = expected_pairs <= have_pairs and all(
        row_functional_ok(r) for r in chains
        if (r.get("case"), r.get("chain")) in expected_pairs)
    gate("功能证明（默认链集合；两侧）", func_ok)

    status = "FUNCTION_RECHECK_COMPLETE" if all(gates.values()) else "NEEDS_REVIEW"
    out = output_root / "11_汇总与证据_summary"
    out.mkdir(exist_ok=True)
    manifest = {
        "run_status": status, "mode": "plugin", "function_only": True,
        "marking": "插件版功能补充复核", "official_acceptance": "NOT_CLAIMED",
        "final_builtin_acceptance": "NOT_RUN",
        "frozen_round": ctx.get("frozen_round"),
        "gates": gates, "reasons": reasons,
        "chains_mode": ctx.get("chains_mode"),
        "chains_run": sorted("{}/{}".format(c, ch) for c, ch in sorted(have_pairs)),
        "performance": "NOT_MEASURED_THIS_ROUND（引用既有轮次）",
        "context": ctx, "stages": stages, "evidence_root": str(root),
        "chain_attempt": chain_attempt,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    lines = [
        "# 插件版功能补充复核（官方四例 · 冻结网表）", "",
        f"执行状态：**{status}**。",
        "形态：**插件版功能补充复核**——使用修订后的功能路径（模型 `dffeas-v3` + 本地策略修正 "
        "`noDF-local-r1` + 支持配置预检；test3 为无切割整模块合并证明），在冻结的既有轮次产物上"
        "复验四例功能。**未重新综合、未重测性能**；**最终内置四例验收：NOT_RUN**——本复核不构成官方验收，"
        "也不能替代内置四例验收。", "",
        "证据根目录：`{}`；功能证明链采用 `{}`。".format(root, chain_attempt), "",
        "- 算法提交：`{}`".format(ctx.get("target_commit")),
        "- 项目 HEAD：`{}`".format(ctx.get("project_head")),
        "- 源码 SHA-256：`{}`".format(ctx.get("source_sha256")),
        "- 插件 SHA-256：`{}`".format(ctx.get("plugin_sha256", "NOT_BUILT")),
        "- 流程 / 模型 / 策略：{} / {} / {}".format(ctx.get("flow_version"),
                                                   ctx.get("model_version"),
                                                   ctx.get("strategy_version")),
        "- 冻结来源轮次：`{}`（输入逐文件哈希对照该轮 ALL_SHA256.txt）".format(ctx.get("frozen_round")),
        "- 链集合：{}（main=主路径+对照+定位；full=全部链）".format(ctx.get("chains_mode", "main")), "",
        "## 检查结果", "", "| 项目 | 结果 |", "|---|---|",
    ]
    lines += ["| {} | {} |".format(name, "满足" if ok else "未满足或缺证据")
              for name, ok in gates.items()]
    lines += ["", "## 每例两侧功能状态", "",
              "两侧分别独立运行；不使用“两链同结果”推断（test3 为无切割合并证明，"
              "其余用例为分区路径）。"]
    lines += ["- " + s for s in per_side_function_lines(chains)]
    lines += ["", "## 模型、策略与判据", "",
              "- 模型：器件语义模型 v3（clrn 异步清零 / ena 时钟使能 / power_up 初值；"
              "支持配置预检阻断未支持条件，未支持不静默建模）。",
              "- 策略：本地策略修正 noDF-local-r1——EQY setup（-m）只生成分区与脚本 → 严格转换"
              "（仅删除恰一处 ` -set-def-formal`，其余逐字节不变；格式不符即停止）→ 本地执行；"
              "附前提探针（noDF 必需 SAT；DF 记录历史签名）。",
              "- 判据（联合，不依赖单一 SUCCESS 字样）：成功标记 + 基例数 >= 归纳长度 + 断言导入覆盖 + "
              "全文无 ERROR；链级另加全部 noDF 前提探针 SAT。",
              "- 探针局限：`sat -seq 1` 仅证明初态前提可满足，不声称任意时刻可达性。",
              "- 合并证明语义：比较器对 gold 未定义位采用 x 容差；不声称对任意独立二态初值逐点相等。", "",
              "## 资源与性能（引用，未重测）", "",
              "- 本轮**未重新综合、未测 CPU/内存**；资源与性能请引用对应既有轮次（见 `frozen_round` 下 "
              "`05_公开四例_public/round01/summary.json`、`09_时间内存开销_performance/` 与该轮结论报告）。"
              "数字未在本轮产生，不得作为本轮新测引用。", "",
              "## 未完成与边界", "",
              "- 内置四例验收：NOT_RUN（本复核不替代）；流程一致性/测量自检/性能：本轮 NOT_RUN（见阶段表）。",
              "- 四例范围之外（H1/H2/规模/多驱动/回归）不在本模式范围。", "",
              "## 证据", "",
              "- `10_验证工具自检_selfcheck/chains/{}/frozen_input_verification.json`：冻结输入逐文件哈希核对。".format(chain_attempt),
              "- `10_验证工具自检_selfcheck/chains/{}/precheck_report.txt`：支持配置预检。".format(chain_attempt),
              "- `10_验证工具自检_selfcheck/chains/{}/**`：逐分区转换记录、证明与探针日志、合并证明。".format(chain_attempt),
              "- `01_来源与环境_meta/stages.json`：阶段状态（含 NOT_RUN 及原因）。",
              "- `10_验证工具自检_selfcheck/attempt01/**`：形式化自检（初值/清零/使能/LUT/矛盾前提回归）。",
    ]
    (output_root / "00_本轮验证结论.md").write_text("\n".join(lines) + "\n")
    return status
