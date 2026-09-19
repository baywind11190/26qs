# blind05（无可优化结构负例）

## 测试目的
测试目的：无可优化结构负例（普通 mux、无共享 selector 的 PMUX）。
输入结构：8 路 case 选择（8 个独立数据输入）+ 普通优先级 mux 链。
预期：EQY PASS；资源 SAME 或接近 SAME，不能明显 REGRESS。

## 结果摘要
- Trigger: NO（pair-swap candidate=0 / rebuilt=0；Pattern C 输出 0 行）
- EQY: PASS
- Total before/after: 72 / 72
- Comb before/after: 72 / 72
- DFF before/after: 0 / 0
- runtime（3 次中位数）: 0.090s -> 0.090s
- RSS（3 次最大值）: 29488 kB -> 29620 kB
- 结论: PASS（EQY 正确；资源无负优化）

## 复现说明
- TOP: blind05_top
- 流程与 1000 节点压力测试同口径（baseline/optimized 各 3 次 + EQY gold=原RTL / gate=optimized_generic.il）
- 本目录包含: README.md / design.v / test_purpose.txt / verify.eqy / verify.log / baseline_stat.json / optimized_stat.json / baseline_run{1..3}.time + .log / optimized_run{1..3}.time + .log / trigger_summary.txt / artifacts.sha256 / blind05_record.md
- 环境: Yosys 0.69（optimized 含 6c5fcd0 pmux_opt 集成）、EQY v0.69、Z3 4.8.12、cycloneiv mapping
