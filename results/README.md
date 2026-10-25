# PMUX 结果目录导航

当前唯一执行入口为 [Windows原生V8](D:/codex/0000_26qs/scripts/pmux_validation/README.md)，规则正文为 [POLICY.md](D:/codex/0000_26qs/scripts/pmux_validation/POLICY.md)。本页只索引既有证据，不启动实验，也不把不同轮次合并为一个结果。

## 四个V8入口轮次

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

新增用例 `WAITING_OFFICIAL_CASES`，固定四例接入及单例logic_units独立门禁尚待适配；7.1允许范围和计量接受性等待确认问题统一看 [第18号记录](D:/codex/02_嵌赛/验证流程版本更新说明/18_1022答疑与V8符合性核对及待确认问题_20261023.md)。本地四例PASS不等于官方效率全集或最终验收通过。

## 英文路径迁移

本次迁移不重算任何历史结论。原导航已保存到 [navigation_before.md](_migrations/20261025_ascii_layout/navigation_before.md)，完整路径与哈希见 [迁移台账](_migrations/20261025_ascii_layout/manifest.json)，操作说明见 [迁移记录](_migrations/20261025_ascii_layout/README.md)。新轮次在自身英文目录内执行，不再创建随机桥接目录；历史工作证据已归入所属轮次或 _shared_evidence。旧自检缓存保存在 official_eval/_history/selfcheck_cache_v8.json，新活动缓存 official_eval/_cache/selfcheck_v8.json 为空，须按新指纹真实自检。
