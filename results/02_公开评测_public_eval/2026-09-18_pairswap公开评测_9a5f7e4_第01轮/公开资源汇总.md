# PMUX Official Evaluation Summary

| Case | EQY | Base cells | Opt cells | Cell reduction | Base comb | Opt comb | Comb reduction | Base DFF | Opt DFF | DFF reduction | Base time | Opt time | Time overhead | Base RSS | Opt RSS | RSS overhead |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| test1 | PASS | 510 | 431 | +15.49% | 286 | 207 | +27.62% | 222 | 222 | +0.00% | 0.2500s | 0.2200s | -12.00% | 36484kB | 35320kB | -3.19% |
| test2 | PASS | 25 | 25 | +0.00% | 25 | 25 | +0.00% | 0 | 0 | N/A | 0.0900s | 0.0900s | +0.00% | 31444kB | 31604kB | +0.51% |
| test3 | PASS | 30 | 30 | +0.00% | 12 | 12 | +0.00% | 17 | 17 | +0.00% | 0.1300s | 0.1100s | -15.38% | 31872kB | 31880kB | +0.03% |
| test4 | PASS | 46 | 46 | +0.00% | 35 | 35 | +0.00% | 10 | 10 | +0.00% | 0.1200s | 0.1200s | +0.00% | 32520kB | 32072kB | -1.38% |

## Aggregate resource results

- Total cells: 611 -> 532 (+12.93%)
- Cyclone IV combinational cells: 358 -> 279 (+22.07%)
- DFFEAS: 249 -> 249 (+0.00%)
- Arithmetic mean of per-case total-cell reduction: +3.87%

## Negative EQY self-test

- Status: EXPECTED_FAIL
- Return code: 2

> Resource reduction uses `(baseline - optimized) / baseline × 100%`.

> Time/RSS overhead uses `(optimized - baseline) / baseline × 100%`.
