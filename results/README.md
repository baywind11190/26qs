# 当前活动版本：V9

入口为[D:/codex/0000_26qs/scripts/pmux_validation/validate_windows_v9.cmd](D:/codex/0000_26qs/scripts/pmux_validation/validate_windows_v9.cmd)，唯一规则见工程POLICY.md。V9结果根为D:/0026_qs_result，r/e/c/a分别保存轮次、短EQY现场、验证缓存和开发证据。V8入口已退役，以下保留V8历史原文和原判定，不作为当前操作指令。

V9改造与一次九例正式轮次已完成：**FAIL / NEEDS_REVIEW**。18条功能主链PASS，资源/内存PASS，平均逻辑缩减13.158%；pipeline首次时间+43.593%，按用户1—10秒扩展复核后+48.619%，仍超过5%和15%。共90预热+18首次+10复核=118个有效样本，没有追加轮次。

[本轮报告](D:/0026_qs_result/r/2026-10-27_1646_v9_17f9361_r01/00_report.md) · [第21号实施与实测记录](D:/codex/02_嵌赛/验证流程版本更新说明/21_V9预热与条件复核升级及九例实测记录_20261027.md) · [V9结果导航](D:/0026_qs_result/README.md)。交付NOT_RUN，官方认可NOT_CLAIMED。

---

# PMUX 结果目录导航

当前唯一执行入口为 [Windows原生V8](D:/codex/0000_26qs/scripts/pmux_validation/README.md)，规则正文为 [POLICY.md](D:/codex/0000_26qs/scripts/pmux_validation/POLICY.md)。本页只索引既有证据，不启动实验，也不把不同轮次合并为一个结果。

<!-- nine-case-live-status -->
## 当前九例正式验证：2026-10-27

正式V8已默认接入受管理短EQY工作根，命令入口保持plan/run。最新独立轮次为 **FAIL / NEEDS_REVIEW**：18次综合全部有效、18条功能主链PASS，资源和内存PASS；九例平均逻辑缩减13.158%。balanced、pipeline、crossbar墙钟分别+8.507%、+16.321%、+7.107%超过5%目标，其中pipeline超过15%。不补跑，不改阈值。

算法固定17f9361099dcda757c16bb81caa18ddb52d74c4e / p3-local-lut。[本轮主报告](D:/codex/0000_26qs/results/official_eval/2026-10-27_1045_v8_eqy_short_17f9361_r01/00_report.md)、[第20号接入与实测记录](D:/codex/02_嵌赛/验证流程版本更新说明/20_V8短EQY工作目录正式接入与九例实测记录_20261027.md)。交付NOT_RUN、官方认可NOT_CLAIMED；原2026-10-26 20:16九例FAIL及23:39六链专项PASS均保留原判定，不混算。
<!-- /nine-case-live-status -->

## 六链 EQY 路径专项复核

2026-10-26 23:39独立功能复核 **PASS**：balanced、pipeline、feedback的原版和优化版共六条主链、104个分区全部闭合，104个noDF前提探针有效SAT，无工具错误。路径因素经同工具、同字节读取对照确认，最长拼接路径由260～275字符降至175～189字符。

见 [专项报告](D:/codex/0000_26qs/results/official_eval/2026-10-26_2339_eqy_pathfix_17f9361_r01/00_report.md)。短工作现场为D:/eqy_work/2026-10-26_2016_v8_nine_cases_17f9361_r01/a02，已核验归档。此前 [23:35启动阻断记录](D:/codex/0000_26qs/results/official_eval/2026-10-26_2335_eqy_pathfix_17f9361_r01/00_report.md) 保留：身份字符串的斜杠差异导致预检停止，六链均NOT_RUN，未执行EQY setup或证明。

本次新增综合和性能测量均为0；原20:16九例报告及其FAIL判定不变。该六链专项为此前独立结果；正式V8默认接入与新九例实测见第20号记录；专项PASS不代表九例整体验收或官方认可。

## 历史四例V8入口轮次

算法完整提交均为 `17f9361099dcda757c16bb81caa18ddb52d74c4e`，集成为 `p3-local-lut`。下表保持各轮原判定；本页补全导航不表示本次重新执行。

| 轮次与主报告 | 正式综合 | 原结果 |
|---|---:|---|
| [10-23 0117](D:/codex/0000_26qs/results/official_eval/2026-10-23_0117_v8_same_run_17f9361_r01/00_report.md) | 0次 | 失败，工程FAIL/NEEDS_REVIEW；联合测量自检后处理失败 |
| [10-23 0121](D:/codex/0000_26qs/results/official_eval/2026-10-23_0121_v8_measurement_fix_17f9361_r01/00_report.md) | 8次有效 | 工程FAIL；test3墙钟+15.021%、test4+13.284% |
| [10-23 1038](D:/codex/0000_26qs/results/official_eval/2026-10-23_1038_v8_same_run_17f9361_r01/00_report.md) | 8次有效 | 工程FAIL；test3墙钟+16.909%；为历史共享自检缓存的证据来源；新活动缓存从空开始 |
| [10-23 1232](D:/codex/0000_26qs/results/official_eval/2026-10-23_1232_v8_same_run_17f9361_r01/00_report.md) | 8次有效 | 该轮工程PASS；不反向改判0121或1038 |

后3轮功能、资源、内存通过，四例平均逻辑单元缩减约28.7583%；逐例原始数值以各自主报告、CSV/JSON及日志为准。功能证明、资源、时间、内存、交付分别记录；交付包仍 `NOT_RUN`，官方认可 `NOT_CLAIMED`。

## 保留的同次采集前身与直接诊断

| 轮次与主报告 | 原状态与边界 |
|---|---|
| [10-22 2136同次采集](D:/codex/0000_26qs/results/official_eval/2026-10-22_2136_same_run_pre_v8_17f9361_r01/00_report.md) | 正式8次；test2 +6.626%、test3 +8.161%超过5%；额外80次诊断单列，是下列诊断的直接来源 |
| [无调试墙钟/Job CPU第01轮](D:/codex/0000_26qs/results/official_eval/2026-10-23_diag_wall_jobcpu_test2-test3_17f9361_r01/00_report.md) | 失败；有效综合0/40，PowerShell参数转换错误 |
| [无调试墙钟/Job CPU第02轮](D:/codex/0000_26qs/results/official_eval/2026-10-23_diag_wall_jobcpu_test2-test3_17f9361_r02/00_report.md) | 完成40/40次；不采内存，Job CPU和墙钟分列 |
| [普通启动墙钟第03轮](D:/codex/0000_26qs/results/official_eval/2026-10-23_diag_normal_wall_test2-test3_17f9361_r03/00_report.md) | 完成40/40次；不采Job CPU或内存 |
| [test2阶段墙钟第04轮](D:/codex/0000_26qs/results/official_eval/2026-10-23_diag_test2_phase_wall_17f9361_r04/00_report.md) | INCOMPLETE_STOPPED；有效0/20，worker未返回指标 |
| [test2阶段墙钟第05轮](D:/codex/0000_26qs/results/official_eval/2026-10-23_diag_test2_phase_wall_17f9361_r05/00_report.md) | 完成20/20次；原始与网表输出窗口后处理派生记录都保留，未启动ETW/WPR |

诊断的重复样本、均值、中位数和阶段归因只用于各自报告，不能替换、平均或混入V8正式单次门槛。现有两个诊断ZIP、旧共享自检缓存和原ASCII工作证据均已按台账迁入英文路径，内容哈希保持；不能因为工程FAIL删除1038或其他失败现场。

## 证据与资料位置

V8轮次内的 `01_meta` 记录构建/身份，`05_public/round01` 保存同次正式产物，`09_performance/round01` 保存账本与摘要，`10_selfcheck` 保存证明/探针，`11_summary` 保存manifest、逐例结果与全量哈希。2136及诊断按各自英文目录读取，原报告正文保留历史路径，由迁移台账定位。

赛题原件主位置为 [D:/codex/02_嵌赛/赛题说明](D:/codex/02_嵌赛/赛题说明)；工程旧 `赛题/` 的同名文件和两份独有原件按授权核对迁入此处。第00～18号记录及V8实施材料保留原文；旧来源路径在历史正文中不全盘替换。

V7及以前不被V8使用的运行产物、工具和活动说明按2026-10-24 [清理方案](D:/codex/02_嵌赛/清理的方案.md)清单处理；其说明、原路径、日期和原判定集中于 [旧版本说明](D:/codex/02_嵌赛/旧版本说明.md)。旧目录名的official不构成官方认可。日后新轮次仍在 `results/official_eval` 独立建目录，不覆盖或自行清理既有证据。

新增五例现已取得并纳入九例清单，单例logic_units不增加门禁随本次接入实现；九例新结果不覆盖或拼接历史四例结果。7.1范围及计量接受性等待确认问题继续参考第18号原文，本轮实测状态参考第19号记录。

## 英文路径迁移

本次迁移不重算任何历史结论。原导航已保存到 [navigation_before.md](_migrations/20261025_ascii_layout/navigation_before.md)，完整路径与哈希见 [迁移台账](_migrations/20261025_ascii_layout/manifest.json)，操作说明见 [迁移记录](_migrations/20261025_ascii_layout/README.md)。新轮次综合在自身英文目录内执行；EQY使用受管理短根并在轮次保存核验归档，不创建随机桥接目录；历史工作证据已归入所属轮次或 _shared_evidence。旧自检缓存保存在 official_eval/_history/selfcheck_cache_v8.json，活动缓存 official_eval/_cache/selfcheck_v8.json 中的旧四例条目不适用于本次九例新指纹，须以本轮真实自检记录为准。
