#!/usr/bin/env python3
"""官方四例验证入口（official4-p4）。Linux/WSL，标准库实现。

默认目标：官方四例内置验收——先自动准备内置工具（baseline 复用登记核对；
optimized 按缓存键查可复用构建，未命中则在缓存命名空间内从本地 Yosys 基础
提交建立隔离源码树并构建、冒烟验证后登记），再执行真实内置调度：四例两侧
运行逐字节相同的外部脚本（直接调用 synth_intel），收集资源、功能证明
（RTL↔最终映射网表）与性能（每例 15 对交错）；准备或身份检查失败时生成
明确的阻断/失败记录，不加载插件、不启动验收进程，也不自动退回插件方案。

显式插件预检：`run <commit> --mode plugin`。本地编译插件后运行四例（资源、功能、
性能），全程标记“四例插件预检”；插件结果不构成内置验收。

范围与判定规则见同目录 POLICY.md；本入口固定官方公开四例（test1~test4），
不默认运行回归、H2、规模或多驱动测试（相关模块与资产保留原位）。
"""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import uuid

PACKAGE = Path(__file__).resolve().parent
ROUND_LABEL_DEFAULT = "稳定版-四例"
ROUND_PARENT_REL = "results/官方口径评测"
SELFCHECK_CACHE_REL = "results/官方口径评测/_共享自检缓存_selfcheck/selfcheck_cache.json"

# 插件预检的阶段计划（默认调度只含四例所需内容；不含回归/H2/规模/多驱动）。
PLUGIN_PLAN = (
    ("flowcheck", "run_flowcheck.py", ()),
    ("formal_selfcheck", "run_selfcheck.py", ()),
    ("measurement_selfcheck", "measure.py", ("--selftest",)),
    ("public", "run_public.py", ()),
    ("chains", "run_eqy_chains.py", ()),
    ("performance", "measure.py", ()),
)
# 功能补充复核（--function-only）：只运行功能相关阶段；不重新综合、不测性能。
FUNCTION_ONLY_PLAN = (
    ("formal_selfcheck", "run_selfcheck.py", ()),
    ("chains", "run_eqy_chains.py", ()),
)
FUNCTION_ONLY_SKIPPED = (
    ("flowcheck", "功能复核：未重新综合（流程一致性引用既有轮次）"),
    ("measurement_selfcheck", "功能复核：未测性能（测量自检引用既有轮次）"),
    ("public", "功能复核：不重新综合四例（使用冻结映射网表）"),
    ("performance", "功能复核：不重测性能（引用既有轮次）"),
)
PLUGIN_STAGE_DEPS = {"chains": ("public",)}
SELFCHECK_STAGES = ("flowcheck", "formal_selfcheck", "measurement_selfcheck")
PLUGIN_STAGES = ("build",) + tuple(name for name, _, _ in PLUGIN_PLAN)

# 内置四例执行计划（工具自动准备后调度）。两侧内置二进制直接运行逐字节相同的
# 外部脚本（gen_builtin_synth_ys）；flowcheck 核对优化版自动调用 pmux_opt
# 的位置与次数；chains 使用内置产物 mapped 网表（链集合 c4a/c4b 主证明）；
# performance 使用同一外部脚本按 performance_pairs（默认 15）对交错测量。
BUILTIN_PLAN = (
    ("flowcheck", "run_builtin_flowcheck.py", ()),
    ("formal_selfcheck", "run_selfcheck.py", ()),
    ("measurement_selfcheck", "measure.py", ("--selftest",)),
    ("public", "run_builtin_public.py", ()),
    ("chains", "run_eqy_chains.py", ("--attempt", "run01", "--chains", "main",
                                     "--input-mode", "builtin")),
    ("performance", "measure.py", ()),
)
BUILTIN_STAGES = ("build",) + tuple(name for name, _, _ in BUILTIN_PLAN)
# 内置模式与插件模式检查内容一致的自检阶段（可按指纹复用缓存）；
# 内置 flowcheck 为专用检查（内置调用证据），不跨模式复用缓存。
BUILTIN_CACHED_STAGES = ("formal_selfcheck", "measurement_selfcheck")

BUILTIN_MISSING_HINT = (
    "内置证据未就绪：本次不启动验收进程、不加载插件、不退回插件方案；"
    "补足缺项，或按绑定的算法源码重新构建并登记后再运行。"
)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def verify_package_manifest(package):
    """脚本包清单核对：清单内文件必须一致；活动包文件必须全部登记。

    任一项不符即停止（不静默刷新清单）。
    """
    package = Path(package)
    manifest = json.loads((package / "PACKAGE_SHA256.json").read_text())
    problems = []
    for rel, want in manifest.items():
        f = package / rel
        if not f.is_file():
            problems.append("清单文件缺失: " + rel)
        elif digest(f) != want:
            problems.append("内容与清单不符: " + rel)
    active = [package / n for n in ("validate.py", "report.py", "test_validation.py",
                                    "POLICY.md", "SKILL.md", "config.json")]
    for sub in ("runner", "suite-official4"):
        active += [p for p in (package / sub).rglob("*")
                   if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".so"]
    for p in active:
        rel = str(p.relative_to(package))
        if rel not in manifest:
            problems.append("未登记文件: " + rel)
    if problems:
        raise ValueError("脚本包清单不一致（先同步 PACKAGE_SHA256.json 或审核变更后升版本）: "
                         + "; ".join(problems[:8]))


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def selected_tool_data(cfg):
    """四例流程实际依赖的数据文件子集（intel/cycloneiv 与 share 直下）。

    完整 tool_data 仍保留在 config 中供审计；其余厂商技术库不参与 cycloneiv
    四例流程，不再逐轮核对（预检仅覆盖四例及实际使用依赖）。
    """
    rules = cfg["tool_data_fourcase_filter"]
    direct = set(rules["direct_share_files"])
    out = []
    for item in cfg["tool_data"]:
        p = Path(item["path"])
        if any(sub in item["path"] for sub in rules["include_subpaths"]):
            out.append(item)
        elif p.parent.name == "share" and p.name in direct:
            out.append(item)
    return out


def preflight(commit):
    cfg = json.loads((PACKAGE / "config.json").read_text())
    repo = Path(cfg["repo"])
    if not re.fullmatch(r"[0-9a-fA-F]{7,40}", commit):
        raise ValueError("Supply a Git commit hash (7-40 hex characters), not a branch or file SHA-256")
    sha = git(repo, "rev-parse", "--verify", commit + "^{commit}")
    source = subprocess.check_output(["git", "-C", str(repo), "show", sha + ":src/pmux_opt.cc"])
    if not source:
        raise ValueError("Empty algorithm source")
    # 本流程构建单个独立翻译单元；新的本地源码依赖需要审核构建方式。
    includes = re.findall(rb'^\s*#\s*include\s*"([^"\n]+)"', source, re.M)
    for inc in includes:
        if not inc.startswith((b"kernel/", b"libs/", b"frontends/", b"backends/", b"passes/")):
            raise ValueError(f"New local source dependency needs build-profile review: {inc!r}")
    # 关键工具 + 四例实际依赖的数据文件指纹。
    for item in [*cfg["tools"].values(), *selected_tool_data(cfg)]:
        if digest(item["path"]) != item["sha256"]:
            raise ValueError("Tool or data file changed; qualify a new flow version: " + item["path"])
    if git(cfg["yosys_source"], "rev-parse", "HEAD") != cfg["yosys_src_commit"]:
        raise ValueError("Yosys source commit changed")
    if git(cfg["yosys_source"], "status", "--porcelain", "--untracked-files=no"):
        raise ValueError("Yosys tracked source is dirty; review provenance before running")
    # 四例冻结输入指纹（新的 official4-v1 清单；不再检查 H2/规模等未使用资产）。
    suite_manifest = PACKAGE / cfg["suite_manifest"]
    suite = json.loads(suite_manifest.read_text())
    for item in suite["files"]:
        target = PACKAGE / "suite-official4" / item["file"]
        if digest(target) != item["sha256"]:
            raise ValueError("Frozen four-case input changed: " + item["file"])
    # 脚本包清单与活动包文件核对（不一致必须停止，不静默刷新）。
    verify_package_manifest(PACKAGE)
    cfg.update(target_commit=sha, source_sha256=hashlib.sha256(source).hexdigest(),
               project_head=git(repo, "rev-parse", "HEAD"),
               suite_manifest_sha256=digest(suite_manifest),
               config_sha256=digest(PACKAGE / "config.json"),
               suite_verified=True,
               tool_data_checked=len(selected_tool_data(cfg)),
               tool_data_total=len(cfg["tool_data"]))
    return cfg, source


def check_builtin_evidence(cfg, run_identity=True, source_sha256=None):
    """只读检查内置四例验收证据。返回 (ok, missing, evidence)。

    规则：目标文件缺失时不运行任何进程（直接记为缺项）；仅在文件存在且
    run_identity=True 时运行无害的身份命令（-V / help pmux_opt）。

    指纹绑定（防替换与误用旧构建）：
    - 登记了 binary_sha256 时逐字节核对二进制；
    - 优化版构建所用的算法源码 passes/opt/pmux_opt.cc 必须等于登记哈希，
      且与请求提交的源码（source_sha256）一致；不一致即阻断，不误用旧构建；
    - 优化版源码仅允许登记的集成改动（git diff 摘要与登记一致）；baseline
      要求无未提交改动。
    """
    b = cfg.get("builtin") or {}
    missing, evidence = [], {"checked_at": datetime.now().astimezone().isoformat()}

    def run_readonly(cmd, timeout=120):
        p = subprocess.run(cmd, text=True, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=timeout)
        return p.returncode, p.stdout

    for side in ("baseline", "optimized"):
        spec = b.get(side) or {}
        path = Path(spec.get("path", ""))
        if not path.is_file():
            missing.append(f"{side} yosys 可执行文件缺失：{path}")
            continue
        ev = {"path": str(path), "sha256": digest(path)}
        if spec.get("binary_sha256") and ev["sha256"] != spec["binary_sha256"]:
            missing.append(f"{side} yosys 二进制与登记指纹不一致（被替换或未登记重建）：{path}")
        if run_identity:
            try:
                rc, out = run_readonly([str(path), "-V"])
            except (OSError, subprocess.SubprocessError) as exc:
                missing.append(f"{side} yosys 无法运行身份检查：{exc}")
                rc, out = 1, ""
            ev["version_rc"] = rc
            ev["version"] = out.strip().splitlines()[0] if out.strip() else ""
            if rc != 0 or b.get("expected_version", "") not in out:
                missing.append(f"{side} yosys 版本不满足以 0.69 为基准的身份检查：{ev['version']!r}")
        evidence[side] = ev
    opt = evidence.get("optimized")
    if opt and run_identity:
        try:
            rc, out = run_readonly([opt["path"], "-p", "help pmux_opt"])
        except (OSError, subprocess.SubprocessError) as exc:
            missing.append(f"优化版 yosys 无法运行 pmux_opt 检查：{exc}")
            rc, out = 1, ""
        opt["help_rc"] = rc
        opt["has_pmux_opt"] = ("No such command" not in out) and ("pmux_opt" in out)
        if rc != 0 or not opt["has_pmux_opt"]:
            missing.append("优化版 yosys 未包含内置 pmux_opt pass（help 检查失败）")
    for side in ("baseline", "optimized"):
        spec = b.get(side) or {}
        src = Path(spec.get("src_repo", ""))
        if not (src / ".git").exists():
            missing.append(f"{side} 源码仓库缺失：{src}")
            continue
        try:
            head = git(src, "rev-parse", "HEAD")
            diff_text = git(src, "diff")
        except subprocess.CalledProcessError as exc:
            missing.append(f"{side} 源码仓库 git 检查失败：{exc}")
            continue
        ev = {"repo": str(src), "head": head,
              "diff_sha256": hashlib.sha256(diff_text.encode()).hexdigest(),
              "diff_files": sorted(line.split()[-1] for line in diff_text.splitlines()
                                   if line.startswith("diff --git"))}
        evidence[f"{side}_src"] = ev
        if spec.get("src_commit") and head != spec["src_commit"]:
            missing.append(f"{side} 源码提交与登记不符：{head} != {spec['src_commit']}")
        if side == "baseline":
            if diff_text:
                missing.append("baseline 源码仓库存在未提交改动（影响来源证据）")
        else:
            want = spec.get("integration_diff_sha256")
            if want and ev["diff_sha256"] != want:
                missing.append("优化版源码 diff 与登记集成补丁不一致（改动被调整或未登记）")
            elif not want and diff_text:
                missing.append("优化版源码存在未登记的未提交改动")
            alg_rel = spec.get("algorithm_source_path", "passes/opt/pmux_opt.cc")
            alg = src / alg_rel
            if not alg.is_file():
                missing.append(f"优化版缺少算法源码：{alg_rel}")
            else:
                alg_sha = digest(alg)
                evidence["optimized_algorithm_source"] = {"path": alg_rel, "sha256": alg_sha}
                if spec.get("algorithm_source_sha256") and alg_sha != spec["algorithm_source_sha256"]:
                    missing.append("优化版算法源码与登记哈希不一致")
                if source_sha256 and alg_sha != source_sha256:
                    missing.append("优化版构建绑定的算法源码与请求提交不一致"
                                   "（先重新构建并登记，再运行）")
            for rel in b.get("integration_evidence", []):
                if not (src / rel).is_file():
                    missing.append(f"优化版集成/插入调用证据缺失：{rel}")
            for rel, needle, why in (
                ("passes/opt/CMakeLists.txt", "pmux_opt", "未包含 pmux_opt 注册"),
                ("techlibs/intel/synth_intel.cc", "pmux_opt", "未包含 pmux_opt 调用（C24/C37 要求）"),
            ):
                f = src / rel
                if f.is_file() and needle not in f.read_text(errors="replace"):
                    missing.append(f"{rel} {why}")
    abc = b.get("abc") or {}
    for side in ("baseline", "optimized"):
        p = Path(abc.get(side, ""))
        if not p.is_file():
            missing.append(f"{side} yosys-abc 缺失：{p}")
        else:
            evidence[f"abc_{side}"] = {"path": str(p), "sha256": digest(p)}
    # 实际数据文件（构建 share/intel 下的 cycloneiv 与 common）。
    for side in ("baseline", "optimized"):
        share = Path(b.get(side, {}).get("path", "")).parent / "share" / "intel"
        if not share.is_dir():
            missing.append(f"{side} 构建缺少 share/intel 数据文件目录")
            continue
        files = sorted(p for p in share.rglob("*")
                       if p.is_file() and p.suffix == ".v" and ("cycloneiv" in p.parts or "common" in p.parts))
        evidence[f"{side}_share_intel"] = {
            str(p.relative_to(share)): digest(p) for p in files}
    return (len(missing) == 0), missing, evidence


def next_round_dir(parent, prefix):
    """创建新轮次目录（禁止覆盖：编号递增取下一个未用编号）。"""
    for number in range(1, 10000):
        root = parent / f"{prefix}_第{number:02d}轮"
        try:
            root.mkdir()
            return root
        except FileExistsError:
            continue
    raise RuntimeError("No unused round number")


def make_round(cfg, source, label, mode, *, collect_tools_env=True):
    parent = Path(cfg["repo"]) / ROUND_PARENT_REL
    parent.mkdir(exist_ok=True)
    prefix = datetime.now().strftime("%Y-%m-%d_%H%M") + "_" + label + "_" + cfg["target_commit"][:7]
    root = next_round_dir(parent, prefix)
    cfg["ascii_bridge"] = str(Path(cfg["repo"]) / "results" / ("_eval_ascii_" + uuid.uuid4().hex))
    Path(cfg["ascii_bridge"]).mkdir()
    cfg["mode"] = mode
    meta = root / "01_来源与环境_meta"
    meta.mkdir()
    shutil.copytree(PACKAGE / "runner", root / "03_脚本与插件_runner",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copyfile(PACKAGE / "validate.py", root / "01_来源与环境_meta/validate.py.snapshot")
    shutil.copyfile(PACKAGE / "report.py", root / "01_来源与环境_meta/report.py.snapshot")
    shutil.copyfile(PACKAGE / "POLICY.md", root / "POLICY.md")
    shutil.copyfile(PACKAGE / "config.json", meta / "config.json")
    shutil.copyfile(PACKAGE / cfg["suite_manifest"], meta / "suite_manifest.json")
    # 冻结四例输入与自检素材（不含回归/H2/规模资产）。
    tree = root / "02_冻结源码与输入_assets/tree"
    shutil.copytree(PACKAGE / "suite-official4/tree", tree)
    (tree / "src").mkdir()
    (tree / "src/pmux_opt.cc").write_bytes(source)
    shutil.copytree(PACKAGE / "suite-official4/selfcheck",
                    root / "10_验证工具自检_selfcheck/assets")
    cfg["created_at"] = datetime.now().astimezone().isoformat()
    cfg["runner_sha256"] = {p.name: digest(p) for p in (root / "03_脚本与插件_runner").iterdir()
                            if p.is_file()}
    save(root / "validation_context.json", cfg)
    (meta / "project_status_before.txt").write_text(
        git(cfg["repo"], "status", "--porcelain", "--untracked-files=no") + "\n")
    (meta / "algorithm_commit.txt").write_text(
        git(cfg["repo"], "show", "-s", "--format=fuller", cfg["target_commit"]) + "\n")
    env_lines = [subprocess.check_output(["uname", "-a"], text=True), "Python: " + sys.version + "\n"]
    if collect_tools_env:
        env_lines.append(subprocess.check_output([cfg["tools"]["yosys"]["path"], "-V"], text=True))
        env_lines.append(subprocess.check_output([cfg["tools"]["eqy"]["path"], "--version"], text=True))
        env_lines.append(subprocess.check_output([cfg["tools"]["z3"]["path"], "--version"], text=True))
        compiler = subprocess.check_output([cfg["tools"]["yosys_config"]["path"], "--cxx"], text=True).strip()
        for command in ([compiler, "--version"], ["lscpu"]):
            result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            env_lines.append("\n" + repr(command) + "\n" + result.stdout)
        env_lines.append("\n" + Path("/proc/meminfo").read_text())
    (meta / "environment.txt").write_text("".join(env_lines))
    return root


def execute(root, name, cmd, stages, timeout=10800):
    meta = root / "01_来源与环境_meta"
    entry = {"name": name, "command": list(map(str, cmd)), "state": "RUNNING",
             "started_at": datetime.now().astimezone().isoformat()}
    stages.append(entry)
    save(meta / "stages.json", stages)
    print("START", name, flush=True)
    with (meta / (name + ".log")).open("x") as log:
        p = subprocess.Popen(cmd, cwd=root, stdout=log, stderr=subprocess.STDOUT,
                             env=dict(os.environ, LC_ALL="C.UTF-8", PYTHONUNBUFFERED="1"),
                             start_new_session=True)
        try:
            rc = p.wait(timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            os.killpg(p.pid, signal.SIGKILL)
            p.wait()
            rc = 124
    entry.update(rc=rc, state="COMPLETED" if rc == 0 else "ERROR",
                 finished_at=datetime.now().astimezone().isoformat())
    save(meta / "stages.json", stages)
    print("END", name, "rc=" + str(rc), flush=True)
    return rc


# ---------------------------------------------------------------- 自检与指纹
def selfcheck_fingerprints(cfg, runner_dir):
    """自检证据指纹：关键工具、四例输入、本轮代码/配置。任一变化即失效。"""
    return {
        "flow_version": cfg["flow_version"],
        "model_version": cfg.get("model_version"),
        "strategy_version": cfg.get("strategy_version"),
        "baseline_yosys_sha256": cfg["tools"]["yosys"]["sha256"],
        "abc_sha256": cfg["tools"]["abc"]["sha256"],
        "eqy_sha256": cfg["tools"]["eqy"]["sha256"],
        "z3_sha256": cfg["tools"]["z3"]["sha256"],
        "suite_manifest_sha256": cfg["suite_manifest_sha256"],
        "runner_sha256": {p.name: digest(p) for p in sorted(Path(runner_dir).iterdir())
                          if p.is_file()},
        "entry_sha256": {name: digest(PACKAGE / name) for name in ("validate.py", "report.py")},
    }


def load_selfcheck_cache(path):
    path = Path(path)
    if path.is_file():
        return json.loads(path.read_text())
    return {"cache_schema": 1, "entries": {}}


def cache_entry_valid(cache, stage, fingerprints):
    """指纹匹配且结果为真实通过时才允许复用；缺证据或指纹不一致不得假定已自检。"""
    entry = ((cache or {}).get("entries") or {}).get(stage)
    return bool(entry and entry.get("ok") and entry.get("fingerprint") == fingerprints)


def update_selfcheck_cache(path, cache, fingerprints, stage, ok, evidence_root):
    path = Path(path)
    entries = cache.setdefault("entries", {})
    entries[stage] = {"fingerprint": fingerprints, "ok": bool(ok),
                      "finished_at": datetime.now().astimezone().isoformat(),
                      "evidence_root": str(evidence_root)}
    # 首次运行时共享缓存目录可能尚不存在，写入前创建父目录。
    path.parent.mkdir(parents=True, exist_ok=True)
    save(path, cache)


# ---------------------------------------------------------------- 运行
def run_builtin(cfg, source, label, build_cache_dir=None):
    """内置四例验收：自动准备工具（复用/构建）→ 身份检查 → 完整内置调度。"""
    root = make_round(cfg, source, label, mode="builtin", collect_tools_env=False)
    print("ROUND=" + str(root), flush=True)
    meta = root / "01_来源与环境_meta"
    stages = []

    # 第一步：工具准备——查找可复用构建；未命中则在缓存命名空间内真实构建
    # （隔离源码树 + 逐字节算法源码 + 幂等集成 + 冒烟验证 + registry 登记）。
    # 本轮有效工具配置（路径/指纹/来源记录）写入 validation_context.json，
    # 各阶段 runner 统一从此读取；不修改仓库 config.json。
    sys.path.insert(0, str(PACKAGE / "runner"))
    from prepare_builtin import prepare_builtin, BuildError
    try:
        prep = prepare_builtin(cfg, source_sha256=cfg["source_sha256"],
                               source_bytes=source, cache_dir=build_cache_dir)
    except BuildError as exc:
        detail = "内置工具准备失败：" + str(exc)
        print("ERROR:", detail, flush=True)
        stages.append({"name": "build", "state": "ERROR", "rc": 3,
                       "detail": detail, "build_dir": exc.build_dir, "logs": exc.logs})
        save(meta / "stages.json", stages)
        from report import build_builtin_build_failed_report
        status = build_builtin_build_failed_report(root, error=str(exc), cfg=cfg,
                                                   build_dir=exc.build_dir, logs=exc.logs)
        print("RESULT=" + status + "\nREPORT=" + str(root / "00_本轮验证结论.md"), flush=True)
        return 3
    cfg["builtin"] = prep["builtin"]
    cfg["builtin_prepare"] = prep["record"]
    save(root / "validation_context.json", cfg)
    save(meta / "builtin_prepare.json", prep["record"])

    # 第二步：身份检查（构建/复用后仍须核对匹配关系；只在文件存在时运行无害身份命令）。
    ok, missing, evidence = check_builtin_evidence(cfg, run_identity=True,
                                                   source_sha256=cfg["source_sha256"])
    save(meta / "builtin_evidence.json", {"ok": ok, "missing": missing, "evidence": evidence})
    if not ok:
        stages.append({"name": "build", "state": "BLOCKED", "rc": 3, "missing": missing})
        save(meta / "stages.json", stages)
        from report import build_builtin_block_report
        build_builtin_block_report(root, status="BUILTIN_NOT_READY", missing=missing,
                                   evidence=evidence, cfg=cfg)
        print("RESULT=BUILTIN_NOT_READY")
        print("REPORT=" + str(root / "00_本轮验证结论.md"))
        return 3

    stages.append({"name": "build", "state": "COMPLETED", "rc": 0,
                   "detail": "工具准备完成：" + prep["record"]["summary"]})
    save(meta / "stages.json", stages)

    runner = root / "03_脚本与插件_runner"
    cache_path = Path(cfg["repo"]) / SELFCHECK_CACHE_REL
    fingerprints = selfcheck_fingerprints(cfg, runner)
    cache = load_selfcheck_cache(cache_path)
    failed = set()
    status = "NEEDS_REVIEW"
    from report import build_builtin_report
    try:
        for name, script, args in BUILTIN_PLAN:
            if name == "performance":
                args = ("--pairs", str(cfg["performance_pairs"]))
            if any(d in failed for d in PLUGIN_STAGE_DEPS.get(name, ())):
                stages.append({"name": name, "state": "NOT_RUN", "reason": "dependency failed"})
                failed.add(name)
                save(meta / "stages.json", stages)
                continue
            if name in BUILTIN_CACHED_STAGES and cache_entry_valid(cache, name, fingerprints):
                entry = cache["entries"][name]
                stages.append({"name": name, "state": "REUSED", "rc": 0,
                               "from_cache": str(cache_path),
                               "source_round": entry.get("evidence_root")})
                save(meta / "stages.json", stages)
                print("REUSE", name, "from", entry.get("evidence_root"), flush=True)
                continue
            rc = execute(root, name, [sys.executable, str(runner / script), *args], stages)
            if rc:
                failed.add(name)
            if name in BUILTIN_CACHED_STAGES:
                update_selfcheck_cache(cache_path, cache, fingerprints, name, rc == 0, root)
                if rc:
                    raise RuntimeError(name + " gate failed; dependent evaluation stopped")
    except Exception as exc:
        save(meta / "orchestrator_error.json", {"error": str(exc)})
        print("ERROR:", exc, flush=True)
    finally:
        save(meta / "stages.json", stages)
        status = build_builtin_report(root, chain_attempt="run01")
        index = root / "11_汇总与证据_summary/ALL_SHA256.txt"
        index.parent.mkdir(parents=True, exist_ok=True)
        print("Hashing evidence", flush=True)
        with index.open("x") as f:
            for directory, dirs, files in os.walk(root):
                dirs[:] = sorted(d for d in dirs if d != "__pycache__")
                for name in sorted(files):
                    path = Path(directory) / name
                    if path != index:
                        f.write(digest(path) + "  " + str(path.relative_to(root)) + "\n")
        print("RESULT=" + status + "\nREPORT=" + str(root / "00_本轮验证结论.md"), flush=True)
    return 0 if status == "BUILTIN_FOUR_CASE_LOCAL_ACCEPTANCE_COMPLETE" else 2


def run_plugin(cfg, source, label, chains, function_only=False, frozen_round=None):
    cfg["function_only"] = bool(function_only)
    cfg["frozen_round"] = str(frozen_round) if frozen_round else None
    root = make_round(cfg, source, label, mode="plugin", collect_tools_env=True)
    print("ROUND=" + str(root), flush=True)
    stages = []
    runner = root / "03_脚本与插件_runner"
    cache_path = Path(cfg["repo"]) / SELFCHECK_CACHE_REL
    from report import build_report
    status = "NEEDS_REVIEW"
    try:
        cmd = [cfg["tools"]["yosys_config"]["path"], "--build", str(runner / "pmux_opt.so"),
               str(root / "02_冻结源码与输入_assets/tree/src/pmux_opt.cc")]
        if execute(root, "build", cmd, stages, timeout=900):
            raise RuntimeError("Plugin build failed")
        cfg["plugin_sha256"] = digest(runner / "pmux_opt.so")
        cfg["chains_mode"] = chains
        save(root / "validation_context.json", cfg)
        sys.path.insert(0, str(runner))
        import p3_common as C
        rc = C.run_yosys("help pmux_opt\n", root / "01_来源与环境_meta/baseline_help.log")
        base = (root / "01_来源与环境_meta/baseline_help.log").read_text()
        rc2 = C.run_yosys("help pmux_opt\n", root / "01_来源与环境_meta/plugin_help.log", plugin=True)
        opt = (root / "01_来源与环境_meta/plugin_help.log").read_text()
        cfg["isolation"] = {"baseline_rc": rc, "plugin_rc": rc2,
                            "baseline_no_pmux": "No such command" in base,
                            "plugin_has_pmux": rc2 == 0 and "No such command" not in opt and "pmux_opt" in opt}
        save(root / "validation_context.json", cfg)
        if not (cfg["isolation"]["baseline_no_pmux"] and cfg["isolation"]["plugin_has_pmux"]):
            raise RuntimeError("Baseline/plugin pass isolation failed")

        fingerprints = selfcheck_fingerprints(cfg, runner)
        cache = load_selfcheck_cache(cache_path)
        failed = set()
        plan = FUNCTION_ONLY_PLAN if function_only else PLUGIN_PLAN
        for name, script, args in plan:
            if name == "performance":
                args = ("--pairs", str(cfg["performance_pairs"]))
            if any(d in failed for d in PLUGIN_STAGE_DEPS.get(name, ())):
                stages.append({"name": name, "state": "NOT_RUN", "reason": "dependency failed"})
                failed.add(name)
                continue
            if name in SELFCHECK_STAGES and cache_entry_valid(cache, name, fingerprints):
                entry = cache["entries"][name]
                stages.append({"name": name, "state": "REUSED", "rc": 0,
                               "from_cache": str(cache_path),
                               "source_round": entry.get("evidence_root")})
                save(root / "01_来源与环境_meta/stages.json", stages)
                print("REUSE", name, "from", entry.get("evidence_root"), flush=True)
                continue
            if name == "chains":
                args = ("--attempt", "run01", "--chains", chains)
                if function_only:
                    args = (*args, "--frozen-round", cfg["frozen_round"])
            rc = execute(root, name, [sys.executable, str(runner / script), *args], stages)
            if rc:
                failed.add(name)
            if name in SELFCHECK_STAGES:
                update_selfcheck_cache(cache_path, cache, fingerprints, name, rc == 0, root)
                if rc:
                    raise RuntimeError(name + " gate failed; dependent evaluation stopped")
        if function_only:
            for name, reason in FUNCTION_ONLY_SKIPPED:
                stages.append({"name": name, "state": "NOT_RUN", "reason": reason})
            save(root / "01_来源与环境_meta/stages.json", stages)
    except Exception as exc:
        save(root / "01_来源与环境_meta/orchestrator_error.json", {"error": str(exc)})
        print("ERROR:", exc, flush=True)
    finally:
        save(root / "01_来源与环境_meta/stages.json", stages)
        status = build_report(root, chain_attempt="run01", mode="plugin")
        index = root / "11_汇总与证据_summary/ALL_SHA256.txt"
        index.parent.mkdir(parents=True, exist_ok=True)
        print("Hashing evidence", flush=True)
        with index.open("x") as f:
            for directory, dirs, files in os.walk(root):
                dirs[:] = sorted(d for d in dirs if d != "__pycache__")
                for name in sorted(files):
                    path = Path(directory) / name
                    if path != index:
                        f.write(digest(path) + "  " + str(path.relative_to(root)) + "\n")
        print("RESULT=" + status + "\nREPORT=" + str(root / "00_本轮验证结论.md"), flush=True)
    return 0 if status in ("FOUR_CASE_PLUGIN_CHECKS_COMPLETE", "FUNCTION_RECHECK_COMPLETE") else 2


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("action", choices=["plan", "run"])
    ap.add_argument("commit")
    ap.add_argument("--label", default=ROUND_LABEL_DEFAULT)
    ap.add_argument("--mode", choices=["builtin", "plugin"], default="builtin",
                    help="builtin=内置四例验收（默认；未就绪时阻断并记录）；plugin=显式四例插件预检")
    ap.add_argument("--chains", choices=["main", "full"], default="main",
                    help="插件预检功能证明链集合（main=主路径+对照+定位；full=全部链）")
    ap.add_argument("--function-only", action="store_true",
                    help="功能补充复核：只运行 build + formal_selfcheck + chains（冻结输入；不综合/不测性能）")
    ap.add_argument("--frozen-round", default=None,
                    help="功能补充复核的冻结来源轮次目录（需含 05_公开四例_public 与 11_汇总与证据_summary/ALL_SHA256.txt）")
    ap.add_argument("--builtin-cache-dir", default=None,
                    help="内置构建缓存命名空间（默认 config.builtin.cache_dir；仅影响 builtin 模式；"
                         "用于复用检查与空缓存未命中构建验证）")
    args = ap.parse_args()
    if not re.fullmatch(r"[\w\-]+", args.label):
        ap.error("Label may contain only letters, digits, Chinese, underscore and hyphen")
    if args.function_only and args.mode != "plugin":
        ap.error("--function-only 仅适用于 --mode plugin")
    if args.frozen_round and not args.function_only:
        ap.error("--frozen-round 需要与 --function-only 一起使用")
    cfg, source = preflight(args.commit)
    if args.action == "plan":
        sys.path.insert(0, str(PACKAGE / "runner"))
        from prepare_builtin import plan_builtin
        plan = plan_builtin(cfg, cfg["source_sha256"], cache_dir=args.builtin_cache_dir)
        print(json.dumps({k: cfg[k] for k in ["target_commit", "source_sha256", "flow_version",
              "suite_version", "model_version", "strategy_version", "suite_manifest_sha256",
              "performance_pairs", "performance_scheme", "tool_data_checked"]},
              ensure_ascii=False, indent=2))
        print(json.dumps({"mode_default": "builtin", "builtin_plan": plan,
                          "note": "plan 只读：不创建轮次/构建目录、不编译、不登记。run 默认先自动准备"
                                  "（复用或构建）再执行内置四例验收；四例插件预检需 --mode plugin。"},
                         ensure_ascii=False, indent=2))
        print("只读预检完成。")
        return 0
    if args.mode == "builtin":
        return run_builtin(cfg, source, args.label, build_cache_dir=args.builtin_cache_dir)
    frozen = None
    if args.frozen_round:
        p = Path(args.frozen_round)
        if not p.is_absolute():
            p = Path(cfg["repo"]) / p
        if not p.is_dir():
            raise SystemExit("冻结轮次目录不存在: " + str(p))
        frozen = p.resolve()
    return run_plugin(cfg, source, args.label, args.chains,
                      function_only=args.function_only, frozen_round=frozen)


if __name__ == "__main__":
    sys.exit(main())
