# blind06 盲测记录（commit 6c5fcd0；方案A /tmp 工作区）

## 测试目的
测试目的：PMUX 前后混合普通组合逻辑（and/or/xor/not/reduce/普通 mux），验证不破坏正确性。
输入结构：成对交换 PMUX + 前置组合逻辑（xor/not/reduce）+ 后置普通 mux 与 xor。
预期：EQY PASS。

## 结果
Case: blind06
是否触发优化: YES（pair-swap candidate=1 / rebuilt=1；Pattern C 输出 0 行）
EQY: PASS
Total before/after: 44 / 31
Comb before/after: 44 / 31
DFF before/after: 0 / 0
runtime: median 0.090s -> 0.090s（3 次）
RSS: max 29496 kB -> 29472 kB
网表变化: generic.il=changed；mapped.il=changed
是否异常: 无
结论: PASS（EQY 正确；资源无负优化）
