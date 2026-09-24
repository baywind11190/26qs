#!/usr/bin/env python3
"""官方四例验证入口（official4-p1）。Linux/WSL，标准库实现。

默认目标：官方四例内置验收——先只读检查内置证据（原版/优化版 Yosys 0.69
可追溯构建、优化版内置 pmux_opt、插入调用证据、ABC 与数据文件）；证据未就绪或
本版本执行器未实现时，生成明确的阻断记录，不加载插件、不启动验收进程，
也不自动退回插件方案。

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
PLUGIN_STAGE_DEPS = {"chains": ("public",)}
SELFCHECK_STAGES = ("flowcheck", "formal_selfcheck", "measurement_selfcheck")
PLUGIN_STAGES = ("build",) + tuple(name for name, _, _ in PLUGIN_PLAN)

BUILTIN_MISSING_HINT = (
    "内置执行本版本未就绪：仅完成入口契约、预检与阻断记录；"
    "不得用插件结果或空实现冒充内置验收。"
)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


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
    cfg.update(target_commit=sha, source_sha256=hashlib.sha256(source).hexdigest(),
               project_head=git(repo, "rev-parse", "HEAD"),
               suite_manifest_sha256=digest(suite_manifest),
               config_sha256=digest(PACKAGE / "config.json"),
               suite_verified=True,
               tool_data_checked=len(selected_tool_data(cfg)),
               tool_data_total=len(cfg["tool_data"]))
    return cfg, source


def check_builtin_evidence(cfg, run_identity=True):
    """只读检查内置四例验收证据。返回 (ok, missing, evidence)。

    规则：目标文件缺失时不运行任何进程（直接记为缺项）；仅在文件存在且
    run_identity=True 时运行无害的身份命令（-V / help pmux_opt）。
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
            clean = not git(src, "status", "--porcelain", "--untracked-files=no")
        except subprocess.CalledProcessError as exc:
            missing.append(f"{side} 源码仓库 git 检查失败：{exc}")
            continue
        evidence[f"{side}_src"] = {"repo": str(src), "head": head, "tracked_clean": clean}
        if not clean:
            missing.append(f"{side} 源码仓库存在未提交改动（影响来源证据）")
        if side == "optimized":
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
    prefix = datetime.now().strftime("%Y-%m-%d") + "_" + label + "_" + cfg["target_commit"][:7]
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
    entries = cache.setdefault("entries", {})
    entries[stage] = {"fingerprint": fingerprints, "ok": bool(ok),
                      "finished_at": datetime.now().astimezone().isoformat(),
                      "evidence_root": str(evidence_root)}
    save(Path(path), cache)


# ---------------------------------------------------------------- 运行
def run_builtin(cfg, source, label):
    root = make_round(cfg, source, label, mode="builtin", collect_tools_env=False)
    print("ROUND=" + str(root), flush=True)
    ok, missing, evidence = check_builtin_evidence(cfg, run_identity=True)
    meta = root / "01_来源与环境_meta"
    save(meta / "builtin_evidence.json", {"ok": ok, "missing": missing, "evidence": evidence})
    status = "BUILTIN_NOT_READY" if not ok else "BUILTIN_EXECUTION_NOT_READY"
    from report import build_builtin_block_report
    build_builtin_block_report(root, status=status, missing=missing, evidence=evidence, cfg=cfg)
    print("RESULT=" + status)
    print("REPORT=" + str(root / "00_本轮验证结论.md"))
    return 3


def run_plugin(cfg, source, label, chains):
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
        for name, script, args in PLUGIN_PLAN:
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
            rc = execute(root, name, [sys.executable, str(runner / script), *args], stages)
            if rc:
                failed.add(name)
            if name in SELFCHECK_STAGES:
                update_selfcheck_cache(cache_path, cache, fingerprints, name, rc == 0, root)
                if rc:
                    raise RuntimeError(name + " gate failed; dependent evaluation stopped")
    except Exception as exc:
        save(root / "01_来源与环境_meta/orchestrator_error.json", {"error": str(exc)})
        print("ERROR:", exc, flush=True)
    finally:
        save(root / "01_来源与环境_meta/stages.json", stages)
        status = build_report(root, chain_attempt="run01", mode="plugin")
        index = root / "11_汇总与证据_summary/ALL_SHA256.txt"
        print("Hashing evidence", flush=True)
        with index.open("x") as f:
            for directory, dirs, files in os.walk(root):
                dirs[:] = sorted(d for d in dirs if d != "__pycache__")
                for name in sorted(files):
                    path = Path(directory) / name
                    if path != index:
                        f.write(digest(path) + "  " + str(path.relative_to(root)) + "\n")
        print("RESULT=" + status + "\nREPORT=" + str(root / "00_本轮验证结论.md"), flush=True)
    return 0 if status == "FOUR_CASE_PLUGIN_CHECKS_COMPLETE" else 2


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("action", choices=["plan", "run"])
    ap.add_argument("commit")
    ap.add_argument("--label", default=ROUND_LABEL_DEFAULT)
    ap.add_argument("--mode", choices=["builtin", "plugin"], default="builtin",
                    help="builtin=内置四例验收（默认；未就绪时阻断并记录）；plugin=显式四例插件预检")
    ap.add_argument("--chains", choices=["main", "full"], default="main",
                    help="插件预检功能证明链集合（main=主路径+对照+定位；full=全部链）")
    args = ap.parse_args()
    if not re.fullmatch(r"[\w\-]+", args.label):
        ap.error("Label may contain only letters, digits, Chinese, underscore and hyphen")
    cfg, source = preflight(args.commit)
    if args.action == "plan":
        ok, missing, _ = check_builtin_evidence(cfg, run_identity=False)
        print(json.dumps({k: cfg[k] for k in ["target_commit", "source_sha256", "flow_version",
              "suite_version", "suite_manifest_sha256", "performance_pairs", "tool_data_checked"]},
              ensure_ascii=False, indent=2))
        print(json.dumps({"mode_default": "builtin",
                          "builtin_evidence_files_present": ok,
                          "builtin_missing": missing,
                          "note": "内置 pass/版本身份检查在 run 预检执行（plan 只读，不启动进程）"},
                         ensure_ascii=False, indent=2))
        print("只读预检完成。run 默认执行内置四例预检（证据未就绪将阻断并记录，不退回插件）；"
              "四例插件预检需 --mode plugin。")
        return 0
    if args.mode == "builtin":
        return run_builtin(cfg, source, args.label)
    return run_plugin(cfg, source, args.label, args.chains)


if __name__ == "__main__":
    sys.exit(main())
