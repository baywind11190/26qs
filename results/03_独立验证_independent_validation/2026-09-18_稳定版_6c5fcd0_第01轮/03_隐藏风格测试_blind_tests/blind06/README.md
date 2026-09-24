# blind06（PMUX + 混合组合逻辑）

## 测试目的
测试目的：PMUX 前后混合普通组合逻辑（and/or/xor/not/reduce/普通 mux），验证不破坏正确性。
输入结构：成对交换 PMUX + 前置组合逻辑（xor/not/reduce）+ 后置普通 mux 与 xor。
预期：EQY PASS。

## 结果摘要
- Trigger: YES（pair-swap candidate=1 / rebuilt=1；Pattern C 输出 0 行）
- EQY: PASS
- Total before/after: 44 / 31
- Comb before/after: 44 / 31
- DFF before/after: 0 / 0
- runtime（3 次中位数）: 0.090s -> 0.090s
- RSS（3 次最大值）: 29496 kB -> 29472 kB
- 结论: PASS（EQY 正确；资源无负优化）

## 复现说明
- TOP: blind06_top
- 流程与 1000 节点压力测试同口径（baseline/optimized 各 3 次 + EQY gold=原RTL / gate=optimized_generic.il）
- 本目录包含: README.md / design.v / test_purpose.txt / verify.eqy / verify.log / baseline_stat.json / optimized_stat.json / baseline_run{1..3}.time + .log / optimized_run{1..3}.time + .log / trigger_summary.txt / artifacts.sha256 / blind06_record.md
- 环境: Yosys 0.69（optimized 含 6c5fcd0 pmux_opt 集成）、EQY v0.69、Z3 4.8.12、cycloneiv mapping
