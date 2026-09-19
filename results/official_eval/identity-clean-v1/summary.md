# PMUX Official Evaluation Summary

| Case | EQY | Base cells | Opt cells | Cell reduction | Base comb | Opt comb | Comb reduction | Base DFF | Opt DFF | DFF reduction | Base time | Opt time | Time overhead | Base RSS | Opt RSS | RSS overhead |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| test1 | PASS | 510 | 510 | +0.00% | 286 | 286 | +0.00% | 222 | 222 | +0.00% | 0.2200s | 0.2200s | +0.00% | 36360kB | 36100kB | -0.72% |
| test2 | PASS | 25 | 25 | +0.00% | 25 | 25 | +0.00% | 0 | 0 | N/A | 0.0800s | 0.0800s | +0.00% | 31724kB | 31760kB | +0.11% |
| test3 | PASS | 30 | 30 | +0.00% | 12 | 12 | +0.00% | 17 | 17 | +0.00% | 0.0900s | 0.0900s | +0.00% | 32000kB | 31628kB | -1.16% |
| test4 | PASS | 46 | 46 | +0.00% | 35 | 35 | +0.00% | 10 | 10 | +0.00% | 0.1000s | 0.1000s | +0.00% | 32292kB | 32660kB | +1.14% |

## Aggregate resource results

- Total cells: 611 -> 611 (+0.00%)
- Cyclone IV combinational cells: 358 -> 358 (+0.00%)
- DFFEAS: 249 -> 249 (+0.00%)
- Arithmetic mean of per-case total-cell reduction: +0.00%

## Negative EQY self-test

- Status: EXPECTED_FAIL
- Return code: 2

> Resource reduction uses `(baseline - optimized) / baseline × 100%`.

> Time/RSS overhead uses `(optimized - baseline) / baseline × 100%`.
