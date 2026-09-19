# blind08 盲测记录（commit 6c5fcd0；方案A /tmp 工作区）

## 测试目的
测试目的：多 PMUX 混放（可优化对/不可优化/独立 control/表达式折叠），检查插件只优化正确目标、不跨控制域误合并。
输入结构：sc 共享 control 成对交换对 + uc1/uc2 独立 control 普通选择 + ec 表达式折叠。
预期：EQY PASS。

## 结果
Case: blind08
是否触发优化: YES（pair-swap candidate=1 / rebuilt=1；Pattern C 输出 1 行）
EQY: PASS
Total before/after: 51 / 42
Comb before/after: 51 / 42
DFF before/after: 0 / 0
runtime: median 0.090s -> 0.090s（3 次）
RSS: max 29528 kB -> 29804 kB
网表变化: generic.il=changed；mapped.il=changed
是否异常: 无
结论: PASS（EQY 正确；资源无负优化）
