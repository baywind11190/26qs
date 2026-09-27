---
name: pmux-stable-validation
description: 验证 PMUX 官方四例（test1~test4）。默认允许按固定方案自动准备内置工具（匹配时复用；未命中时在隔离源码树构建），随后运行四例十五对功能/资源/性能评测；可显式进入四例插件预检（--mode plugin），以及插件版功能补充复核（--mode plugin --function-only --frozen-round ）。用于用户明确要求评测并给出精确 Git 提交时；不用于算法开发或 Yosys 集成开发。
---

# PMUX 官方四例验证（official4-p4）

本地验证入口，固定官方公开四例（test1~test4）。默认范围只有四例所需内容：来源检查、四例功能、四例资源、四例性能（每例 15 对）与统一报告；不默认运行 A/B/C/D/H1 回归、H2、规模或多驱动测试（相关模块与资产保留原位、默认不调用）。

方法版本（本入口）：模型 `dffeas-v3`（器件语义）+ 策略 `noDF-local-r1`（严格删 `-set-def-formal`，附前提探针）+ test3 无切割合并证明 + 支持配置预检 + 自检 r2。每轮证明均从该轮真实输入重新生成；两侧（c4a/c4b）分别独立运行与记录。

## 唯一执行入口

- WSL 发行版 Ubuntu-24.04、用户 fpga；工程 `/home/fpga/fpga/pmux-opt`。
- 脚本：`scripts/pmux_validation/validate.py`；规则：同目录 `POLICY.md`。
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
