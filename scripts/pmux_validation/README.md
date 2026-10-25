# Windows V8 验证使用说明

当前入口为 `D:\codex\0000_26qs\scripts\pmux_validation\validate_windows_v8.cmd`，固定加载同目录 `config.windows.v8.json`。正式规则以 [POLICY.md](D:/codex/0000_26qs/scripts/pmux_validation/POLICY.md) 为准；轮次里的POLICY是当轮原文快照。旧版操作已归并至 [旧版本说明](D:/codex/02_嵌赛/旧版本说明.md)。

V8每例原版后优化版各一次，当前test1～test4共8次正式综合；同一次Yosys运行采集墙钟、主进程退出事件峰值，导出ABC9后/器件映射前功能网表及最终资源网表。功能证明随后由EQY独立执行。不预热、不重复平均、不补跑、不默认追加稳定性诊断。官方用例总数变为N时目标为2N次，当前代码的新增用例接入尚待适配。

## 只读预检

以下命令在 **Windows PowerShell** 执行，作用是核对指定算法提交、依赖、规则来源及执行计划，不创建轮次、不编译。示例为现有7.1提交：

```powershell
& 'D:\codex\0000_26qs\scripts\pmux_validation\validate_windows_v8.cmd' plan 17f9361099dcda757c16bb81caa18ddb52d74c4e --integration-profile p3-local-lut
```

预期 `builtin_plan.blocked=[]`、当前四例 `formal_synthesis_expected_runs=8`；同时核对 `policy_source`、两侧路径/身份、`build_required`和缓存复用原因。任何阻断须先查明，不跳过校验或静默刷新清单。算法参数必须是完整40位Git提交，不能用分支名、源码SHA或二进制SHA代替。VS Code的“V8只读预检”任务会分别询问完整提交及集成选项。

- `p3`：内置早期PMUX调用，身份 `pmux-opt-inline-p3-v1`。
- `p3-local-lut`：早期调用加ABC9后/厂商map_cells前7.1局部LUT调用，身份 `pmux-opt-inline-p3-local-lut-v1`；含已登记7.1补丁的提交必须选此项，补丁冻结哈希参与缓存键。

匹配缓存可复用；未命中时，已授权run在隔离源码树按精确提交构建并登记。两种集成、编译器、公共依赖、Yosys/ABC及源码身份均按规则核对，失败不回退独立插件。

## 执行与失败处理

只有用户明确授权正式验证后，才在同一PowerShell环境将上述 `plan` 改为 `run`，保留同一完整提交及集成选项。预检失败、工具身份不符、自检失败或正式样本不完整时停止并保留记录，不自动重试、追加测量或换用旧流程。修复后新开轮次，不覆盖旧轮次。

墙钟由PowerShell 5.1 `Measure-Command`记录，包含中间/最终输出、同次调试和请求/响应开销；构建、自检、EQY及事后分析不计入。峰值只看同一 `yosys.exe` 在退出调试事件放行前读取的 `PeakWorkingSetSize`，原始单位字节。两者分别逐例判断5%目标和15%门槛，保留60秒/2GiB及原版超限例外；具体本地计量的官方接受性仍待确认。

功能使用 `dffeas-v3` 模型及严格 `noDF-local-r1`策略，独立证明原始RTL到本轮两侧post-ABC网表，输入哈希绑定同次产物；test3保留分区与整设计合并证明日志。证明、资源、时间、内存不能互相抵消，未执行为 `NOT_RUN`，未证明或工具错误不能记PASS。

## 英文结果布局与历史路径

新轮次使用 `results/official_eval/YYYY-MM-DD_HHMM_<label>_<commit7>_rNN`，默认label为 `v8_same_run`，只接受英文字母、数字、下划线及连字符；同名前缀轮号递增，禁止覆盖。输出根路径解析后须为安全ASCII且无空格，否则plan和run在创建目录前阻断，不建立随机替代目录。

阶段目录为 `01_meta`、`02_assets`、`03_runner`、`04_flowcheck`、`05_public`、`09_performance`、`10_selfcheck`、`11_summary`，工具链证据在 `01_meta/toolchain_evidence`；布局版本 `ascii-v1` 写入新上下文。正式综合直接读取冻结RTL；EQY在本轮阶段的work和merged最终路径原位运行，不再生成ascii_bridge或跨目录回拷。失败、超时与中断的产物继续原位保留，证明inputs仍检查八份两侧网表及模型并绑定正式post_abc哈希。

活动自检缓存是 `results/official_eval/_cache/selfcheck_v8.json`；旧缓存原字节在 `_history/selfcheck_cache_v8.json`。代码和路径变化使旧指纹失效，后续已授权run按新指纹重新自检，不把空缓存写成通过。

历史四轮桥接各归入所属轮次legacy_workspace；2136形式化桥接归入legacy_formal_workspace；多轮共用的旧桥接归入 `_shared_evidence/2026-10-22_1823_v7_17f9361`。所有历史日志、报告正文、上下文、冻结脚本、规则快照、ALL_SHA256及ZIP字节保持原文。`results/_migrations/20261025_ascii_layout/manifest.json`记录旧新路径及哈希，支持按原绝对路径、原相对路径和共享桥接来源定位；原清单通过映射校验，不刷新成新“原清单”。当前导航使用新路径，历史快照仅作追溯，不承诺旧命令在迁移后直接重跑。

本次英文路径迁移的正式端到端验证为 `NOT_RUN`；文件哈希核对、单元测试和只读plan不等于正式验收。

## 既有轮次与当前限制

| V8轮次 | 原结果 |
|---|---|
| 10-23 0117 | 失败/工程FAIL；正式综合0次 |
| 10-23 0121 | 工程FAIL；test3 +15.021%、test4 +13.284% |
| 10-23 1038 | 工程FAIL；test3 +16.909% |
| 10-23 1232 | 该轮工程PASS；不改判此前失败 |

[完整results导航](D:/codex/0000_26qs/results/README.md)列出四轮报告、2136同次采集前身和五个直接诊断轮次；全部保留，不混算。历史共享自检缓存的来源仍是1038轮，不能因为其工程FAIL而删除；它已与历史证据一起保留，新活动缓存从空entries开始，不继承旧ok或改写旧指纹。

交付包仍 `NOT_RUN`，官方认可 `NOT_CLAIMED`；新增效率用例 `WAITING_OFFICIAL_CASES`。新增用例接入、单例 `logic_units` 独立门禁、7.1允许范围及计量待确认项见 [第18号记录](D:/codex/02_嵌赛/验证流程版本更新说明/18_1022答疑与V8符合性核对及待确认问题_20261023.md)，本次清理未修复。赛题原件统一在 [资料目录赛题说明](D:/codex/02_嵌赛/赛题说明)。

每轮主报告 `00_report.md`，完整身份、逐例证据、运行计数和哈希见轮次内01_meta/05_public/10_selfcheck/09_performance/11_summary。工程验证、交付和就绪分别记录，只有交付及当前所需检查也通过才能声明READY。本地PASS不等于官方验收。
