# Results ASCII layout migration — 2026-10-25

状态：已完成。用户批准的全英文命名和取消随机桥接方案已实施。

## 完成内容

- 当前结果入口为 `results/official_eval`，导航为 `results/README.md`。新轮次使用 `YYYY-MM-DD_HHMM_<label>_<commit7>_rNN`，默认label为 `v8_same_run`。
- 新上下文为 `ascii-v1`；正式输入直接读取冻结RTL，EQY直接写最终work/merged，不再创建随机桥接或回拷目录。
- 历史10轮、2个ZIP、旧缓存以及6个有内容的ASCII工作树已归位；只有2个原本为空的随机根目录删除，无原始证据文件删除或去重。
- 新活动缓存 `_cache/selfcheck_v8.json` 的 entries 为空；原缓存按原字节保存在 `_history/selfcheck_cache_v8.json`。
- 报告正文、原日志、脚本/规则快照、原配置、原ALL_SHA256和ZIP内容未改写。历史字符串仍记录原执行路径，通过本台账定位，不能据此直接重跑旧脚本。

## 验证结果

- [完整台账](manifest.json)：20,746原文件，306,402,266字节，3,378原目录记录；源路径、目标路径、大小、SHA-256、Git跟踪状态和空目录拓扑均登记。
- [迁移后验证](verification.json)：20,746文件全部存在且原字节SHA-256一致，缺失0、变化0；除批准的2个空随机根外，原目录拓扑都有对应位置。
- [迁移前](legacy_hashes_before.json)与[迁移后](legacy_hashes_after.json)旧清单验证：9份ALL_SHA256中10,921条全部匹配，异常0。没有刷新旧清单来掩盖变化。
- [测试日志](tests.log)：120项测试通过，包含英文命名、路径阻断、原位证明错误/超时/中断、证明输入绑定、迁移冲突/恢复/定位/旧清单。
- [原生冒烟摘要](smoke_results.json)与[日志](native_smoke.log)：现有小型RTL正例实际PASS，负例实际FAIL且满足REJECT预期，noDF前提均为SAT。工具身份与配置指纹相符；完整临时冒烟现场路径见摘要。这不是正式四例验收。
- [迁移后V8只读plan](plan.log)：blocked=[]，baseline/optimized均reuse，build_required=false，formal_synthesis_expected_runs=8，规则来源SHA-256为 `4bb8538650c7a00d275e588b8e37e22d8cc227949269a39f68c5cf5bd63758aa`。
- 最终结果树无非ASCII名称、_eval_ascii_*、_eval_formal_*或目录链接。当前配置68个绝对路径存在，当前导航链接已核对。
- 算法源码及官方输入无差异；核心资源、交付和功能判定函数的AST与修改前一致。
- 正式四例run：**NOT_RUN**；正式公开例综合实际0次。未构建工具、未提交/推送/重置Git，上次清理的未提交差异保留。

## 历史工作目录归属

| 来源 | 迁移位置（相对于official_eval） |
|---|---|
| 0117、0121、1038、1232桥接 | 对应英文轮次/legacy_workspace |
| ad2d9c12a5fb4d76b6f29d3f682309e4共享桥接 | _shared_evidence/2026-10-22_1823_v7_17f9361 |
| _eval_formal_17f9361_20261022 | 2026-10-22_2136_same_run_pre_v8_17f9361_r01/legacy_formal_workspace |
| 0200a46df60a407caa4ca8f9cbe5f629、9f8aac09f39e4fcda8b1524a6aa157e8 | 执行时再次确认为空后删除 |

同内容证据按各自完整路径保留，不能按文件名或哈希合并。旧根导航原文保存在 [navigation_before.md](navigation_before.md)。[operations.jsonl](operations.jsonl)按台账文件索引记录20,746次移动；台账原始字节SHA-256为 `0c6a7d71e94186420aed20c1685a1440fbc88afab79ed8a65419c5ddf29a1f3d`。

## 只读查询及校验

以下命令使用 Windows PowerShell，固定工程Python；仅定位/核对，不生成轮次、不综合。退出0表示核对通过；退出2或抛错时停止，不修改原证据或原哈希清单。相对路径的 --base 是旧目录，不是旧文档文件名。

```powershell
$asciiPython = 'D:\codex\0000_26qs\.tools\msys64\mingw64\bin\python3.exe'
$asciiMigration = 'D:\codex\0000_26qs\scripts\pmux_validation\migrate_results_layout.py'
& $asciiPython -B $asciiMigration verify
& $asciiPython -B $asciiMigration verify-legacy
& $asciiPython -B $asciiMigration resolve --path 'D:/codex/0000_26qs/results/_eval_ascii_094ada9a41454b0ba3f987f84e615345/chains/test1.v'
& $asciiPython -B $asciiMigration resolve --base 'results/官方口径评测/2026-10-23_1232_Windows同次墙钟与峰值内存_v8_17f9361_第01轮' --path '00_本轮验证结论.md'
```

迁移前后哈希检查相互独立：`verify`核对迁移台账，`verify-legacy`用旧路径映射核对原ALL_SHA256。已有台账时不得重建plan覆盖它。apply允许在源或目标唯一存在且哈希正确时恢复中断，源目标同时存在或内容变化即拒绝；rollback仅逆向恢复历史文件及原目录，不撤回当前代码/文档，也不删除后来生成的文件。不要用Git重置回滚本次工作。

路径安全边界：当前工程输出根为纯ASCII、无空格和shell特殊字符；不新增空格根路径支持。不同工具的既有安装路径按现有调用方式使用，工具目录本身没有迁移。

## 当前修改与Git身份

工程HEAD仍为 `fe24325b5b585119e56ddf84f1a811ffdd8598a8`，资料HEAD仍为 `a93787654ac54c4e51acaa04387c0b8cf57afc69`。工作直接在用户指定现有目录实施，无新分支/工作树；新增台账、工具和测试为本轮差异，原有清理差异没有重置。

