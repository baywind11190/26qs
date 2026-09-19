# blind01（Selector 顺序打乱）

## 测试目的
测试目的：Selector 顺序打乱（case value 非升序 + 数据切片乱序），检查共享 selector 识别。
输入结构：2 个共享同一 2-bit sel 的 4 分支 PMUX（p/q 成对交换），case 顺序 2,0,3,1 与 3,1,2,0。
预期：EQY PASS；Trigger 记录真实数据，不预设。

## 结果摘要
- Trigger: YES（pair-swap candidate=1 / rebuilt=1；Pattern C 输出 0 行）
- EQY: PASS
- Total before/after: 26 / 16
- Comb before/after: 26 / 16
- DFF before/after: 0 / 0
- runtime（3 次中位数）: 0.080s -> 0.070s
- RSS（3 次最大值）: 29220 kB -> 29560 kB
- 结论: PASS（EQY 正确；资源无负优化）

## 复现说明
- TOP: blind01_top
- 流程与 1000 节点压力测试同口径（baseline/optimized 各 3 次 + EQY gold=原RTL / gate=optimized_generic.il）
- 本目录包含: README.md / design.v / test_purpose.txt / verify.eqy / verify.log / baseline_stat.json / optimized_stat.json / baseline_run{1..3}.time + .log / optimized_run{1..3}.time + .log / trigger_summary.txt / artifacts.sha256 / blind01_record.md
- 环境: Yosys 0.69（optimized 含 6c5fcd0 pmux_opt 集成）、EQY v0.69、Z3 4.8.12、cycloneiv mapping
