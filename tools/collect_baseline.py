#!/usr/bin/env python3

import csv
import hashlib
import json
import re
import statistics
from pathlib import Path

ROOT = Path(".")
OUT = ROOT / "results" / "01_基础基线_baseline" / "baseline_summary.csv"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_elapsed(text):
    m = re.search(
        r"Elapsed \(wall clock\) time \(h:mm:ss or m:ss\):\s*(\S+)",
        text
    )
    if not m:
        raise RuntimeError("Cannot find elapsed time")

    value = m.group(1)
    parts = value.split(":")

    if len(parts) == 2:
        minutes = int(parts[0])
        seconds = float(parts[1])
        return minutes * 60 + seconds

    if len(parts) == 3:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds

    raise RuntimeError(f"Unknown elapsed format: {value}")


def parse_rss(text):
    m = re.search(
        r"Maximum resident set size \(kbytes\):\s*(\d+)",
        text
    )
    if not m:
        raise RuntimeError("Cannot find RSS")
    return int(m.group(1))


def parse_eqy_status(path):
    text = path.read_text(errors="replace")
    m = re.search(r"DONE \((PASS|FAIL), rc=(\d+)\)", text)
    if not m:
        return "UNKNOWN"
    return m.group(1)


rows = []

for i in range(1, 5):
    case = f"test{i}"

    rtl = ROOT / "pmux_case" / "competition_case" / case / f"{case}.v"
    stat_json = ROOT / "results" / "01_基础基线_baseline" / f"{case}_cycloneiv.json"
    eqy_log = ROOT / "results" / "01_基础基线_baseline" / "02_基础等价检查_equivalence" / f"{case}.log"

    with open(stat_json, "r") as f:
        stat = json.load(f)

    design = stat["design"]
    cell_types = design.get("num_cells_by_type", {})

    total_cells = int(design["num_cells"])
    comb_cells = int(cell_types.get("cycloneiv_lcell_comb", 0))
    dffeas_cells = int(cell_types.get("dffeas", 0))
    other_cells = total_cells - comb_cells - dffeas_cells

    times = []
    rss_values = []

    for r in range(1, 4):
        perf_file = (
            ROOT / "results" / "01_基础基线_baseline" / "perf" /
            f"{case}_run{r}.time"
        )

        text = perf_file.read_text(errors="replace")
        times.append(parse_elapsed(text))
        rss_values.append(parse_rss(text))

    rows.append({
        "case_id": case,
        "top": case,
        "input_sha256": sha256_file(rtl),
        "eqy_status": parse_eqy_status(eqy_log),
        "baseline_total_cells": total_cells,
        "cycloneiv_lcell_comb": comb_cells,
        "dffeas": dffeas_cells,
        "other_cells": other_cells,
        "time_run1_s": f"{times[0]:.4f}",
        "time_run2_s": f"{times[1]:.4f}",
        "time_run3_s": f"{times[2]:.4f}",
        "time_median_s": f"{statistics.median(times):.4f}",
        "rss_run1_kb": rss_values[0],
        "rss_run2_kb": rss_values[1],
        "rss_run3_kb": rss_values[2],
        "rss_max_kb": max(rss_values),
    })


OUT.parent.mkdir(parents=True, exist_ok=True)

with open(OUT, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote: {OUT}")
print()

for row in rows:
    print(
        f"{row['case_id']}: "
        f"EQY={row['eqy_status']}, "
        f"cells={row['baseline_total_cells']}, "
        f"time_median={row['time_median_s']} s, "
        f"rss_max={row['rss_max_kb']} kB"
    )
