#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V7 单次 PowerShell Measure-Command 墙钟计时及退出事件内存。"""
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from measure_v4 import CASES, memory_errors, resource_signature, save
from process_utils import terminate_process_tree

SCHEME = "pmux-perf-single-powershell-wall-exitpeak-v7"
METHOD = "powershell-measure-command-elapsed-wall-v1"
POLICY = {"wall_runs_per_side": 1, "memory_runs_per_side": 1,
          "stage_timeout_s": 1800}
TICKS_PER_MILLISECOND = 10_000
MEASURE_SCRIPT = Path(__file__).with_name("measure_command_v7.ps1")


def schedule():
    """Eight ordinary wall-time runs followed by eight independent memory runs."""
    for purpose in ("wall_time", "memory"):
        for case in CASES:
            for side in ("baseline", "optimized"):
                yield {"case": case, "side": side, "purpose": purpose}


def compare(base_ticks, opt_ticks):
    if (type(base_ticks) is not int or type(opt_ticks) is not int
            or base_ticks <= 0 or opt_ticks <= 0):
        return {"wall_overhead_pct": None, "wall_5pct": "INVALID",
                "wall_15pct": "INVALID", "wall_verdict": "INVALID",
                "official_midband_score": "NOT_DETERMINED"}
    over = (opt_ticks - base_ticks) * 100.0 / base_ticks
    within5 = opt_ticks * 100 <= base_ticks * 105
    within15 = opt_ticks * 100 <= base_ticks * 115
    return {"wall_overhead_pct": over,
            "wall_5pct": "PASS" if within5 else "FAIL",
            "wall_15pct": "PASS" if within15 else "FAIL",
            "wall_verdict": "PASS" if within5 else "FAIL",
            "official_midband_score": ("NOT_DETERMINED" if not within5 and within15
                                       else "ABOVE_15_THRESHOLD" if not within15
                                       else "UP_TO_5_THRESHOLD")}


def wall_errors(row, require_synthesis=True):
    errors = []
    if row.get("performance_scheme") != SCHEME:
        errors.append("performance scheme mismatch")
    if row.get("wall_time_method") != METHOD:
        errors.append("Measure-Command method identity mismatch")
    for key in ("time_span_ticks", "native_pid"):
        if type(row.get(key)) is not int or row[key] <= 0:
            errors.append(key + " missing or invalid")
    ms = row.get("total_milliseconds")
    ticks = row.get("time_span_ticks")
    if (type(ms) not in (int, float) or not math.isfinite(ms) or ms <= 0
            or type(ticks) is not int
            or not math.isclose(ms, ticks / TICKS_PER_MILLISECOND,
                                rel_tol=0.0, abs_tol=1e-6)):
        errors.append("TimeSpan ticks/milliseconds mismatch")
    if row.get("rc") != 0 or row.get("timed_out") is not False:
        errors.append("native Yosys failed or timed out")
    if row.get("process_exit_observed") is not True:
        errors.append("native process exit was not observed")
    if row.get("stdout_capture_complete") is not True or row.get("stderr_capture_complete") is not True:
        errors.append("native output capture incomplete")
    if row.get("measure_command_module") != "Microsoft.PowerShell.Utility":
        errors.append("Measure-Command cmdlet source mismatch")
    if row.get("measure_command_source") != "Microsoft.PowerShell.Utility":
        errors.append("Measure-Command command source mismatch")
    if row.get("powershell_major") != 5 or row.get("powershell_minor") != 1:
        errors.append("Windows PowerShell 5.1 identity mismatch")
    if not row.get("powershell_path") or not isinstance(row.get("powershell_sha256"), str) \
            or len(row["powershell_sha256"]) != 64:
        errors.append("PowerShell executable identity missing")
    if row.get("powershell_identity_match") is not True:
        errors.append("PowerShell executable does not match fixed tool identity")
    script_hash = row.get("measure_script_sha256")
    if not isinstance(script_hash, str) or len(script_hash) != 64:
        errors.append("Measure-Command script identity missing")
    if not row.get("actual_command") or not row.get("working_directory"):
        errors.append("actual command or working directory missing")
    env_hash = row.get("environment_sha256")
    if not isinstance(env_hash, str) or len(env_hash) != 64:
        errors.append("inherited environment fingerprint missing")
    for key in ("stdout_path", "stderr_path"):
        if not row.get(key) or not Path(row[key]).is_file():
            errors.append(key + " missing")
    if row.get("measurement_error") not in (None, ""):
        errors.append("PowerShell measurement failed: " + str(row["measurement_error"]))
    if require_synthesis:
        command = row.get("actual_command") or []
        if not command or Path(str(command[0])).name.lower() != "yosys.exe":
            errors.append("target is not a direct Windows yosys.exe invocation")
        if not row.get("case") or row.get("purpose") != "wall_time":
            errors.append("wall-time run case/purpose identity missing")
        for key in ("flow_match", "stat_exists", "resource_match"):
            if row.get(key) is not True:
                errors.append(key + " missing/false")
        outputs = row.get("required_outputs") or {}
        if not outputs or any(value is not True for value in outputs.values()):
            errors.append("required synthesis output missing")
    return errors


def _powershell_identity(context):
    spec = context.get("wall_time_tool") or {}
    exe = Path(spec.get("path", ""))
    if not exe.is_file():
        raise FileNotFoundError("Fixed Windows PowerShell missing: " + str(exe))
    digest = hashlib.sha256(exe.read_bytes()).hexdigest()
    if spec.get("sha256") and digest.lower() != spec["sha256"].lower():
        raise ValueError("Windows PowerShell SHA-256 mismatch")
    return exe


def run_wall_measured(command, *, cwd, log_path, stdout_path, stderr_path,
                      result_path, timeout_s, powershell_path, env=None):
    """Run one direct native command; only the PS Measure-Command TimeSpan scores."""
    cwd = Path(cwd).resolve()
    log_path, stdout_path, stderr_path, result_path = map(
        lambda value: Path(value).resolve(), (log_path, stdout_path, stderr_path, result_path))
    if not MEASURE_SCRIPT.is_file():
        raise FileNotFoundError("V7 PowerShell measurement script missing: " + str(MEASURE_SCRIPT))
    if not cwd.is_dir():
        raise FileNotFoundError("V7 working directory missing: " + str(cwd))
    exe = Path(command[0]).resolve()
    argv = [str(exe), *[str(part) for part in command[1:]]]
    request_path = cwd / "measure_request.json"
    request = {
        "schema": 1, "method": METHOD, "performance_scheme": SCHEME,
        "executable": str(exe),
        "arguments": argv[1:], "argument_string": subprocess.list2cmdline(argv[1:]),
        "working_directory": str(cwd), "timeout_ms": max(1, int(timeout_s * 1000)),
        "stdout_path": str(stdout_path), "stderr_path": str(stderr_path),
        "result_path": str(result_path),
    }
    request_path.write_text(json.dumps(request, ensure_ascii=False, indent=2), encoding="utf-8")
    helper = [str(powershell_path), "-NoLogo", "-NoProfile", "-NonInteractive",
              "-ExecutionPolicy", "Bypass", "-File", str(MEASURE_SCRIPT),
              "-RequestPath", str(request_path)]
    powershell_path = Path(powershell_path).resolve()
    result = {"wall_time_method": METHOD, "performance_scheme": SCHEME,
              "actual_command": argv, "powershell_command": helper,
              "powershell_path": str(powershell_path),
              "powershell_sha256": hashlib.sha256(powershell_path.read_bytes()).hexdigest(),
              "working_directory": str(cwd), "request_path": str(request_path),
              "request_sha256": hashlib.sha256(request_path.read_bytes()).hexdigest(),
              "measure_script": str(MEASURE_SCRIPT),
              "measure_script_sha256": hashlib.sha256(MEASURE_SCRIPT.read_bytes()).hexdigest(),
              "stdout_path": str(stdout_path), "stderr_path": str(stderr_path),
              "powershell_host_stdout": str(log_path.with_suffix(".host.stdout.log")),
              "powershell_host_stderr": str(log_path.with_suffix(".host.stderr.log")),
              "rc": None, "timed_out": False, "process_exit_observed": False,
              "stdout_capture_complete": False, "stderr_capture_complete": False,
              "measurement_error": None}
    result["environment_sha256"] = hashlib.sha256(json.dumps(
        sorted((str(key), str(value)) for key, value in (env or os.environ).items()),
        ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
    proc = None
    try:
        with open(result["powershell_host_stdout"], "wb") as host_out, \
                open(result["powershell_host_stderr"], "wb") as host_err:
            proc = subprocess.Popen(helper, cwd=str(cwd), env=env,
                                    stdout=host_out, stderr=host_err,
                                    **({"creationflags": subprocess.CREATE_NO_WINDOW}
                                       if os.name == "nt" else {}))
            result["powershell_pid"] = proc.pid
            try:
                result["powershell_returncode"] = proc.wait(timeout=timeout_s + 30)
            except subprocess.TimeoutExpired:
                result["timed_out"] = True
                terminate_process_tree(proc)
                try:
                    result["powershell_returncode"] = proc.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    result["measurement_error"] = "PowerShell watchdog could not stop process tree"
            if result["powershell_returncode"] != 0 and not result["measurement_error"]:
                result["measurement_error"] = "PowerShell measurement host exited nonzero"
        if result_path.is_file():
            measured = json.loads(result_path.read_text(encoding="utf-8"))
            result.update(measured)
            result["result_path"] = str(result_path)
            result["powershell_returncode"] = proc.returncode if proc else None
            if result.get("timed_out"):
                result["timed_out"] = True
        elif not result.get("measurement_error"):
            result["measurement_error"] = "PowerShell did not write measurement result"
    except Exception as exc:
        result["measurement_error"] = "{}: {}".format(type(exc).__name__, exc)
        if proc is not None and proc.poll() is None:
            terminate_process_tree(proc)
    return result


def judge_case(summary):
    walls = summary.get("wall_runs") or []
    memories = summary.get("memory_runs") or []
    wall_valid = (len(walls) == 2 and {r.get("side") for r in walls} == {"baseline", "optimized"}
                  and all(not wall_errors(r) for r in walls))
    if wall_valid:
        base_row = next(row for row in walls if row.get("side") == "baseline")
        opt_row = next(row for row in walls if row.get("side") == "optimized")
        base_cmd, opt_cmd = base_row.get("actual_command") or [], opt_row.get("actual_command") or []
        wall_valid = (
            base_row.get("environment_sha256") == opt_row.get("environment_sha256")
            and base_row.get("flow_sha256") == opt_row.get("flow_sha256")
            and base_cmd[1:] == opt_cmd[1:]
            and base_row.get("powershell_path") == opt_row.get("powershell_path")
            and base_row.get("powershell_sha256") == opt_row.get("powershell_sha256")
            and base_row.get("measure_script_sha256") == opt_row.get("measure_script_sha256")
            and base_row.get("measure_command_module") == opt_row.get("measure_command_module")
            and base_row.get("measure_command_source") == opt_row.get("measure_command_source")
            and base_row.get("powershell_version") == opt_row.get("powershell_version")
            and base_row.get("case") == opt_row.get("case") == summary.get("case")
            and base_row.get("purpose") == opt_row.get("purpose") == "wall_time"
            and Path(base_row.get("working_directory", "")).parent
            == Path(opt_row.get("working_directory", "")).parent)
        all_flow_hashes = {row.get("flow_sha256") for row in walls + memories}
        wall_valid = wall_valid and len(all_flow_hashes) == 1
    memory_valid = (len(memories) == 2
                    and {r.get("side") for r in memories} == {"baseline", "optimized"}
                    and all(not memory_errors(r) and r.get("performance_scheme") == SCHEME
                            and r.get("case") == summary.get("case")
                            and r.get("purpose") == "memory"
                            and r.get("flow_match") is True
                            and r.get("stat_exists") is True
                            and r.get("resource_match") is True
                            and all(value is True for value in
                                    (r.get("required_outputs") or {}).values())
                            and set(r.get("required_outputs") or {}) == {"mapped.il", "stat.json"}
                            for r in memories))
    complete = (summary.get("execution_complete") is True
                and summary.get("performance_scheme") == SCHEME
                and summary.get("wall_policy") == POLICY)
    wall_valid = wall_valid and complete
    memory_valid = memory_valid and complete

    def value(rows, side, key, valid):
        return next((row.get(key) for row in rows if row.get("side") == side), None) if valid else None

    base_ticks = value(walls, "baseline", "time_span_ticks", wall_valid)
    opt_ticks = value(walls, "optimized", "time_span_ticks", wall_valid)
    wall_judgment = compare(base_ticks, opt_ticks)
    base_mem = value(memories, "baseline", "yosys_peak_working_set_bytes", memory_valid)
    opt_mem = value(memories, "optimized", "yosys_peak_working_set_bytes", memory_valid)
    mem_valid_positive = (type(base_mem) is int and type(opt_mem) is int
                          and base_mem > 0 and opt_mem > 0)
    mem_over = ((opt_mem - base_mem) * 100.0 / base_mem) if mem_valid_positive else None
    mem_ok = bool(mem_valid_positive and opt_mem * 100 <= base_mem * 105)
    time_absolute = (opt_ticks is not None and opt_ticks <= 60 * 10_000_000) or (
        base_ticks is not None and base_ticks > 60 * 10_000_000)
    memory_absolute = (opt_mem is not None and opt_mem <= 2 * 1024**3) or (
        base_mem is not None and base_mem > 2 * 1024**3)
    limit_ok = bool(wall_valid and memory_valid and time_absolute and memory_absolute)
    valid = bool(wall_valid and memory_valid and mem_valid_positive)
    reasons = []
    if not wall_valid:
        reasons.append("Measure-Command墙钟样本缺失、无效或性能轮次未完成")
    elif wall_judgment["wall_5pct"] == "FAIL":
        reasons.append("墙钟时间相对开销超过本地5%目标")
    if not memory_valid or not mem_valid_positive:
        reasons.append("退出事件内存样本缺失或无效")
    elif not mem_ok:
        reasons.append("内存相对开销超过5%")
    if valid and not limit_ok:
        reasons.append("超过60秒墙钟/2GB且原版未超限")
    return {"case": summary.get("case"), "valid": valid, "wall_valid": wall_valid,
            "memory_valid": memory_valid, "wall_base_ticks": base_ticks,
            "wall_opt_ticks": opt_ticks,
            "wall_base_ms": base_ticks / TICKS_PER_MILLISECOND if base_ticks else None,
            "wall_opt_ms": opt_ticks / TICKS_PER_MILLISECOND if opt_ticks else None,
            **wall_judgment, "base_memory_bytes": base_mem, "opt_memory_bytes": opt_mem,
            "base_memory_mib": base_mem / 1024**2 if base_mem else None,
            "opt_memory_mib": opt_mem / 1024**2 if opt_mem else None,
            "mem_overhead_pct": mem_over, "mem_ok": mem_ok,
            "wall_absolute_ok": bool(time_absolute), "memory_absolute_ok": bool(memory_absolute),
            "limit_ok": limit_ok, "limit_bits": {
                "wall_exempt_upstream_over_60s": bool(base_ticks and base_ticks > 60 * 10_000_000),
                "memory_exempt_upstream_over_2gib": bool(base_mem and base_mem > 2 * 1024**3)},
            "pass": bool(valid and wall_judgment["wall_5pct"] == "PASS" and mem_ok and limit_ok),
            "reasons": reasons}


def run(context, round_dir, binaries, flows, *, wall_execute=None, memory_execute=None):
    from win_measure import run_measured
    if context.get("performance_scheme") != SCHEME or context.get("wall_policy") != POLICY:
        raise ValueError("v7 fixed policy mismatch")
    if os.name != "nt" or context.get("mode") != "builtin":
        raise ValueError("v7 requires Windows builtin mode")
    powershell = _powershell_identity(context)
    root = Path(round_dir)
    out = root / "09_时间内存开销_performance" / "round01"
    out.mkdir(parents=True, exist_ok=False)
    wall_execute = wall_execute or run_wall_measured
    memory_execute = memory_execute or run_measured
    summaries = {case: {"case": case, "performance_scheme": SCHEME,
                        "wall_time_method": METHOD, "wall_policy": POLICY,
                        "memory_metric": "yosys_peak_working_set_bytes",
                        "wall_runs": [], "memory_runs": []} for case in CASES}
    expected = {(case, side): resource_signature(
        root / f"05_公开四例_public/round01/{case}/{side}/stat.json")
        for case in CASES for side in binaries}
    started = time.monotonic()
    error = None
    completed = 0
    env = os.environ.copy()
    try:
        for item in schedule():
            case, side, purpose = item["case"], item["side"], item["purpose"]
            folder = out / case / purpose / side
            folder.mkdir(parents=True, exist_ok=False)
            flow = flows[case]
            (folder / "flow.ys").write_text(flow, encoding="utf-8")
            remaining = POLICY["stage_timeout_s"] - (time.monotonic() - started)
            # Reserve bounded timeout cleanup and stream-drain time inside the 30-minute stage cap.
            native_timeout = remaining - 45.0
            if native_timeout <= 0:
                raise TimeoutError("30 minute performance protection limit")
            command = [str(binaries[side]), "-s", "flow.ys"]
            if purpose == "wall_time":
                row = wall_execute(command, cwd=folder, log_path=folder / "run.log",
                                   stdout_path=folder / "yosys.stdout.bin",
                                   stderr_path=folder / "yosys.stderr.bin",
                                   result_path=folder / "measure_result.json",
                                   timeout_s=native_timeout, powershell_path=powershell, env=env)
                wall_tool = context.get("wall_time_tool") or {}
                row["powershell_identity_match"] = (
                    str(Path(row.get("powershell_path", "")).resolve()).lower()
                    == str(Path(wall_tool.get("path", "")).resolve()).lower()
                    and (row.get("powershell_sha256") or "").lower()
                    == str(wall_tool.get("sha256", "")).lower())
                row.update(item, performance_scheme=SCHEME, execution_kind="synthesis")
                row["flow_match"] = (folder / "flow.ys").read_text(encoding="utf-8") == flow
                row["flow_sha256"] = hashlib.sha256(flow.encode("utf-8")).hexdigest()
                row["stat_exists"] = (folder / "stat.json").is_file()
                row["required_outputs"] = {name: (folder / name).is_file()
                                           for name in ("mapped.il", "stat.json")}
                try:
                    row["resource_match"] = resource_signature(folder / "stat.json") == expected[case, side]
                except (OSError, ValueError, KeyError, TypeError):
                    row["resource_match"] = False
                issues = wall_errors(row)
            else:
                row = memory_execute(command, cwd=folder, log_path=folder / "run.log",
                                     timeout_s=native_timeout)
                row.update(item, performance_scheme=SCHEME, execution_kind="synthesis",
                           cpu_role="not_scored_debug_run")
                row["flow_match"] = (folder / "flow.ys").read_text(encoding="utf-8") == flow
                row["flow_sha256"] = hashlib.sha256(flow.encode("utf-8")).hexdigest()
                row["stat_exists"] = (folder / "stat.json").is_file()
                row["required_outputs"] = {name: (folder / name).is_file()
                                           for name in ("mapped.il", "stat.json")}
                try:
                    row["resource_match"] = resource_signature(folder / "stat.json") == expected[case, side]
                except (OSError, ValueError, KeyError, TypeError):
                    row["resource_match"] = False
                issues = memory_errors(row)
                if row.get("performance_scheme") != SCHEME:
                    issues.append("performance scheme mismatch")
                for key in ("flow_match", "stat_exists", "resource_match"):
                    if row.get(key) is not True:
                        issues.append(key + " missing/false")
                if any(value is not True for value in row["required_outputs"].values()):
                    issues.append("required synthesis output missing")
            row["validation_errors"] = issues
            run_key = "wall_runs" if purpose == "wall_time" else "memory_runs"
            summaries[case][run_key].append(row)
            save(folder / "metrics.json", row)
            completed += 1
            print("v7 {}/16 {} {} {}".format(completed, case, purpose, side), flush=True)
            if issues:
                raise ValueError("invalid sample: " + str(issues))
        if time.monotonic() - started >= POLICY["stage_timeout_s"]:
            raise TimeoutError("30 minute performance protection limit")
    except Exception as exc:
        error = "{}: {}".format(type(exc).__name__, exc)
    complete = error is None and completed == 16
    for summary in summaries.values():
        summary.update(execution_complete=complete, execution_error=error)
        case_dir = out / summary["case"]
        case_dir.mkdir(exist_ok=True)
        save(case_dir / "summary.json", summary)
    save(out / "performance_summary.json", list(summaries.values()))
    save(out / "execution_status.json", {
        "complete": complete, "completed": completed, "planned": 16,
        "wall_runs_planned": 8, "memory_runs_planned": 8,
        "error": error, "elapsed_s": time.monotonic() - started,
        "wall_time_method": METHOD, "performance_scheme": SCHEME})
    return 0 if complete else 1
