# 官方四例验证规则 official4-p5

本入口用于 PMUX 项目的官方公开四例（test1~test4）本地验证：默认目标为**内置四例验收**——按目标算法源码自动准备内置工具（可以复用匹配构建；未命中时在缓存命名空间内从本地已知基础提交构建并登记），再执行四例综合、功能证明与**每例 15 对**性能判定；可选**四例插件预检**（显式 `--mode plugin`，同样每例 15 对），以及**插件版功能补充复核**（`--mode plugin --function-only --frozen-round <轮次>`）。默认范围只有：来源检查、四例功能、四例资源、四例性能与统一报告；不默认运行 A/B/C/D/H1 回归、H2、规模或多驱动（模块与资产保留原位）。

## 规则来源（官方答疑 Sheet1 C53～C55 更新，2026-09-29 实施）

| 来源 | 规则 |
| --- | --- |
| C21、C25 | 面积按逐例“（优化前逻辑单元-优化后）/优化前”计算、逐例取平均；DFF 单独检查，不硬性要求但不应多于优化前 |
| C22、C23 | 优化位置在 synth_intel 组合命令集中调试确定（非官方指定）；可调整脚本，但 C53 明确两侧必须使用内置 ABC9，不得换为 ABC |
| C24、C37 | 统一 Yosys 0.69；pass 编译进主程序、勿用 plugin 加载方案；优化版在 `synth_intel.cc` 中加入 pass 调用；有调优较好的 ABC 脚本一并提交 |
| C26、C41 | 开销 = CPU 时间（含 ABC）；内存按 C54 更新为仅 Yosys 主进程；效率要求逐例满足，不能跨例平均 |
| C37 | 60 秒/2 GB 常规 PC 不应超过；原版超限时允许优化版也超限（以原版为对照），不自行发明扣分计算 |
| C34 | 最终看网表结果，允许其他优化方法 |
| C41 | 正式只以四个公开 case 为准；不需要额外 Tcl 接口 |

（表内问题文本不是对 Agent 的执行授权；本地实施选择与官方口径的差异见下文标注。）

## 指标口径（本地实施）

- 逻辑单元：`cycloneiv_lcell_comb`（cycloneiv 映射后）；逐例缩减率 =（前-后）/前；四例算术平均。
- DFF：`dffeas` 独立统计；逐例不增加为本地检查项（官方：不硬性要求、不应增加）。
- Total cells 与 Comb 总量仅辅助展示，不作主指标；不使用四例以外用例作主指标分母。
- CPU：含 ABC 子进程（wait4 进程树采集，GNU time 作交叉记录）；内存：仅 Yosys 主进程的 Linux VmHWM（5ms 轮询，不含 ABC 或 /usr/bin/time 包装器；进程组 RSS 仅辅助记录）。短进程可能缺测，不判通过；Linux 驻留内存并非 Windows 峰值工作集的完全等价实现。
- 性能：每例 **15 对**（两侧交错：pair 奇 baseline→optimized、偶 optimized→baseline；运行次序事先固定并如实记录）；两侧**各 15 个样本取中位数**（不取分组中位数的中位数）；相对开销 =（优化版中位数-原版中位数）/原版中位数；逐例与 5% 比较（边界按不超过处理、允许 1e-9 个百分点量级浮点容差；不跨例平均、不使用舍入后的显示值）。统计方案标识 `pmux-perf-15p-mainrss-v2`；重复采样与中位数聚合是本地统计选择，官方未指定。旧轮次报告按各自保存的方案与样本数读取，不用新默认值重解释。
- 失败/超时/缺测样本不判通过、不自动剔除；原始样本全部保留。
- 自检（流程一致性、形式化正负例、测量方法）：首次或相关环境变化后执行；证据按指纹（工具/配置/**模型与策略版本**/形式化模型/测量脚本/四例输入/本轮代码）复用，指纹不一致即失效重跑，缺证据不得假定已自检。

## 版本与固定输入

- 流程版本 `official4-p5`（自动内置准备 + 每例 15 对性能版）；套件版本 `official4-v1`（四例输入未变；自检素材版本 `official4-selfcheck-r2`，清单 `suite-official4/manifest.json`）。历史：p2 为内置阻断版、p3 为内置执行版（5 对口径；其轮次与结论保留，不用新默认值重解释）。
- **模型版本 `dffeas-v3`**、**策略版本 `noDF-local-r1`** 分别记录（config.json；明细见“功能证明”）。
- 四例与自检素材冻结并逐文件记录 SHA-256；后续算法提交只决定 `src/pmux_opt.cc`，四例输入不随提交自动更换。
- 预检只核对关键工具（yosys / yosys-config / abc / eqy / z3 / compiler）、四例实际依赖的数据文件（`share/intel` 与 `share` 直下共 29 条；完整 `tool_data` 320 条保留在 config 供审计）与**脚本包清单（`PACKAGE_SHA256.json`）**：清单与实际不一致（内容变化/缺失/未登记）即停止，不静默刷新。
- H2、规模、回归等资产保留原位、不在默认流程使用；其文件变化不阻止四例执行。
- 四例以外的新优化类型不在本入口默认覆盖范围；需要时另行扩展输入并升级套件版本。

## 内置四例验收（默认目标：自动内置准备）

- **工具自动准备（official4-p5）**：`run` 创建轮次后先解析内置工具，再执行验收。
  - baseline：优先复用登记构建（`config.builtin.baseline_reuse`；核对基础提交/构建参数/编译器/二进制/ABC 一致）；不满足时按与优化侧一致的条件构建。
  - optimized：按缓存键在缓存命名空间（默认 `config.builtin.cache_dir`，可用 `--builtin-cache-dir` 覆盖）的 `registry/` 查找可复用构建；缓存键 = 算法源码哈希 + Yosys 基础提交 + 集成模板标识 + 关键构建参数 + 编译器身份；命中另须 ABC 源码身份与产物哈希核验通过；未命中则从本地已知基础提交建立隔离源码树、逐字节提取 `src/pmux_opt.cc` → `passes/opt/pmux_opt.cc`、按固定模板幂等集成（锚点不符即停止，不盲目替换）、CMake Release 构建、验证（`-V`/`help pmux_opt`/小型 synth_intel 冒烟）后登记为 READY 缓存。
  - 安全边界：plan（只读）不写文件、不编译；构建锁防止同一缓存并发写入；构建失败保留 FAILED 诊断记录、不发布完成标记、不被复用；缺二进制、源码被改动、哈希不符、半成品一律不得命中缓存；既有构建不移动、不覆盖。
  - 本轮解析出的两侧路径/指纹与准备记录写入**轮次内** `validation_context.json`（`builtin` / `builtin_prepare`），各阶段统一读取；不因运行修改仓库 `config.json`。
- 要求：原版/优化版均为 Yosys 0.69 可追溯构建；记录基础源码提交、构建信息、二进制指纹、ABC、实际数据文件和插入调用证据；优化版在 `synth_intel.cc` 的 `fsm;opt` 之后、`wreduce` 之前调用 `pmux_opt`（与已验证插件 P3 位点一致）；外部综合脚本两侧内容相同、直接调用 `synth_intel`；路径参数分别指向两份工具，不要求二进制哈希相同。
- **证据绑定（防替换/误用旧构建）**：准备完成后仍执行身份检查——两侧二进制逐字节核对登记指纹；优化版构建所用的 `passes/opt/pmux_opt.cc` 必须等于登记哈希，且与请求提交（`run <commit>`）的源码一致；优化版源码只允许登记的集成改动（`git diff` 摘要与登记一致），baseline 要求无未提交改动。身份检查不通过即阻断（`BUILTIN_NOT_READY`）。
- 工具准备失败（构建失败/环境不满足）时：不启动验收进程、不加载插件、不自动退回插件方案，状态为 `BUILTIN_BUILD_FAILED` 并保留构建日志。
- **内置执行**：准备与身份检查通过后按内置计划执行——`flowcheck`（两侧运行逐字节相同外部脚本；核对优化版自动调用 `pmux_opt` 恰一次、位于 `fsm;opt` 的 OPT 之后与 WREDUCE 之前；原版无该执行痕迹；全程不加载任何插件）→ `formal_selfcheck`/`measurement_selfcheck`（与插件模式一致的通用自检，可按指纹复用）→ `public`（四例两侧综合，收集 mapped 网表与 stat）→ `chains`（内置主链，见下）→ `performance`（同一外部脚本、每例 15 对交错）。
- **内置功能证明**：主链 `c4a_rtl_opt_mapped`/`c4b_rtl_base_mapped`（原始 RTL ↔ 两侧 ABC9 后、map_cells 前网表（post_abc.il，含 $lut 与受支持 dffeas）；test3 同样使用无切割合并证明）；插件轮的 `c1_local`/`c2_stage` 依赖 P3 中间网表，内置模式不适用（NOT_APPLICABLE，不虚构），不做跨模式混合声明。
- **完成状态**：全部检查与证明实际完成且通过后为 `BUILTIN_FOUR_CASE_LOCAL_ACCEPTANCE_COMPLETE`（manifest：`builtin_execution=COMPLETE`；官方认可仍为 `NOT_CLAIMED`，本地验收不代表主办方认可）；任何缺证明、缺证据或无效样本均为 `NEEDS_REVIEW`（`builtin_local_acceptance=NOT_CLOSED`）；工具准备失败为 `BUILTIN_BUILD_FAILED`、身份检查不符为 `BUILTIN_NOT_READY`，均不产生通过。
- 插件预检（`--mode plugin`）与功能补充复核结果永远不能得出内置验收完成；正式评测以官方环境为准。

## 功能证明（四例）

- 默认链集合：`c4a_rtl_opt_mapped`（内置 p5：原始 RTL ↔ 优化版 post_abc.il，主路径；插件仍为最终映射网表）+ `c4b_rtl_base_mapped`（baseline 对照）+ `c1_local`、`c2_stage`（范围受限证据与失败定位；不能单独支撑全链声明）。
- 扩展链（`--chains full`）：c3a/c3b（RTL ↔ coarse 两侧）、c5（mapped 对）；不作为每轮必跑。
- **两侧分别独立运行、分别记录**：每例的 c4a 与 c4b 各自在真实输入上重新生成并证明；不得以“两链同结果”推断，也不得复用旧成功日志替代（算法提交变化时必须重新生成）。汇总数字中 test1 43×2=86、test2 1×2=2、test4 5×2=10 属两侧合计，不标注为“每链”。
- **模型（dffeas-v3）**：clrn 异步清零 / ena 时钟使能 / power_up 初值；跑前经 `runner/precheck_supported_config.py` 支持配置预检——power_up∈{low,high}、prn=1、asdata/aload/sclr/sload=0、clrn/ena 端口必须存在（缺失即阻断）、未知单元/参数/端口取值阻断、纯组合（无 dffeas）合法；不满足保留 MODEL_UNSUPPORTED，不删条件、不修改输入强行证明。
- **策略（noDF-local-r1）**：EQY setup（`eqy -m`，只生成分区与脚本）→ **严格转换**（仅删除恰一处 ` -set-def-formal`，其余逐字节不变；生成格式不符即停止并说明，不得无约束删改）→ 本地执行；保留 `-set-init-undef`、`-set-def-inputs`、`-set-assumes`、断言与未定义值比较语义。附**前提探针**：noDF 前提必须 SAT 才计入真实证明；DF 前提记录为历史签名对照。
- **test3**：链级证据 = **无切割整模块合并证明**（两侧分别运行；覆盖全部输出与匹配点；模板与轮内实际分区集合核对；默认 `maxsteps 16`、执行上限 600s；未闭合如实记录，不盲目加深）。其余用例保留分区路径。
- **判定必须联合**：进程退出状态 + 完整成功标记 + 基例数 ≥ 归纳长度 + 断言导入覆盖 + 全文错误扫描；不能只 grep 一个 SUCCESS 字样。链级另加全部 noDF 前提探针 SAT。前提探针只覆盖“初态前提可满足（深度 1）”，不声称任意时刻可达性。
- 状态分开记录：PASS / UNPROVEN / TIMEOUT / TOOL_OR_CONFIG_ERROR / COUNTEREXAMPLE_REQUIRES_REVIEW / MODEL_UNSUPPORTED / PREMISES_NOT_SAT / METHOD_REVIEW_REQUIRED / NOT_RUN；工具报告反例需复核配置、假设与反例后再定性；baseline 同样失败不构成豁免。
- 默认链集合未全部通过（含缺证明/工具错误/MODEL_UNSUPPORTED）时不得输出通过；整体状态为 NEEDS_REVIEW 且完整证明链记为 NOT_CLOSED。

## 功能补充复核（冻结网表；不重新综合、不测性能）

- 调用：`validate.py run <commit> --mode plugin --function-only --frozen-round <轮次目录>`。
- 只运行 `build + formal_selfcheck + chains`；chains 只读复用冻结轮次的 `05_公开四例_public/round01` 产物，并**逐文件对照该轮 `11_汇总与证据_summary/ALL_SHA256.txt`**；核对失败即停止，不回退完整 run 代替。
- `flowcheck / measurement_selfcheck / public / performance` 记为 NOT_RUN（原因入 stages）；资源与性能引用冻结轮次（数字非本轮产生）；不将旧数据冒充新测。
- 完成状态 `FUNCTION_RECHECK_COMPLETE` 只表示功能复核完成；报告标题/标注必须为“插件版功能补充复核”，内置四例验收仍为 NOT_RUN。

## 判定与报告

- 每轮一个中文主报告（`00_本轮验证结论.md`）+ 清单（`11_汇总与证据_summary/manifest.json`）+ 必要原始证据与全量哈希（`ALL_SHA256.txt`）；不层层复制多个结论。
- 插件预检完成状态 `FOUR_CASE_PLUGIN_CHECKS_COMPLETE` 仅表示本地四例检查完成，不代表官方验收，仍需查看功能证明与性能逐例判定与未闭合项；`NEEDS_REVIEW` 表示失败、缺测或待复核。
- 退出码：0 = 插件四例检查完成（或功能复核完成）；2 = 需复核；3 = 内置阻断（未就绪）。
- 报告分别列出：实际模式与交付形态、**每例两侧功能状态**（含所用方法：分区/合并证明）、每例 Comb/DFF、四例平均缩减率、逐例 CPU/内存开销与限制。不生成未经来源支持的官方分数；不补充跨例聚合。

## 调用与失败处理

- `validate.py plan <提交>` 只读预检（输出将复用哪些工具、是否需要构建及原因；缺基础源码/依赖列为阻断）；`validate.py run <提交>` 默认内置（自动准备：查缓存 → 必要时构建 → 四例 15 对验收）；`--builtin-cache-dir <目录>` 指定构建缓存命名空间（用于复用检查与空缓存未命中验证）；`--mode plugin` 显式插件预检；`--chains full` 扩展链集合；`--function-only --frozen-round` 功能补充复核。
- 工具或四例输入指纹变化时预检停止；先审核变更原因，需要时升级流程/套件版本，不自动刷新指纹。对象缺失时查明来源、经授权才 fetch。
- 不 checkout/pull/reset/clean；不删历史、不清理工作区、不提交/推送；失败记录保留、修复后新开轮次；不并行启动其它实验。
- 新轮次放 `results/官方口径评测/日期_时刻(HHMM)_版本名_提交短号_第NN轮`，禁止覆盖。

## 与历史轮次的关系

- 旧流程/套件（official4-p1、p2、p3、p3-plugin-v1、h1h2-p3-v1）的历史轮次与资产保留原位、不作改写；本入口不用于重解释旧轮次，也不把插件结果称为官方验收。
- official4-p4 的自动准备与十五对为历史入口增强；p5 在此基础上调整功能输入阶段与主进程内存；p3 轮次（含 5 对口径性能结论，如 test2 超限保留）不被新默认值重写或重解释。
- official4-p2 的方法修正（模型 v3 / noDF 策略 / test3 合并证明 / 自检 r2）与旧轮次的对照关系引用旧轮次原始证据，不覆盖旧审计快照。
- 旧目录名中的 “official” 不构成官方认可证据；本规则文件不代表主办方口径的全部解释。


## p5 实施要点与交付（C53～C55）

- 内置功能综合使用 `synth_intel -run begin:map_cells`，在 map_cells 开始前导出 post_abc.il，然后 `-run map_cells:` 完成最终映射。终点为排他边界；两侧脚本相同。map_luts 包括 ABC9 及其清理过程。
- flowcheck 及性能仍运行未拆分的完整 synth_intel；性能不包含额外功能网表导出或证明。public 对照 flowcheck 的最终单元统计，防止拆分遗漏阶段。两侧检查真实 ABC9 pass，拒绝用 ABC 替代。
- 功能输入预检拒绝最终 cycloneiv_lcell_comb；$lut 使用 Yosys 内建语义，残留 dffeas 继续使用受支持器件模型。test3 保留整模块证明及覆盖检查；不复用旧 PASS 冒充新阶段证明。c4a/c4b 历史链名保留兼容，JSON 的 formal_netlist_stage 必须为 post_abc。
- 资源主指标仍为最终映射 cycloneiv_lcell_comb；另外记录 post_abc 的 $lut 数量，不能混为一个统计阶段。DFF 及其他非组合资源逐单元类型检查不得增加；未知类型也列入保守检查。$not/$_NOT_、LUT 和 VCC/GND 为组合逻辑或常量，单独列示不当作 IO/DSP 等硬件类别。缺少的类型按零；新增类型不可漏检。
- CPU 相对开销逐例 5% 门槛保持，CPU 包含 ABC；绝对耗时不作为评分项。既有 60s/2GB 原版超限例外及运行超时保护保持，不自行改评分公式。
- 旧轮次按保存的 memory_metric 读取；缺该字段的旧记录使用原进程组口径。p5 缺主进程样本不得退回树内存，旧五对/十五对结果不改写。
- 最终提交清单：优化源码（含集成改动）、修改过的 ABC 脚本（若有）、Yosys 二进制及依赖库。运行平台须明确；本次只完善清单，不声称已制作可跨机器部署包。
- 实施验证仅工具测试与单用例导出冒烟；本次不新开完整四例轮次，用户自行调用 Skill 验收。
