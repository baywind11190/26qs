# PMUX Windows 原生 V8 工程

本工程位于 `D:\codex\0000_26qs`。当前入口是 [validate_windows_v8.cmd](D:/codex/0000_26qs/scripts/pmux_validation/validate_windows_v8.cmd)，固定使用 `config.windows.v8.json`；唯一规则正文为 [POLICY.md](D:/codex/0000_26qs/scripts/pmux_validation/POLICY.md)，操作说明见 [验证 README](D:/codex/0000_26qs/scripts/pmux_validation/README.md)。Yosys 是电路综合工具；EQY 是独立运行的功能等价证明工具。

当前已获得 test1～test4，每例原版后优化版各一次，共8次正式综合，同一次运行采集墙钟、Yosys主进程退出事件峰值及功能/资源网表。先做只读 `plan` 核对规则来源、完整算法提交、集成选项、预计8次及 `builtin_plan.blocked` 为空，再按授权执行 `run`。VS Code任务只提供V8只读预检。

当前结果布局为 `ascii-v1`：新轮次在 `results/official_eval/YYYY-MM-DD_HHMM_<label>_<commit7>_rNN`，默认label为 `v8_same_run`，主报告为 `00_report.md`。轮次和内部阶段均为英文路径，报告正文保持中文；正式输入和EQY工作文件直接在所属轮次内使用，不再创建随机桥接目录。解析后的输出根路径必须为安全ASCII且无空格，否则plan/run在写入前阻断。

## 当前轮次

以下均为既有结果的导航，本次文档整理未追加综合或EQY。算法提交为 `17f9361099dcda757c16bb81caa18ddb52d74c4e`，使用 `p3-local-lut`；项目HEAD、算法源码哈希和工具哈希另按轮次证据核对。

| V8轮次 | 原判定及限制 |
|---|---|
| 2026-10-23 0117 | 失败，工程FAIL；联合计量自检后处理停止，正式综合0次 |
| 2026-10-23 0121 | 工程FAIL；8次有效，test3墙钟+15.021%、test4+13.284% |
| 2026-10-23 1038 | 工程FAIL；8次有效，test3墙钟+16.909% |
| 2026-10-23 1232 | 该轮工程PASS；8次有效，不能反向改判此前失败轮次 |

后3轮功能、资源、内存检查通过，四例平均逻辑单元缩减约28.7583%。各轮独立保存，不平均、不混算。2026-10-22 2136同次采集前身和2026-10-23五个直接诊断轮次全部保留，诊断不替代正式单次结果；完整报告链接见 [results目录导航](D:/codex/0000_26qs/results/README.md)。

新增官方用例仍为 `WAITING_OFFICIAL_CASES`；新增用例接入和逐例 `logic_units` 增加的独立门禁尚待适配。7.1局部LUT允许范围、同次调试计量及部分计量细节待官方确认，见 [第18号记录](D:/codex/02_嵌赛/验证流程版本更新说明/18_1022答疑与V8符合性核对及待确认问题_20261023.md)。交付包 `NOT_RUN`，官方认可 `NOT_CLAIMED`；四例本地PASS不等于全部官方验收通过。

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
