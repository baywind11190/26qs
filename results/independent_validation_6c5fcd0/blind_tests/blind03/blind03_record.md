# blind03 盲测记录（commit 6c5fcd0；方案A /tmp 工作区）

## 测试目的
测试目的：多个独立 control 域（ca/cb/cc）共存，检查不同控制域之间不能串扰。
输入结构：域 a 共享 ca 成对交换；域 b 不同 control 普通选择；域 c 表达式折叠。
预期：EQY PASS。

## 结果
Case: blind03
是否触发优化: YES（pair-swap candidate=1 / rebuilt=1；Pattern C 输出 1 行）
EQY: PASS
Total before/after: 56 / 47
Comb before/after: 56 / 47
DFF before/after: 0 / 0
runtime: median 0.090s -> 0.080s（3 次）
RSS: max 29440 kB -> 29988 kB
网表变化: generic.il=changed；mapped.il=changed
是否异常: 无
结论: PASS（EQY 正确；资源无负优化）
