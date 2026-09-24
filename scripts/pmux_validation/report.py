"""官方四例（official4-p1）判定与中文报告；缺失证据永不算通过。

判定规则（详见 POLICY.md，来源为官方答疑 Sheet1 C21~C26、C34、C37、C41）：
- 逻辑单元（cycloneiv_lcell_comb）逐例缩减率算术平均；DFF 单独检查、不应增加；
- 逐例比较 CPU/内存相对开销与 5%（边界值按不超过处理；不跨例平均、不使用舍入值）；
- 60s/2GB 以原版为对照，原版超限时允许优化版也超限，不自行发明扣分计算；
- 插件预检永远不能得出内置验收完成；缺功能证明、工具错误、无效样本不输出通过。
"""
import json
from pathlib import Path

OVERHEAD_LIMIT_PCT = 5.0
# 判定使用未舍入值；仅容忍 1e-9 个百分点量级的浮点表示误差（不等于四舍五入后的显示值比较）。
OVERHEAD_EPS_PCT = 1e-9
CPU_LIMIT_S = 60.0
RSS_LIMIT_KB = 2 * 1024 * 1024
CASES = ("test1", "test2", "test3", "test4")
MAIN_CHAINS = ("c1_local", "c2_stage", "c4a_rtl_opt_mapped", "c4b_rtl_base_mapped")
FULL_CHAINS = ("c1_local", "c2_stage", "c3a_rtl_opt", "c3b_rtl_base",
               "c4a_rtl_opt_mapped", "c4b_rtl_base_mapped", "c5_mapped_pair")
EXPECTED_PLUGIN_STAGES = {"build", "flowcheck", "formal_selfcheck", "measurement_selfcheck",
                          "public", "chains", "performance"}
BUILTIN_FOLLOW_UP = (
    "1) 在 validate.py 增加内置执行路径：两份 Yosys 0.69 对四例直接调用 synth_intel（外部脚本内容相同），记录网表与 stat。",
    "2) 内置形态功能证明：原始 RTL 与优化版最终映射网表按默认链集合口径运行 EQY；条件不满足时保留 MODEL_UNSUPPORTED。",
    "3) 资源与性能统计复用现有 runner（cycloneiv_lcell_comb、DFF、逐例 5% 与 60s/2GB 对照）。",
    "4) 内置 pass 位于 synth_intel.cc 内部，流程一致性检查与插件形态不同，需单独设计并验证。",
    "5) 完成执行路径的模拟测试覆盖后，方可开放 run 默认执行；在此之前保持阻断。",
)


def overhead_pct(base, opt):
    """未舍入相对开销（%）。基线为零或缺失时不可计算。"""
    if base is None or opt is None or base == 0:
        return None
    return (opt - base) / base * 100.0


def judge_case_performance(summ, pairs=5):
    """逐例性能判定。无效样本不判通过；5% 边界按不超过处理；不做跨例平均。"""
    runs = summ.get("runs") or []
    reasons = []

    def count(side):
        return sum(1 for r in runs if r.get("side") == side)

    valid = (
        len(runs) == pairs * 2
        and count("baseline") == pairs and count("optimized") == pairs
        and all(
            r.get("rc") == 0 and not r.get("timed_out") and r.get("stat_exists") is True
            and (r.get("cpu_total_s") or 0) > 0 and (r.get("tree_rss_peak_kb") or 0) > 0
            for r in runs
        )
    )
    base_cpu = summ.get("baseline_cpu_total_median")
    opt_cpu = summ.get("optimized_cpu_total_median")
    base_rss = summ.get("baseline_tree_rss_peak_median")
    opt_rss = summ.get("optimized_tree_rss_peak_median")
    cpu_over = overhead_pct(base_cpu, opt_cpu) if valid else None
    mem_over = overhead_pct(base_rss, opt_rss) if valid else None
    cpu_ok = valid and cpu_over is not None and cpu_over <= OVERHEAD_LIMIT_PCT + OVERHEAD_EPS_PCT
    mem_ok = valid and mem_over is not None and mem_over <= OVERHEAD_LIMIT_PCT + OVERHEAD_EPS_PCT
    limit_ok, limit_bits = False, {}
    if valid and opt_cpu is not None and opt_rss is not None:
        cpu_exempt = base_cpu is not None and base_cpu > CPU_LIMIT_S
        rss_exempt = base_rss is not None and base_rss > RSS_LIMIT_KB
        limit_bits = {"cpu_exempt_upstream_over_limit": cpu_exempt,
                      "rss_exempt_upstream_over_limit": rss_exempt}
        limit_ok = (opt_cpu <= CPU_LIMIT_S or cpu_exempt) and (opt_rss <= RSS_LIMIT_KB or rss_exempt)
    if not valid:
        reasons.append("样本不完整或存在无效样本，不判定通过")
    elif not cpu_ok:
        reasons.append("CPU 相对开销超过 5%")
    if valid and not mem_ok:
        reasons.append("内存相对开销超过 5%")
    if valid and not limit_ok:
        reasons.append("超出 60s/2GB 且原版未超限")
    return {
        "case": summ.get("case"), "valid": valid,
        "cpu_overhead_pct": cpu_over, "mem_overhead_pct": mem_over,
        "cpu_ok": cpu_ok, "mem_ok": mem_ok, "limit_ok": limit_ok, "limit_bits": limit_bits,
        "base_cpu_s": base_cpu, "opt_cpu_s": opt_cpu,
        "base_rss_kb": base_rss, "opt_rss_kb": opt_rss,
        "pass": bool(valid and cpu_ok and mem_ok and limit_ok),
        "reasons": reasons,
    }


def _read_json(path, default):
    path = Path(path)
    return json.loads(path.read_text()) if path.exists() else default


def _fmt_pct(value):
    return f"{value:.3f}%" if value is not None else "不可计算"


def build_report(root, output_root=None, chain_attempt="run01", stages_override=None, mode=None):
    root = Path(root)
    output_root = Path(output_root) if output_root else root
    output_root.mkdir(parents=True, exist_ok=True)
    ctx = _read_json(root / "validation_context.json", {})
    if mode is None:
        mode = ctx.get("mode", "plugin")
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
        r.get("state") == "PASS" and r.get("rc") == 0
        for r in chains if (r.get("case"), r.get("chain")) in expected_pairs)
    gate("功能证明（默认链集合）", default_pass)
    judgments = [judge_case_performance(p, pairs=pairs) for p in perf]
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
              f"完整公开证明链：{'PASS' if default_pass else 'NOT_CLOSED'}。"]
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
              "每侧五次交错运行、取中位数；相对开销 =（优化版-原版）/原版，逐例与 5% 比较"
              "（边界值按不超过处理；不跨例平均、不使用舍入后的显示值）。",
              "CPU 时间为 wait4 采集并覆盖子进程树（含 ABC 子进程）；测量自检含孙进程 CPU 累计检查。",
              "内存为 5ms 间隔进程组 RSS 求和采样；可能漏掉短峰值、重复计入共享页、包含包装进程；"
              "不是精确官方内存计量。",
              "60s/2GB 以原版为对照；原版超限时允许优化版也超限；不自行发明扣分计算。",
              "无效样本（含工具失败、超时、缺失）不判定通过；原始样本全部保留、不自动剔除。", "",
              "## 证据", "",
              "- `validation_context.json`：工具、提交、四例输入套件、代码指纹与隔离检查结果。",
              "- `01_来源与环境_meta/stages.json`：本阶段状态；自检阶段带 `REUSED` 标记时表示按指纹复用。",
              f"- 本报告清单：`{out / 'manifest.json'}`。",
              f"- 全量证据哈希：`{out / 'ALL_SHA256.txt'}`（生成于运行收尾）。", "",
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
                  "内置证据预检通过；但本版本未包含内置四例执行器（见后续清单），因此仍为阻断状态。", ""]
    lines += ["## 后续实现清单", ""] + [f"- {item}" for item in BUILTIN_FOLLOW_UP] + [""]
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
