> 本文保留10月28日历史验证记录；10月29日推送版本与队友任务请以 [最新验收说明](teammate_acceptance_20261029.md) 为准。

# PMUX 稳定预算候选：队友模拟考场验收说明

日期：2026-10-28。此文记录本地开发证据与交付入口，不代表 Windows 正式效率验收通过。

## 规则口径

- 以最新答疑为准。面积为各用例逻辑降幅的算术平均，新增五例也计入；独立 `$not` 算逻辑，任何单例逻辑不能反增（答疑 C67、C115、C130）。
- 效率满分门槛是**每例运行时间和 Yosys 主进程峰值内存相对原版均不超过 5%**，不是跨用例平均。单例任一指标超过 15% 会使效率项不得分（C41、C54、C105）。
- 原版先就同一用例预热 10 次，再依次测原版和优化版；不足 1 秒的用例若初测超过 5%，可复核 5 次取平均，超过 10 秒的用例只测一次。1–10 秒的复核规则未明确（C132）。时间与内存同次采集（C133）。
- 使用 Yosys 0.69、统一 ABC9、`synth_intel -family cycloneiv`；优化 pass 编入主程序，外部综合脚本相同。EQY 检查 ABC 后、厂商单元映射前的 `$lut` 网表（C37、C53–C54、C106）。
- 不通过修改其他 pass 或依赖程序抵消 PMUX pass 开销；ABC 脚本对所有用例统一。本候选未改 ABC、其他 pass 或依赖程序（C114、C130）。

## 本次算法和构建

`src/pmux_opt.cc` 仍注册一个 `pmux_opt` pass：

1. `pmux_opt -arith`：在 coarse 阶段的原 `pmux_opt` 前执行互斥译码 PMUX 加减法共享。匹配同一 2–3 位控制、宽度 1–64 的独立无符号分支；仅当私有运算结果无额外用户和保护边界时重构。不使用用例名或信号名。
2. 原 `pmux_opt`：保持已推送的 1–8 系列算法。
3. `pmux_opt -lut`：ABC9 后执行精确有界 LUT4 分解；全设计统一上限 768 cuts、250000 work、64 rewrites，保留三 LUT 回退与图关系缓存。完整枚举边界二值真值表，不依赖不可达输入假设。

`integration/yosys_0_69_stable_pmux.patch` 是相对官方 Yosys `9f75ca1f9834a39a863915b5dae0c7b1e33533bc` 的**完整**集成补丁：在 `techlibs/intel/synth_intel.cc` 插入三次上述调用，并在 `passes/opt/CMakeLists.txt` 注册源码。`integration/apply_stable_pmux.py --yosys-root <官方Yosys源码目录>` 完成同样的三处改动并复制 `src/pmux_opt.cc`，支持 LF/CRLF 源码；重复执行不会重复插入。建议队友使用脚本后检查源码差异，再构建。不要与历史的 `yosys_0_69_local_lut.patch` 重复叠加。

本地 Clang 18.1.3 Release-O3 内置实验二进制为 `yosys.stable_integrated_20261028`；构建后 EDA 暂写源码和默认 `build/yosys` 已恢复。该 Linux 二进制不作为 Windows 交付物。

## 九例资源与功能

用 `scripts/run_final_nine_regression.py` 对原版与内置候选执行相同 `synth_intel` 外部脚本。原版逻辑数来自同次综合，逻辑为 `cycloneiv_lcell_comb + $not`。

| 用例 | 原版逻辑 | 候选逻辑 | 原版/候选 DFF |
|---|---:|---:|---:|
| test1 | 288 | 181 | 222 / 222 |
| test2 | 25 | 16 | 0 / 0 |
| test3 | 13 | 9 | 17 / 12 |
| test4 | 36 | 29 | 10 / 10 |
| pmux_case01_balanced | 426 | 381 | 12 / 12 |
| pmux_case02_pipeline | 450 | 379 | 24 / 24 |
| pmux_case03_crossbar | 408 | 283 | 10 / 10 |
| pmux_case04_feedback | 368 | 338 | 16 / 16 |
| pmux_case05_nested | 413 | 373 | 12 / 12 |

九例每例面积降幅算术平均 **22.0202522100%**，严格大于用户设定的 21%，且逐例逻辑不高于原版。九例原始 RTL 到 ABC 后网表的实际归纳证明全部 PASS；故意取反 balanced 用例寄存器 D 输入时，checked SAT replay 得到 base-case 反例。两个算术边界用例验证：可共享时共享 1 组；给运算结果增加独立输出后共享 0 组，两者均形式等价。译码 PMUX 边界 16 项通过，局部 LUT 随机/保护/千节点边界 34 项通过。

五个新增官方 RTL 输入按字节复制到 `tests/official_new5/`，便于队友 fetch 后复现；文件哈希与原下载用例一致。被跟踪的源码和集成补丁不依赖 `results/` 下的实验文件。

## 运行开销：5% 尚未验收通过

Linux 开发诊断同批轮换原版 A、同二进制原版 B、旧缓存实验版、最终内置版，每组预热 1 次、记录 10 次，共 396 次完整综合。未删除任何尖峰。对同 trial 原版 A，时间超过 5% 的配对：原版 B **29/90**、旧缓存版 **23/90**、最终内置版 **14/90**；内置版内存超过 5% 为 **2/90**。内置版时间最差单对为 test4 **+42.56%**。这组数据不能证明逐次 5% 达标。

再按 C132 的短用例规则做一次预热 10 次、初测、触发后五对复核的 Linux 模拟：test2 的复核平均时间 **+7.87%**，test4 **+13.16%**；其余用例初测时间与内存均在 +5% 内。九例内存最终判定均在 +5% 内。**本地时间诊断未满足 5% 门槛。**每次预热、初测和复核的原始墙钟、主进程 CPU、峰值内存及算法耗时见 `docs/linux_official_like_20261028.json`；此文件是 Linux 诊断记录，不代替 Windows 正式验收。

最差样本中的优化 pass 仅占约 0.4–2 ms，而 `read_verilog`、ABC9、techmap 等阶段出现更大的差值。比如 test4 某次候选相对原版，`read_verilog` 在优化 pass 之前已多 16.85 ms；相同原版二进制 A/B 也频繁超过 5%。这些事实说明尖峰不能全部归因于优化 pass，但尚不能唯一确认波动来源，也不能借此声称正式效率通过。为避免扭曲比赛口径，没有改其他 pass、ABC 程序、全局电源或杀毒设置，也没有择优挑批次。

试过将所有用例统一使用 512 cuts：九例面积平均降到 21.9901%，test4 优化 pass 平均省约 0.28 ms，但在同批完整综合对照中时间没有稳定改善，test2 反而变慢。因此保留当前 768 cuts 候选，不根据单次有利测量替换版本。

本地采集是 Linux 单调墙钟及同次 Yosys 主进程峰值 RSS；ABC 子进程等待包含在墙钟中，ABC 内存不计入主进程 RSS。正式 Windows `Measure-Command` / PeakWorkingSet 及队友模拟考场仍须实际验收。早期答疑“CPU 时间”与后期 `Measure-Command` 建议不完全一致，原始墙钟、主进程 CPU 和 per-pass CPU 都留在本地日志中。

## 队友验收入口（待满足 5% 门槛并推送后）

1. 推送后 fetch `下一轮优化研究` 分支并记录完整 commit SHA；对官方 Yosys 0.69 `9f75ca1...` 执行 `python integration/apply_stable_pmux.py --yosys-root <官方Yosys源码目录>`，确认三处集成改动，编译 Windows 可执行程序及相对路径依赖。若在既有集成树工作，只添加缺少的 `pmux_opt -arith` 调用并更新同一个源码文件；该脚本对部分集成树会报错，避免重复插入。
2. 原版和优化版使用相同官方 0.69 基座、ABC9 版本、构建参数和外部脚本；九例输入来自本仓库 `pmux_case/competition_case/` 及 `tests/official_new5/`。先跑 `scripts/run_final_nine_regression.py` 或等效 Windows 脚本，保留每例 Formal、逻辑和 DFF 证据。
3. 按 C132 预热、顺序及触发复核规则，同次记录完整运行时间与 Yosys 主进程峰值工作集；保留单次原始值、复核全部值、日志和网表。若任例超过 +5%，直接反馈具体用例和数据，不以九例平均掩盖。

本报告保留 5% 时间风险。队友的 Windows 验收是下一道门槛；不能把本地面积/Formal 成功表述成效率满分或正式交付完成。
