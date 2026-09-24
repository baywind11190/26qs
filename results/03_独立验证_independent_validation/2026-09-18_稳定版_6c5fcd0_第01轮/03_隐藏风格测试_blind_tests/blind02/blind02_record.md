# blind02 盲测记录（commit 6c5fcd0；方案A /tmp 工作区）

## 测试目的
测试目的：Partial Decode —— 控制位宽 4-bit 但仅出现 2 个 case value（5/11），验证条件折叠不依赖 full decode。
输入结构：2 个共享 4-bit c 的表达式 PMUX（每个仅 2 个 case 分支 + default）。
预期：EQY PASS。

## 结果
Case: blind02
是否触发优化: YES（pair-swap candidate=0 / rebuilt=0；Pattern C 输出 2 行）
EQY: PASS
Total before/after: 3 / 3
Comb before/after: 3 / 3
DFF before/after: 0 / 0
runtime: median 0.070s -> 0.070s（3 次）
RSS: max 29528 kB -> 29124 kB
网表变化: generic.il=changed；mapped.il=changed
是否异常: 无
结论: PASS（EQY 正确；资源无负优化）
