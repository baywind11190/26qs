---
name: pmux-stable-validation
description: Windows V8当前四例内置验证；默认validate_windows_v8.cmd，同次采集时间与峰值，正式综合8次。具体规则以同目录POLICY.md为准。旧WSL/十五对流程仅供历史复查；新增官方用例接入尚待适配。
---

# Windows V8当前入口

## 2026-10-23：1022答疑与V8核对

最新来源为工程赛题目录的《FPGA创新大赛问题汇总 1022.xlsx》Sheet1，重点新增第114～117行。完整对照、整改清单及可直接询问老师的问题见[第18号说明](D:/codex/02_嵌赛/验证流程版本更新说明/18_1022答疑与V8符合性核对及待确认问题_20261023.md)。

- 第114行：允许调整ABC脚本，但不得通过优化其他pass或依赖程序抵消PMUX增加的时间。当前7.1对一般LUT4网络做局部优化，其允许范围待老师确认，不凭pass名称认定。
- 第115行：月底前提供3～5例；新增例也计入全部用例平均优化率，并要求逐例资源不增加；cells以输出网表统计。当前只有已获得四例，正式综合8次。新增N例接入后须覆盖全部用例，各原/优一次；现行固定四例代码尚待适配，不能把“8次”视为永久总数。
- 第116～117行：推荐Windows exe；WSL方案须现场编译执行并自备时间/内存工具。当前项目仍选原生Windows；不把问题栏的“任意墙钟方法”当成官方已肯定。
- 默认入口仍为`D:/codex/0000_26qs/scripts/pmux_validation/validate_windows_v8.cmd`，唯一规则正文仍为`D:/codex/0000_26qs/scripts/pmux_validation/POLICY.md`。先plan核对规则来源、当前四例预计8次及blocked为空，再按授权run。
- 同次调试峰值、计时请求/响应包装、证明网表导出边界为本地实现，具体接受性待确认；NOT计数细节、2GB单位和效率中间档见第18号提问。
- 已登记代码缺口：新增用例接入，以及单例logic_units增加的独立门禁。本次仅文档同步，未整改代码。当前实测四例资源均未增加。
- 本轮正式结果不变：功能/资源/内存通过，test3墙钟+15.021%、test4+13.284%，工程FAIL；四例平均逻辑缩减28.7583%。新增用例WAITING_OFFICIAL_CASES，交付包NOT_RUN，不能宣称全部官方验收通过。

以下既有V8安排继续适用于当前四例；旧V7/V6/WSL和重复采样内容仅用于各自历史用途，不作为当前默认入口。本次未重新综合、运行EQY或追加测量。


## 历史WSL及旧版本用法（非当前默认）

# PMUX 官方四例验证（official4-p5）

本地验证入口，固定官方公开四例（test1~test4）。默认范围只有四例所需内容：来源检查、四例功能、四例资源、四例性能（每例 15 对）与统一报告；不默认运行 A/B/C/D/H1 回归、H2、规模或多驱动测试（相关模块与资产保留原位、默认不调用）。

方法版本（本入口）：模型 `dffeas-v3`（器件语义）+ 策略 `noDF-local-r1`（严格删 `-set-def-formal`，附前提探针）+ test3 无切割合并证明 + 支持配置预检 + 自检 r2。每轮证明均从该轮真实输入重新生成；两侧（c4a/c4b）分别独立运行与记录。

## 唯一执行入口

- WSL 发行版 Ubuntu-24.04、用户 fpga；工程 `/home/fpga/fpga/pmux-opt`。
- 脚本：`scripts/pmux_validation/validate.py`；规则：同目录 `POLICY.md`，完整位置 `D:/codex/0000_26qs/scripts/pmux_validation/POLICY.md`；当前默认入口 `validate_windows_v8.cmd`、正式综合共8次，同次采集墙钟与峰值内存。旧V7/V6只用于历史复查。
- 结果：`results/官方口径评测/日期_时刻(HHMM)_版本名_提交短号_第NN轮`（拒绝覆盖、自动新编号）。

## 三种形态

- **内置四例验收（默认）**：自动准备两侧内置工具——原版（baseline）核对登记后复用；优化版按缓存键（算法源码哈希/基础提交/集成模板/关键构建参数/编译器/ABC 身份）查找匹配构建，命中且产物核验通过即复用；未命中则在隔离源码树构建（逐字节提取 `src/pmux_opt.cc`、幂等集成、冒烟验证、登记 READY 缓存）。随后执行真实内置调度（`flowcheck` → 自检 → `public` → 内置主链功能证明 `c4a/c4b` → **每例 15 对性能**），全部完成状态词 `BUILTIN_FOUR_CASE_LOCAL_ACCEPTANCE_COMPLETE`（本地验收，官方认可 `NOT_CLAIMED`）；构建失败保留诊断（`BUILTIN_BUILD_FAILED`）、身份不符阻断（`BUILTIN_NOT_READY`），均不加载插件、不启动验收进程、不自动退回插件。
- **四例插件预检（显式 `--mode plugin`）**：本地编译插件后运行四例（每例 15 对）；结果始终标记“四例插件预检”，永远不构成内置验收。
- **插件版功能补充复核（`--mode plugin --function-only --frozen-round <轮次目录>`）**：只运行 build + formal_selfcheck + chains；chains 只读复用冻结轮次的 `05_公开四例_public` 产物并逐文件对照该轮 `ALL_SHA256.txt`；不重新综合、不测性能（资源/性能引用冻结轮次）；报告标注“插件版功能补充复核”；完成状态 `FUNCTION_RECHECK_COMPLETE`，否则 NEEDS_REVIEW。

## 执行

用户明确要求验证且给出精确 Git 提交时（不是分支名、不是源码或插件 SHA-256）：

```bash
python3 /home/fpga/fpga/pmux-opt/scripts/pmux_validation/validate.py plan <commit>
python3 /home/fpga/fpga/pmux-opt/scripts/pmux_validation/validate.py run <commit>
python3 /home/fpga/fpga/pmux-opt/scripts/pmux_validation/validate.py run <commit> --mode plugin
python3 /home/fpga/fpga/pmux-opt/scripts/pmux_validation/validate.py run <commit> --mode plugin \
    --function-only --frozen-round "results/官方口径评测/<既有轮次目录>"
```

Windows PowerShell 用 `wsl.exe -d Ubuntu-24.04 -- python3 ...` 包装，不把 Bash 命令交给 PowerShell。

- `plan` 只读：输出将复用哪些工具、是否需要构建及原因（不创建目录、不编译）。`run` 先自动准备再验收；未命中构建属正常可执行流程，不回问用户；构建耗时不计入综合性能。讨论或编写文档时不得运行。
- `--builtin-cache-dir <目录>`（可选）：内置构建缓存命名空间，用于复用检查与空缓存未命中验证；默认取 `config.builtin.cache_dir`。
- 工作区已有未提交改动不阻止提取精确提交；不 checkout/pull/reset/clean。

## 失败处理与汇报

- 失败与阻断记录保留；修复后新开轮次、不覆盖旧输出；不与其他性能实验并行；不因性能超限追加采样或改统计。
- 冻结构建校验失败、支持配置预检阻断、策略转换格式不符、集成锚点不符：均立即停止并说明，不回退代替。
- 缺失证据、工具错误、无效性能样本不会被判为通过；插件预检/功能复核不输出内置验收完成。
- 最终中文汇报：实际模式与交付形态（复用还是新建构建）、**每例两侧功能状态**（含方法：分区/合并证明）、四例 Comb/DFF 与平均缩减率、功能证明状态与探针结论、逐例 CPU/内存开销与 5% 判定（每例 15 对）、缺项或未就绪清单、报告路径。


## p5 最新口径

- 两侧必须 ABC9 / cycloneiv；默认内置功能证明使用 ABC9 后 map_cells 前的 post_abc.il，资源仍统计最终 mapped.il。保留 dffeas 必要模型和 test3 整模块证明。
- 性能仍完整 synth_intel，不包含额外网表导出；CPU 含 ABC、十五对中位数、逐例相对 5% 不变。内存只判 Yosys 主进程 Linux VmHWM，不计 ABC/计时包装器；采样局限在报告注明。
- 除 DFF 外，其他资源逐类型不得增加；报告分别声明功能和资源阶段。不能因历史最终网表证明通过就跳过本轮新阶段验证。
- 新版已做针对性检查；升级本身未运行完整四例验收。用户明确要求验证提交时才运行，不把工具升级当算法通过。
- 交付需源码、必要 ABC 脚本、二进制及依赖库；实际打包另按确认的运行平台执行。
