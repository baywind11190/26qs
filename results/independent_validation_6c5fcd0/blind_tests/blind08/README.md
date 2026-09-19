# blind08（多 PMUX 混放）

## 测试目的
测试目的：多 PMUX 混放（可优化对/不可优化/独立 control/表达式折叠），检查插件只优化正确目标、不跨控制域误合并。
输入结构：sc 共享 control 成对交换对 + uc1/uc2 独立 control 普通选择 + ec 表达式折叠。
预期：EQY PASS。

## 结果摘要
- Trigger: YES（pair-swap candidate=1 / rebuilt=1；Pattern C 输出 1 行）
- EQY: PASS
- Total before/after: 51 / 42
- Comb before/after: 51 / 42
- DFF before/after: 0 / 0
- runtime（3 次中位数）: 0.090s -> 0.090s
- RSS（3 次最大值）: 29528 kB -> 29804 kB
- 结论: PASS（EQY 正确；资源无负优化）

## 复现说明
- TOP: blind08_top
- 流程与 1000 节点压力测试同口径（baseline/optimized 各 3 次 + EQY gold=原RTL / gate=optimized_generic.il）
- 本目录包含: README.md / design.v / test_purpose.txt / verify.eqy / verify.log / baseline_stat.json / optimized_stat.json / baseline_run{1..3}.time + .log / optimized_run{1..3}.time + .log / trigger_summary.txt / artifacts.sha256 / blind08_record.md
- 环境: Yosys 0.69（optimized 含 6c5fcd0 pmux_opt 集成）、EQY v0.69、Z3 4.8.12、cycloneiv mapping
