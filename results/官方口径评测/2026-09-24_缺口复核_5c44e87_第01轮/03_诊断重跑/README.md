# 诊断重跑说明（限时、独立目录）

- **目标**：第 03 轮 c4a（RTL↔优化版 mapped，主路径）的 **43 个 UNKNOWN 分区**
  （test1 40 个 + test3 2 个 + test4 1 个；状态快照自第 03 轮 `chains/run01` 的 summary）。
- **固定提交**：`5c44e87ec403a4e2d7f961e09a3cae6f09919074`（不随分支更新）。
- **隔离性**：全部输入（分区 `.sv/.il`）自第 03 轮逐文件拷贝，sha256 记录于
  `diagnostic_summary.json`；**未改动第 03 轮任何文件**；本目录独立存放。

## 协议（两臂；唯一变化 = 求解深度与单次超时）

| 臂 | 与轮内 "simple" 的差异 | 进程上限 | 并发 |
| --- | --- | --- | --- |
| `run01` | `-maxsteps 5 → 20`；追加 `-timeout 60`（单次求解上限） | 90s/分区 | 8 |
| `run02` | `-maxsteps 5 → 40`；追加 `-timeout 60` | 90s/分区 | 8 |

未改变：初始状态处理（`-set-init-undef` 等）、复位假设（无）、模型条件
（`form_cells_cycloneiv.v` 与 `check_mapped_model` 条件）、输入文件、工具链
（baseline Yosys 0.69，与轮内策略一致）。

## 结果

| 臂 | maxsteps | PASS | UNKNOWN | 备注 |
| --- | --- | --- | --- | --- |
| `run01` | 20 | **1** | 42 | 唯一 PASS = `test3.gpioout`（0.31s；基例 1..6 后归纳步闭合） |
| `run02` | 40 | **1** | 42 | 无新增闭合；`test4.dataout` 触发单次求解 60s 超时（597k 变量 / 1.6M 子句；按 run.sh 语义同为 UNKNOWN） |

## 解释

1. `test1.q0` 等 41 个分区在两档深度下均为「基例 1..maxsteps 全证 + **归纳步各长度均失败**」
   → 不可闭合性与深度无关（结构性，非时间受限）。
2. `test3.gpioout` 属「深度临界」：默认 depth 5 仅差一步（归纳长度 6 即闭合）。
3. `test4.dataout` 属规模/求解困难类：更深后进入求解超时分支，仍未闭合。

## 分类器与脚本修订

- 日志判定规则与链 `run.sh` 相同；勘误项（`Interrupted SAT solver: TIMEOUT!` → UNKNOWN）
  经**日志重解析**应用于两臂汇总，**未重跑任何求解**。
- `run_diagnose.py` 修订：r1（run01 执行）→ r2 参数化 + run 目录创建修复（run02 执行）
  → r3 分类器勘误（重解析）。当前版本 sha256 见本目录 `ALL_SHA256.txt`（上级目录同名文件为准）。

## 声明

- 诊断结果**不改变**第 03 轮判定（NEEDS_REVIEW / NOT_CLOSED），**不构成功能通过依据**。
- 未修改算法、测试输入、模型或配置；未重跑性能测试。
