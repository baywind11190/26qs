# PMUX Official Evaluation Summary

| Case | EQY | Base cells | Opt cells | Cell reduction | Base comb | Opt comb | Comb reduction | Base DFF | Opt DFF | DFF reduction | Base time | Opt time | Time overhead | Base RSS | Opt RSS | RSS overhead |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| test2 | PASS | 25 | 25 | +0.00% | 25 | 25 | +0.00% | 0 | 0 | N/A | 0.0900s | 0.0900s | +0.00% | 31524kB | 31108kB | -1.32% |

## Aggregate resource results

- Total cells: 25 -> 25 (+0.00%)
- Cyclone IV combinational cells: 25 -> 25 (+0.00%)
- DFFEAS: 0 -> 0 (N/A)
- Arithmetic mean of per-case total-cell reduction: +0.00%

## Negative EQY self-test

- Status: EXPECTED_FAIL
- Return code: 2

> Resource reduction uses `(baseline - optimized) / baseline × 100%`.

> Time/RSS overhead uses `(optimized - baseline) / baseline × 100%`.
