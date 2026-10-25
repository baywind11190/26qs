# Windows 原生 V8 验证规则

本文件是现行正式验证规则的唯一正文，位置为 `D:\codex\0000_26qs\scripts\pmux_validation\POLICY.md`。V8同次采集规则形成于2026-10-23；2026-10-24按已授权清理方案收拢活动说明，保留现行计量、资源、证明、构建、身份和失败判定，不回算历史结果。轮次内 `POLICY.md` 是当轮原文快照，来源路径及SHA-256写入 `validation_context.json` 的 `policy_source`，不得覆盖旧快照。

## 来源、范围和限制

- 赛题及官方答疑主位置统一为 `D:\codex\02_嵌赛\赛题说明`。主要来源为题目原文及1008、1020、1022答疑；[第18号记录](D:/codex/02_嵌赛/验证流程版本更新说明/18_1022答疑与V8符合性核对及待确认问题_20261023.md)保留逐条核对、代码缺口和待确认问题。
- C21/C25：面积按逐例逻辑单元缩减率取算术平均；DFF单独检查，不硬性要求缩减，但不应增加。C24/C37、1020第106行：使用官网Yosys 0.69、Windows `yosys.exe`，优化pass编进主程序并由 `synth_intel.cc` 调用，不使用独立插件代替内置验收。官方未指定精确源码提交或二进制哈希，本地须记录真实构建身份。
- C22/C23/C53：两侧必须使用内置ABC9，不得换为ABC。1020第101/104行允许基于Yosys 0.69调整ABC脚本和techmap；这是许可，不是必须修改。1022第114行禁止通过优化其他pass或依赖程序抵消PMUX增加的时间；7.1对一般LUT4网络的局部优化是否允许，仍待官方确认，不能仅凭pass名称认定。
- C87/C90～C92要求相对原版、单次运行、综合全流程及同版本同环境比较。1020第102行允许PowerShell `Measure-Command`，无需补充Yosys计时代码。本地按用户确认将墙钟经过时间用于早期“CPU时间”要求的等效比较，实际字段仍标为墙钟时间。该解释和同次调试采集实现不代表官方已明确认可。
- 1020第105行确认相关效率指标不超过原版5%得效率满分，任一用例超过原版15%不计效率分；5%～15%的中间评分未说明，不推算官方分数。C37的60秒/2GB及原版超限例外单列记录。
- 1022第115行说明将新增3～5例，新增例计入全部用例平均优化率且逐例资源不增加，cells以输出网表统计。当前已获得test1～test4，正式综合8次；官方用例总数变为N时目标为2N次。当前固定四例接入代码及单例 `logic_units` 增加的独立门禁尚待适配，本次清理不修复这些缺口，也不把四例当成官方效率全集。新增输入尚未取得时记 `WAITING_OFFICIAL_CASES`，不自行编造。
- 1022第116～117行推荐Windows exe；本项目继续选原生Windows，不启动旧WSL流程。默认范围是当前四例所需的来源、调用、功能、资源、时间、内存及报告，不自动扩展回归、H2、随机、规模、多驱动、FPGA/eLinx或稳定性诊断。

## 当前入口与执行边界

入口为 `scripts/pmux_validation/validate_windows_v8.cmd`，固定加载 `config.windows.v8.json`；方案标识为 `pmux-perf-single-powershell-same-run-exitpeak-v8`，套件为 `official4-v1`。Yosys是电路综合工具，EQY是从真实输入证明功能等价的工具。使用完整40位算法Git提交；算法提交、项目HEAD、源码SHA-256、二进制SHA-256分别记录，不能互换。

先执行只读 `plan`，核对 `policy_source`、算法身份、集成选项、将复用的工具、`build_required`、预计正式综合次数及 `builtin_plan.blocked`。当前四例应为 `formal_synthesis_expected_runs=8`，`blocked` 必须为空。`plan` 不创建目录、不写文件、不编译。只有用户授权执行验证后才启动 `run`；工具构建属于已授权run的准备步骤，耗时不计入综合性能。

入口绝对指定固定Python；Bash/make/Python优先使用项目工具环境，清除冲突的Python/Bash环境变量并保留系统目录。预检记录关键工具实际路径、版本及SHA-256。只在Windows运行综合、EQY和计量；缺失依赖、身份不符或自检异常时停止，不回退Linux工具或独立PMUX插件。

## 两种内置集成及工具准备

- `--integration-profile p3`：集成身份 `pmux-opt-inline-p3-v1`。优化侧在 `synth_intel.cc` 的 `fsm; opt` 之后、`wreduce` 之前调用 `pmux_opt` 恰一次；原版无PMUX调用，不插入局部LUT调用。
- `--integration-profile p3-local-lut`：集成身份 `pmux-opt-inline-p3-local-lut-v1`。在上述早期调用之外，优化侧在ABC9、清理及命名完成后、厂商 `map_cells` 之前调用 `pmux_opt -lut` 恰一次。含已登记7.1补丁的提交必须选择此项；遗漏选项、补丁缺失或不被识别时预检阻断。补丁从目标Git提交冻结，记录SHA-256，并参与候选缓存键；实际日志须核对两个调用及导出边界。
- 两侧均为可追溯的Yosys 0.69，外部综合脚本逐字节相同，直接调用 `synth_intel -family cycloneiv`，只切换可执行程序。保留两侧基础提交、构建参数、编译器、Yosys/ABC身份、工具数据及插入调用证据；两侧二进制哈希无需相同。
- baseline优先复用已登记构建，核对基础提交、构建参数、编译器、二进制和ABC；不满足时按与候选一致的条件构建。optimized按缓存键查找配置命名空间的 `registry/`，`--builtin-cache-dir` 可覆盖命名空间。缓存键绑定算法源码哈希、Yosys基础提交、集成模板/补丁、关键构建参数、编译器与公共依赖身份，命中还须核验ABC源码身份和产物哈希。两种集成分别保持身份及缓存语义。
- 缓存未命中时，从本地已知基础提交建立隔离源码树，逐字节提取目标提交 `src/pmux_opt.cc` 到 `passes/opt/pmux_opt.cc`，按固定模板幂等集成；锚点不符立即停止，不盲目替换。CMake Release构建后以版本、`help pmux_opt`及小型综合冒烟验证，再登记READY。不得用工作区当前算法替换请求提交。
- 构建锁防止同一缓存并发写入；缺二进制、源码改动、哈希不符、半成品不得命中。失败保留FAILED诊断及日志，不发布完成标记，不复用失败缓存，不移动或覆盖既有构建，不自动退回插件方案。
- 准备后再次检查两侧二进制与登记指纹、优化构建源码与请求提交源码哈希、登记集成diff；baseline要求源码无未提交改动。身份失败为 `BUILTIN_NOT_READY`，准备失败为 `BUILTIN_BUILD_FAILED`，均不启动验收进程。两侧解析路径、指纹和准备记录写入轮次 `validation_context.json` 的 `builtin`/`builtin_prepare`，各阶段统一读取，不因运行改写仓库配置。
- 可复用身份匹配且无V6内部CPU计量补丁的旧Yosys构建；V8测量自检使用自己的指纹和缓存，不能继承旧计量合格结论。名称含旧版号但仍由V8实际使用的构建、registry、来源清单和日志必须保留真实路径及原字节。

## 输入、清单和自检

四例及自检素材由 `suite-official4/manifest.json` 冻结并逐文件记录SHA-256，后续算法提交不自动更换四例输入。预检核对关键工具（Yosys、yosys-config、ABC、EQY、Z3、编译器）、实际依赖的工具数据与 `PACKAGE_SHA256.json`。完整工具数据清单供审计；清单与实际内容不一致、缺失或存在未登记活动文件时停止，不静默刷新指纹。缺Git对象先查明来源，需获取时另按授权操作。

正式综合前完成工具、形式化正负例和V8计量专用自检，不使用公开四例预热；流程一致性在八次正式产物上只读分析，不再额外跑公开四例。自检证据按工具、配置、模型/策略版本、形式模型、测量脚本、固定输入和流程代码指纹核对复用，变化即失效，缺证据不能假定已自检。核对原始证据哈希及实际结果，不能只读 `ok=true`。工具自检不等于算法验收或官方精度认可。

## 八次正式综合与同次计量

1. 当前四例顺序test1→test4，每例原版后优化版，各一次，整轮正式综合8次。不预热、不平均、不取中位数、不补跑、不剔除样本，不默认追加80次或其他重复诊断。
2. 同一次Yosys运行同时产出 `Measure-Command` 墙钟、退出事件主进程峰值、功能输入 `post_abc.il`、完整映射 `mapped.il` 和stat。`post_abc.il` 在ABC9后、厂商 `map_cells` 前导出；局部LUT集成须在7.1之后导出。脚本按阶段边界完成中间导出再继续映射，两侧脚本相同。
3. 时间保存原始 `TimeSpan.Ticks` 和 `TotalMilliseconds`，名称为墙钟经过时间。包括RTL读取、ABC9、PMUX调用、中间/最终网表和stat写出、退出收尾、同次调试观测及本机请求/响应包装开销，不作扣除。PowerShell/worker初始化、工具构建、专用自检、EQY和事后分析不计入。
4. 内存只统计同一 `yosys.exe` 主进程。在匹配根PID的 `EXIT_PROCESS_DEBUG_EVENT` 中调用 `GetProcessMemoryInfo`，读取系统累计 `PeakWorkingSetSize` 后再 `ContinueDebugEvent` 放行最后清理；原始单位字节，MiB=字节/1024²。不加ABC、EQY、编译器或进程树。调试可能影响运行及内存布局，结果明确属于同次调试观测运行。
5. 根PID、完整退出事件、成功读取、正数读数及成功放行缺一即无效，不回退轮询值或退出后读取值。启动断点只处理一次，程序自身异常交还Windows，不吞崩溃；超时终止本轮Job并处理待决调试事件，不影响其他任务。
6. 样本必须 `metrics_valid=True`、存在且无 `measurement_error`、`rc=0`、`timed_out=False`，stat/网表/日志存在且完整，时间和峰值为有限正数。同时核对根进程调试、完整退出/输出、内存采集、time/memory根PID一致、内存方法及产物哈希；PowerShell须为5.1且实际程序身份匹配，Ticks与毫秒一致。缺字段须指出具体样本及字段，不能以部分有效样本判通过。
7. 任何正式调用或样本失败、超时、缺事件、PID不符、读取/放行失败、输出不完整或统计不匹配，保留现场并停止，不补跑。性能阶段保护上限30分钟，超时保护不是评分公式。
8. 八次完成后，调用/阶段/资源只分析这八次产物，EQY随后独立证明。原始测量先保存为待验证，调用或证明未通过不得给验收PASS。取消的独立完整/分段资源对照标 `NOT_RUN`，不把日志分析写成独立综合对照PASS。两侧脚本、冻结输入和工具身份逐例核对，正式样本、调度账本和性能摘要必须一一对应且无额外综合；局部LUT调用/阶段/证明与输入哈希须完整闭合。

同次采集是用户确认的本地规则。官方第54行明确峰值工作内存只看 `yosys.exe`，第91/92行答复单次计时，未指定必须同次、调试实现、请求/响应包装或当前导出边界，接受性仍待确认。题目写2GB，本地绝对阈值按2GiB，保留原始字节与单位差异。

## 功能证明：模型与noDF策略

- 主链为 `c4a_rtl_opt_mapped` 和 `c4b_rtl_base_mapped`，分别从原始RTL对比本轮优化侧及原版 `post_abc.il`；链名为兼容保留，`formal_netlist_stage` 必须为 `post_abc`。两侧分别独立生成、运行、记录，EQY实际输入SHA-256必须逐例匹配同次正式综合导出的网表；不能推断“两链同结果”，不能复用旧PASS代替新提交证明。
- 功能输入使用Yosys内建 `$lut` 语义及受支持的 `dffeas` 模型，拒绝最终 `cycloneiv_lcell_comb` 冒充功能输入。最终映射网表用于资源统计，不混淆阶段。
- 模型 `dffeas-v3`：保留 `clrn` 异步清零、`ena` 时钟使能及 `power_up` 初值。运行前由 `runner/precheck_supported_config.py` 检查 `power_up∈{low,high}`、`prn=1`、`asdata/aload/sclr/sload=0`、`clrn/ena` 端口存在；未知单元、参数或端口值阻断。无 `dffeas` 的纯组合设计合法。不支持时记录 `MODEL_UNSUPPORTED`，不删条件、不改输入强行证明。
- 策略 `noDF-local-r1`：EQY setup（`eqy -m`）只生成分区及脚本，随后严格转换，仅删除恰一处 ` -set-def-formal`，其余逐字节不变。格式不符停止；保留 `-set-init-undef`、`-set-def-inputs`、`-set-assumes`、断言及未定义值比较语义。noDF前提探针必须SAT才算真实证明；DF前提仅记历史签名对照。探针只证明深度1初态前提可满足，不声称任意时刻可达性。
- test3保存EQY分区尝试及整设计无切割合并证明日志，两侧独立运行，合并证明须覆盖全部输出、匹配点和断言，模板与本轮实际分区集合核对。默认 `maxsteps 16`，证明执行上限600秒；未闭合如实记录，不盲目加深。其余用例保留分区路径。
- 成功判定须联合进程退出状态、完整成功标记、基例数≥归纳长度、断言导入覆盖、全文错误扫描及全部noDF前提探针SAT，不能只凭退出码0或一个SUCCESS字样。
- 分别记录 `PASS`、`UNPROVEN`、`TIMEOUT`、`TOOL_OR_CONFIG_ERROR`、`COUNTEREXAMPLE_REQUIRES_REVIEW`、`MODEL_UNSUPPORTED`、`PREMISES_NOT_SAT`、`METHOD_REVIEW_REQUIRED`、`NOT_RUN`；反例须复核工具、配置、假设和反例后定性，baseline同样失败不构成豁免。
- 当前内置主链缺证明或未全部通过时为 `NEEDS_REVIEW`，完整证明链 `NOT_CLOSED`。旧插件 `c1_local`/`c2_stage` 依赖的中间网表不在本模式内伪造，记 `NOT_APPLICABLE`；可选扩展链不能替代必需主链，也不自动扩大默认范围。

## 资源和效率判定

- 最终 `mapped.il`/stat统计LUT（`cycloneiv_lcell_comb`）、独立NOT输出位、逻辑总数、DFF（`dffeas`）、IO端口/位及其他全部cell类型、总cells。逻辑单元=`cycloneiv_lcell_comb`数+独立取反位，独立NOT按输出位宽核对；post-ABC `$lut` 数单列，不重复计入最终资源。
- DFF、IO端口/位和其他硬件按两侧类型并集逐项比较，缺少类型按0，优化侧新增类型不得漏检；未知类型、未分类单元或映射不完整不得判资源通过。`$not`/`$_NOT_`、LUT及VCC/GND属于组合逻辑或常量，单列，不冒充IO/DSP等其他硬件类别。
- 逐例缩减率=（原版逻辑单元−优化版逻辑单元）÷原版逻辑单元；已获得四例取算术平均。资源统计完整、硬件不增加和平均达到10%共同决定资源技术指标；`area_requirement_met` 为10%基本目标，`area_20pct_band_met` 仅为20%数值档，20%不是基本PASS门槛。不根据旧增量回归参照替代与未修改原版的正式比较。
- 面积使用未舍入值及1e-9个百分点量级浮点容差，不根据显示值改判，不推算中间评分。新增官方用例须并入同一范围，当前新增用例接入及逐例 `logic_units` 独立门禁缺口仍按第18号记录如实披露。
- 时间及内存各自逐例相对开销=（优化版−原版）÷原版；5%为本地目标，另报15%门槛，边界按不超过处理，不能跨例或跨轮平均抵消。V8以原始Ticks及字节整数比较，不用舍入后的显示百分比改判。绝对60秒/2GiB单列，原版对应指标已超限时保留C37原版超限例外，不自行发明扣分。原始时间、字节和两侧数据全部保存。

## 报告、状态及证据管理

每轮使用 `results/official_eval/YYYY-MM-DD_HHMM_<label>_<commit7>_rNN` 独立目录，默认label为 `v8_same_run`，仅允许英文字母、数字、下划线及连字符；同名前缀的轮号递增，禁止覆盖。布局版本为 `ascii-v1`。主报告为 `00_report.md`，配 `11_summary/manifest.json`、逐例汇总、全部必要原始证据和 `ALL_SHA256.txt`。报告说明实际集成、复用/新建构建、算法/源码/工具/输入身份、正式运行计数、每例两侧功能状态和方法、资源与平均缩减、时间、内存、证据完整性及未完成项，不层层复制结论。

轮次阶段统一为 `01_meta`、`02_assets`、`03_runner`、`04_flowcheck`、`05_public`、`09_performance`、`10_selfcheck`、`11_summary`；工具链与构建证据为 `01_meta/toolchain_evidence`。在plan及run写入前检查解析后的工程输出根路径为安全ASCII且无空格，不满足即阻断，不生成备用工作目录。正式综合直接读取本轮冻结RTL；EQY的work与merged在所属阶段最终证据路径原位执行，失败、超时及中断产物原位保留。阶段内规范命名的inputs仍完整检查八份两侧网表及模型，逐份绑定正式post_abc哈希，不弱化原支持配置预检。新流程不创建随机 `_eval_ascii_*`、独立 `_eval_formal_*`、ascii_bridge或相应目录链接，也不通过结束后的回拷保存EQY现场。

活动自检缓存为 `results/official_eval/_cache/selfcheck_v8.json`。路径及脚本变更会使旧指纹失效，新的活动缓存从空entries开始；历史缓存原字节保存于 `results/official_eval/_history/selfcheck_cache_v8.json`。不得重写旧指纹、沿用历史ok或修改证据路径后冒充重新自检；后续已授权run按新指纹完成自检再登记。

- `verification_verdict` 只覆盖本轮工程四例，`overall_verdict` 保留兼容含义并附scope。本地适用检查全部实际通过才能PASS，完整状态 `BUILTIN_FOUR_CASE_LOCAL_ACCEPTANCE_COMPLETE` 不等于官方认可。失败、缺测或待复核为 `NEEDS_REVIEW`，不能把未执行写成通过。
- `delivery_verdict` 独立检查C55源码、集成、必要ABC脚本、程序及依赖库和本地整套EQY包基本自检，使用与算法和当前ZIP SHA-256绑定的实测证据。基本自检只支持启动/基本运行声明，包内完整四例复现须另有实跑证据；新二进制不能继承旧包验收。
- 交付 `PAUSED`/`NOT_RUN`/`FAIL` 时 `project_readiness=NOT_READY`，当前所需检查全部通过才READY。交付未重新执行记 `NOT_RUN`；官方认可独立为 `NOT_CLAIMED`，设计答辩材料不由脚本自动判定。
- 功能、资源、时间、内存、工程、交付和就绪分别记录，一项PASS不抵消其他失败。退出码只说明流程状态，须结合主报告、manifest及实际证据。失败修复后另开轮次，不追加挑选样本，不与其他性能实验并行。
- 不自动checkout/pull/reset/clean、切分支、提交、推送或清理现有工作树，Git对象缺失时先查来源。普通新轮次不得删除旧轮次、失败现场、日志、CSV、网表或哈希清单。

## 历史和一次性清理边界

2026-10-24的明确授权仅按 [清理的方案](D:/codex/02_嵌赛/清理的方案.md)精确清单移除不被V8使用的V7及以前旧资产，历史说明归并到 [旧版本说明](D:/codex/02_嵌赛/旧版本说明.md)，不继续要求已列入清理的旧资产保留原位。V8实际依赖、全部V8轮次、0117失败、0121/1038 FAIL、1232 PASS、2136同次采集前身、五个直接诊断轮次及共享自检证据完整保留，不选择性只留PASS，不混算、不重算或改判。

2026-10-25用户明确授权将results文件系统路径统一为英文，并取消随机桥接目录。此一次性例外只改变路径：四个V8桥接整树归入各自轮次legacy_workspace，2136形式化桥接归入legacy_formal_workspace，共用旧桥接归入 `_shared_evidence/2026-10-22_1823_v7_17f9361`；只删除执行前再次确认为空的两个随机桥接根。历史日志、报告正文、validation_context、冻结脚本、规则快照、哈希清单及ZIP字节保持原文，不按新路径全盘替换，不按哈希合并不同证据副本。旧新文件和目录路径、大小、SHA-256与原Git跟踪状态登记于 `results/_migrations/20261025_ascii_layout/manifest.json`，历史绝对路径、相对路径及共享桥接引用通过迁移定位功能读取；当前导航使用新路径。原哈希清单经映射核对，不重建成“原清单”；历史快照作为证据保留，不承诺旧命令直接重跑。路径迁移检查不构成新正式验收，本次正式run为NOT_RUN。

本次范围不授权日后日常流程自行清理证据，V8及以后轮次原始证据和失败记录必须完整保留。旧版计量、WSL插件操作与已清理资产的原路径、来源、日期及原判定只在历史说明中查阅。第00～18号记录、V8实施材料和所有现存轮次内规则快照保持原文。
