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

PAGE_SIZE = os.sysconf("SC_PAGE_SIZE")
CLK_TCK = os.sysconf("SC_CLK_TCK")


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

    def __init__(self, root_pid: int, interval_s: float = 0.005):
        super().__init__(daemon=True)
        self.root_pid = root_pid
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
        mon = TreeRssMonitor(p.pid, sample_interval)
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
    rtl: Path, top: str, out_dir: Path, *, pairs=5, plugin=True, timeout_s=1800
):
    """交错测量一个用例的两侧。"""
    out_dir.mkdir(parents=True, exist_ok=False)
    ys_dir = out_dir / "ys"
    ys_dir.mkdir(exist_ok=True)
    runs = []

    def one(side, optimized, seq):
        stat_json = out_dir / f"{side}_{seq:02d}.stat.json"
        ys_text = gen_measure_ys(rtl, top, optimized=optimized, stat_json=stat_json)
        ys_path = ys_dir / f"{side}_{seq:02d}.ys"
        ys_path.write_text(ys_text)
        cmd = [str(C.TOOL_YOSYS), "-s", str(ys_path)]
        if optimized:
            cmd = [str(C.TOOL_YOSYS), "-m", str(C.PLUGIN_SO), "-s", str(ys_path)]
        res = run_measured(
            cmd,
            cwd=C.REPO,
            log_path=out_dir / f"{side}_{seq:02d}.log",
            timeout_s=timeout_s,
        )
        res["side"] = side
        res["seq"] = seq
        res["stat_exists"] = stat_json.exists()
        runs.append(res)
        return res

    for i in range(pairs):
        if i % 2 == 0:
            order = ("baseline", "optimized")
        else:
            order = ("optimized", "baseline")
        for side in order:
            r = one(side, side == "optimized", i + 1)
            print(
                f"  [{rtl.stem}] pair{i+1} {side}: rc={r['rc']} "
                f"cpu={r['cpu_total_s']}s wall={r['wall_s']}s "
                f"rss_tree={r['tree_rss_peak_kb']}kB "
                f"gn_rss={r['gn_time_maxrss_kb']}kB"
            )

    # 汇总（中位数与全部原值）
    def collect(side, key):
        vals = [r[key] for r in runs if r["side"] == side and r["rc"] == 0 and not r["timed_out"] and r[key] is not None]
        return vals

    summary = {"case": top, "pairs": pairs, "runs": runs}
    for side in ("baseline", "optimized"):
        for key, name in (
            ("cpu_total_s", "cpu_total"),
            ("cpu_user_s", "cpu_user"),
            ("cpu_system_s", "cpu_system"),
            ("tree_rss_peak_kb", "tree_rss_peak"),
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


# ---------------------------------------------------------------- 主入口
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--cases", nargs="*", default=["test1", "test2", "test3", "test4"])
    ap.add_argument("--pairs", type=int, default=5)
    ap.add_argument("--out", type=str, default=None)
    args = ap.parse_args()

    base = (
        C.ROUND_DIR / "09_时间内存开销_performance" / "round01"
        if args.out is None
        else Path(args.out)
    )

    if args.selftest:
        return selftest(C.ROUND_DIR / "09_时间内存开销_performance" / "selftest")

    summaries = []
    for case in args.cases:
        rtl = C.TREE / "pmux_case" / "competition_case" / case / f"{case}.v"
        print(f"=== {case} ===")
        summ = measure_case(rtl, case, base / case, pairs=args.pairs)
        summaries.append(summ)

    # 汇总 CSV
    import csv

    with open(base / "performance_summary.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "case",
                "cpu_base_median_s", "cpu_opt_median_s", "cpu_overhead_pct",
                "rss_base_median_kb", "rss_opt_median_kb", "rss_overhead_pct",
                "wall_base_median_s", "wall_opt_median_s",
                "gn_rss_base_median_kb", "gn_rss_opt_median_kb",
            ]
        )
        for s in summaries:
            b = s.get("baseline_cpu_total_median")
            o = s.get("optimized_cpu_total_median")
            rb = s.get("baseline_tree_rss_peak_median")
            ro = s.get("optimized_tree_rss_peak_median")
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
