# H1 固定提交验证

本目录案例逐字节复制自开发侧历史目录 `results/next_round/pattern_h1_regression/cases/`。
原生成器路径未保存，不宣称恢复了生成器。本次保留现存 RTL 作为确定性回归输入。

| 案例 | 用途 | P 流程 stable / H1 预期 pair-swap 次数 |
|---|---|---|
| h1_n1_three_special | 三个特殊 pair，拒绝 | 0 / 0 |
| h1_n2_small_two_special | 四个 pair 中两个特殊，拒绝 | 0 / 0 |
| h1_n3_width_mismatch | 位宽不匹配，拒绝 | 0 / 0 |
| h1_n4_different_control | 控制信号不同，拒绝 | 0 / 0 |
| h1_n5_partial_decode | 非完整译码，拒绝 | 0 / 0 |
| h1_n6_ctrlwidth1 | 单位控制宽度边界，拒绝 | 0 / 0 |
| h1_p1_threshold | 双特殊 pair 接受阈值 | 0 / 1 |
| h1_p2_swapbit2 | 非零 swap bit | 0 / 1 |
| h1_p3_shuffle | 分支顺序打乱 | 0 / 1 |
| h1_p4_large | 较大结构 | 0 / 1 |
| h1_p5_zero_special | 旧功能：零特殊 pair | 1 / 1 |
| h1_p6_one_special | 旧功能：一个特殊 pair | 1 / 1 |

执行方法见 `docs/frozen_validation.md`。
