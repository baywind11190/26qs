# PMUX 最新 Commit 独立验证报告

- Commit: `6c5fcd052987206d9e117f518f1d98fc9046c72d`
- Commit subject: test: add PMUX scale stress benchmark framework
- Commit 日期: Fri Sep 18 16:27:08 2026 +0800
- 验证定位: 独立验证（黑盒口径）——不修改算法、不修改评测规则；核心算法开发与独立验证由不同成员完成
- 执行模式: 方案A（/tmp 独立工作区运行；主仓库保持 main、未切换分支、无额外修改）

## 0. 最终判定（分项）

| 项目 | 判定 |
|---|---|
| 公开测试 test1~test4 | PASS（4/4 EQY 等价） |
| Negative EQY | 正常（EXPECTED_FAIL，rc=2） |
| 1000 节点压力（3 组） | PASS（3/3） |
| 隐藏测试风格盲测（8 类） | PASS（8/8） |
| 异常（EQY FAIL / crash / timeout / RSS / 资源负优化） | 未发现（0 项） |
| **整体独立验证** | **PASS** |

## 1. 环境

- OS: Ubuntu 24.04.5 LTS
- Yosys baseline: 0.69 (git sha1 9f75ca1f9, Release) @ `/home/fpga/eda/yosys-baseline/build/yosys`
- Yosys optimized: 0.69 (git sha1 9f75ca1f9-dirty，含目标 pmux_opt 集成) @ `/home/fpga/eda/yosys-optimized/build/yosys`
- 算法集成: `6c5fcd0:src/pmux_opt.cc`（sha256 `c7c1f16b4c99edd3...`，blob e995b524e）集成至 optimized Yosys `passes/opt/pmux_opt.cc`
- 同源审计插件: `pmux_opt.so` sha256 `4b9ddb3dacb187d6...`（未被本流程使用，仅存档）
- EQY: v0.69；Z3: 4.8.12
- Mapping: `synth_intel -family cycloneiv`
- 评测脚本（未修改）: `tools/official_benchmark.py`、`scripts/official_eval/run_case.tcl`、官方 RTL `pmux_case/competition_case/test*.v`

## 2. 公开评测 test1~test4（Run: `6c5fcd0-official-v1`）

| Case | EQY | Total B | Total O | Comb B | Comb O | DFF B | DFF O | Time median B/O | RSS max B/O |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| test1 | PASS | 510 | 431 | 286 | 207 | 222 | 222 | 0.22s / 0.19s | 36324 / 36564 kB |
| test2 | PASS | 25 | 25 | 25 | 25 | 0 | 0 | 0.08s / 0.08s | 31196 / 32668 kB |
| test3 | PASS | 30 | 24 | 12 | 11 | 17 | 12 | 0.09s / 0.09s | 31804 / 32992 kB |
| test4 | PASS | 46 | 46 | 35 | 35 | 10 | 10 | 0.11s / 0.11s | 32236 / 33512 kB |

- 聚合: Total 611→526（**+13.91%**）；Comb 358→278（+22.35%）；DFF 249→244（+2.01%）
- Negative EQY: `EXPECTED_FAIL`，return code = 2
- 结论: 4/4 正确；达到 ≥10% 官方面积目标，未达到 ≥20% 面积满分目标（Total 口径）
- 证据: 本包 `official/6c5fcd0-official-v1/`（完整副本；原始位置 `results/official_eval/6c5fcd0-official-v1/`，含 `validation_verdict_zh.md`、集成 diff、构建日志、pair-swap 诊断、算法文件哈希）

## 3. 1000 节点压力测试（3 组）

| Case | Nodes | EQY | Total B | Total O | Comb B | Comb O | Time median B/O | RSS max B/O | Status |
|---|---:|---|---:|---:|---:|---:|---|---|---|
| mixed_1000 | 995 | PASS | 2341 | 1675 | 2341 | 1675 | 1.110s / 0.960s | 70120 / 62236 kB | PASS |
| pattern_a_1000 | 996 | PASS | 4150 | 2656 | 4150 | 2656 | 1.660s / 1.080s | 95148 / 77108 kB | PASS |
| negative_1000 | 1000 | PASS | 2600 | 2600 | 2600 | 2600 | 1.150s / 1.160s | 74088 / 74184 kB | PASS |

- 判定条件（任务安排）: actual nodes 已记录 / EQY PASS / runtime ≤60s / RSS ≤2GB / 无明显资源负优化 —— **5 项全过**
- 补充: negative_1000 为负控制组（无可优化结构），触发 0/0、网表归一化后与 baseline 逐字节一致；mixed/pattern_a 为正向优化组（-28.45% / -36.00%）
- 证据: 本包 `scale_1000/<case>/`（各 3 次 log+time、stat、EQY 日志、记录 md、网表；原始目录 `/tmp/pmux_scale/results/scale_1000/6c5fcd0/`）；本目录 `scale_1000_summary.md/csv`

## 4. 隐藏测试风格盲测（8 类）

| Case | 测试目的 | Trigger | EQY | Resource | 结论 |
|---|---|---|---|---|---|
| blind01 | Selector 顺序打乱 | YES（pair-swap candidate=1 / rebuilt=1；Pattern C 输出 0 行） | PASS | Total 26→16; Comb 26→16 | PASS（EQY 正确；资源无负优化） |
| blind02 | Partial Decode | YES（pair-swap candidate=0 / rebuilt=0；Pattern C 输出 2 行） | PASS | Total 3→3; Comb 3→3 | PASS（EQY 正确；资源无负优化） |
| blind03 | 多个独立 Control | YES（pair-swap candidate=1 / rebuilt=1；Pattern C 输出 1 行） | PASS | Total 56→47; Comb 56→47 | PASS（EQY 正确；资源无负优化） |
| blind04 | 外部数据依赖 | YES（pair-swap candidate=0 / rebuilt=0；Pattern C 输出 1 行） | PASS | Total 10→10; Comb 10→10 | PASS（EQY 正确；资源无负优化） |
| blind05 | 无可优化结构负例 | NO（pair-swap candidate=0 / rebuilt=0；Pattern C 输出 0 行） | PASS | Total 72→72; Comb 72→72 | PASS（EQY 正确；资源无负优化） |
| blind06 | PMUX + 混合组合逻辑 | YES（pair-swap candidate=1 / rebuilt=1；Pattern C 输出 0 行） | PASS | Total 44→31; Comb 44→31 | PASS（EQY 正确；资源无负优化） |
| blind07 | 边界位宽 W=1/2/4/8/12/16 | YES（pair-swap candidate=6 / rebuilt=6；Pattern C 输出 0 行） | PASS | Total 259→172; Comb 259→172 | PASS（EQY 正确；资源无负优化） |
| blind08 | 多 PMUX 混放 | YES（pair-swap candidate=1 / rebuilt=1；Pattern C 输出 1 行） | PASS | Total 51→42; Comb 51→42 | PASS（EQY 正确；资源无负优化） |

- 关键场景: blind04（external data 不误常量化）、blind05（无误触发）、blind07（W=1/2/4/8/12/16 全覆盖）、blind08（不跨控制域误合并）均通过
- 证据: 本包 `blind_tests/blind01…blind08/`（README + RTL + EQY 配置/日志 + stat + 运行日志（baseline_run*.log / optimized_run*.log）+ time/RSS）；原始目录 `/tmp/pmux_blind_tests/6c5fcd0/`

## 5. 异常记录（任务 07 口径）

- **未发现** EQY FAIL / crash / timeout / RSS 超限 / 明显资源负优化（全部子项 0 例），07 异常处理流程未触发，无 failures/ 目录需要。
- 说明: 所有流程两侧均出现相同的 ABC 固有提示（`ABC: Error: Abc_FrameUpdateGia(): Transformation has failed.`），baseline/optimized 完全一致且 rc=0，判定为工具链固有信息，非异常。
- negative_1000 网表原始 diff（仅版本字符串/安装路径）经归一化分析确认为工具标识差异，网表内容逐字节一致。

## 6. 复现信息

- 官方评测: `python3 tools/official_benchmark.py --baseline-yosys /home/fpga/eda/yosys-baseline/build/yosys --optimized-yosys /home/fpga/eda/yosys-optimized/build/yosys --eqy /home/fpga/eda/eqy/install/bin/eqy --case all --repeat 3 --run-id <id>`
- 1000 节点: 由 `scripts/gen_scale_case.py --mode {mixed,pattern_a,negative} --target 1000` 生成；流程见各 case 记录 md（baseline/optimized 各 3 次 + EQY）
- 盲测: `bash /tmp/pmux_blind_tests/run_blind.sh <case_dir> <top>`（同口径）；记录 `make_blind_record.py`
- 算法哈希: `src/pmux_opt.cc` sha256 见上；已归档于 `official/6c5fcd0-official-v1/pmux_opt.6c5fcd0.cc(.sha256)`

## 7. 最终自检（08 文档清单）

- [x] Commit 明确（完整 SHA / subject / 日期 见文首）
- [x] 环境完整
- [x] test1~4 完整（4/4 EQY PASS + 资源 + time/RSS）
- [x] Negative EQY 完整（EXPECTED_FAIL, rc=2）
- [x] mixed_1000 / pattern_a_1000 / negative_1000 完整
- [x] 8 类 blind tests 完整（含 WIDTH 边界 6 档）
- [x] 异常有最小复现 —— 无异常（0 项，已说明）
- [x] Total / Comb / DFF 完整
- [x] time / RSS 完整（3 次口径）
- [x] 最终 PASS/FAIL 有证据（本目录及所列证据路径）

## 8. 交付物清单（本目录）

```text
results/independent_validation_6c5fcd0/
├── PMUX_最新Commit独立验证报告.md     ← 本报告
├── PMUX_隐藏测试结果.md
├── official/
│   └── 6c5fcd0-official-v1/          ← 官方评测完整原始证据
│       （manifest / summary / test1~test4 EQY+log+stat / negative_check 等）
├── scale_1000/
│   ├── mixed_1000/  pattern_a_1000/  negative_1000/
│   └── 全部顶层证据（RTL/记录/各 3 次 log+time/stat/EQY 证据/网表；EQY 工作目录除外）
├── blind_tests/
│   └── blind01/ ... blind08/          ← README + RTL + EQY + stat + 运行日志+time
├── official_eval_summary.csv
├── scale_1000_summary.csv
├── scale_1000_summary.md
├── blind_summary.md
└── commit_info.txt
```
