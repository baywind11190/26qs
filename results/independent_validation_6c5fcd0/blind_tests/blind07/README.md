# blind07（边界位宽 W=1/2/4/8/12/16）

## 测试目的
测试目的：边界位宽覆盖 W = 1 / 2 / 4 / 8 / 12 / 16。
输入结构：同一 sel 下 6 个参数化成对交换实例（swap_pair，W 分别为 1/2/4/8/12/16）。
预期：EQY PASS；各位宽单独验证。

## 结果摘要
- Trigger: YES（pair-swap candidate=6 / rebuilt=6；Pattern C 输出 0 行）
- EQY: PASS
- Total before/after: 259 / 172
- Comb before/after: 259 / 172
- DFF before/after: 0 / 0
- runtime（3 次中位数）: 0.180s -> 0.140s
- RSS（3 次最大值）: 30788 kB -> 29828 kB
- 结论: PASS（EQY 正确；资源无负优化）

## 复现说明
- TOP: blind07_top
- 流程与 1000 节点压力测试同口径（baseline/optimized 各 3 次 + EQY gold=原RTL / gate=optimized_generic.il）
- 本目录包含: README.md / design.v / test_purpose.txt / verify.eqy / verify.log / baseline_stat.json / optimized_stat.json / baseline_run{1..3}.time + .log / optimized_run{1..3}.time + .log / trigger_summary.txt / artifacts.sha256 / blind07_record.md
- 环境: Yosys 0.69（optimized 含 6c5fcd0 pmux_opt 集成）、EQY v0.69、Z3 4.8.12、cycloneiv mapping
