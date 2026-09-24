# blind02（Partial Decode）

## 测试目的
测试目的：Partial Decode —— 控制位宽 4-bit 但仅出现 2 个 case value（5/11），验证条件折叠不依赖 full decode。
输入结构：2 个共享 4-bit c 的表达式 PMUX（每个仅 2 个 case 分支 + default）。
预期：EQY PASS。

## 结果摘要
- Trigger: YES（pair-swap candidate=0 / rebuilt=0；Pattern C 输出 2 行）
- EQY: PASS
- Total before/after: 3 / 3
- Comb before/after: 3 / 3
- DFF before/after: 0 / 0
- runtime（3 次中位数）: 0.070s -> 0.070s
- RSS（3 次最大值）: 29528 kB -> 29124 kB
- 结论: PASS（EQY 正确；资源无负优化）

## 复现说明
- TOP: blind02_top
- 流程与 1000 节点压力测试同口径（baseline/optimized 各 3 次 + EQY gold=原RTL / gate=optimized_generic.il）
- 本目录包含: README.md / design.v / test_purpose.txt / verify.eqy / verify.log / baseline_stat.json / optimized_stat.json / baseline_run{1..3}.time + .log / optimized_run{1..3}.time + .log / trigger_summary.txt / artifacts.sha256 / blind02_record.md
- 环境: Yosys 0.69（optimized 含 6c5fcd0 pmux_opt 集成）、EQY v0.69、Z3 4.8.12、cycloneiv mapping
