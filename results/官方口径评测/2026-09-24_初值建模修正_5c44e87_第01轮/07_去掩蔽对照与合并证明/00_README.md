# 07 去掩蔽对照与合并证明（受控诊断）

- 日期：2026-09-24；固定算法提交 5c44e87…；**不改算法、官方输入、网表；不新增复位假设；不重跑性能；不提交推送；旧结果保留**。
- 基础：`06_器件语义模型_v3`（模型 v3）；所有运行 = 在 `07/tree` 内自包含的副本上执行；主入口未修改。

## 目的（按用户指令）

1. **核实实际分区前提是否可满足**：把“检测到 x”与“已证明约束矛盾（前提 UNSAT）”分开记录（`01_前提可满足性审计.md`、`audit_summary.csv`）。
2. **`-set-def-formal` 移除的四例功能对照**：先说明它实际约束了什么、确认移除不引入空检查/不放宽必须保留的条件，并用正确例与故意错误例验证检出能力（`02_setdef_formal_约束分析.md`、`03_检出能力对照.md`、`04_四例_noDF对照.md`）。
3. **test3.rw 重新证明**：用保留信号关系的合并（整模块/合并 miter）方式，不以“已知伪影”豁免（`05_test3_rw_合并证明.md`）。
4. 报告区分**模型检查通过 / 分区证明通过 / 整题证明通过**（`06_总结.md`）。

## 目录

- `tree/run01/` — 自包含工作树：四例 × 两链的分区副本 + 各分区 `probe_DF/noDF`（前提探针）、`run_noDF.ys/log`（noDF 实际证明）
- `scripts/run_audit_and_noDF.py` — 生成并运行全部 106 分区的 3 项运行（幂等、可重跑）
- `audit_summary.csv` — 逐分区：DF 状态/是否有 x/前提结论；noDF 状态/前提结论/基例失败长度
- `01_前提可满足性审计.md`、`02_setdef_formal_约束分析.md`、`03_检出能力对照.md`、
  `04_四例_noDF对照.md`、`05_test3_rw_合并证明.md`、`06_总结.md`、`08_四用例证据索引.md`
- `07_gpioout_合并证明/` — gpioout 聚焦与限时策略尝试（全模块四断言 QED@k11、gpioout-only、BMC、诊断；
  `attempts_summary.csv`、`SHA256.txt`、`run_attempts.py`）

## 复现

- 前提探针：`run.ys` 最终 sat 行替换为 `chformal -assert -remove` + `sat -seq 1 -set-init-undef [-set-def-formal] -set-def-inputs -set-assumes miter`
  （无证明目标；输出 `SAT solving finished - no model found.` = 前提 UNSAT；`- model found:` = 前提 SAT）。
- noDF 证明：`run.ys` 删除 `-set-def-formal`（其余逐行一致）后 `yosys -ql run.log run.ys`。
