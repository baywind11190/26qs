# 09 test3 原版对照（c4b）无切割合并证明

- 目标：补齐 test3 **原版对照侧（baseline，c4b）** 的无切割整模块合并证明；与优化侧（c4a）既有证据
  （`05_test3_rw_合并证明/`、`07_gpioout_合并证明/`）**分列独立**，不以优化侧通过替代原版侧结论。
- 素材（第03轮冻结输入 + 经检查的 v3 模型）：
  - RTL `stage/test3.v`（`46ef97a9…`，与套件冻结清单一致）；
  - 原版映射网表 `stage/test3_baseline_mapped.il`（`1f619554…`，与 v3 重跑 inputs_manifest 一致）；
  - v3 器件语义模型 `stage/form_cells_cycloneiv_v3.v`（`d1f0e185…`）。
- 方式：EQY setup（`eqy -m`，只生成分区/脚本、不执行证明）经 ASCII 桥（`results/_step1_c4b_ascii/`）
  重建整模块合并 IL `modules/test3_c4b.il`（`b7b72f73…`；路径归一化后与 06 目录 v3 重跑 c4b 模块 `diff=0`）。
  证明配方 = 无切割 miter `modules/test3.sv` + **noDF**（`-set-init-undef -set-def-inputs`，无 `-set-def-formal`）
  - `-maxsteps 16`（300s 执行上限）；四断言 `rw/sr/gpioout/sr_out`；比较器含 gold 未定义位 **x 容差**。

## 结果

| 项 | 结果 |
| --- | --- |
| 前提探针（noDF，seq 1） | **PREMISES_SAT**（可满足；`probe_noDF.log`） |
| 合并证明 | **PASS@k14**（归纳步 1..13 失败、14 通过；基例 14/14 全真；无浅反例） |
| 可重复性 | 重跑同结果（`proof_m16_rerun.log`） |
| 覆盖 | `__mp_rw`(1) / `__mp_sr`(8) / `__po_gpioout`(8) / `__po_sr_out`(1)：test3 全部输出 + 内部匹配点 |

## 限制

- 未运行 BMC/更大深度（按执行说明，默认不跑历史诊断策略）；未做性能或综合。
- 仅为实验证据，不构成官方验收；本步未改动主入口。
- 优化侧（c4a）证据引用 `05/07` 目录原始记录，本目录未复制改写。

## 文件

- `00_provenance.json`：来源、核对与结果的结构化记录；
- `stage/`：冻结输入副本；`modules/`：miter 与合并 IL；`eqy_setup/`：setup 配置、日志与 gate 读入脚本；
- `probe_noDF.ys/.log`、`proof_m16.ys/.log`、`proof_m16_rerun.log`；
- `SHA256.txt`：本目录全量哈希；ASCII 桥工作目录：`results/_step1_c4b_ascii/`。
