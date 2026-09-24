# 04 四例 noDF 功能对照（移除 `-set-def-formal`）

- 协议：`run.ys` 仅删除 `-set-def-formal`（其余逐行一致：`-tempinduct -set-init-undef -set-def-inputs -maxsteps 5 -set-assumes -prove-asserts`）。
- 范围：106 个分区（四例 × 优化/基线两链）；c4a ≡ c4b。前提审计见 01；检出能力见 03。

## 1. 结果总表（每链）

| 用例 | noDF 结果 | 前提 | 判读 |
| --- | --- | --- | --- |
| test1 | **43/43 PASS**（归纳长度 1；基例 1 真实、归纳真实） | 全部 SAT | 40 个原“空证明”分区现为**真实证明**；3 个原真实分区保持真实通过 |
| test2 | 1/1 PASS | SAT | 真实 |
| test3 | rw FAIL@base1；sr、sr_out、gpioout FAIL@base2 | 全部 SAT | **全部为 `sr[7]≡rw` 切割构造伪影**（§3） |
| test4 | **5/5 PASS** | 全部 SAT | 5 个原“空证明”分区现为**真实证明**（含 dataout） |

- 与 DF 对照（每链）：
  - test1：40 空 PASS → 真实 PASS；3 真实 PASS 不变；
  - test4：5 空 PASS → 真实 PASS；
  - test3：sr_out 空 PASS → 伪影 FAIL；sr/gpioout 空 UNKNOWN → 伪影 FAIL；rw 真实 FAIL → 伪影 FAIL（同一机理，见 §3）；
  - test2 不变（无初值）。
- 结论：**noDF 恢复了真实检查**；test1/test2/test4 的证明全部在“前提可满足 + 基例真实 + 归纳真实”的意义下成立。

## 2. 与原目标的对照

- 用户要求“确认移除后没有引入新的空检查或放宽必须保留的条件”：
  - 空检查：无（106/106 前提 SAT；检出能力对照通过）；
  - 必须保留条件：`-set-def-inputs`、`-set-assumes`、断言、设计/网表、深度与策略均保留（02 有代码级说明）。
- 用户要求“结合正确例和故意错误例验证检出能力”：见 03（正确例真实通过；mux 篡改与最小反相例均被检出）。

## 3. test3 四个分区 FAIL 的定性：切割构造伪影（非功能差异）

共性：`test3.v` 中 `assign rw = sr[7]` 使网表出现别名 `connect \sr[7] \rw`；
分区生成器对该别名网的“切割（寄存器输出→输入）”在两处不一致或被重复施加：

| 分区 | 伪影形式（证据） | 基础反例 |
| --- | --- | --- |
| rw | gate 保留 `rw_dffeas_q`（Q=rw、D=sr[6]、init 0）且比较值取 FF 输出；gold 侧把同一寄存器切为输入（rw=输入） | t0：gold=输入(1) vs gate=FF 初值(0) |
| sr | gold 的“保持分支”被改写成 `{ \rw \sr[6:1] }`（sr[7] 的保持读取被替换为 rw 输入）⇒ cs=1 时 gold 模型把 rw 装入 sr[7]（真实 RTL 应保持） | t2：gold sr[7]=1 vs gate 保持 0 |
| sr_out | gold 把 `sr[7]` 与 `rw` **各自**切为独立输入（`{ \sr[7] \rw \cs \clk } = { \__pi_sr__7 \__pi_rw \__pi_cs \__pi_clk }`，同一物理网双输入）；gate 保留 rw FF（6 处引用） | base2（同一别名不一致） |
| gpioout | gold 的 rw 读取被替换（`S=rw`、数据 `{ \rw \sr[6:0] }` 等）；gate 保留 rw FF（8 处引用） | base2（同上） |

交叉验证（关键）：**无切割的合并证明**（05）在 noDF 下对 **rw+sr+sr_out 直接通过**（归纳长度 1）
⇒ 两侧对这些信号的功能等价；分区级 FAIL 不代表真实差异。

## 4. 仍未解决（test3）

- `test3.gpioout`：模块级合并证明亦未闭合（UNKNOWN，未发现反例）——保持“未证明”；**补记（2026-09-24 晚）：已在 maxsteps 11 闭合（全模块四断言、QED）；长度≤10 未闭合系 x 弛豫窗口所致，见 `07_gpioout_合并证明/` 与 `08_四用例证据索引.md`**；
- 分区切割伪影属分区生成层问题（建议在工具层修复别名网处理，或对该类分区采用合并证明补充）；
- 本轮**未**改动任何分区生成器/网表/算法（用户约束），仅以副本实验与合并证明方式闭合 rw/sr/sr_out。
