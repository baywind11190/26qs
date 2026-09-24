# PMUX Commit 验证结论

- Commit：`6c5fcd052987206d9e117f518f1d98fc9046c72d`
- Run ID：`6c5fcd0-official-v1`
- 核心结论：**通过：4/4 EQY 正确，总 cell 缩减达到 10% 及以上；达到题目面积要求，但未达到 20% 面积满分目标。**

## 1. 正确性

| Case | EQY |
|---|---|
| test1 | PASS |
| test2 | PASS |
| test3 | PASS |
| test4 | PASS |

- Negative EQY：`EXPECTED_FAIL`，return code = `2`

## 2. 资源

- Total cells：`611 → 526`，缩减 **+13.91%**
- Cyclone IV combinational cells：`358 → 278`，缩减 **+22.35%**
- DFFEAS：`249 → 244`，变化 **+2.01%**

- ≥10% 官方面积目标：**达到**
- ≥20% 面积满分目标：**未达到**

> 题目评分口径优先看 Total cells；cycloneiv_lcell_comb 是组合逻辑子集。

## 3. 每个 case

| Case | Total cells | Reduction | Comb | Comb reduction | Time median | RSS max |
|---|---:|---:|---:|---:|---:|---:|
| test1 | 510→431 | +15.49% | 286→207 | +27.62% | 0.2200s→0.1900s | 36324→36564 kB |
| test2 | 25→25 | +0.00% | 25→25 | +0.00% | 0.0800s→0.0800s | 31196→32668 kB |
| test3 | 30→24 | +20.00% | 12→11 | +8.33% | 0.0900s→0.0900s | 31804→32992 kB |
| test4 | 46→46 | +0.00% | 35→35 | +0.00% | 0.1100s→0.1100s | 32236→33512 kB |

## 4. Pair-swap 触发情况

| Case | 正式流程 rebuilt | 推荐流程 rebuilt |
|---|---:|---:|
| test1 | 1 | 1 |
| test2 | 0 | 0 |
| test3 | 0 | 0 |
| test4 | 0 | 0 |

## 5. 性能解释

官方 case 多为亚秒级，0.01 s 波动就可能形成明显百分比变化；主要检查异常变慢、超时或内存暴涨。
官方性能约束：节点规模 ≤1000 时完整优化耗时 ≤60 s、峰值内存 ≤2 GB。

## 6. 可复现信息

- project commit：`825d0af3fc642de9101644160d7d987b25f1a40f`
- project worktree dirty：`False`
- mapping：`cycloneiv`
- repeat：`3`
- EQY：`EQY v0.69`
- Z3：`Z3 version 4.8.12 - 64 bit`

