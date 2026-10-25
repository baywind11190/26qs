---
name: pmux-stable-validation
description: Windows原生V8当前四例内置验证；先validate_windows_v8.cmd只读plan，授权后run。同次采集墙钟与主进程峰值，当前正式综合8次；规则以同目录POLICY.md为准。
---

# Windows V8 当前入口

本技能仅用于用户明确要求验证精确算法提交时；讨论方案、审查或编写文档时不得启动正式验证。唯一规则正文为 [POLICY.md](D:/codex/0000_26qs/scripts/pmux_validation/POLICY.md)，执行说明见 [README.md](D:/codex/0000_26qs/scripts/pmux_validation/README.md)。历史操作见 [旧版本说明](D:/codex/02_嵌赛/旧版本说明.md)，不启动旧WSL或独立插件入口。

## 预检与执行

在 **Windows PowerShell** 调用固定入口：

```powershell
& 'D:\codex\0000_26qs\scripts\pmux_validation\validate_windows_v8.cmd' plan 17f9361099dcda757c16bb81caa18ddb52d74c4e --integration-profile p3-local-lut
```

替换为用户指定的完整40位算法Git提交；分支名、项目HEAD、源码或二进制SHA不得冒充算法提交。`p3`为早期内置PMUX调用；`p3-local-lut`增加ABC9后、map_cells前7.1调用。目标含已登记7.1补丁时必须选后者，补丁哈希参与构建缓存身份。

`plan`只读，不写文件、不建目录、不编译。核对 `policy_source`、集成、工具路径/身份、缓存复用或构建原因、`builtin_plan.blocked=[]`及当前四例 `formal_synthesis_expected_runs=8`。阻断时停止，不自动刷新清单、切分支或退回插件。

仅在用户已授权正式验证时，将同一命令中的 `plan` 改为 `run`。匹配缓存复用；未命中按精确提交在隔离树构建并登记READY。准备/身份失败保留诊断，不能启动验收或复用半成品。工作区改动不替代冻结提交，不自动checkout/pull/reset/clean、提交或推送。

## V8必须保持的边界

- 当前test1～test4每例原版后优化版各一次，共8次正式综合，同次采集Measure-Command墙钟、退出事件主进程峰值及功能/资源网表；不预热、不平均、不补跑、不自动追加诊断。
- 墙钟含同次调试、请求/响应及网表/stat输出，名称和原始Ticks/毫秒保持墙钟；构建、自检、EQY和事后分析独立。内存只看同一yosys.exe，退出事件读取成功后放行，原始字节保留；任何事件、PID、读取、放行或产物异常均停止。
- 原始RTL到两侧本轮post_abc.il分别证明，哈希绑定正式产物；保留dffeas-v3支持配置预检、严格noDF转换/前提SAT探针和test3合并证明/覆盖核对。缺证明、TIMEOUT或UNPROVEN不能算PASS。
- 资源用最终映射网表，逻辑单元=LUT+独立NOT输出位；DFF、IO及其他硬件按类型并集检查。四例缩减率算术平均10%为基本目标，20%数值档另报；时间/内存逐例分别比较5%及15%，不混算轮次，不推算中间官方分数。
- 运行或证明失败保留现场并停止，修复后另开轮次；不覆盖、筛选失败样本或以其他轮次PASS改判。

## 英文路径与证据位置

布局版本为ascii-v1，新轮次在 `results/official_eval/YYYY-MM-DD_HHMM_<label>_<commit7>_rNN`，label默认v8_same_run且仅ASCII字母、数字、下划线、连字符；主报告00_report.md。阶段为01_meta、02_assets、03_runner、04_flowcheck、05_public、09_performance、10_selfcheck、11_summary。输出根路径解析后必须为安全ASCII且无空格；不合规则在plan/run写入前阻断，不创建随机桥接或链接替身。EQY直接在本轮最终work/merged路径执行，保留所有失败/超时/中断证据；inputs预检和正式post_abc哈希绑定不变。

活动自检缓存为 `results/official_eval/_cache/selfcheck_v8.json`，旧缓存原文在_history/selfcheck_cache_v8.json。新缓存从空entries开始，代码与路径变化后的旧指纹不得伪造复用。历史证据迁移保持原字节及原判定，原日志/上下文/规则快照/ALL_SHA256不全盘替换；通过 `results/_migrations/20261025_ascii_layout/manifest.json` 将旧绝对、相对及共享桥接路径定位到新位置。迁移检查不构成新的正式run或历史结果改判。

## 报告与限制

中文汇报实际提交/集成、复用或新建构建、每例两侧功能状态及证明方法、模型/探针、资源与平均缩减、逐例墙钟和峰值开销、完整性、工程/交付/就绪状态、未完成项及主报告路径。具体字段和判定遵循POLICY。

既有V8：0117失败且正式综合0次，0121 FAIL（test3 +15.021%、test4 +13.284%），1038 FAIL（test3 +16.909%），1232该轮PASS。完整证据链接及2136前身、五个诊断轮次见 [results导航](D:/codex/0000_26qs/results/README.md)，全部保留且不混算。

交付 `NOT_RUN`、官方认可 `NOT_CLAIMED`；新增用例 `WAITING_OFFICIAL_CASES`。新增用例接入、单例logic_units独立门禁以及7.1/计量接受性待确认，见 [第18号记录](D:/codex/02_嵌赛/验证流程版本更新说明/18_1022答疑与V8符合性核对及待确认问题_20261023.md)。赛题原件主位置为 [资料目录赛题说明](D:/codex/02_嵌赛/赛题说明)。当前四例不等于官方效率全集，本地PASS不等于官方验收。
