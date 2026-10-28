"""Windows V8 官方套件报告入口与共用判定；缺失证据永不算通过。

正式墙钟、退出事件内存及同次产物判定由 report_v8.py 负责。
共用资源、功能和交付判定，以及工具准备失败/阻断报告保留在此。
"""
import json
import math
import hashlib
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'runner'))
import result_layout as L
from measure_v8 import SCHEME, evaluate_summary

OVERHEAD_EPS_PCT = 1e-9
import official_suite as S
BUILTIN_EXPECTED_STAGES = {'build', 'flowcheck', 'formal_selfcheck',
                           'measurement_selfcheck', 'public', 'chains', 'performance'}
BUILTIN_MAIN_CHAINS = ('c4a_rtl_opt_mapped', 'c4b_rtl_base_mapped')
BUILTIN_COMPLETE_STATUS = 'BUILTIN_SUITE_LOCAL_ACCEPTANCE_COMPLETE'
BUILTIN_FOLLOW_UP = (
    '1) 按日志修复失败原因后，使用 validate_windows_v8.cmd plan <完整提交> 只读预检，'
    '再运行已授权的内置套件验收。',
    '2) baseline 按登记核对复用；optimized 按算法源码、基础提交、集成模板、构建参数、'
    '编译器和 ABC 身份复用缓存，未命中时在隔离源码树构建；失败保留 FAILED 诊断。',
    '3) 内置外部脚本、插入位点与判定方法见 POLICY.md。',
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
    """委派 V8 逐例判定；无效或旧格式证据不得通过。"""
    return evaluate_summary(summ)


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


def per_side_function_lines(chains, context):
    """每例两侧功能状态（两侧分别独立运行；不使用“两链同结果”推断）。"""
    def find(case, chain):
        return next((r for r in chains if r.get("case") == case and r.get("chain") == chain), None)

    lines = []
    for case in S.case_ids(context):
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


def build_report(root, output_root=None, chain_attempt='run01', stages_override=None, mode=None):
    """兼容既有调用接口，仅支持 V8 内置报告。"""
    ctx = _read_json(Path(root) / 'validation_context.json', {})
    if (mode if mode is not None else ctx.get('mode', 'builtin')) != 'builtin':
        raise ValueError('Only Windows V8 builtin reports are supported')
    return build_builtin_report(root, output_root=output_root, chain_attempt=chain_attempt,
                                stages_override=stages_override)


def build_builtin_block_report(root, status, missing, evidence, cfg):
    """内置套件验收的未就绪阻断记录（不执行任何验收进程）。"""
    root = Path(root)
    out = root / L.SUMMARY
    out.mkdir(parents=True, exist_ok=True)
    context = {k: cfg.get(k) for k in ("flow_version", "suite_version", "target_commit",
                                       "source_sha256", "project_head", "suite_verified")}
    manifest = {
        "run_status": status, "mode": "builtin", "marking": "官方套件内置验收（未就绪阻断）",
        "official_acceptance": "NOT_CLAIMED", "builtin_execution": "NOT_READY",
        "missing_items": missing, "follow_up": list(BUILTIN_FOLLOW_UP),
        "evidence": evidence, "context": context, "evidence_root": str(root),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    lines = [
        "# 官方套件内置验收 —— 未就绪阻断", "",
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
        "## 内置套件验收要求（契约）", "",
        "- 原版与优化版均为 Yosys 0.69 的可追溯构建；记录基础源码提交、构建信息、二进制指纹、"
        "ABC、实际数据文件和插入调用证据。",
        "- 优化版在 `synth_intel.cc` 中调用 `pmux_opt`（C24/C37）；外部综合脚本两侧内容相同、"
        "直接调用 `synth_intel`。",
        "- 路径参数分别指向两份工具，不要求二进制哈希相同。",
        "## 证据", "",
        f"- 内置证据检查：`{root / (L.META + '/builtin_evidence.json')}`",
        f"- 清单：`{out / 'manifest.json'}`",
    ]
    (root / L.REPORT).write_text("\n".join(lines) + "\n")
    return status


def build_builtin_build_failed_report(root, error, cfg, build_dir=None, logs=None):
    """内置工具准备失败记录（构建失败/环境不满足）；不启动验收进程、不退回插件。"""
    root = Path(root)
    out = root / L.SUMMARY
    out.mkdir(parents=True, exist_ok=True)
    context = {k: cfg.get(k) for k in ("flow_version", "suite_version", "target_commit",
                                       "source_sha256", "project_head", "suite_verified")}
    manifest = {
        "run_status": "BUILTIN_BUILD_FAILED", "mode": "builtin",
        "marking": "官方套件内置验收（工具准备失败）",
        "official_acceptance": "NOT_CLAIMED", "builtin_execution": "BUILD_FAILED",
        "error": error, "build_dir": build_dir, "logs": logs or {},
        "context": context, "evidence_root": str(root),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    lines = [
        "# 官方套件内置验收 —— 工具准备失败", "",
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
              f"- 工具准备记录：`{root / (L.META + '/builtin_prepare.json')}`",
              f"- 阶段记录：`{root / (L.META + '/stages.json')}`",
              f"- 清单：`{out / 'manifest.json'}`",
              ]
    (root / L.REPORT).write_text("\n".join(lines) + "\n")
    return "BUILTIN_BUILD_FAILED"


def build_builtin_report(root, output_root=None, chain_attempt='run01', stages_override=None):
    """保留原接口，将正式字段和结论逻辑交给 V8 报告模块。"""
    root = Path(root)
    ctx = _read_json(root / 'validation_context.json', {})
    if str(ctx.get('performance_scheme','')).endswith('-v9'):
        from report_v9 import build_report
        return build_report(root, output_root=output_root, chain_attempt=chain_attempt, stages_override=stages_override)
    if ctx.get('performance_scheme') != SCHEME:
        raise ValueError('Only the Windows V8 same-run report scheme is supported')
    from report_v8 import build_report
    return build_report(root, output_root=output_root, chain_attempt=chain_attempt,
                        stages_override=stages_override)
