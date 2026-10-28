# V8 短 EQY 接入审查

本次为只读源码审查，未启动 EDA、正式验证或单元测试；只写本文件。工程 HEAD 实查为 32fb6dd978068034436161c1103011d89fce328c，与 baseline.json 一致。已有九例/历史清理工作树改动未作为本次缺陷。

## 阻断问题

1. `runner/run_selfcheck.py:judge` 的 REJECT 分支缺少 noDF 前提 SAT 门禁。该分支要求至少一个干净 rc=0 的 FAIL，最后只要求 `valid_probes`；而 `function_common.classify_probe_result` 对干净完成的 PREMISES_UNSAT 同样返回 VALID。因此一个多分区负例即使其他分区前提 UNSAT，也可被接受。最小复现场景：分区 A 为 FAIL/rc0/noDF SAT，分区 B 为 PASS/rc0/noDF UNSAT，所有 errors 为空，当前 judge 返回 True。与接口约定“noDF SAT must be valid”不一致。建议 REJECT 同时要求全部 noDF verdict 为 PREMISES_SAT，并增加此混合分区回归。已即时通知 parent。

## workspace 子任务：规格与质量审查

- case_map 按 cfg.official_cases 顺序生成，不受历史三例固定表限制；selfcheck_map 按 checks 生成。创建拒绝覆盖；job_dir核对冻结身份；路径身份比较采用ntpath规范化。
- stage_input 对源绑定、字节哈希和长度检查，禁止同名不同源；不会归一化输入文本。
- check_work 检查实际分区与SV/IL覆盖，以及策略脚本引用真实文件；同时检查原始cwd拼接长度和解析后绝对长度，实际分区检查发生在setup之后。
- archive 使用copytree保留空目录，复制前后逐文件核对；verify_archive严格比较文件集、空目录集与SHA/size；resolve_evidence使用归档映射，不依赖外部workspace存在。
- legacy eqy_recheck_support 公共接口仍在，固定c01/c02/c04映射保留，公共检查/归档委托manager。
- 除上述runtime问题外，本次未发现workspace实现的具体阻断缺陷。

## runtime 子任务：规格与质量审查

- managed主链来自 S.context_cases 的全部用例，每例两条I.CHAINS；18链路径均经case_map分配，legacy TARGET_CASES仅限显式functional_recheck。
- 正式输入仍绑定post_abc；配置、setup、分区及合并作业在短路径执行，正常摘要和哈希清单仍在轮次目录。
- test3合并覆盖核对、maxsteps16、600/120超时保留；分区depth5和selfcheck300保留。
- proof非零返回/ERROR和probe非零返回/ERROR不能被判为成功；负例须有真实FAIL，工具错不再冒充REJECT。但REJECT的SAT门禁遗漏需修复。
- setup后实际分区集合与结果集合核对，缺失结果不能通过。

## 跨模块核对

- workspace在prepare前创建。prepare_builtin返回builtin身份，configure_windows_runtime只改变环境变量，不更改cfg.tools，因此目前未发现prepare前后workspace tools绑定失配。
- orchestrator finally覆盖build失败、身份检查早退及阶段异常。execute捕获中断/超时并终止进程树、等待退出后返回，归档在其后执行。
- report_v8以verify_archive为独立门禁，并通过resolve_evidence逐条核对归档postABC与正式样本hash；外部workspace删除不影响这部分读取。
- formal缓存指纹包含manager/runtime快照哈希与版本/根/路径限值，不包含单轮workspace路径，允许同规则后续轮次复用；命中还要求源轮自检摘要SHA、检查集合和完整归档。旧无归档缓存不能误命中。

## 未实测范围

未执行新测试、真实工具或正式run。parent/runtime agent正在完善测试，本审查不将其尚未收到的结果写为通过。上述问题修复后应由parent核对新增回归与集成结果。
