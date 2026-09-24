#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""official4-p2 功能验证公共库：noDF 策略严格转换、EQY setup、执行与日志联合判定。

设计约定：
- 不读取轮次上下文（不 import p3_common），工具路径与超时由调用方传入，便于单元测试；
- 策略修正必须“逐字节可核对”：只允许删除恰一处 ` -set-def-formal`，其余文本不变；
  任何不符（数量不为 1、无 sat 行、出现额外变化）立即抛 TransformError，由调用方停止；
- 判定不依赖单一 SUCCESS 字样：须同时满足成功标记、基例与归纳长度、断言导入覆盖与
  错误扫描（见 classify_proof_text / verify_expected_asserts），由调用方再叠加退出状态。
"""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
from pathlib import Path

STRATEGY_VERSION = "noDF-local-r1"
MODEL_VERSION = "dffeas-v3"

SAT_PREFIX = "sat -tempinduct"
DEF_FORMAL = " -set-def-formal"

MARK_BASE_FAIL = "model found for base case"
MARK_INDUCT_FAILED = "Induction step failed"
MARK_INDUCT_SUCCESS = "Induction step proven: SUCCESS!"
MARK_EXHAUSTED = "Reached maximum"


class TransformError(ValueError):
    """EQY 生成的 run.ys 不符合预期格式：必须停止并说明，不得静默继续。"""


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_sat_line(lines):
    idx = [i for i, l in enumerate(lines) if l.strip().startswith(SAT_PREFIX)]
    if len(idx) != 1:
        raise TransformError(
            "expect exactly one '{}' line, found {}".format(SAT_PREFIX, len(idx)))
    return idx[0]


def transform_run_ys(text: str):
    """严格删除唯一一处 ` -set-def-formal`；返回 (new_text, info)。

    校验：sat 行恰一条；` -set-def-formal` 恰一处；删除后其余文本逐字节不变。
    任何不符即抛 TransformError（调用方必须停止并说明）。
    """
    lines = text.splitlines()
    i = _find_sat_line(lines)
    before = lines[i]
    n = before.count(DEF_FORMAL)
    if n != 1:
        raise TransformError(
            "expect exactly one '{}' token on sat line, found {}: {!r}".format(
                DEF_FORMAL.strip(), n, before))
    after = before.replace(DEF_FORMAL, "", 1)
    if "set-def-formal" in after:
        raise TransformError("token still present after removal")
    new_lines = list(lines)
    new_lines[i] = after
    new_text = "\n".join(new_lines) + ("\n" if text.endswith("\n") else "")
    if text.replace(DEF_FORMAL, "", 1) != new_text:
        raise TransformError("transform changed more than the expected token")
    return new_text, {"sat_line_before": before, "sat_line_after": after,
                      "removed_def_formal": 1}


def make_probe_ys(text: str, variant: str) -> str:
    """把最终 sat 行替换为“无证明目标”的前提探针。

    variant='noDF'：sat -seq 1 -set-init-undef -set-def-inputs -set-assumes miter
    variant='DF'  ：额外带 -set-def-formal（历史签名对照，仅记录）
    解读（01 文档口径）：'SAT solving finished - no model found.' = 前提 UNSAT；
    'SAT solving finished - model found:' = 前提 SAT（深度 1，不代表所有时刻可达性）。
    """
    if variant not in ("noDF", "DF"):
        raise ValueError("unknown probe variant: {!r}".format(variant))
    lines = text.splitlines()
    i = _find_sat_line(lines)
    probe = ["chformal -assert -remove", "sat -seq 1 -set-init-undef"]
    if variant == "DF":
        probe[1] += " -set-def-formal"
    probe[1] += " -set-def-inputs -set-assumes miter"
    new_lines = lines[:i] + probe + lines[i + 1:]
    return "\n".join(new_lines) + ("\n" if text.endswith("\n") else "")


def classify_proof_text(text: str) -> dict:
    """联合判定证明日志（标记、长度、覆盖、错误）；不使用 yosys 退出码。

    状态：PASS 需同时满足——出现 `Induction step proven: SUCCESS!`、基例数量 >= 成功
    归纳长度、至少 1 条断言导入记录、全文无 `ERROR:`。浅反例（基例 model found）→ FAIL；
    `Reached maximum` → UNKNOWN；其余缺失 → INCOMPLETE；仅错误 → TOOL_OR_CONFIG_ERROR。
    """
    out = {"state": "INCOMPLETE", "induct_len": None, "failed_steps": 0,
           "base_proven": 0, "base_fail_len": None, "asserts": [], "errors": []}
    out["errors"] = re.findall(r"ERROR: (.*)", text)[:8]
    out["base_proven"] = len(re.findall(r"Base case for induction length \d+ proven", text))
    out["failed_steps"] = len(re.findall(MARK_INDUCT_FAILED, text))
    sidx = text.find(MARK_INDUCT_SUCCESS)
    if sidx >= 0:
        mm = list(re.finditer(r"Trying induction with length (\d+)", text[:sidx]))
        out["induct_len"] = int(mm[-1].group(1)) if mm else None
    idx = text.find(MARK_BASE_FAIL)
    if idx >= 0:
        mm = list(re.finditer(r"\[base case (\d+)\]", text[:idx]))
        out["base_fail_len"] = int(mm[-1].group(1)) if mm else None
    out["asserts"] = sorted(set(re.findall(r"Import proof for assert: (\S+)", text)))
    if out["base_fail_len"] is not None:
        out["state"] = "FAIL"
    elif MARK_EXHAUSTED in text:
        out["state"] = "UNKNOWN"
    elif sidx >= 0:
        ok = (not out["errors"] and out["base_proven"] >= 1
              and out["induct_len"] is not None
              and out["base_proven"] >= out["induct_len"]
              and len(out["asserts"]) >= 1)
        out["state"] = "PASS" if ok else "INCOMPLETE"
    elif out["errors"]:
        out["state"] = "TOOL_OR_CONFIG_ERROR"
    return out


def classify_probe_text(text: str) -> dict:
    res = {"verdict": "OTHER", "x_in_init": None}
    m = re.search(r"Final init constraint equation: .*? = (\S+)", text)
    if m:
        res["x_in_init"] = "x" in m.group(1)
    if "SAT solving finished - no model found." in text:
        res["verdict"] = "PREMISES_UNSAT"
    elif "SAT solving finished - model found:" in text:
        res["verdict"] = "PREMISES_SAT"
    return res


def verify_expected_asserts(assert_suffixes, asserts):
    """要求覆盖全部预期断言（后缀匹配）；返回 (ok, missing)。"""
    missing = [s for s in assert_suffixes if not any(a.endswith(s) for a in asserts)]
    return (not missing), missing


def setup_eqy(cfg_path, workdir, log_path, *, yosys, abc, eqy, timeout_s=1800, jobs=4) -> int:
    """EQY setup-only（-m）：只生成分区与脚本，不执行证明。拒绝覆盖既有路径。"""
    cfg_path, workdir, log_path = Path(cfg_path), Path(workdir), Path(log_path)
    if workdir.exists():
        raise FileExistsError("refusing to reuse workdir: {}".format(workdir))
    if log_path.exists():
        raise FileExistsError("refusing to overwrite log: {}".format(log_path))
    env = dict(os.environ, YOSYS=str(yosys), ABC=str(abc), LC_ALL="C.UTF-8",
               PATH=str(Path(yosys).parent) + os.pathsep + os.environ.get("PATH", "/usr/bin:/bin"))
    cmd = [str(eqy), "-m", "-j", str(jobs), "-d", str(workdir),
           "--yosys", str(yosys), "--abc", str(abc), str(cfg_path)]
    with log_path.open("x") as f:
        p = subprocess.Popen(cmd, cwd=str(cfg_path.parent), stdout=f,
                             stderr=subprocess.STDOUT, env=env, start_new_session=True)
        try:
            return p.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, 9)
            p.wait()
            return 124


def run_yosys_script(ys_path, log_path, cwd, *, yosys, timeout_s) -> int:
    """在指定目录执行 yosys 脚本（-ql 写日志）；超时杀进程组并返回 124。拒绝覆盖日志。"""
    ys_path, log_path, cwd = Path(ys_path), Path(log_path), Path(cwd)
    if log_path.exists():
        raise FileExistsError("refusing to overwrite log: {}".format(log_path))
    cmd = [str(yosys), "-ql", str(log_path.resolve()), ys_path.name]
    with open(os.devnull, "wb") as devnull:
        p = subprocess.Popen(cmd, cwd=str(cwd), stdout=devnull,
                             stderr=subprocess.STDOUT, start_new_session=True)
        try:
            return p.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, 9)
            p.wait()
            return 124
