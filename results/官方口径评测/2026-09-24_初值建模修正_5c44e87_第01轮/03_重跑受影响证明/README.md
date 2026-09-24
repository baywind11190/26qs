# 受影响的四例功能证明 —— 重跑说明（run01）

## 协议（相对第 03 轮的唯一变化 = 模型）

- 模型：`form_cells_cycloneiv_v2.v`（dffeas 补 power_up 初值建模）。
- 其余全部不变：四例 RTL、优化/基线 mapped 网表（逐字节一致，哈希见 `inputs_manifest.json`）、
  工具链（baseline Yosys 0.69 / EQY 0.69）、链定义、策略（simple / use sat / depth 5）、
  EQY 自生成的 run.ys（含其 ff2anyinit/setundef 步骤，原样使用）。
- 输入经 ASCII 暂存（`results/_reproof_ascii_5c44e87/inputs/`）：中文路径会令 `.ids` 生成时非 ASCII
  字节损坏（首次实验即因此失败，见 `00_实验_test1_c4a/work_失败_输入路径编码问题/`）；第 03 轮同样
  经由 ASCII 桥接运行，机制一致。
- 固定提交 `5c44e87…`；不重跑性能；不修改生成网表；旧记录保留。

## 结果（8 链；对照对象 = 第 03 轮同链）

| 链 | 状态分布（新） | 与第 03 轮状态级差异 |
| --- | --- | --- |
| test1 c4a | 3 FAIL / 40 UNKNOWN | 无（集合同） |
| test1 c4b | 3 FAIL / 40 UNKNOWN | 无 |
| test2 c4a / c4b | 1 PASS | 无 |
| test3 c4a / c4b | 1 FAIL / 2 UNKNOWN / 1 PASS | 无 |
| test4 c4a / c4b | 4 PASS / 1 UNKNOWN | 无 |

机制级变化（FAIL 分区）：

- test1 `state`、`por6_out`、`inter0007_out`：**基例 1 → 基例 2**（初值类反例消失；新反例跨 `reset=1`
  边界，见各分区 `work/strategies/*/simple/trace.vcd`；分析见上级 `00_证据确认_初值逐项.md`）。
- test3 `rw`：仍为基例 1（疑似两侧表示差异，未证明，同上文档）。
- 40 个 UNKNOWN 状态未变（深度 5 口径；本目录不包含深度臂）。

init 属性注入量化（分区 `.il`）：`state` 1+4=5；`por6`/`inter0007` 1+1=2；全链
`reproof_summary.csv` 的 `partition_il_init_attrs` 列（test1 全部 ≥1）。

## 变体对照（`变体对照/`）

- `去ff2anyinit`、`去两条释放语句`：与标准运行结果一致（FAIL，叙事相同）→ 证明两条释放语句
  在 v2 下对已初始化 FF 无操作（详见 `../02_修正与检查/修正说明.md`）。

## 文件

- `run_reproof.py`：重跑脚本（拒绝覆盖；写入 `inputs_manifest.json`、`reproof_summary.json/csv`）。
- `run01/<case>/<chain>/`：`config.eqy`、`eqy.log`、`work/`（含逐分区 `status/run.log/trace.vcd`）。
- `00_实验_test1_c4a/`：链路机制验证的实验（含一次因中文输入路径失败的尝试，保留）。
- `变体对照/`：两变体脚本与日志。
