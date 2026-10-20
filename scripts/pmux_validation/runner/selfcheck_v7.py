#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Small real-process checks for the V7 PowerShell wall-time measurement path."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from measure_v7 import METHOD, SCHEME, run_wall_measured, wall_errors


def _sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _alive(pid):
    import ctypes
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
    kernel32.OpenProcess.restype = ctypes.c_void_p
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    kernel32.WaitForSingleObject.restype = ctypes.c_uint32
    handle = kernel32.OpenProcess(0x00100000, False, int(pid))  # SYNCHRONIZE
    if not handle:
        error = ctypes.get_last_error()
        if error == 87:  # ERROR_INVALID_PARAMETER: PID no longer exists
            return False
        raise OSError(error, "OpenProcess failed while checking timeout descendant")
    wait_state = kernel32.WaitForSingleObject(handle, 0)
    kernel32.CloseHandle(handle)
    if wait_state == 258:  # WAIT_TIMEOUT
        return True
    if wait_state == 0:  # WAIT_OBJECT_0
        return False
    raise OSError(ctypes.get_last_error(), "WaitForSingleObject failed")


def run(context, output_dir):
    if os.name != "nt":
        raise RuntimeError("V7 measurement selfcheck requires Windows")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    compiler = Path(context["tools"]["compiler"]["path"])
    compiler_hash = _sha(compiler)
    if compiler_hash.lower() != context["tools"]["compiler"]["sha256"].lower():
        raise RuntimeError("fixed compiler identity mismatch")
    probe_source = Path(__file__).with_name("wall_time_probe.c")
    probe = output_dir / "wall_time_probe.exe"
    compile_log = output_dir / "compile.log"
    with compile_log.open("wb") as log:
        # MSYS2's linker may misdecode a Unicode destination passed from a
        # Windows process. Compile under an ASCII temp path, then copy with the
        # Python Windows filesystem API to the evidence directory.
        with tempfile.TemporaryDirectory(prefix="pmux-v7-probe-") as temp_dir:
            temp_probe = Path(temp_dir) / "wall_time_probe.exe"
            subprocess.run([str(compiler), "-O2", str(probe_source), "-o", str(temp_probe)],
                           stdout=log, stderr=subprocess.STDOUT, check=True, timeout=120)
            shutil.copyfile(temp_probe, probe)

    powershell = Path(context["wall_time_tool"]["path"])
    result = {"schema": 1, "performance_scheme": SCHEME, "method": METHOD,
              "selftest_ok": False, "compiler_path": str(compiler),
              "compiler_sha256": compiler_hash,
              "probe_source_sha256": _sha(probe_source), "probe_sha256": _sha(probe),
              "powershell_path": str(powershell), "powershell_sha256": _sha(powershell),
              "checks": {}, "records": {}}
    passed = True

    def invoke(name, mode, timeout=15):
        folder = output_dir / name
        folder.mkdir()
        row = run_wall_measured(
            [str(probe), mode], cwd=folder, log_path=folder / "host.log",
            stdout_path=folder / "native.stdout.bin", stderr_path=folder / "native.stderr.bin",
            result_path=folder / "measure_result.json", timeout_s=timeout,
            powershell_path=powershell, env=os.environ.copy())
        row["powershell_identity_match"] = (
            Path(row.get("powershell_path", "")).resolve() == powershell.resolve()
            and row.get("powershell_sha256", "").lower()
            == context["wall_time_tool"]["sha256"].lower())
        row["side"] = "probe"
        result["records"][name] = row
        return folder, row

    folder, row = invoke("delayed_exit_and_unicode_path", "--delayed")
    result["checks"]["waits_for_native_exit_and_captures_both_streams"] = bool(
        row.get("rc") == 0 and row.get("process_exit_observed") is True
        and row.get("stdout_capture_complete") is True
        and row.get("stderr_capture_complete") is True
        and row.get("time_span_ticks", 0) >= 2_000_000
        and (folder / "late.marker").is_file()
        and b"probe-late-output" in (folder / "native.stdout.bin").read_bytes()
        and b"probe-error-stream-end" in (folder / "native.stderr.bin").read_bytes()
        and not wall_errors(row, require_synthesis=False))

    folder, row = invoke("large_stdout_stderr", "--large")
    result["checks"]["large_output_drains_without_deadlock"] = bool(
        row.get("rc") == 0 and row.get("stdout_capture_complete") is True
        and row.get("stderr_capture_complete") is True
        and (folder / "native.stdout.bin").stat().st_size == 1024 * 1024
        and (folder / "native.stderr.bin").stat().st_size == 1024 * 1024
        and not wall_errors(row, require_synthesis=False))

    folder, row = invoke("nonzero_exit", "--fail")
    result["checks"]["native_nonzero_exit_is_invalid"] = bool(
        row.get("rc") == 7 and row.get("process_exit_observed") is True
        and "native Yosys failed or timed out" in wall_errors(row, require_synthesis=False))

    folder, row = invoke("timeout_kills_process_tree", "--tree", timeout=1.0)
    child_pid = None
    pid_file = folder / "child.pid"
    if pid_file.is_file():
        try:
            child_pid = int(pid_file.read_text(encoding="ascii").strip())
        except (OSError, ValueError):
            child_pid = None
    result["records"]["timeout_kills_process_tree"]["child_pid"] = child_pid
    child_stopped = child_pid is not None and not _alive(child_pid)
    result["checks"]["timeout_is_invalid_and_kills_descendants"] = bool(
        row.get("timed_out") is True and row.get("time_span_ticks", 0) > 0
        and row.get("process_exit_observed") is not True and child_stopped)

    result["selftest_ok"] = all(result["checks"].values())
    result["note"] = (
        "Probe only: verifies Measure-Command invocation, full target exit/output capture, "
        "timeout cleanup, and failure classification. It is not a synthesis performance sample."
    )
    (output_dir / "selftest_results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name, ok in result["checks"].items():
        print("selfcheck {}: {}".format(name, "PASS" if ok else "FAIL"), flush=True)
    print("selftest_ok={}".format(result["selftest_ok"]), flush=True)
    return 0 if result["selftest_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(run(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")), sys.argv[2]))
