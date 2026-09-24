# blind04（外部数据依赖）

## 测试目的
测试目的：branch 中混合 control 表达式与外部数据；允许折叠 control 确定 bit，不得错误常量化 external-data 依赖 bit。
输入结构：4 分支 PMUX，分支内混合 ctl 位与 ext 位。
预期：EQY PASS（最关键）。

## 结果摘要
- Trigger: YES（pair-swap candidate=0 / rebuilt=0；Pattern C 输出 1 行）
- EQY: PASS
- Total before/after: 10 / 10
- Comb before/after: 10 / 10
- DFF before/after: 0 / 0
- runtime（3 次中位数）: 0.090s -> 0.080s
- RSS（3 次最大值）: 29108 kB -> 29252 kB
- 结论: PASS（EQY 正确；资源无负优化）

## 复现说明
- TOP: blind04_top
- 流程与 1000 节点压力测试同口径（baseline/optimized 各 3 次 + EQY gold=原RTL / gate=optimized_generic.il）
- 本目录包含: README.md / design.v / test_purpose.txt / verify.eqy / verify.log / baseline_stat.json / optimized_stat.json / baseline_run{1..3}.time + .log / optimized_run{1..3}.time + .log / trigger_summary.txt / artifacts.sha256 / blind04_record.md
- 环境: Yosys 0.69（optimized 含 6c5fcd0 pmux_opt 集成）、EQY v0.69、Z3 4.8.12、cycloneiv mapping
