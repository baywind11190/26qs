# blind01 盲测记录（commit 6c5fcd0；方案A /tmp 工作区）

## 测试目的
测试目的：Selector 顺序打乱（case value 非升序 + 数据切片乱序），检查共享 selector 识别。
输入结构：2 个共享同一 2-bit sel 的 4 分支 PMUX（p/q 成对交换），case 顺序 2,0,3,1 与 3,1,2,0。
预期：EQY PASS；Trigger 记录真实数据，不预设。

## 结果
Case: blind01
是否触发优化: YES（pair-swap candidate=1 / rebuilt=1；Pattern C 输出 0 行）
EQY: PASS
Total before/after: 26 / 16
Comb before/after: 26 / 16
DFF before/after: 0 / 0
runtime: median 0.080s -> 0.070s（3 次）
RSS: max 29220 kB -> 29560 kB
网表变化: generic.il=changed；mapped.il=changed
是否异常: 无
结论: PASS（EQY 正确；资源无负优化）
