# blind04 盲测记录（commit 6c5fcd0；方案A /tmp 工作区）

## 测试目的
测试目的：branch 中混合 control 表达式与外部数据；允许折叠 control 确定 bit，不得错误常量化 external-data 依赖 bit。
输入结构：4 分支 PMUX，分支内混合 ctl 位与 ext 位。
预期：EQY PASS（最关键）。

## 结果
Case: blind04
是否触发优化: YES（pair-swap candidate=0 / rebuilt=0；Pattern C 输出 1 行）
EQY: PASS
Total before/after: 10 / 10
Comb before/after: 10 / 10
DFF before/after: 0 / 0
runtime: median 0.090s -> 0.080s（3 次）
RSS: max 29108 kB -> 29252 kB
网表变化: generic.il=changed；mapped.il=changed
是否异常: 无
结论: PASS（EQY 正确；资源无负优化）
