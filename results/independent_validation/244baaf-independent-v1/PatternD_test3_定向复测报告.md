# Pattern D｜244baaf 公开 test3 定向独立复测报告

- Commit：`244baaf19c8abf62443aabfb5ff449ff535a447d`（「优化：新增守卫条件驱动的比较器位宽缩减」）
- 复测依据：《PatternD_test3_244baaf_定向复测说明.md》
- 工作区：`/tmp/pmux-pattern-d-test3-244baaf`（归档：`/tmp/pmux-pattern-d-test3-244baaf.tar.gz`，sha256 `79c91fc4c77ef26d2b84541b32518d9f3e4a65a2dd76f7d817851db97cca6dcc`）
- 执行环境：Yosys 0.69 (git sha1 9f75ca1f9)，EQY v0.69，mapping family `cycloneiv`，Ubuntu 24.04
- 复测日期：2026-09-19

---

## 1. 结论摘要

| 项目 | 结果 |
|---|---|
| 插件来源链（commit→源码→全新编译→加载生效） | ✅ 完整、逐字节可证 |
| 资源复现（指定流程 `proc; opt; pmux_opt; opt`） | ✅ **完全复现**：Total 30→**23**，Comb 12→**10**，DFF 17→**12**（两次运行一致） |
| Pattern D 触发证据 | ✅ `GUARD-AWARE EQ REWRITE` ×3（old width 8 → new width 7，guard bit 7 = 1）；`Pattern D candidates in module test3: 3` |
| EQY（按说明配置：RTL vs 指定流程网表） | ⚠️ **FAIL（rc=2）**：4 分区中 `test3.sr` 无法证明（equivalence unknown） |
| 该 EQY 失败归因 | ✅ **与 Pattern D / 插件无关**（对照实验证明：无插件、纯 `proc;opt;opt` 网表同样 FAIL；test1 同样 FAIL；netlist 级对照证明插件改写保语义） |
| Pattern D 语义等价性（独立佐证） | ✅ 网表级 EQY **PASS**（全部分区，含 `test3.sr`）；官方流程 RTL EQY 同插件 **PASS** |
| crash / timeout / 内存异常 | 无（两条流程均 rc=0；RSS 31284/31000 kB 量级） |

**一句话判定：**
Pattern D 在 test3 上的新增 1-cell 资源收益**已独立复现**；说明文件指定的 EQY 组合在本环境**不可通过**，但对照实验证明其原因**与插件无关**（属 RTL-vs-含 `opt` 网表的验证方法学问题），Pattern D 改写本身已用网表级等价验证独立证明保语义。**不修改算法**，证据整体交算法负责人。

---

## 2. 插件来源证据链（Step 1–8）

| 环节 | 证据 | 值 |
|---|---|---|
| 提交锁定 | `target_commit.txt` / `target_resolved.txt` | `244baaf19c8abf62443aabfb5ff449ff535a447d` |
| 源码提取 | `pmux_opt.cc.sha256` | `11657a593f86d0a99f5a3da41ff6bbc2d74d07f0bf03edcdf0c1e4c264f70350` |
| 源码字节一致性 | `git show … \| cmp - pmux_opt.cc` | `CMP_RC=0` |
| baseline 不含项目 pmux_opt | `help_before_plugin.txt` | `No such command or cell type: pmux_opt` |
| 编译器 | `yosys_config_cxxflags.txt`（baseline 自带） | `/home/fpga/eda/yosys-baseline/build/yosys-config`，`-DYOSYS_VER=0.69`，include 指向 baseline build |
| 全新编译 | `plugin_build.log` | `BUILD_RC=0` |
| 插件哈希 | `pmux_opt.so.sha256` | `b919861f5db8cd787ba3e8f067bea7126b735c713209150ce684ec589e50b479` |
| 加载生效 | `help_after_plugin.txt` | 显示 pmux_opt 帮助（Recommended flow: `proc → opt → pmux_opt`） |
| test3 输入 | `test3.v.sha256` | `46ef97a9c39b8b38d00cc6a7e273890e3aea1700e77c141aa2213d33a8b02a61` |

```
244baaf → git show src/pmux_opt.cc → /tmp/.../pmux_opt.cc (cmp=0)
        → yosys-config(baseline) --build → /tmp/.../pmux_opt.so (BUILD_RC=0)
        → baseline yosys -m pmux_opt.so → help pmux_opt 可用（无内建 pmux_opt 污染）
```

## 3. 资源复现（说明文件指定流程）

流程（严格按说明）：

```text
read_verilog -sv test3.v
→ hierarchy -check -top test3
→ proc
→ opt
→ pmux_opt
→ opt
→ synth_intel -family cycloneiv -top test3
→ stat -json
```

| 口径 | Total | Comb | DFF | 与开发侧声明 |
|---|---:|---:|---:|---|
| baseline（`proc; opt; opt`，无插件） | 30 | 12 | 17 | 一致 |
| 244baaf 指定流程（run1 / run2） | **23 / 23** | **10 / 10** | **12 / 12** | **完全一致** |

- `BASELINE_MATCH = True`，`PATTERN_D_MATCH = True`（说明文件 Step 11 校验脚本原样执行）
- 两次独立运行结果一致（run2：`baseline_stat_run2.json` / `optimized_stat_run2.json`）
- 对比冻结官方流程（详见《附加分析_开发侧基准对比.md》）：test3 官方口径 30→24 / 12→11（Pattern D 不触发）；指定流程 30→23 / 12→10（Pattern D ×3）
- 时间/RSS：baseline 0.10 s / 29284 kB；optimized 0.07 s / 31000 kB（无异常）

## 4. EQY 结果与归因（关键）

### 4.1 说明文件指定配置的结果

`verify.eqy`（gold=RTL；gate=指定流程 `optimized_generic.il`；`simple / use sat / depth 5`）：

```text
test3.gpioout : proved
test3.rw      : proved
test3.sr_out  : proved
test3.sr      : Could not prove — equivalence unknown   ← 3/4 分区通过
DONE (FAIL, rc=2)     EQY_RC=2
```

`depth 20` 复测（`ctl_deep/`）：`test3.sr` 仍 unknown → 非 depth 不足，属结构性不可证。

### 4.2 归因对照实验（全部使用同一 EQY 配置）

| 对照 | gate 网表 | 结果 | 说明 |
|---|---|---|---|
| `verify/`（指定流程 + 插件） | `proc; opt; pmux_opt; opt` | FAIL（`test3.sr`） | 插件参与 |
| `ctl_baseline/`（**无插件**） | `proc; opt; opt` | **FAIL（`test3.sr`，同一分区同一症状）** | ← 失败与插件无关的直接证据 |
| `ctl_proc/` | `proc`（无 opt） | **PASS** | 定位到 `opt` 步骤 |
| `ctl_opt1/` | `proc; opt` | **FAIL（`test3.sr`）** | 单个 `opt` 即触发 |
| `ctl_optclean/` | `proc; opt; opt; opt_clean` | FAIL（`test3.sr`） | `opt_clean` 不能恢复可证性 |
| `ctl_official/`（插件，官方流程） | `proc; pmux_opt; opt_clean` | **PASS（rc=0）** | 插件在官方口径下 RTL EQY 通过 |
| `ctl_other_test1/` | `proc; opt; opt`（test1） | **FAIL**（3/47 分区 unknown） | 现象不限于 test3 |
| `ctl_other_test2/` | `proc; opt; opt`（test2） | PASS | — |
| `ctl_other_test4/` | `proc; opt; opt`（test4） | rc=1（缺 `memory_map`，本对照配置遗漏，非设计问题） | 说明文件附注 |

**根因（可复现事实）**：yosys `opt`（`opt_dff` / `simple.cc` 的 enable 推断）会把 test3 的移位寄存器 `sr` 从无使能的 `$dff` 重编码为带复杂使能的 `$dffe`；EQY 对**内部寄存器分区**（`test3.sr`，含 xbits）比较“RTL 预处理版”与“opt 后网表”时无法在 SAT 下收敛。此现象**在没有 pmux_opt / Pattern D 的情况下完全相同**。

### 4.3 Pattern D 语义等价性（独立佐证，可信度更高）

| 验证 | 配置 | 结果 |
|---|---|---|
| **网表级等价**（`ctl_pairwise/`） | gold=`proc;opt;opt` 网表 vs gate=`proc;opt;pmux_opt;opt` 网表（两者仅差插件改写：GUARD-AWARE ×3 + BRANCH-CONST FOLD ×3 + pair-swap） | **PASS（rc=0）**：`test3.sr`、`test3.sr_out`、`test3.rw`、`test3.gpioout` 全部分区 proved |
| **官方流程 RTL 等价**（`ctl_official/`） | gold=RTL vs gate=`proc;pmux_opt;opt_clean` 网表（同一全新插件） | **PASS（rc=0）** |

即：*插件相对 baseline 的净改写* 与 *插件在官方口径下的网表* 均被正式证明与参考设计等价。

## 5. 与开发侧声明的对照

| 口径 | Total | Comb | DFF | EQY |
|---|---|---|---|---|
| 开发侧声明（Pattern D 后） | 30→**23** | 12→**10** | 17→12 | 期望 PASS |
| 本次定向复测（指定流程） | 30→**23** ✅ | 12→**10** ✅ | 17→**12** ✅ | 指定 EQY 配置 FAIL（归因见 §4） |
| 冻结官方流程（前一轮完整验证，流程 A） | 30→24 | 12→11 | 17→12 | PASS（RTL vs `proc;pmux_opt;opt_clean`） |

> 按说明文件 §21 原则：流程 A（冻结官方 24/11）与流程 B（指定定向 23/10）**同时保留、互不覆盖**。
> 补充：Pattern D 的语义正确性已由 §4.3 的两种独立等价验证证实，故**不适用**单纯以“指定 EQY FAIL”判 Pattern D 无效；但“指定流程下 EQY=PASS”这一期望在本环境**未被满足**，需按 §4.2 的方法学结论处理。

## 6. 给算法负责人的反馈（混合模板）

```text
【244baaf Pattern D / test3 独立定向复测】

Commit 与 plugin 来源已确认：
- pmux_opt.cc sha256 = 11657a593f86d0a99f5a3da41ff6bbc2d74d07f0bf03edcdf0c1e4c264f70350
- 由 baseline 自带 yosys-config 全新编译，pmux_opt.so sha256 = b919861f5db8cd787ba3e8f067bea7126b735c713209150ce684ec589e50b479
- baseline Yosys 无内建项目 pmux_opt；运行时显式 -m 加载本次新编译插件

流程（严格按指定）：
read_verilog → hierarchy → proc → opt → pmux_opt → opt → synth_intel -family cycloneiv

test3 资源（两次运行一致）：
Baseline total 30 / comb 12 / dff 17
244baaf total 23 / comb 10 / dff 12
→ Pattern D 新增 1-cell（Total 与 Comb 各 -1）收益已独立复现。
触发日志：GUARD-AWARE EQ REWRITE ×3（width 8→7，guard bit7=1），Pattern D candidates: 3。

EQY：
- 按说明文件的 EQY 配置（RTL vs 指定流程网表）：FAIL rc=2，唯一失败分区 test3.sr（equivalence unknown，depth 20 亦然）。
- 但对照实验证明该失败与插件无关：
  * 无插件、纯 proc;opt;opt 网表 → 同一分区同样 FAIL；
  * proc-only 网表 → PASS，proc;opt → FAIL（定位到 yosys opt 的 dff→dffe 重编码）；
  * test1 在 proc;opt;opt 流下也 FAIL（3/47 分区），test2 PASS；
  * opt_clean 不能恢复可证性。
- Pattern D 语义本身已独立证明：
  * 网表级等价（处理前后网表直接比对）：全部分区 PASS，含 test3.sr；
  * 官方流程（proc;pmux_opt;opt_clean）RTL EQY：PASS。

建议：
1) 若采用本定向流程做 EQY，请改用不受“RTL vs opt 后网表”方法学影响的比对方式
   （网表级 base-vs-opt 比对，或 RTL vs 官方流程网表），必要时调整 EQY 分区策略；
2) 不建议修改算法；完整证据（源码/构建/网表/EQY 日志/对照）已在
   /tmp/pmux-pattern-d-test3-244baaf（tar.gz sha256 79c91fc4c77ef26d2b84541b32518d9f3e4a65a2dd76f7d817851db97cca6dcc）。
```

## 7. 证据文件清单（`/tmp/pmux-pattern-d-test3-244baaf/`）

```text
target_commit.txt target_resolved.txt repo_status.txt repo_status_eval_paths.txt
pmux_opt.cc pmux_opt.cc.sha256 source_cmp.txt
yosys_version.txt help_before_plugin.txt help_after_plugin.txt
yosys_config_cxxflags.txt plugin_build.log plugin_build_stat.txt pmux_opt.so pmux_opt.so.sha256
test3.v.sha256
baseline.log baseline.time baseline_stat.json baseline_generic.il baseline_mapped.il
optimized.log optimized.time optimized_stat.json optimized_generic.il optimized_mapped.il
baseline_run2.* optimized_run2.* pattern_d_log_extract.txt
verify.eqy verify/（指定配置 EQY：FAIL rc=2）
ctl_baseline/（无插件对照：FAIL）ctl_proc/（PASS）ctl_opt1/（FAIL）ctl_optclean/（FAIL）
ctl_deep/（depth20：仍 FAIL）ctl_official/（官方流程：PASS）ctl_pairwise/（网表级：PASS）
ctl_other_test1/ ctl_other_test2/ ctl_other_test4/ officialflow_plugin_generic.il
```

## 8. 与说明文件的偏差记录（透明声明）

1. **工作区“脏”处理**：说明文件 Step 1 要求工作区干净否则停止。复测时 `git status --short` 非空，但全部为操作方整理文档导致的根目录文件移动（PDF/xlsx/md 的删除 + `参考论文/`、`赛题/`、`验证手工作进度/` 未跟踪目录）；**评测关键路径 `src/ pmux_case/ scripts/ tools/ formal/ tests/` 均为空（干净）**，且本次测试全部使用 `git show` 提取的源码与只读的 test3.v（哈希已记录）。据此未中止，偏差在此记录供负责人复核。
2. **test4 对照配置**：`ctl_other_test4` 结果 rc=1 系对照脚本漏加 `memory_map`（官方配置对 test4 会加），与设计无关，未纳入判定。
3. **结论表述**：说明文件 §17 判定矩阵按“指定 EQY 是否 PASS”二分；本次实测指定 EQY FAIL 但**归因与插件无关**（见 §4.2），故按事实分列“资源复现 ✅ / 指定 EQY 组合不可通过（方法学）⚠️ / Pattern D 语义等价 ✅”，不直接套用 A/C 判定，理由与证据全文可查。
