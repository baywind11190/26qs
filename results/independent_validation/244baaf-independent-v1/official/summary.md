# PMUX Official Evaluation Summary

| Case | EQY | Base cells | Opt cells | Cell reduction | Base comb | Opt comb | Comb reduction | Base DFF | Opt DFF | DFF reduction | Base time | Opt time | Time overhead | Base RSS | Opt RSS | RSS overhead |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| test1 | PASS | 510 | 431 | +15.49% | 286 | 207 | +27.62% | 222 | 222 | +0.00% | 0.2000s | 0.1800s | -10.00% | 36056kB | 36764kB | +1.96% |
| test2 | PASS | 25 | 25 | +0.00% | 25 | 25 | +0.00% | 0 | 0 | N/A | 0.0700s | 0.0700s | +0.00% | 31704kB | 32592kB | +2.80% |
| test3 | PASS | 30 | 24 | +20.00% | 12 | 11 | +8.33% | 17 | 12 | +29.41% | 0.0900s | 0.0800s | -11.11% | 32028kB | 33276kB | +3.90% |
| test4 | PASS | 46 | 46 | +0.00% | 35 | 35 | +0.00% | 10 | 10 | +0.00% | 0.1000s | 0.1000s | +0.00% | 32160kB | 33768kB | +5.00% |

## Aggregate resource results

- Total cells: 611 -> 526 (+13.91%)
- Cyclone IV combinational cells: 358 -> 278 (+22.35%)
- DFFEAS: 249 -> 244 (+2.01%)
- Arithmetic mean of per-case total-cell reduction: +8.87%

## Negative EQY self-test

- Status: EXPECTED_FAIL
- Return code: 2

> Resource reduction uses `(baseline - optimized) / baseline × 100%`.

> Time/RSS overhead uses `(optimized - baseline) / baseline × 100%`.
