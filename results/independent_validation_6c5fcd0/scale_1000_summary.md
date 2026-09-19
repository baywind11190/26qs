# 1000 节点三组结果汇总（commit 6c5fcd0；方案A：/tmp 独立工作区）

## 1. 主表

| Case | Nodes | EQY | Total B | Total O | Comb B | Comb O | Time | RSS | Status |
|---|---:|---|---:|---:|---:|---:|---:|---:|---|
| mixed_1000 | 995 | PASS | 2341 | 1675 | 2341 | 1675 | 1.11s -> 0.96s | 70120 -> 62236 kB | PASS |
| pattern_a_1000 | 996 | PASS | 4150 | 2656 | 4150 | 2656 | 1.66s -> 1.08s | 95148 -> 77108 kB | PASS |
| negative_1000 | 1000 | PASS | 2600 | 2600 | 2600 | 2600 | 1.15s -> 1.16s | 74088 -> 74184 kB | PASS |

注：Time = baseline/optimized 各 3 次运行的中位数；RSS = 各 3 次运行的最大值（口径见 summary_computation.log）。

## 2. DFF

| Case | DFF B | DFF O |
|---|---:|---:|
| mixed_1000 | 0 | 0 |
| pattern_a_1000 | 0 | 0 |
| negative_1000 | 0 | 0 |

## 3. 资源变化汇总

| Case | Total 变化 | Comb 变化 | 触发情况 |
|---|---:|---:|---|
| mixed_1000 | -28.45% | -28.45% | pair-swap 74/74 rebuilt；Pattern C 触发 |
| pattern_a_1000 | -36.00% | -36.00% | pair-swap 166/166 rebuilt |
| negative_1000 | 0.00% | 0.00% | 触发 0/0；网表归一化后与 baseline 完全一致 |

## 4. PASS 条件核对（任务安排）

- 三组 actual nodes 已记录：995 / 996 / 1000 —— 通过
- 三组 EQY PASS：rc=0（mixed 5:27 / pattern_a 7:48 / negative 7:53；分区全证）—— 通过
- optimized runtime <= 60 s：0.96 / 1.08 / 1.16 s —— 通过
- optimized peak RSS <= 2 GB：62236 / 77108 / 74184 kB（约 0.06–0.07 GB）—— 通过
- 无明显资源负优化：两案例正收益、负控制组零变化零回退 —— 通过

结论：三组 1000 节点压力测试全部通过。依据 05 文档“下一步”，进入任务5：隐藏测试风格盲测。

## 5. 数据来源与复核

- 统一计算输出：`summary_computation.log`（本目录，按 05 文档口径逐 case 执行）
- 每案例完整记录：`<case>/<case>_record.md` + `artifacts.sha256`
- 汇总 CSV：`scale_1000_summary.csv`（本目录）
