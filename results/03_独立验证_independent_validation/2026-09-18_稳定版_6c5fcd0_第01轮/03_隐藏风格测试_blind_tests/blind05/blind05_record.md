# blind05 盲测记录（commit 6c5fcd0；方案A /tmp 工作区）

## 测试目的
测试目的：无可优化结构负例（普通 mux、无共享 selector 的 PMUX）。
输入结构：8 路 case 选择（8 个独立数据输入）+ 普通优先级 mux 链。
预期：EQY PASS；资源 SAME 或接近 SAME，不能明显 REGRESS。

## 结果
Case: blind05
是否触发优化: NO（pair-swap candidate=0 / rebuilt=0；Pattern C 输出 0 行）
EQY: PASS
Total before/after: 72 / 72
Comb before/after: 72 / 72
DFF before/after: 0 / 0
runtime: median 0.090s -> 0.090s（3 次）
RSS: max 29488 kB -> 29620 kB
网表变化: generic.il=identical-after-normalization；mapped.il=identical-after-normalization
是否异常: 无
结论: PASS（EQY 正确；资源无负优化）
