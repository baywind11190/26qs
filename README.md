# 最新V9轮次：f3f5f2a（2026-10-30）

本轮FAIL / NEEDS_REVIEW。资源平均缩减20.454%，时间和内存PASS；功能15/18 PASS，test3优化侧及test4两侧FAIL（前提SAT，反例待复核）。90预热+18首次=108有效样本，无条件复核、无追加轮次。3988项哈希全部一致。

[本轮主报告](D:/0026_qs_result/r/2026-10-30_2107_v9_f3f5f2a_r01/00_report.md)。下列已有轮次保持历史原文和原判定，不与本轮混算。

---

# 当前：V9已对齐1030答疑（2026-10-30）

fd24aa7本轮 **FAIL / NEEDS_REVIEW**：功能15/18通过；资源平均缩减19.765%、内存通过；test2复核时间+5.651%。三条反例涉及初态/编码差异，尚不直接定性算法错误。118个有效样本，没有追加轮次。

[正式报告](D:/0026_qs_result/r/2026-10-30_2047_v9_fd24aa7_r01/00_report.md) · [第24号实施与实测记录](D:/codex/02_嵌赛/验证流程版本更新说明/24_V9对齐1030答疑与fd24aa7验证记录_20261030.md) · [活动规则](D:/codex/0000_26qs/scripts/pmux_validation/POLICY.md)。公开基座0.69+24/d0e71cfb7，两调用p3-arith；官方dirty修改未公开。交付NOT_RUN，官方认可NOT_CLAIMED。

以下原有进度段落保留为历史记录，不替代本次状态与活动规则。

---

# 当前活动版本：V9

入口为[D:/codex/0000_26qs/scripts/pmux_validation/validate_windows_v9.cmd](D:/codex/0000_26qs/scripts/pmux_validation/validate_windows_v9.cmd)，唯一规则见工程POLICY.md。V9结果根为D:/0026_qs_result，r/e/c/a分别保存轮次、短EQY现场、验证缓存和开发证据。V8入口已退役，以下保留V8历史原文和原判定，不作为当前操作指令。

V9改造与一次九例正式轮次已完成：**FAIL / NEEDS_REVIEW**。18条功能主链PASS，资源/内存PASS，平均逻辑缩减13.158%；pipeline首次时间+43.593%，按用户1—10秒扩展复核后+48.619%，仍超过5%和15%。共90预热+18首次+10复核=118个有效样本，没有追加轮次。

[本轮报告](D:/0026_qs_result/r/2026-10-27_1646_v9_17f9361_r01/00_report.md) · [第21号实施与实测记录](D:/codex/02_嵌赛/验证流程版本更新说明/21_V9预热与条件复核升级及九例实测记录_20261027.md) · [V9结果导航](D:/0026_qs_result/README.md)。交付NOT_RUN，官方认可NOT_CLAIMED。

---

# PMUX Windows 原生 V8 工程

三例六链EQY路径专项复核已完成：[23:39专项报告](D:/codex/0000_26qs/results/official_eval/2026-10-26_2339_eqy_pathfix_17f9361_r01/00_report.md)。六条主链、104个分区全部有效PASS；使用显式管理的D:/eqy_work短工作根，未重新综合或测性能。该专项历史结果保持原判定；正式V8现已默认接入受管理短根，最新九例实测见下方第20号记录。

本工程位于 `D:\codex\0000_26qs`。当前入口是 [validate_windows_v8.cmd](D:/codex/0000_26qs/scripts/pmux_validation/validate_windows_v8.cmd)，固定使用 `config.windows.v8.json`；唯一规则正文为 [POLICY.md](D:/codex/0000_26qs/scripts/pmux_validation/POLICY.md)，操作说明见 [验证 README](D:/codex/0000_26qs/scripts/pmux_validation/README.md)。Yosys 是电路综合工具；EQY 是独立运行的功能等价证明工具。

当前套件official9-v1包含原test1～test4与用户提供的五份新增官方用例，由唯一cases清单驱动。每例原版后优化版各一次，共18次正式综合、18条必需两侧功能证明；同次采集墙钟、Yosys主进程峰值和功能/资源产物。先只读plan核对精确算法提交、集成、九例ID/top、规则和预计18次及blocked=[]，再按授权run；以后N例按2N推导。

当前结果布局为 `ascii-v1`：新轮次在 `results/official_eval/YYYY-MM-DD_HHMM_<label>_<commit7>_rNN`，默认label为 `v8_same_run`，主报告为 `00_report.md`。轮次和内部阶段均为英文路径，报告正文保持中文；正式综合输入保持本轮冻结位置，EQY自动使用受管理短根并核验归档，不创建随机桥接目录。解析后的输出根路径必须为安全ASCII且无空格，否则plan/run在写入前阻断。

<!-- nine-case-live-status -->
## 当前九例正式验证：2026-10-27

正式V8已默认接入受管理短EQY工作根，命令入口保持plan/run。最新独立轮次为 **FAIL / NEEDS_REVIEW**：18次综合全部有效、18条功能主链PASS，资源和内存PASS；九例平均逻辑缩减13.158%。balanced、pipeline、crossbar墙钟分别+8.507%、+16.321%、+7.107%超过5%目标，其中pipeline超过15%。不补跑，不改阈值。

算法固定17f9361099dcda757c16bb81caa18ddb52d74c4e / p3-local-lut。[本轮主报告](D:/codex/0000_26qs/results/official_eval/2026-10-27_1045_v8_eqy_short_17f9361_r01/00_report.md)、[第20号接入与实测记录](D:/codex/02_嵌赛/验证流程版本更新说明/20_V8短EQY工作目录正式接入与九例实测记录_20261027.md)。交付NOT_RUN、官方认可NOT_CLAIMED；原2026-10-26 20:16九例FAIL及23:39六链专项PASS均保留原判定，不混算。
<!-- /nine-case-live-status -->

## 历史四例轮次

以下为历史轮次导航，这些历史轮次本次未重新执行综合或EQY。算法提交为 `17f9361099dcda757c16bb81caa18ddb52d74c4e`，使用 `p3-local-lut`；项目HEAD、算法源码哈希和工具哈希另按轮次证据核对。

| V8轮次 | 原判定及限制 |
|---|---|
| 2026-10-23 0117 | 失败，工程FAIL；联合计量自检后处理停止，正式综合0次 |
| 2026-10-23 0121 | 工程FAIL；8次有效，test3墙钟+15.021%、test4+13.284% |
| 2026-10-23 1038 | 工程FAIL；8次有效，test3墙钟+16.909% |
| 2026-10-23 1232 | 该轮工程PASS；8次有效，不能反向改判此前失败轮次 |

后3轮功能、资源、内存检查通过，四例平均逻辑单元缩减约28.7583%。各轮独立保存，不平均、不混算。2026-10-22 2136同次采集前身和2026-10-23五个直接诊断轮次全部保留，诊断不替代正式单次结果；完整报告链接见 [results目录导航](D:/codex/0000_26qs/results/README.md)。

五份新增用例已取得并接入九例清单，逐例logic_units不增加门禁已纳入本次实现；实际测试及正式结果见 [第19号记录](D:/codex/02_嵌赛/验证流程版本更新说明/19_官方新增五例接入与V8九例实测记录_20261026.md)。7.1局部LUT范围、同次调试计量及部分评分边界等待官方确认，继续参考第18号原文；交付未重新执行NOT_RUN，官方认可NOT_CLAIMED。本地套件通过不等于官方验收。

## 目录与资料

| 位置 | 用途 |
|---|---|
| `src/` | PMUX算法源码；当前工作区源码不代替指定提交的冻结源码 |
| `scripts/pmux_validation/` | V8入口、规则、脚本、自检及固定套件 |
| `pmux_case/`、`tests/` | 公开用例和测试输入，具体用途以真实文件为准 |
| `results/` | 全英文路径的V8轮次、前身、诊断、活动自检缓存及归位的历史工作证据 |
| `.tools/` | V8实际使用的Windows工具、来源、构建和缓存，保持原路径 |
| `参考论文/`、`优化算法手工作进度/` | 算法研究参考，不能作为当前评分或独立验收结论 |
| [资料目录](D:/codex/02_嵌赛/README.md) | 当前说明、赛题原件及有日期记录 |
| [赛题说明](D:/codex/02_嵌赛/赛题说明) | 统一赛题主位置；工程旧 `赛题/` 原件迁入此处 |
| [旧版本说明](D:/codex/02_嵌赛/旧版本说明.md) | V7及以前的原文、原路径、日期和原判定索引 |

2026-10-24清理仅限已授权清单内不再被V8使用的旧资产。历史说明收拢不改变原结论，现存V8证据和失败记录完整保留；后续普通流程不得自行删除轮次。历史证据原字节保留，旧路径通过 `results/_migrations/20261025_ascii_layout/manifest.json` 定位到新路径；新活动自检缓存从空状态开始，原1038来源缓存仅作历史记录。本次路径迁移未执行正式run。协作约束见本工程 [AGENTS.md](D:/codex/0000_26qs/AGENTS.md)。

V9三调用集成：新增 `p3-arith-local-lut`，用于带完整算术共享集成补丁的提交；先plan后run。规则及调用/探针证据要求见 scripts/pmux_validation/POLICY.md。
