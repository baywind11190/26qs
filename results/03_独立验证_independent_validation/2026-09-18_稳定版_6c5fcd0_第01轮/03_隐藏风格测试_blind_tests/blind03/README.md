# blind03（多个独立 Control）

## 测试目的
测试目的：多个独立 control 域（ca/cb/cc）共存，检查不同控制域之间不能串扰。
输入结构：域 a 共享 ca 成对交换；域 b 不同 control 普通选择；域 c 表达式折叠。
预期：EQY PASS。

## 结果摘要
- Trigger: YES（pair-swap candidate=1 / rebuilt=1；Pattern C 输出 1 行）
- EQY: PASS
- Total before/after: 56 / 47
- Comb before/after: 56 / 47
- DFF before/after: 0 / 0
- runtime（3 次中位数）: 0.090s -> 0.080s
- RSS（3 次最大值）: 29440 kB -> 29988 kB
- 结论: PASS（EQY 正确；资源无负优化）

## 复现说明
- TOP: blind03_top
- 流程与 1000 节点压力测试同口径（baseline/optimized 各 3 次 + EQY gold=原RTL / gate=optimized_generic.il）
- 本目录包含: README.md / design.v / test_purpose.txt / verify.eqy / verify.log / baseline_stat.json / optimized_stat.json / baseline_run{1..3}.time + .log / optimized_run{1..3}.time + .log / trigger_summary.txt / artifacts.sha256 / blind03_record.md
- 环境: Yosys 0.69（optimized 含 6c5fcd0 pmux_opt 集成）、EQY v0.69、Z3 4.8.12、cycloneiv mapping
