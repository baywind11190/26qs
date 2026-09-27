#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""内置 Yosys 工具自动准备（official4-p4）。

给定目标算法源码（字节 + SHA-256），解析原版（baseline）与优化版（内置
pmux_opt）两份 Yosys 0.69 构建：

- baseline：优先复用登记的合格构建（config.builtin.baseline_reuse，核对
  基础提交 / 构建配置 / 编译器 / 二进制 / ABC 指纹一致后复用）；不满足时
  按与优化侧一致的构建条件重新构建。
- optimized：按缓存键（算法源码哈希、Yosys 基础提交、集成模板、关键构建
  参数、编译器；另核对 ABC 源码身份与产物哈希）在缓存命名空间
  （cache_dir/registry）查找可复用构建；命中且产物核对通过即复用；未命中
  时从本地 Yosys 基础提交建立隔离源码树，逐字节提取 src/pmux_opt.cc →
  passes/opt/pmux_opt.cc，按固定模板进行（幂等、锚点校验的）集成，
  CMake Release 构建并验证（-V / help pmux_opt / 小型 synth_intel 冒烟）
  后登记为可复用缓存。

安全与边界：
- 查找（plan_builtin）只读：不写任何文件、不编译；缺基础源码或依赖属
  实际阻断，与“缺缓存、可执行构建”区别报告。
- 构建锁避免同一缓存命名空间并发写入；失败条目（FAILED）保留诊断但不
  发布完成标记、不被复用；不自动重试。
- 缺二进制、源码被改动、哈希不匹配、半成品一律不得命中缓存。
- 不移动、不覆盖既有构建树；导入（import_prebuilt）只在缓存目录 registry/
  下写登记文件。
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

SCHEMA = 1
INTEGRATION_ID = "pmux-opt-inline-p3-v1"
# 集成模板（对 Yosys 9f75ca1f9 系基础提交的固定插入；上下文锚点不符即停止）。
CMAKE_ANCHOR = "yosys_pass(muxpack\n\tmuxpack.cc\n)\n"
CMAKE_BLOCK = "yosys_pass(pmux_opt\n\tpmux_opt.cc\n)\n"
SYNTH_ANCHOR = '\t\t\trun("fsm");\n\t\t\trun("opt");\n\t\t\trun("wreduce");\n'
SYNTH_BLOCK = '\t\t\trun("fsm");\n\t\t\trun("opt");\n\t\t\trun("pmux_opt");\n\t\t\trun("wreduce");\n'
ALGORITHM_SOURCE_PATH = "passes/opt/pmux_opt.cc"


class BuildError(RuntimeError):
    """工具准备失败（构建失败 / 环境不满足 / 锚点不符）。"""

    def __init__(self, message, *, build_dir=None, logs=None):
        super().__init__(message)
        self.build_dir = str(build_dir) if build_dir else None
        self.logs = dict(logs or {})


# ---------------------------------------------------------------- 基础工具
def _now():
    return datetime.now().astimezone().isoformat()


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def _run_logged(cmd, *, cwd, log, timeout):
    with open(log, "w") as lf:
        p = subprocess.Popen(cmd, cwd=str(cwd), stdout=lf, stderr=subprocess.STDOUT)
        try:
            return p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait()
            return 124


def build_profile(cfg):
    """关键构建参数（参与缓存键；不含并行度等不影响产物的选项）。"""
    b = cfg["builtin"].get("build_profile") or {}
    return {
        "cmake_build_type": b.get("cmake_build_type", "Release"),
        "shared_libs": bool(b.get("shared_libs", True)),
    }


def compiler_identity(cfg):
    c = cfg["tools"]["compiler"]
    return {"path": c["path"], "sha256": c["sha256"]}


def cache_key(cfg, source_sha256):
    """optimized 缓存键：算法源码哈希、基础提交、集成模板/位置、构建参数、编译器。"""
    return {
        "algorithm_source_sha256": source_sha256,
        "base_commit": cfg["builtin"]["source_commit"],
        "integration_id": INTEGRATION_ID,
        "build_profile": build_profile(cfg),
        "compiler_sha256": cfg["tools"]["compiler"]["sha256"],
    }


def _current_abc_commit(cfg):
    """本地基础源码仓库的 abc 子模块提交（读不到返回 None，不阻断）。"""
    repo = Path(cfg["builtin"]["source_repo"])
    try:
        out = _git(repo, "submodule", "status", "abc")
    except (subprocess.CalledProcessError, OSError):
        return None
    line = out.lstrip("+-").split()
    return line[0] if line else None


# ---------------------------------------------------------------- 集成（纯函数）
def insert_integration(cmake_text, synth_text):
    """幂等集成：返回 (new_cmake, new_synth, already)。

    - 已含标准模板 → 不重复插入；
    - 含 pmux_opt 痕迹但非标准模板 → 报错（报告实际差异，不盲目替换）；
    - 锚点上下文不唯一/不存在 → 报错。
    """
    already = True
    if CMAKE_BLOCK in cmake_text:
        pass
    elif "pmux_opt" in cmake_text:
        raise BuildError("passes/opt/CMakeLists.txt 含 pmux_opt 痕迹但非标准模板，需人工审核")
    else:
        n = cmake_text.count(CMAKE_ANCHOR)
        if n != 1:
            raise BuildError("passes/opt/CMakeLists.txt 锚点上下文不符（匹配 %d 次，期望 1）" % n)
        cmake_text = cmake_text.replace(CMAKE_ANCHOR, CMAKE_ANCHOR + CMAKE_BLOCK, 1)
        already = False
    if SYNTH_BLOCK in synth_text:
        pass
    elif "pmux_opt" in synth_text:
        raise BuildError("techlibs/intel/synth_intel.cc 含 pmux_opt 痕迹但非标准模板，需人工审核")
    else:
        n = synth_text.count(SYNTH_ANCHOR)
        if n != 1:
            raise BuildError("techlibs/intel/synth_intel.cc 锚点上下文不符（匹配 %d 次，期望 1）" % n)
        synth_text = synth_text.replace(SYNTH_ANCHOR, SYNTH_BLOCK, 1)
        already = False
    return cmake_text, synth_text, already


def _check_integration_diff(diff_text):
    """防错：集成 diff 必须恰好是两个文件的固定插入。返回 diff_sha256。"""
    files = sorted(re.findall(r"^diff --git a/(\S+) b/", diff_text, re.M))
    if files != ["passes/opt/CMakeLists.txt", "techlibs/intel/synth_intel.cc"]:
        raise BuildError("集成 diff 文件集合异常：%r" % files)
    if "+yosys_pass(pmux_opt" not in diff_text:
        raise BuildError("集成 diff 缺少 CMakeLists 插入内容")
    if '+\t\t\trun("pmux_opt");' not in diff_text:
        raise BuildError("集成 diff 缺少 synth_intel 插入内容")
    return hashlib.sha256(diff_text.encode()).hexdigest()


# ---------------------------------------------------------------- 缓存登记（只读查找）
def registry_dir(cache_dir):
    return Path(cache_dir) / "registry"


def _read_registry_entries(cache_dir):
    d = registry_dir(cache_dir)
    entries = []
    if d.is_dir():
        for f in sorted(d.glob("*.json")):
            try:
                e = json.loads(f.read_text())
            except (OSError, ValueError):
                continue
            if isinstance(e, dict):
                e["_file"] = str(f)
                entries.append(e)
    return entries


def verify_entry_files(entry, sides=("baseline", "optimized")):
    """核对登记条目引用的产物（文件存在 + 哈希一致 + 源码树在）。返回 (ok, reasons)。"""
    reasons = []
    for side in sides:
        spec = entry.get(side) or {}
        if not spec:
            reasons.append("缺少 %s 登记" % side)
            continue
        for key, label in (("binary", "二进制"), ("abc", "ABC")):
            p = Path(spec.get(key, "") or "")
            if not p.is_file():
                reasons.append("%s %s缺失：%s" % (side, label, p))
            elif spec.get(key + "_sha256") and _sha256_file(p) != spec[key + "_sha256"]:
                reasons.append("%s %s与登记不符：%s" % (side, label, p))
        src = Path(spec.get("src_dir", "") or "")
        if not (src / ".git").exists():
            reasons.append("%s 源码树缺失：%s" % (side, src))
        if side == "optimized" and spec.get("algorithm_source_path"):
            alg = src / spec["algorithm_source_path"]
            if not alg.is_file():
                reasons.append("算法源码缺失：%s" % alg)
            elif spec.get("algorithm_source_sha256") and \
                    _sha256_file(alg) != spec["algorithm_source_sha256"]:
                reasons.append("算法源码与登记不符：%s" % alg)
    return (not reasons), reasons


def find_cached_optimized(cache_dir, key, *, current_abc_commit=None):
    """在缓存命名空间查找可复用的优化版构建（READY + 键匹配 + 产物核对）。"""
    for e in _read_registry_entries(cache_dir):
        if e.get("status") != "READY":
            continue
        if e.get("key") != key:
            continue
        if current_abc_commit and e.get("abc_source_commit") and \
                e["abc_source_commit"] != current_abc_commit:
            continue
        ok, _ = verify_entry_files(e)
        if ok:
            return e
    return None


def resolve_baseline_reuse(cfg):
    """config.builtin.baseline_reuse 核对。返回 (spec, reasons)；reasons 为空即可复用。"""
    spec = (cfg["builtin"].get("baseline_reuse") or {}) or None
    if not spec:
        return None, ["无 baseline 复用登记"]
    reasons = []
    if spec.get("build_profile") != build_profile(cfg):
        reasons.append("构建参数与当前配置不一致")
    c = cfg["tools"]["compiler"]
    if spec.get("compiler_sha256") and spec["compiler_sha256"] != c["sha256"]:
        reasons.append("编译器身份与当前登记不一致")
    if spec.get("src_commit") and cfg["builtin"].get("source_commit") and \
            spec["src_commit"] != cfg["builtin"]["source_commit"]:
        reasons.append("基础提交与当前配置不一致")
    ok, why = verify_entry_files({"baseline": spec}, sides=("baseline",))
    reasons += why
    return spec, reasons


def _build_environment_blockers(cfg):
    """需要构建时的可执行性检查（缺基础依赖 = 实际阻断）。"""
    blocked = []
    src = Path(cfg["builtin"]["source_repo"])
    if not (src / ".git").exists():
        blocked.append({"item": "source_repo", "detail": "Yosys 基础源码仓库缺失：%s" % src})
    else:
        try:
            head = _git(src, "rev-parse", "HEAD")
            if head != cfg["builtin"]["source_commit"]:
                blocked.append({"item": "source_commit",
                                "detail": "基础源码 HEAD=%s 与登记 %s 不一致"
                                          % (head, cfg["builtin"]["source_commit"])})
        except (subprocess.CalledProcessError, OSError) as exc:
            blocked.append({"item": "source_repo", "detail": "git 检查失败：%s" % exc})
    for name in ("cmake", "rsync"):
        if not shutil.which(name):
            blocked.append({"item": name, "detail": "%s 不可用" % name})
    comp = Path(cfg["tools"]["compiler"]["path"])
    if not comp.is_file():
        blocked.append({"item": "compiler", "detail": "编译器缺失：%s" % comp})
    return blocked


# ---------------------------------------------------------------- 计划（只读）
def plan_builtin(cfg, source_sha256, cache_dir=None):
    """只读解析“将复用哪些工具 / 是否需要构建及原因”。不写文件、不编译。"""
    cache_dir = Path(cache_dir) if cache_dir else Path(cfg["builtin"]["cache_dir"])
    out = {"cache_dir": str(cache_dir), "integration_id": INTEGRATION_ID,
           "baseline": {}, "optimized": {}, "blocked": []}
    bspec, breasons = resolve_baseline_reuse(cfg)
    if bspec and not breasons:
        out["baseline"] = {"action": "reuse", "path": bspec.get("binary"),
                           "reason": "baseline 登记核对通过（构建参数/编译器/基础提交/二进制/ABC 一致）"}
    else:
        out["baseline"] = {"action": "build", "reason": "；".join(breasons) or "无可用 baseline 登记"}
    key = cache_key(cfg, source_sha256)
    hit = find_cached_optimized(cache_dir, key,
                                current_abc_commit=_current_abc_commit(cfg))
    if hit:
        out["optimized"] = {"action": "reuse", "path": hit["optimized"]["binary"],
                            "reason": "缓存命中：%s" % hit.get("_file")}
    else:
        out["optimized"] = {"action": "build", "reason": "缓存未命中（无匹配且产物核验通过的 READY 条目）"}
    out["build_required"] = ("build" in (out["baseline"]["action"], out["optimized"]["action"]))
    if out["build_required"]:
        out["blocked"] = _build_environment_blockers(cfg)
    return out


# ---------------------------------------------------------------- 构建
def _acquire_lock(cache_dir):
    d = registry_dir(cache_dir)
    d.mkdir(parents=True, exist_ok=True)
    lock = d / ".build-lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise BuildError("构建锁已存在（另一个构建可能正在进行）：%s；"
                         "确认无并发构建后，请人工检查并删除锁文件" % lock)
    os.write(fd, ("pid=%d time=%s\n" % (os.getpid(), _now())).encode())
    os.close(fd)
    return lock


def _release_lock(lock):
    try:
        os.unlink(lock)
    except FileNotFoundError:
        pass


def _unique_build_dir(cache_dir, source_sha256):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    short = source_sha256[:7]
    for i in range(100):
        name = "%s_%s" % (ts, short) + ("_%d" % i if i else "")
        d = cache_dir / name
        try:
            d.mkdir()
            return d
        except FileExistsError:
            continue
    raise BuildError("无法创建唯一构建目录（cache_dir=%s）" % cache_dir)


def _copy_source_tree(cfg, dst, logs, side):
    src = Path(cfg["builtin"]["source_repo"])
    log = logs / ("rsync-%s.log" % side)
    cmd = ["rsync", "-a", "--exclude=/build/", str(src) + "/", str(dst) + "/"]
    rc = _run_logged(cmd, cwd=logs.parent, log=log, timeout=3600)
    if rc:
        raise BuildError("复制基础源码失败（rc=%d），日志 %s" % (rc, log))


def _write_provenance(cfg, src_tree, copy_cmd, logs, side):
    src = Path(cfg["builtin"]["source_repo"])

    def git_out(*args):
        try:
            return _git(src, *args)
        except (subprocess.CalledProcessError, OSError) as exc:
            return "<git error: %s>" % exc

    lines = [
        "# Yosys 基础源码来源证据（隔离复制品）",
        "date: %s" % _now(),
        "side: %s" % side,
        "source_repo: %s" % src,
        "source_head: %s" % git_out("rev-parse", "HEAD"),
        "source_status_tracked: %s" % git_out("status", "--porcelain", "--untracked-files=no"),
        "source_submodules:",
    ]
    for line in git_out("submodule", "status").splitlines():
        lines.append(" " + line)
    lines += [
        "copy_cmd: %s" % " ".join(copy_cmd),
        "copy_head: %s" % _git(src_tree, "rev-parse", "HEAD"),
    ]
    (logs / ("source_provenance_%s.txt" % side)).write_text("\n".join(lines) + "\n")


def _cmake_build(src_tree, logs, side, cfg):
    profile = build_profile(cfg)
    build = src_tree / "build"
    (logs / ("build-%s.start" % side)).write_text(_now() + "\n")
    cfg_log = logs / ("cmake-%s.log" % side)
    cmd = ["cmake", "-S", str(src_tree), "-B", str(build),
           "-DCMAKE_BUILD_TYPE=%s" % profile["cmake_build_type"],
           "-DBUILD_SHARED_LIBS=%s" % ("ON" if profile["shared_libs"] else "OFF"),
           "-DCMAKE_CXX_COMPILER=%s" % cfg["tools"]["compiler"]["path"]]
    rc = _run_logged(cmd, cwd=src_tree, log=cfg_log, timeout=1800)
    if rc:
        raise BuildError("cmake 配置失败（rc=%d），日志 %s" % (rc, cfg_log))
    b_log = logs / ("build-%s.log" % side)
    jobs = str((cfg["builtin"].get("build_profile") or {}).get("parallel_jobs", 8))
    cmd = ["cmake", "--build", str(build), "-j", jobs]
    rc = _run_logged(cmd, cwd=src_tree, log=b_log, timeout=7200)
    if rc:
        raise BuildError("编译失败（rc=%d），日志 %s" % (rc, b_log))
    (logs / ("build-%s.end" % side)).write_text(_now() + "\n")


def _verify_binary(binary, need_pmux, expected_version):
    if not binary.is_file():
        raise BuildError("构建产物缺失：%s" % binary)
    p = subprocess.run([str(binary), "-V"], text=True, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, timeout=300)
    version_ok = p.returncode == 0 and expected_version in p.stdout
    if not version_ok:
        raise BuildError("二进制身份检查失败：%s（rc=%d）" % (binary, p.returncode))
    help_ok = None
    if need_pmux:
        p2 = subprocess.run([str(binary), "-p", "help pmux_opt"], text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
        help_ok = p2.returncode == 0 and "No such command" not in p2.stdout \
            and "pmux_opt" in p2.stdout
        if not help_ok:
            raise BuildError("优化版缺少内置 pmux_opt pass（help 检查失败）")
    return {"version": p.stdout.strip().splitlines()[0] if p.stdout.strip() else "",
            "version_ok": version_ok, "help_pmux_ok": help_ok}


def _smoke(build_dir, opt_binary, logs):
    """小型 synth_intel 调用冒烟（冻结 test4 输入；检查 rc=0 且 PMUX_OPT 恰一次）。"""
    rtl = Path(__file__).resolve().parent.parent / \
        "suite-official4/tree/pmux_case/competition_case/test4/test4.v"
    if not rtl.is_file():
        raise BuildError("冒烟输入缺失：%s" % rtl)
    smoke_dir = build_dir / "smoke"
    smoke_dir.mkdir(exist_ok=True)
    ys = smoke_dir / "smoke.ys"
    ys.write_text("read_verilog -sv %s\nsynth_intel -family cycloneiv -top test4\n" % rtl)
    log = smoke_dir / "smoke.log"
    rc = _run_logged([str(opt_binary), "-s", str(ys)], cwd=smoke_dir, log=log, timeout=900)
    text = log.read_text(errors="replace")
    count = len(re.findall(r"\bExecuting\s+PMUX_OPT\b", text))
    ok = rc == 0 and count == 1
    if not ok:
        raise BuildError("冒烟验证失败（rc=%d，PMUX_OPT 次数=%d），日志 %s" % (rc, count, log))
    return {"smoke_ok": True, "smoke_log": str(log)}


def _write_registry_entry(cache_dir, entry):
    d = registry_dir(cache_dir)
    d.mkdir(parents=True, exist_ok=True)
    path = d / (entry["name"] + ".json")
    path.write_text(json.dumps(entry, ensure_ascii=False, indent=2) + "\n")
    return path


def _specs_from_entry(entry):
    return entry.get("baseline") or {}, entry.get("optimized") or {}


def _assemble_builtin_cfg(cfg, baseline_spec, opt_spec):
    """组装本轮有效 builtin 配置（用于 validation_context.json 与身份检查）。"""
    return {
        "baseline": {"path": baseline_spec["binary"], "src_repo": baseline_spec["src_dir"],
                     "src_commit": baseline_spec["src_commit"],
                     "binary_sha256": baseline_spec["binary_sha256"]},
        "optimized": {"path": opt_spec["binary"], "src_repo": opt_spec["src_dir"],
                      "src_commit": opt_spec["src_commit"],
                      "binary_sha256": opt_spec["binary_sha256"],
                      "algorithm_source_path": opt_spec.get("algorithm_source_path",
                                                             ALGORITHM_SOURCE_PATH),
                      "algorithm_source_sha256": opt_spec["algorithm_source_sha256"],
                      "integration_diff_sha256": opt_spec["integration_diff_sha256"]},
        "abc": {"baseline": baseline_spec["abc"], "optimized": opt_spec["abc"]},
        "expected_version": cfg["builtin"]["expected_version"],
        "integration_evidence": list(cfg["builtin"]["integration_evidence"]),
    }


def _build_sides(cfg, source_bytes, source_sha256, cache_dir, *,
                 need_baseline, baseline_spec, opt_reuse_spec):
    """在缓存命名空间新建构建（只构建需要的侧），验证后登记 READY。"""
    cache_dir.mkdir(parents=True, exist_ok=True)
    lock = _acquire_lock(cache_dir)
    try:
        build_dir = _unique_build_dir(cache_dir, source_sha256)
        logs = build_dir / "build-logs"
        logs.mkdir()
        entry = {
            "schema": SCHEMA, "name": build_dir.name, "created_at": _now(),
            "status": "BUILDING", "imported": False, "build_dir": str(build_dir),
            "key": cache_key(cfg, source_sha256),
            "integration_id": INTEGRATION_ID,
            "build_profile": build_profile(cfg),
            "compiler": compiler_identity(cfg),
            "abc_source_commit": _current_abc_commit(cfg),
            "logs": {"dir": str(logs)},
        }
        sides = []
        if need_baseline:
            sides.append("baseline")
        if opt_reuse_spec is None:
            sides.append("optimized")
        if not sides:
            raise BuildError("没有需要构建的侧（内部错误）")
        try:
            src_commit = cfg["builtin"]["source_commit"]
            for side in sides:
                tree = build_dir / ("%s-src" % side)
                _copy_source_tree(cfg, tree, logs, side)
                head = _git(tree, "rev-parse", "HEAD")
                if head != src_commit:
                    raise BuildError("复制后 %s 树 HEAD=%s 与登记基础提交 %s 不一致"
                                     % (side, head, src_commit))
                if side == "optimized":
                    alg = tree / ALGORITHM_SOURCE_PATH
                    alg.write_bytes(source_bytes)
                    if _sha256_file(alg) != source_sha256:
                        raise BuildError("提取的算法源码哈希与请求提交不一致")
                    cmake = tree / "passes/opt/CMakeLists.txt"
                    synth = tree / "techlibs/intel/synth_intel.cc"
                    c_new, s_new, _ = insert_integration(cmake.read_text(), synth.read_text())
                    cmake.write_text(c_new)
                    synth.write_text(s_new)
                    diff_text = _git(tree, "diff")
                    diff_sha = _check_integration_diff(diff_text)
                    entry["optimized"] = {
                        "action": "built", "src_dir": str(tree), "src_commit": head,
                        "algorithm_source_path": ALGORITHM_SOURCE_PATH,
                        "algorithm_source_sha256": source_sha256,
                        "integration_diff_sha256": diff_sha,
                        "binary": str(tree / "build/yosys"),
                        "binary_sha256": None,
                        "abc": str(tree / "build/yosys-abc"), "abc_sha256": None,
                    }
                else:
                    if _git(tree, "diff"):
                        raise BuildError("baseline 树存在未提交改动")
                    entry["baseline"] = {
                        "action": "built", "src_dir": str(tree), "src_commit": head,
                        "binary": str(tree / "build/yosys"), "binary_sha256": None,
                        "abc": str(tree / "build/yosys-abc"), "abc_sha256": None,
                    }
                _cmake_build(tree, logs, side, cfg)
                _write_provenance(cfg, tree, ["rsync", "-a", "--exclude=/build/",
                                              str(cfg["builtin"]["source_repo"]) + "/",
                                              str(tree) + "/"], logs, side)
            # 完整登记复用侧信息（若 baseline 或 optimized 某侧为复用）。
            if not need_baseline and baseline_spec is not None:
                entry["baseline"] = dict(baseline_spec, action="reuse")
            if opt_reuse_spec is not None:
                entry["optimized"] = dict(opt_reuse_spec, action="reuse")
            # 产物身份 + 验证。
            verification = {}
            for side in ("baseline", "optimized"):
                spec = entry[side]
                binary = Path(spec["binary"])
                spec = dict(spec)
                if not binary.is_file():
                    raise BuildError("构建产物缺失：%s" % binary)
                spec["binary_sha256"] = _sha256_file(binary)
                abc = Path(spec["abc"])
                if not abc.is_file():
                    raise BuildError("构建 ABC 缺失：%s" % abc)
                spec["abc_sha256"] = _sha256_file(abc)
                entry[side] = spec
                if side in sides:
                    verification[side] = _verify_binary(
                        binary, side == "optimized", cfg["builtin"]["expected_version"])
            if "optimized" in sides:
                verification["smoke"] = _smoke(build_dir, Path(entry["optimized"]["binary"]), logs)
            entry["verification"] = verification
            entry["status"] = "READY"
        except Exception as exc:
            entry["status"] = "FAILED"
            entry["error"] = str(exc)
            _write_registry_entry(cache_dir, entry)
            raise BuildError(str(exc), build_dir=build_dir,
                             logs={"dir": str(logs)}) from exc
        path = _write_registry_entry(cache_dir, entry)
        entry["_file"] = str(path)
        return entry
    finally:
        _release_lock(lock)


def prepare_builtin(cfg, source_sha256, source_bytes=None, cache_dir=None):
    """解析（必要时构建）两侧内置工具；返回 {builtin, record, registry_entry}。

    - 缓存命中/复用：不编译；
    - 未命中：真实构建（构建锁 + 日志 + 失败登记；失败抛 BuildError，不发布完成标记）。
    """
    cache_dir = Path(cache_dir) if cache_dir else Path(cfg["builtin"]["cache_dir"])
    plan = plan_builtin(cfg, source_sha256, cache_dir=cache_dir)
    if plan["blocked"]:
        raise BuildError("构建环境不满足：" + "；".join(
            "%s: %s" % (b["item"], b["detail"]) for b in plan["blocked"]))
    need_baseline = plan["baseline"]["action"] == "build"
    bspec, _ = resolve_baseline_reuse(cfg)
    key = cache_key(cfg, source_sha256)
    hit = find_cached_optimized(cache_dir, key,
                                current_abc_commit=_current_abc_commit(cfg))
    record = {"cache_dir": str(cache_dir), "integration_id": INTEGRATION_ID}
    if hit is not None and not need_baseline:
        builtin = _assemble_builtin_cfg(cfg, bspec, hit["optimized"])
        record["baseline"] = {"action": "reuse", "path": bspec["binary"],
                              "reason": plan["baseline"]["reason"]}
        record["optimized"] = {"action": "reuse", "path": hit["optimized"]["binary"],
                               "source": hit.get("_file"),
                               "reason": plan["optimized"]["reason"]}
        record["registry_entry"] = hit.get("_file")
        record["summary"] = "baseline 复用；optimized 复用（缓存命中 %s）" % (
            Path(hit.get("_file", "")).name)
        return {"builtin": builtin, "record": record, "registry_entry": hit.get("_file")}
    # 需要构建（可能有复用侧，例如 baseline 复用 + optimized 新建）。
    if source_bytes is None:
        source_bytes = subprocess.check_output(
            ["git", "-C", cfg["repo"], "show", "{}:src/pmux_opt.cc".format(cfg["target_commit"])])
        if hashlib.sha256(source_bytes).hexdigest() != source_sha256:
            raise BuildError("从仓库提取的算法源码与请求提交哈希不一致")
    entry = _build_sides(cfg, source_bytes, source_sha256, cache_dir,
                         need_baseline=need_baseline, baseline_spec=bspec,
                         opt_reuse_spec=(hit["optimized"] if hit is not None else None))
    builtin = _assemble_builtin_cfg(cfg, entry["baseline"], entry["optimized"])
    record["baseline"] = {"action": entry["baseline"].get("action"),
                          "path": entry["baseline"]["binary"],
                          "reason": ("新建（%s）" % entry["baseline"]["src_dir"])
                          if entry["baseline"].get("action") == "built"
                          else plan["baseline"]["reason"]}
    record["optimized"] = {"action": "built", "path": entry["optimized"]["binary"],
                           "build_dir": entry["build_dir"],
                           "logs": entry.get("logs"),
                           "reason": "缓存未命中，已从基础提交新建构建"}
    record["registry_entry"] = entry.get("_file")
    record["summary"] = "baseline %s；optimized 新建（%s）" % (
        "复用" if not need_baseline else "新建", entry["build_dir"])
    return {"builtin": builtin, "record": record, "registry_entry": entry.get("_file")}


# ---------------------------------------------------------------- 导入既有构建
def import_prebuilt(cfg, build_dir, name=None):
    """把既有已核验构建登记进缓存命名空间 registry/（不移动、不覆盖既有构建）。

    核对：两侧源码树提交 / baseline 无改动 / 优化侧集成 diff 为标准模板 /
    算法源码哈希 / 二进制与 ABC 存在；跑一次小型冒烟后登记 READY。
    """
    build_dir = Path(build_dir)
    name = name or build_dir.name
    if not build_dir.is_dir():
        raise BuildError("构建目录不存在：%s" % build_dir)
    cache_dir = Path(cfg["builtin"]["cache_dir"])
    for existing in _read_registry_entries(cache_dir):
        if existing.get("name") == name:
            if existing.get("status") == "READY":
                return existing
            raise BuildError("同名条目已存在且非 READY：%s" % existing.get("_file"))
    src_commit = cfg["builtin"]["source_commit"]
    entry = {"schema": SCHEMA, "name": name, "created_at": _now(),
             "status": "BUILDING", "imported": True, "build_dir": str(build_dir),
             "key": None, "integration_id": INTEGRATION_ID,
             "build_profile": build_profile(cfg), "compiler": compiler_identity(cfg),
             "abc_source_commit": _current_abc_commit(cfg),
             "logs": {"dir": str(build_dir / "build-logs")}}
    try:
        for side in ("baseline", "optimized"):
            tree = build_dir / ("%s-src" % side)
            if not (tree / ".git").exists():
                raise BuildError("%s 源码树缺失：%s" % (side, tree))
            head = _git(tree, "rev-parse", "HEAD")
            if head != src_commit:
                raise BuildError("%s 树 HEAD=%s 与登记基础提交不一致" % (side, head))
            spec = {"action": "reuse", "src_dir": str(tree), "src_commit": head,
                    "binary": str(tree / "build/yosys"),
                    "abc": str(tree / "build/yosys-abc")}
            if side == "baseline":
                if _git(tree, "diff"):
                    raise BuildError("baseline 树存在未提交改动（影响来源证据）")
            else:
                diff_text = _git(tree, "diff")
                spec["integration_diff_sha256"] = _check_integration_diff(diff_text)
                alg = tree / ALGORITHM_SOURCE_PATH
                if not alg.is_file():
                    raise BuildError("优化版算法源码缺失：%s" % alg)
                spec["algorithm_source_path"] = ALGORITHM_SOURCE_PATH
                spec["algorithm_source_sha256"] = _sha256_file(alg)
            entry[side] = spec
        for side in ("baseline", "optimized"):
            spec = dict(entry[side])
            binary = Path(spec["binary"])
            if not binary.is_file():
                raise BuildError("%s 二进制缺失：%s" % (side, binary))
            spec["binary_sha256"] = _sha256_file(binary)
            abc = Path(spec["abc"])
            if not abc.is_file():
                raise BuildError("%s ABC 缺失：%s" % (side, abc))
            spec["abc_sha256"] = _sha256_file(abc)
            entry[side] = spec
        entry["key"] = cache_key(cfg, entry["optimized"]["algorithm_source_sha256"])
        verification = {}
        for side in ("baseline", "optimized"):
            verification[side] = _verify_binary(Path(entry[side]["binary"]),
                                                side == "optimized",
                                                cfg["builtin"]["expected_version"])
        verification["smoke"] = _smoke(build_dir, Path(entry["optimized"]["binary"]),
                                       build_dir / "build-logs")
        entry["verification"] = verification
        entry["status"] = "READY"
    except Exception as exc:
        entry["status"] = "FAILED"
        entry["error"] = str(exc)
        _write_registry_entry(cache_dir, entry)
        raise BuildError(str(exc), build_dir=build_dir) from exc
    path = _write_registry_entry(cache_dir, entry)
    entry["_file"] = str(path)
    return entry
