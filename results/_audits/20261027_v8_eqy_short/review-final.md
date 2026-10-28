# V8 短 EQY 接入最终只读复核

结论：在本次约定范围内未发现尚未解决的阻断缺陷。前次审查指出的负例前提门禁缺失已修复，可继续由父任务完成统一测试及已获授权的单次正式验证；本结论不代表正式九例验证已经通过。

本次实际重新阅读 runner/eqy_workspace.py、run_selfcheck.py、validate.py 的初始化/归档/缓存/异常分支、report_v8.py 的归档门禁及新增集成测试。未启动任何工具、测试或正式流程，未修改工程文件。

## 修复与语义

run_selfcheck.py:128 已对 REJECT 增加全部 noDF verdict=PREMISES_SAT 的要求，同时保留真实FAIL、干净退出、无ERROR及VALID探针门禁。混合分区UNSAT不能再被其他分区的真实反例掩盖。runtime-report.md记录该项RED两失败→GREEN九测试；该日志说明已读取，非本审查独立执行。

18主链映射、postABC绑定、test3模板覆盖/maxsteps16、depth5、原有超时及历史六链兼容的前次结论不变，未见改变算法或证明对象语义的新增实现。

## 归一化与异常边界

- 身份路径使用Windows normcase/normpath，文件复制使用二进制流，路径比较不会改写证明输入内容。
- 路径预算同时覆盖实际绝对长度与未消去../的cwd拼接长度；setup后的实际分区引用需存在且包含在work内。
- BuildError与工具身份早退仍进入finally；阶段中断/超时由execute结束子进程树并wait后进入归档。异常不触发补采样。
- 当前归档最终报告同时要求verify_archive通过及01_meta/eqy_archive.json中ok为true，单有可验证manifest不能掩盖归档最终状态失败。
- 归档解析不依赖外部workspace存在。formal缓存更新只发生在本轮归档成功后；命中要求摘要hash、checks名字完整性及源轮归档有效。指纹不含单轮workspace路径，保留后续轮次复用能力。
- 本结论针对正常控制流、工具失败、可捕获异常及中断；不可捕获进程强杀或磁盘完全不可写不作为软件可保证成功归档的情形。

## 已读取证据与待完成事项

- tests-all.log末尾实际记录：Ran 171 tests in 38.884s，OK (skipped=1)。这是既有日志，不是本次独立复跑。
- smoke-launch.log实际记录：SELF_CHECK_RC 0、MERGED_SMOKE_RC 0、ARCHIVE True；JSON中archive_verified=true、formal_synthesis_runs=0、official_cases_synthesized=0。
- 新增archive-only缓存正向测试代码已阅读，包含隐藏外部workspace后缓存仍有效、篡改归档后缓存失效；其新增后的统一全套运行结果尚待父任务取得。
- 正式单次run及资料第20号记录仍由父任务完成，本审查未将其计为已执行。
