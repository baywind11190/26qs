#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P3 v1 validation runner; adapted from the preserved 2026-09-22 round.
See ../POLICY.md for scope, provenance and limitations.
"""

import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p3_common as C
import builtin_common as B
from measure_format import collect_metric_values, format_run_progress, sample_errors, merge_cpu_memory_runs, EXIT_PEAK_SCHEME

PAGE_SIZE = os.sysconf("SC_PAGE_SIZE") if os.name != "nt" else None
CLK_TCK = os.sysconf("SC_CLK_TCK") if os.name != "nt" else None


# ---------------------------------------------------------------- 进程树 RSS 采样
def _read_statm_rss_kb(pid: int):
    try:
        with open(f"/proc/{pid}/statm", "r") as f:
            parts = f.read().split()
        return int(parts[1]) * PAGE_SIZE // 1024
    except (OSError, IndexError, ValueError):
        return None


def _read_proc_stat(pid: int):
    """返回 (ppid, pgrp, starttime)。"""
    try:
        with open(f"/proc/{pid}/stat", "rb") as f:
            data = f.read()
        # comm 可能含空格/括号，取最后一个 ')' 之后
        idx = data.rfind(b")")
        fields = data[idx + 2 :].split()
        ppid = int(fields[1])
        pgrp = int(fields[2])
        starttime = int(fields[19])
        return ppid, pgrp, starttime
    except (OSError, IndexError, ValueError):
        return None


class TreeRssMonitor(threading.Thread):
    """按进程组枚举后代并采样 RSS 总和峰值。"""

    def __init__(self, root_pid: int, interval_s: float = 0.005, target_exe=None):
        super().__init__(daemon=True)
        self.root_pid = root_pid
        self.target_exe = target_exe
        self.main_pid = None
        self.main_starttime = None
        self.main_peak_kb = 0
        self.main_samples = 0
        self.interval_s = interval_s
        self.active = True
        self.peak_kb = 0
        self.sum_last_kb = 0
        self.n_samples = 0
        self.max_gap_s = 0.0
        self.pids_seen = set()

    def _sample_once(self):
        root = _read_proc_stat(self.root_pid)
        if root is None:
            return 0
        root_pgrp = root[1]
        total_kb = 0
        # 枚举 /proc 下所有进程
        for entry in os.listdir("/proc"):
            if not entry.isdigit():
                continue
            pid = int(entry)
            st = _read_proc_stat(pid)
            if st is None:
                continue
            ppid, pgrp, _st = st
            if pgrp != root_pgrp:
                continue
            if self.target_exe and ppid == self.root_pid:
                try:
                    matches = str(Path(f"/proc/{pid}/exe").resolve()) == self.target_exe
                    if matches and (self.main_pid is None or
                                    (pid == self.main_pid and _st == self.main_starttime)):
                        self.main_pid, self.main_starttime = pid, _st
                        status = Path(f"/proc/{pid}/status").read_text()
                        hwm = next((int(l.split()[1]) for l in status.splitlines()
                                    if l.startswith("VmHWM:")), 0)
                        self.main_peak_kb = max(self.main_peak_kb, hwm)
                        self.main_samples += 1
                except (OSError, ValueError):
                    pass
            rss = _read_statm_rss_kb(pid)
            if rss is not None:
                total_kb += rss
                self.pids_seen.add(pid)
        return total_kb

    def run(self):
        last = time.perf_counter()
        while self.active:
            kb = self._sample_once()
            now = time.perf_counter()
            self.max_gap_s = max(self.max_gap_s, now - last)
            last = now
            self.n_samples += 1
            self.sum_last_kb = kb
            if kb > self.peak_kb:
                self.peak_kb = kb
            time.sleep(self.interval_s)
        # 最后再采一次（捕捉退出前的峰值）
        kb = self._sample_once()
        self.n_samples += 1
        if kb > self.peak_kb:
            self.peak_kb = kb


# ---------------------------------------------------------------- 运行器
def run_measured(cmd, *, cwd, log_path, timeout_s=1800, sample_interval=0.005):
    """运行命令（经 /usr/bin/time -v 包裹），返回测量结果 dict。

    返回键：rc, timed_out, wall_s, cpu_user_s, cpu_system_s, cpu_total_s,
           tree_rss_peak_kb, rss_samples, max_sample_gap_s, gn_time（dict）
    """
    if os.name == "nt":
        from win_measure import run_measured as run_windows_measured
        return run_windows_measured(cmd, cwd=cwd, log_path=log_path, timeout_s=timeout_s)

    log_path = Path(log_path)
    time_out = log_path.with_suffix(".gnu_time.txt")

    wrapped = [
        "/usr/bin/time",
        "-v",
        "-o",
        str(time_out),
        *cmd,
    ]

    t0 = time.perf_counter()
    with open(log_path, "w") as lf:
        p = subprocess.Popen(
            wrapped,
            cwd=cwd,
            stdout=lf,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        import shutil
        executable = shutil.which(str(cmd[0])) or str(cmd[0])
        mon = TreeRssMonitor(p.pid, sample_interval, str(Path(executable).resolve()))
        mon.start()

        # 超时守护
        timed_out = False
        completed = threading.Event()

        def _killer():
            nonlocal timed_out
            while not completed.wait(0.05):
                if time.perf_counter() - t0 > timeout_s:
                    timed_out = True
                    try:
                        os.killpg(p.pid, 9)
                    except ProcessLookupError:
                        pass
                    return
                time.sleep(0.05)

        killer = threading.Thread(target=_killer, daemon=True)
        killer.start()

        _pid, status, ru = os.wait4(p.pid, 0)
        completed.set()
        p.returncode = os.waitstatus_to_exitcode(status)
        killer.join(timeout=1)
        wall = time.perf_counter() - t0
        mon.active = False
        mon.join(timeout=2.0)

    rc = os.waitstatus_to_exitcode(status)

    # GNU time 解析
    gn = {}
    if time_out.exists():
        for line in time_out.read_text(errors="replace").splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                gn[k.strip()] = v.strip()
    gn_maxrss = None
    if "Maximum resident set size (kbytes)" in gn:
        try:
            gn_maxrss = int(gn["Maximum resident set size (kbytes)"])
        except ValueError:
            gn_maxrss = None

    def _num(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    gn_user = _num(gn.get("User time (seconds)"))
    gn_sys = _num(gn.get("System time (seconds)"))

    return {
        "rc": rc,
        "timed_out": bool(timed_out),
        "wall_s": round(wall, 4),
        "cpu_user_s": round(ru.ru_utime, 4),
        "cpu_system_s": round(ru.ru_stime, 4),
        "cpu_total_s": round(ru.ru_utime + ru.ru_stime, 4),
        "tree_rss_peak_kb": mon.peak_kb,
        "yosys_main_rss_peak_kb": mon.main_peak_kb or None,
        "yosys_main_pid": mon.main_pid,
        "yosys_main_rss_samples": mon.main_samples,
        "memory_metric": "yosys_main_rss_peak_kb",
        "rss_samples": mon.n_samples,
        "max_sample_gap_s": round(mon.max_gap_s, 4),
        "sample_interval_s": sample_interval,
        "gn_time_maxrss_kb": gn_maxrss,
        "gn_time_user_s": gn_user,
        "gn_time_system_s": gn_sys,
        "gn_time_path": str(time_out),
    }


# ---------------------------------------------------------------- 被测命令构造
def gen_measure_ys(rtl: Path, top: str, *, optimized: bool, stat_json: Path) -> str:
    """无 dump 的完整 P3 流程（测量口径）。"""
    lines = [f"read_verilog -sv {rtl}"]
    lines.append(f"synth_intel -family cycloneiv -top {top} -run begin:coarse")
    lines += [
        "proc", "check", "flatten", "tribuf -logic", "deminout",
        "opt_expr", "opt_clean", "check", "opt -nodffe -nosdff",
        "fsm", "opt",
    ]
    if optimized:
        lines.append("pmux_opt")
    lines += [
        "wreduce", "peepopt", "opt_clean",
        "techmap -map +/cmp2lut.v -D LUT_WIDTH=4",
        "opt_expr", "opt_clean", "alumacc", "opt", "memory -nomap",
        "opt_clean",
    ]
    lines.append(f"synth_intel -family cycloneiv -top {top} -run map_bram:")
    lines.append(f"tee -o {stat_json} stat -json")
    return "\n".join(lines) + "\n"


def measure_case(
    rtl: Path, top: str, out_dir: Path, *, pairs=5, plugin=True, builtin=False,
    timeout_s=1800
):
    """交错测量一个用例的两侧。

    plugin=True：插件拆分流程（baseline 无插件 / optimized 加载 pmux_opt.so）。
    builtin=True：内置流程（两侧内置二进制运行逐字节相同的外部脚本；
    优化版由 synth_intel 内部调用 pmux_opt）。每次运行使用独立工作目录，
    脚本内输出使用相对名（mapped.il / stat.json），两侧脚本逐字节相同。
    """
    out_dir.mkdir(parents=True, exist_ok=False)
    ys_dir = out_dir / "ys"
    ys_dir.mkdir(exist_ok=True)
    runs = []
    builtin_bins = {}
    if builtin:
        builtin_bins = B.select_binaries(C.CONTEXT.get("builtin") or {})

    def one(side, optimized, seq, order):
        if builtin:
            run_dir = out_dir / "{}_{:02d}".format(side, seq)
            run_dir.mkdir(exist_ok=False)
            ys_text = C.gen_builtin_synth_ys(rtl, top)
            (run_dir / "flow.ys").write_text(ys_text)
            stat_json = run_dir / "stat.json"
            log_path = run_dir / "run.log"
            cmd = [str(builtin_bins[side]), "-s", "flow.ys"]
            cwd = run_dir
        else:
            stat_json = out_dir / f"{side}_{seq:02d}.stat.json"
            ys_text = gen_measure_ys(rtl, top, optimized=optimized, stat_json=stat_json)
            ys_path = ys_dir / f"{side}_{seq:02d}.ys"
            ys_path.write_text(ys_text)
            cmd = [str(C.TOOL_YOSYS), "-s", str(ys_path)]
            if optimized:
                cmd = [str(C.TOOL_YOSYS), "-m", str(C.PLUGIN_SO), "-s", str(ys_path)]
            log_path = out_dir / f"{side}_{seq:02d}.log"
            cwd = C.REPO
        if os.name == 'nt' and builtin:
            from win_measure import run_cpu_measured, run_measured as run_exit_measured
            subruns = {}
            for purpose, execute in (('cpu', run_cpu_measured), ('memory', run_exit_measured)):
                subdir = run_dir / purpose
                subdir.mkdir()
                (subdir / 'flow.ys').write_text(ys_text)
                value = execute(cmd, cwd=subdir, log_path=subdir / 'run.log', timeout_s=timeout_s)
                value['stat_exists'] = (subdir / 'stat.json').is_file()
                value['evidence_dir'] = str(subdir)
                (subdir / 'metrics.json').write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
                subruns[purpose] = value
            res = merge_cpu_memory_runs(subruns['cpu'], subruns['memory'])
            try:
                cpu_stat = C.parse_stat_json(run_dir / 'cpu/stat.json')
                memory_stat = C.parse_stat_json(run_dir / 'memory/stat.json')
                res['subruns_stat_match'] = cpu_stat['cell_types'] == memory_stat['cell_types']
            except (OSError, ValueError, KeyError):
                res['subruns_stat_match'] = False
            res['stat_exists'] = all(v['stat_exists'] for v in subruns.values())
            res['cpu_stat_sha256'] = C.sha256_file(run_dir / 'cpu/stat.json') if subruns['cpu']['stat_exists'] else None
            res['memory_stat_sha256'] = C.sha256_file(run_dir / 'memory/stat.json') if subruns['memory']['stat_exists'] else None
        else:
            res = run_measured(cmd, cwd=cwd, log_path=log_path, timeout_s=timeout_s)
            res['stat_exists'] = stat_json.exists()
        res["side"] = side
        res["seq"] = seq
        res["order"] = order
        if builtin:
            res["run_dir"] = str(run_dir)
        runs.append(res)
        return res

    for i in range(pairs):
        if i % 2 == 0:
            order_sides = ("baseline", "optimized")
            order_tag = "B→O"
        else:
            order_sides = ("optimized", "baseline")
            order_tag = "O→B"
        for side in order_sides:
            r = one(side, side == "optimized", i + 1, order_tag)
            print(format_run_progress(rtl.stem, i + 1, order_tag, side, r))

    # 汇总（中位数与全部原值）
    def collect(side, key):
        return collect_metric_values(runs, side, key)

    memory_metric = next((r.get("memory_metric") for r in runs if r.get("memory_metric")),
                         "yosys_main_rss_peak_kb")
    summary = {"case": top, "pairs": pairs, "runs": runs,
               "memory_metric": memory_metric,
               "performance_scheme": (EXIT_PEAK_SCHEME
                                       if memory_metric == "yosys_peak_working_set_bytes"
                                       else "pmux-perf-15p-mainrss-v2")}
    summary['invalid_samples'] = [dict(index=i + 1, side=r.get('side'), reasons=sample_errors(r))
                                  for i, r in enumerate(runs) if sample_errors(r)]
    summary['samples_valid'] = not summary['invalid_samples']
    for side in ("baseline", "optimized"):
        for key, name in (
            ("cpu_total_s", "cpu_total"),
            ("cpu_user_s", "cpu_user"),
            ("cpu_system_s", "cpu_system"),
            ("tree_rss_peak_kb", "tree_rss_peak"),
            ("yosys_main_rss_peak_kb", "yosys_main_rss_peak"),
            ("yosys_peak_working_set_bytes", "yosys_peak_working_set_bytes"),
            ("gn_time_maxrss_kb", "gn_maxrss"),
            ("gn_time_user_s", "gn_cpu_user"),
            ("gn_time_system_s", "gn_cpu_system"),
            ("wall_s", "wall"),
        ):
            vals = collect(side, key)
            if vals:
                summary[f"{side}_{name}_median"] = statistics.median(vals)
                summary[f"{side}_{name}_min"] = min(vals)
                summary[f"{side}_{name}_max"] = max(vals)
                summary[f"{side}_{name}_all"] = vals
    return summary


# ---------------------------------------------------------------- 自检
def selftest(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=False)
    if os.name == "nt":
        return windows_selftest(out_dir)
    results = {}

    # 1) CPU 受控工作：忙循环约 1s
    r = run_measured(
        ["python3", "-c", "s=0\nfor i in range(6*10**7):\n s+=i\nprint(s)"],
        cwd="/tmp", log_path=out_dir / "cpu.log", timeout_s=60,
    )
    results["cpu_work"] = {
        "cpu_total_s": r["cpu_total_s"], "wall_s": r["wall_s"], "rc": r["rc"],
    }

    # 2) 子进程内存分配 300MB
    r = run_measured(
        [
            "python3", "-c",
            "import time\na=bytearray(300*1024*1024)\na[0]=1\ntime.sleep(0.8)",
        ],
        cwd="/tmp", log_path=out_dir / "mem.log", timeout_s=60,
    )
    results["mem_child"] = {
        "tree_rss_peak_kb": r["tree_rss_peak_kb"],
        "gn_time_maxrss_kb": r["gn_time_maxrss_kb"],
        "rss_samples": r["rss_samples"],
        "rc": r["rc"],
    }

    # 3) 孙进程 CPU（bash 里起 python）
    r = run_measured(
        ["bash", "-c", "python3 -c 's=0\nfor i in range(6*10**7):\n s+=i'"],
        cwd="/tmp", log_path=out_dir / "grandchild.log", timeout_s=60,
    )
    results["grandchild_cpu"] = {
        "cpu_total_s": r["cpu_total_s"], "wall_s": r["wall_s"], "rc": r["rc"],
    }

    # 4) 短命进程
    r = run_measured(["true"], cwd="/tmp", log_path=out_dir / "short.log", timeout_s=10)
    results["short_lived"] = {"rc": r["rc"], "rss_samples": r["rss_samples"]}

    # 5) 非零退出
    r = run_measured(
        ["bash", "-c", "exit 3"], cwd="/tmp", log_path=out_dir / "nonzero.log",
        timeout_s=10,
    )
    results["nonzero_exit"] = {"rc": r["rc"]}

    # p5: target process must exclude its allocating child.
    child_code = "import time; a=bytearray(96*1024*1024); time.sleep(0.4)"
    parent_code = "import subprocess,sys,time; subprocess.run([sys.executable,'-c'," + repr(child_code) + "]); time.sleep(0.05)"
    mr = run_measured([sys.executable, "-c", parent_code], cwd="/tmp",
                      log_path=out_dir / "main_only.log", timeout_s=60)
    results["main_only"] = mr

    # 6) 超时
    r = run_measured(
        ["sleep", "10"], cwd="/tmp", log_path=out_dir / "timeout.log",
        timeout_s=0.8,
    )
    results["timeout"] = {"rc": r["rc"], "timed_out": r["timed_out"]}

    # 判定
    ok = True
    checks = []
    cw = results["cpu_work"]
    checks.append(("cpu_work captured (>=0.5s)", cw["cpu_total_s"] >= 0.5))
    mc = results["mem_child"]
    checks.append(("mem_child captured", mc["tree_rss_peak_kb"] >= 250 * 1024))
    mo = results["main_only"]
    checks.append(("main RSS excludes child", mo["rc"] == 0 and
                   0 < (mo.get("yosys_main_rss_peak_kb") or 0) < 64*1024 and
                   mo["tree_rss_peak_kb"] > 96*1024))
    gc = results["grandchild_cpu"]
    checks.append(("grandchild cpu counted", gc["cpu_total_s"] >= 0.5))
    checks.append(("short_lived ok", results["short_lived"]["rc"] == 0))
    checks.append(("nonzero rc", results["nonzero_exit"]["rc"] == 3))
    checks.append(("timeout classified", results["timeout"]["timed_out"] is True))
    for name, passed in checks:
        if not passed:
            ok = False
        results.setdefault("checks", []).append({"name": name, "pass": passed})
    results["selftest_ok"] = ok

    (out_dir / "selftest_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n"
    )
    for name, passed in checks:
        print(f"selftest {name}: {'PASS' if passed else 'FAIL'}")
    print(f"selftest_ok={ok}")
    return 0 if ok else 1


def windows_selftest(out_dir: Path):
    """Windows-only checks for Job Object CPU, main-process peak memory and timeout."""
    results = {}
    native_python = getattr(sys, "_base_executable", sys.executable)
    child_cpu = "import time; end=time.perf_counter()+0.65; x=0\nwhile time.perf_counter()<end: x+=1"
    parent_cpu = "import subprocess; subprocess.run(" + repr([native_python, "-c", child_cpu]) + ",check=True)"
    from win_measure import run_cpu_measured
    cpu = run_cpu_measured([native_python, "-c", parent_cpu], cwd=out_dir,
                           log_path=out_dir / "child_cpu.log", timeout_s=30)
    results["child_cpu"] = cpu

    child_mem = ("import time; value=bytearray(96*1024*1024); "
                 "[value.__setitem__(i,1) for i in range(0,len(value),4096)]; time.sleep(0.5)")
    parent_mem = ("import subprocess; value=bytearray(12*1024*1024); "
                  "[value.__setitem__(i,1) for i in range(0,len(value),4096)]; "
                  "subprocess.run(" + repr([native_python, "-c", child_mem]) + ",check=True)")
    memory = run_measured([native_python, "-c", parent_mem], cwd=out_dir,
                          log_path=out_dir / "child_memory.log", timeout_s=30)
    results["child_memory"] = memory

    short = run_measured([native_python, "-c", "pass"], cwd=out_dir,
                         log_path=out_dir / "short_lived.log", timeout_s=10)
    results["short_lived"] = short
    nonzero = run_measured([native_python, "-c", "raise SystemExit(3)"], cwd=out_dir,
                           log_path=out_dir / "nonzero.log", timeout_s=10)
    results["nonzero_exit"] = nonzero
    timeout = run_measured([native_python, "-c", "import time; time.sleep(10)"], cwd=out_dir,
                           log_path=out_dir / "timeout.log", timeout_s=0.6)
    results["timeout"] = timeout

    checks = [
        ("child CPU included", cpu["rc"] == 0 and cpu["cpu_total_s"] >= 0.5),
        ("main process peak excludes child memory",
         memory["rc"] == 0 and memory["yosys_peak_working_set_bytes"] is not None
         and 12 * 1024 * 1024 < memory["yosys_peak_working_set_bytes"] < 70 * 1024 * 1024
         and memory["memory_capture_complete"]),
        ("short process peak retained",
         short["rc"] == 0 and short["metrics_valid"]
         and short["memory_capture_complete"]
         and short["yosys_peak_working_set_bytes"] is not None
         and short["yosys_peak_working_set_bytes"] > 0),
        ("nonzero exit retained", nonzero["rc"] == 3 and nonzero["metrics_valid"]),
        ("timeout classified", timeout["timed_out"] is True and timeout["rc"] == 124),
    ]
    for name, passed in checks:
        results.setdefault("checks", []).append({"name": name, "pass": passed})
    results["selftest_ok"] = all(passed for _, passed in checks)
    results["method"] = {
        "cpu": "Windows Job Object total user plus kernel time, including descendants",
        "memory": "root PeakWorkingSetSize at EXIT_PROCESS_DEBUG_EVENT before ContinueDebugEvent; ABC excluded",
        "memory_sampling_limit": "no periodic sampling gap; failed or missing final event invalidates the sample",
        "cpu_is_separate_uninstrumented_run": True,
    }
    (out_dir / "selftest_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name, passed in checks:
        print("selftest {}: {}".format(name, "PASS" if passed else "FAIL"))
    print("selftest_ok={}".format(results["selftest_ok"]))
    return 0 if results["selftest_ok"] else 1


# ---------------------------------------------------------------- 主入口
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--cases", nargs="*", default=["test1", "test2", "test3", "test4"])
    ap.add_argument("--pairs", type=int, default=None)
    ap.add_argument("--out", type=str, default=None)
    args = ap.parse_args()

    base = (
        C.ROUND_DIR / "09_时间内存开销_performance" / "round01"
        if args.out is None
        else Path(args.out)
    )

    if args.selftest:
        from runtime_patch import SCHEME as SINGLE_CPU_SCHEME
        if C.CONTEXT.get('performance_scheme') == SINGLE_CPU_SCHEME:
            from selfcheck_v6 import run
            return run(C.CONTEXT, C.ROUND_DIR / '09_时间内存开销_performance' / 'selftest')
        return selftest(C.ROUND_DIR / "09_时间内存开销_performance" / "selftest")

    from runtime_patch import SCHEME as SINGLE_CPU_SCHEME
    if C.CONTEXT.get('performance_scheme') == SINGLE_CPU_SCHEME:
        import measure_v6
        if os.name != 'nt' or C.CONTEXT.get('mode') != 'builtin': raise ValueError('v6 requires Windows builtin')
        if args.pairs is not None or args.out is not None or args.cases != ['test1','test2','test3','test4']:
            raise ValueError('v6 fixed four-case single-run policy cannot be overridden')
        binaries=B.select_binaries(C.CONTEXT['builtin'])
        flows={}
        for case in args.cases:
            rtl=C.stage_to_ascii_bridge(C.TREE/f'pmux_case/competition_case/{case}/{case}.v',f'builtin_inputs/{case}.v')
            flows[case]=C.gen_builtin_synth_ys(rtl,case)
        return measure_v6.run(C.CONTEXT,C.ROUND_DIR,binaries,flows)

    from cpu_statistics import SCHEME as MEAN_CPU_SCHEME
    from cpu_statistics_v5 import SCHEME as ETW_CPU_SCHEME
    if C.CONTEXT.get('performance_scheme') not in (None,'','pmux-perf-15p-mainrss-v2','pmux-perf-5p-mainrss-v1',
                                                  'pmux-perf-15p-windows-separate-cpu-exitpeak-v3',MEAN_CPU_SCHEME,ETW_CPU_SCHEME):
        raise ValueError('unknown performance scheme; cannot infer execution policy')
    if C.CONTEXT.get('performance_scheme') in (MEAN_CPU_SCHEME,ETW_CPU_SCHEME):
        if os.name!='nt' or C.CONTEXT.get('mode')!='builtin':
            raise ValueError('v4 mean policy requires Windows builtin mode')
        if args.pairs is not None or args.out is not None or args.cases!=['test1','test2','test3','test4']:
            raise ValueError('v4 fixed four-case policy cannot be overridden by legacy --pairs/--out/--cases')
        import measure_v4
        import measure_v5
        binaries=B.select_binaries(C.CONTEXT['builtin'])
        flows={}
        for case in args.cases:
            rtl=C.stage_to_ascii_bridge(C.TREE/f'pmux_case/competition_case/{case}/{case}.v',f'builtin_inputs/{case}.v')
            flows[case]=C.gen_builtin_synth_ys(rtl,case)
        return (measure_v5 if C.CONTEXT.get('performance_scheme')==ETW_CPU_SCHEME else measure_v4).run(C.CONTEXT,C.ROUND_DIR,binaries,flows)

    builtin = (C.CONTEXT.get("mode") == "builtin")
    summaries = []
    for case in args.cases:
        rtl_source = C.TREE / "pmux_case" / "competition_case" / case / f"{case}.v"
        rtl = (C.stage_to_ascii_bridge(rtl_source, "builtin_inputs/{}.v".format(case))
               if builtin else rtl_source)
        print(f"=== {case} ===")
        summ = measure_case(rtl, case, base / case, pairs=args.pairs or 5,
                            plugin=not builtin, builtin=builtin)
        summaries.append(summ)

    # 汇总 CSV
    import csv

    windows_memory = bool(summaries and summaries[0].get("memory_metric") ==
                          "yosys_peak_working_set_bytes")
    with open(base / "performance_summary.csv", "w", newline="") as f:
        w = csv.writer(f)
        if windows_memory:
            w.writerow(["case", "cpu_base_median_s", "cpu_opt_median_s", "cpu_overhead_pct",
                        "yosys_peak_working_set_base_bytes", "yosys_peak_working_set_opt_bytes",
                        "yosys_peak_working_set_base_mib", "yosys_peak_working_set_opt_mib",
                        "memory_overhead_pct", "wall_base_median_s", "wall_opt_median_s",
                        "memory_metric"])
        else:
            w.writerow(["case", "cpu_base_median_s", "cpu_opt_median_s", "cpu_overhead_pct",
                        "rss_base_median_kb", "rss_opt_median_kb", "rss_overhead_pct",
                        "wall_base_median_s", "wall_opt_median_s",
                        "gn_rss_base_median_kb", "gn_rss_opt_median_kb"])
        for s in summaries:
            b = s.get("baseline_cpu_total_median")
            o = s.get("optimized_cpu_total_median")
            if windows_memory:
                mb = s.get("baseline_yosys_peak_working_set_bytes_median")
                mo = s.get("optimized_yosys_peak_working_set_bytes_median")
                w.writerow([s["case"], b, o,
                            round((o - b) / b * 100, 4) if b else "",
                            mb, mo,
                            round(mb / (1024 * 1024), 4) if mb else "",
                            round(mo / (1024 * 1024), 4) if mo else "",
                            round((mo - mb) / mb * 100, 4) if mb else "",
                            s.get("baseline_wall_median"), s.get("optimized_wall_median"),
                            s.get("memory_metric")])
                continue
            rb = s.get("baseline_yosys_main_rss_peak_median")
            ro = s.get("optimized_yosys_main_rss_peak_median")
            w.writerow(
                [
                    s["case"], b, o,
                    round((o - b) / b * 100, 4) if b else "",
                    rb, ro,
                    round((ro - rb) / rb * 100, 4) if rb else "",
                    s.get("baseline_wall_median"), s.get("optimized_wall_median"),
                    s.get("baseline_gn_maxrss_median"),
                    s.get("optimized_gn_maxrss_median"),
                ]
            )
    (base / "performance_summary.json").write_text(
        json.dumps(summaries, ensure_ascii=False, indent=2) + "\n"
    )
    print(f"\n结果目录: {C.rel(base)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
