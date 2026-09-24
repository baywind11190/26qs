# blind07 盲测记录（commit 6c5fcd0；方案A /tmp 工作区）

## 测试目的
测试目的：边界位宽覆盖 W = 1 / 2 / 4 / 8 / 12 / 16。
输入结构：同一 sel 下 6 个参数化成对交换实例（swap_pair，W 分别为 1/2/4/8/12/16）。
预期：EQY PASS；各位宽单独验证。

## 结果
Case: blind07
是否触发优化: YES（pair-swap candidate=6 / rebuilt=6；Pattern C 输出 0 行）
EQY: PASS
Total before/after: 259 / 172
Comb before/after: 259 / 172
DFF before/after: 0 / 0
runtime: median 0.180s -> 0.140s（3 次）
RSS: max 30788 kB -> 29828 kB
网表变化: generic.il=changed；mapped.il=changed
是否异常: 无
结论: PASS（EQY 正确；资源无负优化）
