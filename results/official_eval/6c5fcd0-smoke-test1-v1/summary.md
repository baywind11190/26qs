# PMUX Official Evaluation Summary

| Case | EQY | Base cells | Opt cells | Cell reduction | Base comb | Opt comb | Comb reduction | Base DFF | Opt DFF | DFF reduction | Base time | Opt time | Time overhead | Base RSS | Opt RSS | RSS overhead |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| test1 | PASS | 510 | 431 | +15.49% | 286 | 207 | +27.62% | 222 | 222 | +0.00% | 0.2500s | 0.2500s | +0.00% | 36268kB | 36340kB | +0.20% |

## Aggregate resource results

- Total cells: 510 -> 431 (+15.49%)
- Cyclone IV combinational cells: 286 -> 207 (+27.62%)
- DFFEAS: 222 -> 222 (+0.00%)
- Arithmetic mean of per-case total-cell reduction: +15.49%

## Negative EQY self-test

- Status: EXPECTED_FAIL
- Return code: 2

> Resource reduction uses `(baseline - optimized) / baseline × 100%`.

> Time/RSS overhead uses `(optimized - baseline) / baseline × 100%`.
