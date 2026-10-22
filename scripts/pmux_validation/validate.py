#!/usr/bin/env python3
"""PMUX 官方四例验证入口；Windows 默认加载 official4-p6-windows 配置。

内置验收先按平台和工具身份复用或构建 Yosys，再运行四例综合、ABC9 后网表
功能证明、映射资源统计与逐例性能测量。当前 V7 使用 PowerShell 墙钟时间及
独立退出事件内存，旧 V6 CPU 口径保留。p3-local-lut 集成覆盖 ABC9 后局部 LUT。
准备或身份检查失败时保留阻断记录，不加载插件或静默切换流程。

在 Windows 使用 `validate_windows_v7.cmd plan <commit>` 只读检查，使用
`validate_windows_v7.cmd run <commit>` 执行。Linux 的 `config.json` 保留历史 p5
兼容入口；Windows 的 `config.windows.json` 与 p6 结果分开保存。

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
ROUND_LABEL_DEFAULT = "Windows单次内部计时_v6" if os.name == "nt" else "稳定版-四例"
ROUND_PARENT_REL = "results/官方口径评测"
SELFCHECK_CACHE_REL = "results/官方口径评测/_共享自检缓存_selfcheck/selfcheck_cache.json"
CONFIG_PATH = PACKAGE / ("config.windows.json" if os.name == "nt" else "config.json")
sys.path.insert(0, str(PACKAGE / "runner"))
from process_utils import process_group_kwargs, terminate_process_tree
from cpu_statistics import SCHEME as MEAN_CPU_SCHEME, POLICY as CPU_POLICY
from runtime_patch import SCHEME as SINGLE_CPU_SCHEME
import runtime_patch
from cpu_statistics_v5 import SCHEME as ETW_CPU_SCHEME
from measure_v7 import SCHEME as SINGLE_WALL_SCHEME
import integration_profiles as I

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


TEXT_FILE_SUFFIXES = {
    ".c", ".cc", ".cpp", ".h", ".hpp", ".json", ".md", ".py", ".sh",
    ".sv", ".tcl", ".txt", ".v", ".ys", ".yml", ".yaml", ".cmd", ".cmake", '.ps1', '.wprp',
}


def digest_package_file(path):
    """Hash package text with CRLF normalized so Windows autocrlf is portable."""
    path = Path(path)
    data = path.read_bytes()
    if path.suffix.lower() in TEXT_FILE_SUFFIXES:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def normalize_text_file(path):
    path = Path(path)
    if path.suffix.lower() not in TEXT_FILE_SUFFIXES:
        return False
    data = path.read_bytes()
    normalized = data.replace(b"\r\n", b"\n")
    if normalized == data:
        return False
    path.write_bytes(normalized)
    return True


def normalize_text_tree(root):
    root = Path(root)
    changed = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        if normalize_text_file(path):
            changed.append(path)
    return changed


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def verify_package_manifest(package):
    """脚本包清单核对：清单内文件必须一致；活动包文件必须全部登记。

    任一项不符即停止（不静默刷新清单）。
    """
    package = Path(package)
    manifest = json.loads((package / "PACKAGE_SHA256.json").read_text(encoding="utf-8"))
    problems = []
    for rel, want in manifest.items():
        f = package / rel
        if not f.is_file():
            problems.append("清单文件缺失: " + rel)
        elif digest_package_file(f) != want:
            problems.append("内容与清单不符: " + rel)
    active = [package / n for n in ("validate.py", "report.py", "test_validation.py", "test_p5.py",
                                    'test_windows_hardening.py', 'test_cpu_v4.py', 'package_windows.py', 'package_qa.py',
                                    'test_measure_v7.py', 'test_local_lut_integration.py', "POLICY.md", "SKILL.md", "config.json", "config.windows.json",
                                    "config.windows.v7.json", "validate_windows.cmd", "validate_windows_v7.cmd")]
    for sub in ("runner", "suite-official4"):
        active += [p for p in (package / sub).rglob("*")
                   if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".so"]
    for p in active:
        rel = p.relative_to(package).as_posix()
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
        normalized = item["path"].replace(chr(92), "/")
        if any(sub.replace(chr(92), "/") in normalized
               for sub in rules["include_subpaths"]):
            out.append(item)
        elif p.parent.name.lower() in ("share", "yosys") and p.name in direct:
            out.append(item)
    return out


def yosys_share_root(binary):
    """Find the Yosys data directory for either a CMake build or install tree."""
    binary = Path(binary)
    candidates = (
        binary.parent / "share" / "yosys",
        binary.parent / "share",
        binary.parent.parent / "share" / "yosys",
        binary.parent.parent / "share",
    )
    for root in candidates:
        if (root / "intel" / "cycloneiv" / "cells_map.v").is_file():
            return root
    raise FileNotFoundError("找不到 Yosys share 数据目录（缺 intel/cycloneiv/cells_map.v）：%s"
                            % binary)


def validate_performance_policy(cfg):
    scheme=cfg.get('performance_scheme')
    if scheme not in (None,'pmux-perf-15p-mainrss-v2','pmux-perf-5p-mainrss-v1',
                       'pmux-perf-15p-windows-separate-cpu-exitpeak-v3',MEAN_CPU_SCHEME,ETW_CPU_SCHEME,SINGLE_CPU_SCHEME,SINGLE_WALL_SCHEME):
        raise ValueError('Unknown performance scheme; cannot infer measurement policy')
    if scheme == SINGLE_CPU_SCHEME:
        from measure_v6 import POLICY
        if cfg.get('cpu_policy') != POLICY or cfg.get('performance_pairs') != 1: raise ValueError('v6 fixed policy mismatch')
    if scheme == SINGLE_WALL_SCHEME:
        from measure_v7 import POLICY
        if cfg.get('wall_policy') != POLICY: raise ValueError('v7 fixed wall-time policy mismatch')
    if scheme in (MEAN_CPU_SCHEME,ETW_CPU_SCHEME):
        if cfg.get('cpu_policy')!=CPU_POLICY:raise ValueError('v4 fixed CPU policy mismatch')
        reference=cfg.get('cpu_reference_tools') or {}
        if set(reference)!={'wpr','xperf'} or any(not Path(p).is_file() for p in reference.values()):
            raise ValueError('v4 independent reference dependency missing: configure existing WPR and xperf paths')


def preflight(commit, config_path=None, integration_profile='p3'):
    config_path = Path(config_path).resolve() if config_path else CONFIG_PATH
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    validate_performance_policy(cfg)
    if os.name == 'nt':
        configure_windows_runtime(cfg)
        runtime = {}
        for name, spec in cfg.get('runtime_tools', {}).items():
            path = Path(spec['path'])
            if not path.is_file() or digest(path) != spec['sha256']:
                raise ValueError('Fixed runtime tool missing or identity mismatch: ' + str(path))
            if name == 'python' and Path(sys.executable).resolve() != path.resolve():
                raise ValueError('Use validate_windows.cmd with the fixed Python: ' + str(path))
            resolved = shutil.which('python3' if name == 'python' else name)
            if not resolved or Path(resolved).resolve() != path.resolve():
                raise ValueError('Runtime lookup mismatch for ' + name + ': ' + str(resolved))
            version = subprocess.check_output([str(path), '--version'], encoding='utf-8', errors='replace').splitlines()[0]
            runtime[name] = dict(spec, resolved=resolved, version=version)
        cfg['runtime_identity'] = runtime
        if cfg.get('performance_scheme') == SINGLE_WALL_SCHEME:
            spec = cfg.get('wall_time_tool') or {}
            powershell = Path(spec.get('path', ''))
            if not powershell.is_file() or digest(powershell) != spec.get('sha256'):
                raise ValueError('Fixed Windows PowerShell missing or SHA-256 mismatch: ' + str(powershell))
            ps_command = (
                "$cmd=Get-Command -Name 'Microsoft.PowerShell.Utility\\Measure-Command' -CommandType Cmdlet;"
                "if ($PSVersionTable.PSVersion.Major -ne 5 -or $PSVersionTable.PSVersion.Minor -ne 1 "
                "-or $cmd.ModuleName -ne 'Microsoft.PowerShell.Utility') { exit 7 };"
                "[Console]::WriteLine($PSVersionTable.PSVersion.ToString())"
            )
            ps_version = subprocess.check_output(
                [str(powershell), '-NoLogo', '-NoProfile', '-NonInteractive', '-Command', ps_command],
                encoding='utf-8', errors='replace', timeout=30).strip().splitlines()[-1]
            if not ps_version.startswith('5.1.'):
                raise ValueError('Windows PowerShell 5.1 required; got ' + ps_version)
            cfg['wall_time_tool_identity'] = dict(spec, version=ps_version,
                                                  cmdlet='Microsoft.PowerShell.Utility\\Measure-Command')
    repo = Path(cfg["repo"])
    if not re.fullmatch(r"[0-9a-fA-F]{7,40}", commit):
        raise ValueError("Supply a Git commit hash (7-40 hex characters), not a branch or file SHA-256")
    sha = git(repo, "rev-parse", "--verify", commit + "^{commit}")
    source = subprocess.check_output(["git", "-C", str(repo), "show", sha + ":src/pmux_opt.cc"])
    if not source:
        raise ValueError("Empty algorithm source")
    patch = None
    if git(repo, 'ls-tree', '--name-only', sha, '--', I.PATCH_PATH):
        patch = subprocess.check_output(['git', '-C', str(repo), 'show', sha + ':' + I.PATCH_PATH])
    I.configure(cfg, integration_profile, patch)
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
    for path_key, hash_key, label in (
        ("toolchain_dependency_manifest", "toolchain_dependency_manifest_sha256", "MSYS2 依赖清单"),
        ("toolchain_identity_manifest", "toolchain_identity_manifest_sha256", "Windows 工具链身份清单"),
    ):
        path = cfg["builtin"].get(path_key)
        expected = cfg["builtin"].get(hash_key)
        if path and (not Path(path).is_file() or digest(path) != expected):
            raise ValueError(label + "缺失或哈希与配置不符：" + str(path))
    for item in cfg["builtin"].get("toolchain_build_logs", []):
        if not Path(item["path"]).is_file() or digest(item["path"]) != item["sha256"]:
            raise ValueError("工具构建日志缺失或哈希与工具链身份清单不符：" + item["path"])
    # 四例冻结输入指纹（新的 official4-v1 清单；不再检查 H2/规模等未使用资产）。
    suite_manifest = PACKAGE / cfg["suite_manifest"]
    suite = json.loads(suite_manifest.read_text(encoding="utf-8"))
    for item in suite["files"]:
        target = PACKAGE / "suite-official4" / item["file"]
        if digest_package_file(target) != item["sha256"]:
            raise ValueError("Frozen four-case input changed: " + item["file"])
    # 脚本包清单与活动包文件核对（不一致必须停止，不静默刷新）。
    verify_package_manifest(PACKAGE)
    cfg.update(target_commit=sha, source_sha256=hashlib.sha256(source).hexdigest(),
               project_head=git(repo, "rev-parse", "HEAD"),
               suite_manifest_sha256=digest_package_file(suite_manifest),
               config_path=str(config_path.resolve()),
               config_sha256=digest_package_file(config_path),
               suite_verified=True,
               tool_data_checked=len(selected_tool_data(cfg)),
               tool_data_total=len(cfg["tool_data"]))
    return cfg, source


def performance_precondition(root, cfg):
    return I.evidence_errors(Path(root), cfg)


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
        if I.identity(cfg) == I.LOCAL_ID and '-lut' not in out:
            missing.append('优化版 yosys 缺少 pmux_opt -lut 支持')
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
        if runtime_patch.enabled(cfg):
            try:
                if spec.get('runtime_patch') != runtime_patch.verify(src): raise ValueError('runtime patch identity mismatch')
                if spec.get('full_diff_sha256') != ev['diff_sha256']: raise ValueError('full source diff mismatch')
                allowed={'kernel/driver.cc'} | ({'passes/opt/CMakeLists.txt','techlibs/intel/synth_intel.cc'} if side=='optimized' else set())
                files=set(git(src,'diff','--name-only').splitlines())
                if files != allowed: raise ValueError('unexpected source changes: '+str(files))
                diff_text=git(src,'diff','--','.',':(exclude)kernel/driver.cc')
                ev['diff_sha256']=hashlib.sha256(diff_text.encode()).hexdigest()
            except (ValueError,OSError,subprocess.SubprocessError) as exc: missing.append(str(exc))
        if side == "baseline":
            if diff_text:
                missing.append("baseline 源码仓库存在未提交改动（影响来源证据）")
        else:
            want = spec.get("integration_diff_sha256")
            if want and ev["diff_sha256"] != want:
                missing.append("优化版源码 diff 与登记集成补丁不一致（改动被调整或未登记）")
            elif not want and diff_text:
                missing.append("优化版源码存在未登记的未提交改动")
        if cfg.get('performance_scheme') == SINGLE_WALL_SCHEME:
            try:
                committed_driver = git(src, 'show', 'HEAD:kernel/driver.cc')
                current_driver = (src / 'kernel/driver.cc').read_text(encoding='utf-8')
                # git() strips the command's surrounding whitespace; ignore only
                # the committed file's final line terminator for the comparison.
                if current_driver.rstrip('\r\n') != committed_driver.rstrip('\r\n'):
                    raise ValueError(side + ' source includes a modified Yosys runtime driver')
                if '--runtime-json' in current_driver or 'WindowsRuntimeCpu' in current_driver:
                    raise ValueError(side + ' source contains the V6 internal CPU runtime patch')
            except (OSError, subprocess.SubprocessError, ValueError) as exc:
                missing.append(str(exc))
        if side == "optimized":
            if I.identity(cfg) == I.LOCAL_ID:
                from prepare_builtin import insert_integration
                try:
                    cmake = (src / 'passes/opt/CMakeLists.txt').read_text(encoding='utf-8')
                    synth = (src / 'techlibs/intel/synth_intel.cc').read_text(encoding='utf-8')
                    new_cmake, new_synth, already = insert_integration(cmake, synth, I.LOCAL_ID)
                    if not already or (new_cmake, new_synth) != (cmake, synth):
                        raise ValueError('7.1 integration source is incomplete')
                except (OSError, ValueError, RuntimeError) as exc:
                    missing.append(str(exc))
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
        try:
            share = yosys_share_root(b.get(side, {}).get("path", "")) / "intel"
        except FileNotFoundError as exc:
            missing.append(f"{side} 构建缺少 Yosys Intel 数据文件：{exc}")
            continue
        files = sorted(p for p in share.rglob("*")
                       if p.is_file() and p.suffix == ".v" and ("cycloneiv" in p.parts or "common" in p.parts))
        evidence[f"{side}_share_intel"] = {
            str(p.relative_to(share)): digest(p) for p in files}
    return (len(missing) == 0), missing, evidence


def configure_windows_runtime(cfg):
    """Expose the pinned MSYS2 runtime and Yosys/ABC directories to child tools."""
    if os.name != "nt":
        return
    sys.path.insert(0, str(PACKAGE / "runner"))
    from prepare_builtin import _build_env

    extra = []
    for name in ("yosys", "yosys_config", "abc", "eqy", "compiler", "cmake", "ninja"):
        path = (cfg.get("tools", {}).get(name) or {}).get("path")
        if path:
            extra.append(str(Path(path).parent))
    builtin = cfg.get("builtin") or {}
    for side in ("baseline", "optimized"):
        path = (builtin.get(side) or {}).get("path")
        if path:
            extra.append(str(Path(path).parent))
        abc_path = (builtin.get("abc") or {}).get(side)
        if abc_path:
            extra.append(str(Path(abc_path).parent))
    env = _build_env(cfg, extra)
    for name in ('PYTHONHOME', 'PYTHONPATH', 'PYTHONUSERBASE', 'BASH_ENV', 'ENV'):
        os.environ.pop(name, None)
    for name in ("PATH", "MSYSTEM", "PYTHONUTF8", "PYTHONIOENCODING", 'PYTHONNOUSERSITE', 'LC_ALL', 'MSYS2_PATH_TYPE'):
        if name in env:
            os.environ[name] = env[name]


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
    parent.mkdir(parents=True, exist_ok=True)
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
    shutil.copyfile(Path(cfg.get("config_path", PACKAGE / "config.json")), meta / "config.json")
    shutil.copyfile(PACKAGE / cfg["suite_manifest"], meta / "suite_manifest.json")
    normalize_text_file(meta / "suite_manifest.json")
    toolchain = cfg.get("builtin") or {}
    identity_path = toolchain.get("toolchain_identity_manifest")
    if identity_path:
        evidence_dir = meta / "工具链与构建证据"
        evidence_dir.mkdir()
        shutil.copyfile(identity_path, evidence_dir / "toolchain_identity.json")
        dependency_path = toolchain.get("toolchain_dependency_manifest")
        if dependency_path:
            shutil.copyfile(dependency_path, evidence_dir / "msys2_packages.txt")
        log_dir = evidence_dir / "build_logs"
        log_dir.mkdir()
        for item in toolchain.get("toolchain_build_logs", []):
            source_log = Path(item["path"])
            if digest(source_log) != item["sha256"]:
                raise ValueError("工具构建日志哈希变化：" + str(source_log))
            shutil.copyfile(source_log, log_dir / item["name"])
    # 冻结四例输入与自检素材（不含回归/H2/规模资产）。
    tree = root / "02_冻结源码与输入_assets/tree"
    shutil.copytree(PACKAGE / "suite-official4/tree", tree)
    normalized_inputs = normalize_text_tree(tree)
    (tree / "src").mkdir()
    (tree / "src/pmux_opt.cc").write_bytes(source)
    if I.identity(cfg) == I.LOCAL_ID:
        patch_path = tree / I.PATCH_PATH
        patch_path.parent.mkdir(parents=True, exist_ok=True)
        patch_path.write_bytes(cfg['integration_patch']['text'].encode('utf-8'))
        if digest(patch_path) != cfg['integration_patch']['sha256']:
            raise ValueError('Frozen integration patch hash mismatch')
    selfcheck_assets = root / "10_验证工具自检_selfcheck/assets"
    shutil.copytree(PACKAGE / "suite-official4/selfcheck", selfcheck_assets)
    normalized_selfcheck = normalize_text_tree(selfcheck_assets)
    normalized_files = normalized_inputs + normalized_selfcheck
    save(meta / "frozen_text_normalization.json", {
        "policy": "Windows Git autocrlf CRLF 规范化为 LF，保持清单中的冻结输入 SHA-256。",
        "files": [{"path": str(p.relative_to(root)), "sha256": digest(p)}
                  for p in normalized_files],
    })
    cfg["created_at"] = datetime.now().astimezone().isoformat()
    cfg["runner_sha256"] = {p.name: digest(p) for p in (root / "03_脚本与插件_runner").iterdir()
                            if p.is_file()}
    save(root / "validation_context.json", cfg)
    (meta / "project_status_before.txt").write_text(
        git(cfg["repo"], "status", "--porcelain", "--untracked-files=no") + "\n")
    (meta / "algorithm_commit.txt").write_text(
        git(cfg["repo"], "show", "-s", "--format=fuller", cfg["target_commit"]) + "\n")
    env_lines = ["Platform: " + sys.platform + "\n", "Python: " + sys.version + "\n"]
    if collect_tools_env:
        env_lines.append(subprocess.check_output([cfg["tools"]["yosys"]["path"], "-V"], text=True))
        env_lines.append(subprocess.check_output([cfg["tools"]["eqy"]["path"], "--version"], text=True))
        if cfg["tools"].get("z3"):
            env_lines.append(subprocess.check_output([cfg["tools"]["z3"]["path"], "--version"], text=True))
        compiler = (subprocess.check_output([cfg["tools"]["yosys_config"]["path"], "--cxx"], text=True).strip()
                    if cfg["tools"].get("yosys_config") else cfg["tools"]["compiler"]["path"])
        commands = [[compiler, "--version"]]
        commands.append(["lscpu"] if os.name != "nt" else ["cmd.exe", "/c", "ver"])
        for command in commands:
            result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            env_lines.append("\n" + repr(command) + "\n" + result.stdout)
        if os.name != "nt" and Path("/proc/meminfo").is_file():
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
                             env=dict(os.environ, LC_ALL="C.UTF-8", PYTHONUNBUFFERED="1",
                                      PYTHONUTF8="1", PYTHONIOENCODING="utf-8"),
                             **process_group_kwargs())
        try:
            rc = p.wait(timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            terminate_process_tree(p)
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
        "optimized_yosys_sha256": cfg.get('builtin',{}).get('optimized',{}).get('binary_sha256'),
        "builtin_abc_sha256": {side:digest(path) for side,path in cfg.get('builtin',{}).get('abc',{}).items()},
        "compiler_sha256": cfg.get('tools',{}).get('compiler',{}).get('sha256'),
        "platform": cfg.get('platform'),
        "performance_scheme": cfg.get("performance_scheme"),
        "config_sha256": cfg.get("config_sha256"),
        "wall_time_tool_identity": cfg.get("wall_time_tool_identity"),
        "wall_time_method": cfg.get("wall_time_method"),
        "runtime_patch": runtime_patch.identity() if runtime_patch.enabled(cfg) else None,
        "flow_version": cfg["flow_version"],
        "model_version": cfg.get("model_version"),
        "strategy_version": cfg.get("strategy_version"),
        "baseline_yosys_sha256": (cfg.get("builtin",{}).get("baseline",{}).get("binary_sha256") or cfg["tools"]["yosys"]["sha256"]),
        "abc_sha256": cfg["tools"]["abc"]["sha256"],
        "eqy_sha256": cfg["tools"]["eqy"]["sha256"],
        "z3_sha256": (cfg["tools"].get("z3") or {}).get("sha256"),
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
    matched = bool(entry and entry.get("ok") and entry.get("fingerprint") == fingerprints)
    if matched and stage == 'measurement_selfcheck' and fingerprints.get('performance_scheme') == SINGLE_CPU_SCHEME:
        evidence = entry.get('measurement_evidence') or {}
        path = Path(evidence.get('path',''))
        return path.is_file() and digest(path) == evidence.get('sha256')
    if matched and stage == 'measurement_selfcheck' and fingerprints.get('performance_scheme') == SINGLE_WALL_SCHEME:
        evidence = entry.get('measurement_evidence') or {}
        path = Path(evidence.get('path', ''))
        if not path.is_file() or digest(path) != evidence.get('sha256'):
            return False
        try:
            proof = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return False
        return proof.get('selftest_ok') is True and proof.get('method') == 'powershell-measure-command-elapsed-wall-v1'
    return matched


def update_selfcheck_cache(path, cache, fingerprints, stage, ok, evidence_root):
    path = Path(path)
    entries = cache.setdefault("entries", {})
    entries[stage] = {"fingerprint": fingerprints, "ok": bool(ok),
                      "finished_at": datetime.now().astimezone().isoformat(),
                      "evidence_root": str(evidence_root)}
    if stage == 'measurement_selfcheck' and fingerprints.get('performance_scheme') == SINGLE_CPU_SCHEME and ok:
        proof = Path(evidence_root) / '09_时间内存开销_performance/selftest/selftest_results.json'
        if not proof.is_file(): raise ValueError('v6 selfcheck evidence missing')
        entries[stage]['measurement_evidence'] = dict(path=str(proof),sha256=digest(proof))
    if stage == 'measurement_selfcheck' and fingerprints.get('performance_scheme') == SINGLE_WALL_SCHEME and ok:
        proof = Path(evidence_root) / '09_时间内存开销_performance/selftest/selftest_results.json'
        if not proof.is_file(): raise ValueError('v7 selfcheck evidence missing')
        entries[stage]['measurement_evidence'] = dict(path=str(proof),sha256=digest(proof))
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
    configure_windows_runtime(cfg)
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
    cache_path = Path(cfg["repo"]) / cfg.get('selfcheck_cache_rel', SELFCHECK_CACHE_REL)
    fingerprints = selfcheck_fingerprints(cfg, runner)
    cache = load_selfcheck_cache(cache_path)
    failed = set()
    status = "NEEDS_REVIEW"
    from report import build_builtin_report
    try:
        stage_plan=list(BUILTIN_PLAN)
        if cfg.get('performance_scheme')==MEAN_CPU_SCHEME:
            stage_plan.insert(3,('cpu_method_qualification','qualify_cpu_method.py',()))
        elif cfg.get('performance_scheme')==ETW_CPU_SCHEME:
            stage_plan.insert(3,('cpu_etw_selfcheck','cpu_selfcheck_v5.py',()))
        for name, script, args in stage_plan:
            if name == "performance":
                errors = performance_precondition(root, cfg)
                if errors:
                    stages.append({'name': name, 'state': 'NOT_RUN', 'reason': 'integration/formal evidence gate failed', 'errors': errors})
                    failed.add(name)
                    save(meta / 'stages.json', stages)
                    break
                args = () if cfg.get('performance_scheme') in (MEAN_CPU_SCHEME,ETW_CPU_SCHEME,SINGLE_CPU_SCHEME,SINGLE_WALL_SCHEME) else ("--pairs", str(cfg["performance_pairs"]))
            if any(d in failed for d in PLUGIN_STAGE_DEPS.get(name, ())):
                stages.append({"name": name, "state": "NOT_RUN", "reason": "dependency failed"})
                failed.add(name)
                save(meta / "stages.json", stages)
                continue
            if (name in BUILTIN_CACHED_STAGES
                    and not (name == 'flowcheck' and I.identity(cfg) == I.LOCAL_ID)
                    and cache_entry_valid(cache, name, fingerprints)):
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
                if name in ('cpu_method_qualification','cpu_etw_selfcheck'):
                    raise RuntimeError('CPU method qualification failed; no reference/certificate substitution or performance resampling')
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
    cache_path = Path(cfg["repo"]) / cfg.get('selfcheck_cache_rel', SELFCHECK_CACHE_REL)
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
    ap.add_argument("--label", default=None)
    ap.add_argument("--config", default=None,
                    help="指定独立流程配置；默认仍选择平台现行配置")
    ap.add_argument('--integration-profile', choices=['p3', 'p3-local-lut'], default='p3',
                    help='包含已登记7.1补丁的提交必须选择 p3-local-lut')
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
    if args.label is not None and not re.fullmatch(r"[\w\-]+", args.label):
        ap.error("Label may contain only letters, digits, Chinese, underscore and hyphen")
    if args.function_only and args.mode != "plugin":
        ap.error("--function-only 仅适用于 --mode plugin")
    if args.frozen_round and not args.function_only:
        ap.error("--frozen-round 需要与 --function-only 一起使用")
    if args.integration_profile != 'p3' and args.mode != 'builtin':
        ap.error('p3-local-lut requires builtin mode')
    cfg, source = preflight(args.commit, args.config, args.integration_profile)
    if args.label is None:
        args.label = ("WindowsPowerShell墙钟计时_v7" if cfg.get('performance_scheme') == SINGLE_WALL_SCHEME
                      else ROUND_LABEL_DEFAULT)
    if args.action == "plan":
        sys.path.insert(0, str(PACKAGE / "runner"))
        from prepare_builtin import plan_builtin
        plan = plan_builtin(cfg, cfg["source_sha256"], cache_dir=args.builtin_cache_dir)
        cpu_method=None
        if cfg.get('performance_scheme')==MEAN_CPU_SCHEME:
            from cpu_qualification import qualification_status
            cpu_method=qualification_status(cfg)
        elif cfg.get('performance_scheme')==ETW_CPU_SCHEME:
            from cpu_selfcheck_v5 import status as etw_status
            cpu_method=etw_status(cfg)
        print(json.dumps({k: cfg.get(k) for k in ["target_commit", "source_sha256", "flow_version",
              "suite_version", "model_version", "strategy_version", "suite_manifest_sha256",
              "performance_pairs", "performance_scheme", "tool_data_checked", "integration_profile", "integration_patch"]},
              ensure_ascii=False, indent=2))
        print(json.dumps({"mode_default": "builtin", "builtin_plan": plan,
                          'cpu_policy':cfg.get('cpu_policy'),'cpu_method_qualification':cpu_method,
                          'performance_expected_runs':16 if cfg.get('performance_scheme') in (SINGLE_CPU_SCHEME,SINGLE_WALL_SCHEME) else 2720 if cfg.get('performance_scheme') in (MEAN_CPU_SCHEME,ETW_CPU_SCHEME) else None,
                          'wall_policy':cfg.get('wall_policy'),'wall_time_tool_identity':cfg.get('wall_time_tool_identity'),
                          'wall_runs_per_case':1 if cfg.get('performance_scheme')==SINGLE_WALL_SCHEME else None,
                          'wall_runs_total':8 if cfg.get('performance_scheme')==SINGLE_WALL_SCHEME else None,
                          'cpu_pairs_per_case':300 if cfg.get('performance_scheme') in (MEAN_CPU_SCHEME,ETW_CPU_SCHEME) else cfg.get('performance_pairs'),
                          'memory_pairs_per_case':15 if cfg.get('performance_scheme') in (MEAN_CPU_SCHEME,ETW_CPU_SCHEME) else cfg.get('performance_pairs'),
                          'performance_estimate_note':'16次目标性能运行，无预热/重采样/ETW；构建、自检、功能证明另计' if cfg.get('performance_scheme') in (SINGLE_CPU_SCHEME,SINGLE_WALL_SCHEME) else '2720次历史性能方案',
                          "runtime_identity": cfg.get('runtime_identity'),
                          "note": "plan 只读：不创建轮次/构建目录、不编译、不登记。run 默认先自动准备"
                                  "（复用或构建）再执行内置四例验收；四例插件预检需 --mode plugin。"},
                         ensure_ascii=False, indent=2))
        print("只读预检完成。")
        return 0
    if args.mode == "builtin":
        return run_builtin(cfg, source, args.label, build_cache_dir=args.builtin_cache_dir)
    if cfg.get('performance_scheme') in (MEAN_CPU_SCHEME,ETW_CPU_SCHEME,SINGLE_CPU_SCHEME,SINGLE_WALL_SCHEME):
        raise ValueError('mean CPU policy is Windows builtin-only; no plugin substitution')
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
