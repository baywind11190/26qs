# 07 H2 用例结果（正例 / 合法拒绝例 / 驱动异常）

生成器：`gen_h2_cases.py`（确定性无随机，参考语义见各 RTL 头注释）。
P3 口径：`synth_intel` coarse 阶段 `fsm; opt` 之后、`wreduce` 之前。

## 总览

- 用例总数 20（正例 11，拒绝例 9）
- 期望判定 OK：20/20
- EQY c1_local（插件改写局部等价）PASS：20/20
- EQY c2_stage（baseline vs optimized 同阶段对照）PASS：20/20
- 正例独立参考模型（移位表达 vs 用例拼接表达）PASS：10/11

## 正例（期望触发 H2）

| 用例 | ctrl_w | lane_w | banks | baseline comb | optimized comb | H2 rebuilt | c1 | c2 | ref |
|---|---|---|---|---|---|---|---|---|---|
| h2p_c3_lw1 | 3 | 1 | 2 | 28 | 12 | 1 | PASS | PASS | PASS |
| h2p_c3_lw2 | 3 | 2 | 2 | 48 | 24 | 1 | PASS | PASS | PASS |
| h2p_c3_lw4 | 3 | 4 | 2 | 88 | 48 | 1 | PASS | PASS | PASS |
| h2p_c4_lw1 | 4 | 1 | 4 | 60 | 20 | 1 | PASS | PASS | PASS |
| h2p_c4_lw2 | 4 | 2 | 4 | 104 | 40 | 1 | PASS | PASS | PASS |
| h2p_c4_lw4 | 4 | 4 | 4 | 192 | 80 | 1 | PASS | PASS | PASS |
| h2p_c4_lw8 | 4 | 8 | 4 | 368 | 160 | 1 | PASS | PASS | PASS |
| h2p_c5_lw2 | 5 | 2 | 8 | 207 | 64 | 1 | PASS | PASS | PASS |
| h2p_c5_lw4 | 5 | 4 | 8 | 375 | 128 | 1 | PASS | PASS | PASS |
| h2p_c4_lw2_shuffled | 4 | 2 | 4 | 104 | 40 | 1 | PASS | PASS | PASS |
| h2p_c10_lw1 | 10 | 1 | 256 | 5000 | 944 | 1 | PASS | PASS | None |

## 拒绝例（期望不触发 H2）

| 用例 | 拒绝原因 | baseline comb | optimized comb | H2 candidate | c1 | c2 |
|---|---|---|---|---|---|---|
| h2n_wrong_rotation | phase=1 左旋（错误方向） | 76 | 76 | 0 | PASS | PASS |
| h2n_partial_decode | 缺少一个 control 值分支 | 103 | 103 | 0 | PASS | PASS |
| h2n_no_rotation | 所有 phase 同数据（无意义旋转） | 8 | 8 | 0 | PASS | PASS |
| h2n_xz_data | 末尾分支数据为常量 x | 46 | 46 | 0 | PASS | PASS |
| h2n_width_not_div4 | 数据宽度 6 不整除 4 | 82 | 82 | 0 | PASS | PASS |
| h2n_ctrl2 | 控制宽度 2 低于下限（no_rotation 双保险） | 0 | 0 | 0 | PASS | PASS |
| h2n_diff_control | 两个 pmux 使用不同 control（不构成同一 selector 组；不禁止其他 Pattern 合法优化） | 56 | 56 | 0 | PASS | PASS |
| h2n_non_target | 普通 2:1 mux，无 $pmux 结构 | 8 | 8 | 0 | PASS | PASS |
| h2n_ctrl11 | 控制宽度 11 超出上限（512 banks 大例） | 11240 | 11240 | 0 | PASS | PASS |

## 驱动异常（multi-driver selector）

- 构造：克隆 `[]` h2p_c3_lw1 pre_p3 中一个 $eq 条件 cell 注入同一 Y 网络（详见 driver_anomaly_run01/build_meta.json）
- baseline `check -assert`：rc=1，检出问题 2 条（预期失败）
- 插件运行：rc=0，H2 candidate=0，rebuilt=0，崩溃=False
- 判定：baseline 正确识别输入异常；插件未崩溃且未对异常网表执行 H2 重构。

## 边界与规模说明

- `h2p_c10_lw1`（ctrl=10 上限内，256 banks）：触发且大幅缩减（见上表）；c1/c2 各 5121 分区全证。
- `h2n_ctrl11`（ctrl=11 超上限，512 banks，11240 cells）：正确拒绝；c1 5121+ 分区、c2 10241/10241 分区全证。
- 控制宽度 2 拒绝例与 width 不整除以外的 X/Z 用例均未触发（见上表）。

## 证据位置

- 流程与 EQY：`h2_cases_run01/flows/<case>/{baseline,optimized,c1_local,c2_stage,ref_check}/`
- 生成源与哈希：`h2_cases_run01/rtl.sha256`、`cases.json`、`h2_results.json`
- 驱动异常：`h2_cases_run01/driver_anomaly_run01/`
