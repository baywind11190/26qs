#!/usr/bin/env python3

import argparse
import csv
import hashlib
import json
import re
import shutil
import statistics
import subprocess
import sys
from datetime import datetime
from pathlib import Path


BENCHMARK_SCRIPT = Path(__file__).resolve()
ROOT = BENCHMARK_SCRIPT.parents[1]
DEFAULT_EQY = Path("/home/fpga/eda/eqy/install/bin/eqy")
DEFAULT_TIME = Path("/usr/bin/time")
EVAL_SCRIPT = ROOT / "scripts" / "official_eval" / "run_case.tcl"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_capture(cmd, *, cwd=None, env=None):
    p = subprocess.run(
        [str(x) for x in cmd],
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return p.returncode, p.stdout


def yosys_version(path: Path) -> str:
    rc, out = run_capture([path, "-V"])
    if rc != 0:
        raise RuntimeError(
            f"Cannot execute Yosys: {path}\n{out}"
        )
    return out.strip()


def git_head() -> str:
    rc, out = run_capture(
        ["git", "-C", ROOT, "rev-parse", "HEAD"]
    )
    if rc != 0:
        return "UNKNOWN"
    return out.strip()


def git_dirty() -> bool:
    rc, out = run_capture(
        ["git", "-C", ROOT, "status", "--porcelain"]
    )
    if rc != 0:
        raise RuntimeError("Cannot determine Git worktree status")
    return bool(out.strip())


def tool_version(path: Path, *args: str) -> str:
    rc, out = run_capture([path, *args])
    if rc != 0:
        raise RuntimeError(
            f"Cannot query tool version: {path}\n{out}"
        )
    return out.strip()


def parse_elapsed(text: str) -> float:
    m = re.search(
        r"Elapsed \(wall clock\) time \(h:mm:ss or m:ss\):\s*(\S+)",
        text,
    )
    if not m:
        raise RuntimeError("Cannot find elapsed wall-clock time")

    parts = m.group(1).split(":")

    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])

    if len(parts) == 3:
        return (
            int(parts[0]) * 3600
            + int(parts[1]) * 60
            + float(parts[2])
        )

    raise RuntimeError(f"Unknown elapsed format: {m.group(1)}")


def parse_rss(text: str) -> int:
    m = re.search(
        r"Maximum resident set size \(kbytes\):\s*(\d+)",
        text,
    )
    if not m:
        raise RuntimeError("Cannot find maximum RSS")
    return int(m.group(1))


def parse_stat(path: Path):
    data = json.loads(path.read_text())
    design = data["design"]
    types = design.get("num_cells_by_type", {})

    total = int(design["num_cells"])
    comb = int(types.get("cycloneiv_lcell_comb", 0))
    dff = int(types.get("dffeas", 0))

    return {
        "total_cells": total,
        "comb": comb,
        "dffeas": dff,
        "cell_types": {
            key: int(value)
            for key, value in sorted(types.items())
        },
    }


def reduction_pct(baseline, optimized):
    if baseline == 0:
        return None
    return (baseline - optimized) / baseline * 100.0


def overhead_pct(baseline, optimized):
    if baseline == 0:
        return None
    return (optimized - baseline) / baseline * 100.0


def fmt_pct(value):
    if value is None:
        return "N/A"
    return f"{value:+.2f}%"


def case_rtl(case: str) -> Path:
    return (
        ROOT
        / "pmux_case"
        / "competition_case"
        / case
        / f"{case}.v"
    )


def write_eqy_config(case: str, optimized_il: Path, path: Path):
    rtl = case_rtl(case)

    lines = [
        "[gold]",
        f"read_verilog -sv {rtl}",
        f"prep -top {case}",
    ]

    if case == "test4":
        lines.append("memory_map")

    lines += [
        "",
        "[gate]",
        f"read_rtlil {optimized_il}",
        f"prep -top {case}",
    ]

    if case == "test4":
        lines.append("memory_map")

    lines += [
        "",
        "[strategy simple]",
        "use sat",
        "depth 5",
        "",
    ]

    path.write_text("\n".join(lines))


def run_eqy(eqy: Path, case: str, case_dir: Path):
    eqy_dir = case_dir / "eqy"
    eqy_dir.mkdir(parents=True, exist_ok=True)

    config = eqy_dir / "verify.eqy"
    log = eqy_dir / "verify.log"

    optimized_il = case_dir / "optimized" / "generic.il"

    write_eqy_config(case, optimized_il, config)

    rc, out = run_capture(
        [eqy, "-f", "verify.eqy"],
        cwd=eqy_dir,
    )
    log.write_text(out)

    passed = (
        rc == 0
        and "Successfully proved designs equivalent" in out
        and "DONE (PASS, rc=0)" in out
    )

    return {
        "rc": rc,
        "status": "PASS" if passed else "FAIL",
        "log": str(log.relative_to(ROOT)),
    }


def run_negative_eqy(eqy: Path, run_dir: Path):
    check_dir = run_dir / "negative_check"
    check_dir.mkdir(parents=True, exist_ok=True)

    config = check_dir / "negative.eqy"
    log = check_dir / "negative.log"

    gold = ROOT / "formal" / "negative" / "gold.v"
    gate = ROOT / "formal" / "negative" / "gate.v"

    config.write_text(
        "\n".join(
            [
                "[gold]",
                f"read_verilog -sv {gold}",
                "prep -top negative_test",
                "",
                "[gate]",
                f"read_verilog -sv {gate}",
                "prep -top negative_test",
                "",
                "[strategy simple]",
                "use sat",
                "depth 5",
                "",
            ]
        )
    )

    rc, out = run_capture(
        [eqy, "-f", "negative.eqy"],
        cwd=check_dir,
    )
    log.write_text(out)

    expected_fail = (
        rc != 0
        and "Failed to prove equivalence" in out
        and "DONE (FAIL, rc=2)" in out
    )

    return {
        "rc": rc,
        "status": "EXPECTED_FAIL" if expected_fail else "BROKEN",
        "log": str(log.relative_to(ROOT)),
    }


def run_yosys_once(
    yosys: Path,
    time_bin: Path,
    case: str,
    mode: str,
    case_dir: Path,
    repeat_index: int,
):
    out_dir = case_dir / mode
    perf_dir = out_dir / "perf"

    out_dir.mkdir(parents=True, exist_ok=True)
    perf_dir.mkdir(parents=True, exist_ok=True)

    generic = out_dir / "generic.il"
    mapped = out_dir / "mapped.il"
    stat_json = out_dir / "mapped_stat.json"

    time_file = perf_dir / f"run{repeat_index}.time"
    log_file = perf_dir / f"run{repeat_index}.log"

    env = dict(**__import__("os").environ)

    env.update(
        {
            "RTL_FILE": str(case_rtl(case)),
            "TOP": case,
            "GENERIC_NETLIST": str(generic),
            "MAPPED_NETLIST": str(mapped),
            "STAT_JSON": str(stat_json),
        }
    )

    cmd = [
        time_bin,
        "-v",
        "-o",
        time_file,
        yosys,
        "-Q",
        "-c",
        EVAL_SCRIPT,
    ]

    with log_file.open("w") as log:
        p = subprocess.run(
            [str(x) for x in cmd],
            cwd=ROOT,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
        )

    if p.returncode != 0:
        raise RuntimeError(
            f"{case} {mode} run{repeat_index} failed: "
            f"rc={p.returncode}, log={log_file}"
        )

    for required in (generic, mapped, stat_json, time_file):
        if not required.exists():
            raise RuntimeError(
                f"Missing expected output: {required}"
            )

    perf_text = time_file.read_text(errors="replace")

    return {
        "time_s": parse_elapsed(perf_text),
        "rss_kb": parse_rss(perf_text),
    }


def run_case(
    case: str,
    run_dir: Path,
    baseline_yosys: Path,
    optimized_yosys: Path,
    eqy: Path,
    time_bin: Path,
    repeat: int,
):
    print(f"\n===== {case} =====")

    case_dir = run_dir / case
    case_dir.mkdir(parents=True, exist_ok=True)

    perf = {
        "baseline": [],
        "optimized": [],
    }

    # Interleave baseline and optimized runs to reduce temporal drift.
    for r in range(1, repeat + 1):
        for mode, yosys in (
            ("baseline", baseline_yosys),
            ("optimized", optimized_yosys),
        ):
            result = run_yosys_once(
                yosys,
                time_bin,
                case,
                mode,
                case_dir,
                r,
            )
            perf[mode].append(result)

            print(
                f"{case} {mode} run{r}: "
                f"time={result['time_s']:.4f}s, "
                f"rss={result['rss_kb']}kB"
            )

    baseline_stat = parse_stat(
        case_dir / "baseline" / "mapped_stat.json"
    )
    optimized_stat = parse_stat(
        case_dir / "optimized" / "mapped_stat.json"
    )

    eqy_result = run_eqy(eqy, case, case_dir)

    b_times = [x["time_s"] for x in perf["baseline"]]
    o_times = [x["time_s"] for x in perf["optimized"]]

    b_rss = [x["rss_kb"] for x in perf["baseline"]]
    o_rss = [x["rss_kb"] for x in perf["optimized"]]

    b_time_median = statistics.median(b_times)
    o_time_median = statistics.median(o_times)

    b_rss_max = max(b_rss)
    o_rss_max = max(o_rss)

    result = {
        "case": case,
        "eqy_status": eqy_result["status"],
        "eqy_rc": eqy_result["rc"],

        "baseline_total_cells": baseline_stat["total_cells"],
        "optimized_total_cells": optimized_stat["total_cells"],
        "total_cell_reduction_pct": reduction_pct(
            baseline_stat["total_cells"],
            optimized_stat["total_cells"],
        ),

        "baseline_comb": baseline_stat["comb"],
        "optimized_comb": optimized_stat["comb"],
        "comb_reduction_pct": reduction_pct(
            baseline_stat["comb"],
            optimized_stat["comb"],
        ),

        "baseline_dffeas": baseline_stat["dffeas"],
        "optimized_dffeas": optimized_stat["dffeas"],
        "dffeas_reduction_pct": reduction_pct(
            baseline_stat["dffeas"],
            optimized_stat["dffeas"],
        ),

        "baseline_time_runs_s": b_times,
        "optimized_time_runs_s": o_times,
        "baseline_time_median_s": b_time_median,
        "optimized_time_median_s": o_time_median,
        "time_overhead_pct": overhead_pct(
            b_time_median,
            o_time_median,
        ),

        "baseline_rss_runs_kb": b_rss,
        "optimized_rss_runs_kb": o_rss,
        "baseline_rss_max_kb": b_rss_max,
        "optimized_rss_max_kb": o_rss_max,
        "rss_overhead_pct": overhead_pct(
            b_rss_max,
            o_rss_max,
        ),

        "baseline_cell_types": baseline_stat["cell_types"],
        "optimized_cell_types": optimized_stat["cell_types"],
    }

    print(
        f"{case}: EQY={result['eqy_status']}, "
        f"cells={result['baseline_total_cells']}"
        f"->{result['optimized_total_cells']} "
        f"({fmt_pct(result['total_cell_reduction_pct'])}), "
        f"time overhead={fmt_pct(result['time_overhead_pct'])}, "
        f"RSS overhead={fmt_pct(result['rss_overhead_pct'])}"
    )

    return result


def csv_row(result):
    return {
        "case": result["case"],
        "eqy_status": result["eqy_status"],

        "baseline_total_cells": result["baseline_total_cells"],
        "optimized_total_cells": result["optimized_total_cells"],
        "total_cell_reduction_pct":
            "" if result["total_cell_reduction_pct"] is None
            else f"{result['total_cell_reduction_pct']:.6f}",

        "baseline_cycloneiv_lcell_comb": result["baseline_comb"],
        "optimized_cycloneiv_lcell_comb": result["optimized_comb"],
        "comb_reduction_pct":
            "" if result["comb_reduction_pct"] is None
            else f"{result['comb_reduction_pct']:.6f}",

        "baseline_dffeas": result["baseline_dffeas"],
        "optimized_dffeas": result["optimized_dffeas"],
        "dffeas_reduction_pct":
            "" if result["dffeas_reduction_pct"] is None
            else f"{result['dffeas_reduction_pct']:.6f}",

        "baseline_time_median_s":
            f"{result['baseline_time_median_s']:.6f}",
        "optimized_time_median_s":
            f"{result['optimized_time_median_s']:.6f}",
        "time_overhead_pct":
            f"{result['time_overhead_pct']:.6f}",

        "baseline_rss_max_kb": result["baseline_rss_max_kb"],
        "optimized_rss_max_kb": result["optimized_rss_max_kb"],
        "rss_overhead_pct":
            f"{result['rss_overhead_pct']:.6f}",
    }


def write_summary_csv(results, path: Path):
    rows = [csv_row(r) for r in results]

    with path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(rows)


def aggregate(results):
    b_total = sum(r["baseline_total_cells"] for r in results)
    o_total = sum(r["optimized_total_cells"] for r in results)

    b_comb = sum(r["baseline_comb"] for r in results)
    o_comb = sum(r["optimized_comb"] for r in results)

    b_dff = sum(r["baseline_dffeas"] for r in results)
    o_dff = sum(r["optimized_dffeas"] for r in results)

    defined_total = [
        r["total_cell_reduction_pct"]
        for r in results
        if r["total_cell_reduction_pct"] is not None
    ]

    return {
        "baseline_total_cells": b_total,
        "optimized_total_cells": o_total,
        "weighted_total_cell_reduction_pct":
            reduction_pct(b_total, o_total),

        "baseline_comb": b_comb,
        "optimized_comb": o_comb,
        "weighted_comb_reduction_pct":
            reduction_pct(b_comb, o_comb),

        "baseline_dffeas": b_dff,
        "optimized_dffeas": o_dff,
        "weighted_dffeas_reduction_pct":
            reduction_pct(b_dff, o_dff),

        "arithmetic_mean_case_total_reduction_pct":
            statistics.mean(defined_total)
            if defined_total else None,
    }


def write_summary_md(results, agg, negative, path: Path):
    lines = [
        "# PMUX Official Evaluation Summary",
        "",
        "| Case | EQY | Base cells | Opt cells | Cell reduction | Base comb | Opt comb | Comb reduction | Base DFF | Opt DFF | DFF reduction | Base time | Opt time | Time overhead | Base RSS | Opt RSS | RSS overhead |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for r in results:
        lines.append(
            "| "
            + " | ".join(
                [
                    r["case"],
                    r["eqy_status"],
                    str(r["baseline_total_cells"]),
                    str(r["optimized_total_cells"]),
                    fmt_pct(r["total_cell_reduction_pct"]),
                    str(r["baseline_comb"]),
                    str(r["optimized_comb"]),
                    fmt_pct(r["comb_reduction_pct"]),
                    str(r["baseline_dffeas"]),
                    str(r["optimized_dffeas"]),
                    fmt_pct(r["dffeas_reduction_pct"]),
                    f"{r['baseline_time_median_s']:.4f}s",
                    f"{r['optimized_time_median_s']:.4f}s",
                    fmt_pct(r["time_overhead_pct"]),
                    f"{r['baseline_rss_max_kb']}kB",
                    f"{r['optimized_rss_max_kb']}kB",
                    fmt_pct(r["rss_overhead_pct"]),
                ]
            )
            + " |"
        )

    lines += [
        "",
        "## Aggregate resource results",
        "",
        f"- Total cells: {agg['baseline_total_cells']} -> {agg['optimized_total_cells']} ({fmt_pct(agg['weighted_total_cell_reduction_pct'])})",
        f"- Cyclone IV combinational cells: {agg['baseline_comb']} -> {agg['optimized_comb']} ({fmt_pct(agg['weighted_comb_reduction_pct'])})",
        f"- DFFEAS: {agg['baseline_dffeas']} -> {agg['optimized_dffeas']} ({fmt_pct(agg['weighted_dffeas_reduction_pct'])})",
        f"- Arithmetic mean of per-case total-cell reduction: {fmt_pct(agg['arithmetic_mean_case_total_reduction_pct'])}",
        "",
        "## Negative EQY self-test",
        "",
        f"- Status: {negative['status']}",
        f"- Return code: {negative['rc']}",
        "",
        "> Resource reduction uses `(baseline - optimized) / baseline × 100%`.",
        "",
        "> Time/RSS overhead uses `(optimized - baseline) / baseline × 100%`.",
        "",
    ]

    path.write_text("\n".join(lines))


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--baseline-yosys",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "--optimized-yosys",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "--eqy",
        type=Path,
        default=DEFAULT_EQY,
    )
    parser.add_argument(
        "--time-bin",
        type=Path,
        default=DEFAULT_TIME,
    )
    parser.add_argument(
        "--case",
        choices=["all", "test1", "test2", "test3", "test4"],
        default="all",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=3,
    )
    parser.add_argument(
        "--run-id",
        default=None,
    )

    args = parser.parse_args()

    if args.repeat < 1:
        parser.error("--repeat must be >= 1")

    for path in (
        args.baseline_yosys,
        args.optimized_yosys,
        args.eqy,
        args.time_bin,
        EVAL_SCRIPT,
    ):
        if not path.exists():
            raise SystemExit(f"Missing required file: {path}")

    z3_exe = shutil.which("z3")
    if z3_exe is None:
        raise SystemExit("Cannot find z3 in PATH")
    z3_path = Path(z3_exe)

    cases = (
        ["test1", "test2", "test3", "test4"]
        if args.case == "all"
        else [args.case]
    )

    for case in cases:
        rtl = case_rtl(case)
        if not rtl.exists():
            raise SystemExit(f"Missing RTL: {rtl}")

    run_id = args.run_id or datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )

    run_dir = (
        ROOT
        / "results"
        # 2026-09-20 目录整理：输出统一到 results/02_公开评测_public_eval（原 results/official_eval）
        / "02_公开评测_public_eval"
        / run_id
    )

    if run_dir.exists():
        raise SystemExit(
            f"Run directory already exists: {run_dir}"
        )

    run_dir.mkdir(parents=True)

    base_version = yosys_version(args.baseline_yosys)
    opt_version = yosys_version(args.optimized_yosys)
    eqy_version = tool_version(args.eqy, "--version")
    z3_version = tool_version(z3_path, "--version")

    manifest = {
        "run_id": run_id,
        "project_commit": git_head(),
        "project_worktree_dirty": git_dirty(),

        "benchmark_script_path":
            str(BENCHMARK_SCRIPT.relative_to(ROOT)),
        "benchmark_script_sha256":
            sha256_file(BENCHMARK_SCRIPT),

        "baseline_yosys_path":
            str(args.baseline_yosys.resolve()),
        "baseline_yosys_sha256":
            sha256_file(args.baseline_yosys),
        "baseline_yosys_version":
            base_version,

        "optimized_yosys_path":
            str(args.optimized_yosys.resolve()),
        "optimized_yosys_sha256":
            sha256_file(args.optimized_yosys),
        "optimized_yosys_version":
            opt_version,

        "eval_script_path":
            str(EVAL_SCRIPT.relative_to(ROOT)),
        "eval_script_sha256":
            sha256_file(EVAL_SCRIPT),

        "mapping_family": "cycloneiv",
        "repeat": args.repeat,

        "eqy_path": str(args.eqy.resolve()),
        "eqy_version": eqy_version,

        "z3_path": str(z3_path.resolve()),
        "z3_version": z3_version,

        "time_path": str(args.time_bin.resolve()),

        "cases": {
            case: {
                "rtl_path":
                    str(case_rtl(case).relative_to(ROOT)),
                "rtl_sha256":
                    sha256_file(case_rtl(case)),
            }
            for case in cases
        },
    }

    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )

    print(f"Run ID: {run_id}")
    print(f"Output: {run_dir}")
    print(f"Baseline:  {base_version}")
    print(f"Optimized: {opt_version}")

    results = []

    try:
        for case in cases:
            results.append(
                run_case(
                    case,
                    run_dir,
                    args.baseline_yosys,
                    args.optimized_yosys,
                    args.eqy,
                    args.time_bin,
                    args.repeat,
                )
            )

        negative = run_negative_eqy(
            args.eqy,
            run_dir,
        )

        agg = aggregate(results)

        write_summary_csv(
            results,
            run_dir / "summary.csv",
        )

        summary_json = {
            "run_id": run_id,
            "results": results,
            "aggregate": agg,
            "negative_eqy": negative,
        }

        (run_dir / "summary.json").write_text(
            json.dumps(summary_json, indent=2) + "\n"
        )

        write_summary_md(
            results,
            agg,
            negative,
            run_dir / "summary.md",
        )

    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 2

    overall_ok = (
        all(r["eqy_status"] == "PASS" for r in results)
        and negative["status"] == "EXPECTED_FAIL"
    )

    print()
    print("===== FINAL =====")

    for r in results:
        print(
            f"{r['case']}: "
            f"EQY={r['eqy_status']}, "
            f"cells={r['baseline_total_cells']}"
            f"->{r['optimized_total_cells']}, "
            f"reduction={fmt_pct(r['total_cell_reduction_pct'])}, "
            f"time={fmt_pct(r['time_overhead_pct'])}, "
            f"rss={fmt_pct(r['rss_overhead_pct'])}"
        )

    print(
        "Negative EQY:",
        negative["status"],
    )

    print(
        "Overall:",
        "PASS" if overall_ok else "FAIL",
    )

    print(
        "Summary:",
        run_dir / "summary.md",
    )

    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
