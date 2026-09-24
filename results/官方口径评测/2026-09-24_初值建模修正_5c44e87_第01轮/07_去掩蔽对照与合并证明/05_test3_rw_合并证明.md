# 05 test3.rw 合并证明（保留信号关系，不用伪影豁免、不用 sr_out 替代）

## 1. 素材与方式

- 素材：run01 中 EQY 生成的**整模块 miter**（`modules/test3.sv` + `modules/test3.il`，副本在 `05_test3_rw_合并证明/modules/`）。
  该 miter 直接实例化 `\gold.test3` 与 `\gate.test3`（**无任何切割、双方寄存器完整保留**），并逐信号比较：
  - `__mp_rw__assert`（**rw，1 位**，`modules/test3.sv:49`）；
  - `__mp_sr__assert`（sr，8 位）；`__po_sr_out__assert`；`__po_gpioout__assert`。
- 配方：与链内策略同型（proc/chformal/async2sync/formalff/setundef/flatten/dffunmap/opt/sat），
  `-tempinduct -set-init-undef -set-def-inputs -maxsteps 5 -set-assumes -prove-asserts`（noDF regime；DF 版本仅作对照）。

## 2. 前提探针（先核实前提）

| 运行 | 前提 |
| --- | --- |
| `probe_merged_DF.ys` | **PREMISES_UNSAT**（该设计含未声明初值 ⇒ DF 下为矛盾前提/空证明，**不采用**） |
| `probe_merged_noDF.ys` | **PREMISES_SAT**（可真实证明） |

## 3. 证明结果

| 运行 | 覆盖断言 | 结果 |
| --- | --- | --- |
| `run_merged_noDF.ys`（完整模块） | rw + sr + sr_out + gpioout | UNKNOWN（maxsteps 5/6/8 均未闭合；未发现反例） |
| `run_merged_rw_only_noDF_m5.ys`（精简合并 miter：保留 rw + sr + sr_out，去掉 gpioout 断言） | **rw** + sr + sr_out | **PASS（归纳长度 1）** |
| `run_merged_DF.ys`（对照） | 完整模块 | PASS——但前提 UNSAT（空证明），仅作记录 |

- 精简合并 miter 文件：`modules/test3_rw.sv`（由完整 miter 删除 gpioout 比较/覆盖生成，其余不变）。

## 4. 结论

1. **rw 已通过“保留信号关系的合并证明”重新证明**：在双方 sr 移位寄存器（含 gate 的 `rw_dffeas_q` 级）完整保留、
   共用输入（clk/cs/sr_in）的设计上，noDF 前提可满足且归纳证明通过（长度 1）——不是伪影豁免，也**不是**用 sr_out 替代
   （sr_out 只是同一合并证明中被一并覆盖的信号之一）。
2. gpioout 不在此合并证明之内（其断言会使其未闭合，属另案），保持 UNKNOWN（非失败）。（后续已在 `07_gpioout_合并证明/` 中于 **maxsteps 11** 闭合，四断言单次运行通过；见 §5 补记与 08 索引。）
3. 与 04 的交叉关系：分区级 rw/sr/sr_out FAIL 被确认为切割构造伪影（04 §3）；其真实等价性由本合并证明背书。

## 5. 补记（2026-09-24 晚）：完整模块四断言在 maxsteps 11 闭合

- **`full_m16.ys`（≡ `run_merged_noDF_m16.ys`）：全部四断言 PASS@k11**（`Induction step proven: SUCCESS!` + QED；归纳步 1..10 失败、11 通过；基例 1..11 全真；重复性重跑输出一致）。
- 旁证：`gpo_m16/gpo_m48`（gpioout 单断言）PASS@k16；BMC 无 CEX@64/@128（128 用时 157s）；`full_bmc256` 在 180s 与 600s 上限重试下均超时（记录；重试末步 1.64M 变量未收敛）。
- 诊断：`full_ti_def_m12`（仅定义态窗口起点；不单独作充分证明）在 k=1 即通过 ⇒ 拖住 k≤10 的是**窗口起点的 x 弛豫制造态**（gold.sr/gpioout、gate `execute$*` FF 含 x），而非功能差异。
- 结论：先前“未闭合（UNKNOWN）”为**归纳长度不足**；无任何语义/模型/协议改动。分区级 gpioout 反例痕迹保持记录，最终等价性以本无切割合并证明为准。
- 文件：`07_gpioout_合并证明/`（日志、CSV、脚本、SHA256.txt）。
