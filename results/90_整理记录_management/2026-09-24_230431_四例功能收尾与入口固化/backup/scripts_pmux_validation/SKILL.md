---
name: pmux-stable-validation
description: 验证 PMUX 官方四例（test1~test4）。默认目标是内置四例验收（只读预检内置证据；未就绪时阻断并列出缺项，不退回插件），可显式进入四例插件预检（--mode plugin）。用于用户明确要求评测并给出精确 Git 提交时；不用于算法开发或 Yosys 集成开发。
---

# PMUX 官方四例验证（official4-p1）

本地验证入口，固定官方公开四例（test1~test4）。默认范围只有四例所需内容：来源检查、四例功能、四例资源、四例性能与统一报告；不默认运行 A/B/C/D/H1 回归、H2、规模或多驱动测试（相关模块与资产保留原位、默认不调用）。

## 唯一执行入口

- WSL 发行版 Ubuntu-24.04、用户 fpga；工程 `/home/fpga/fpga/pmux-opt`。
- 脚本：`scripts/pmux_validation/validate.py`；规则：同目录 `POLICY.md`。
- 结果：`results/官方口径评测/日期_版本名_提交短号_第NN轮`（拒绝覆盖、自动新编号）。

## 两种形态

- **内置四例验收（默认）**：要求原版/优化版两份 Yosys 0.69 可追溯构建与插入调用证据（预检项见 POLICY）；缺证据时生成阻断记录并列出缺项，不加载插件、不启动验收进程、不自动退回插件。注意：内置执行器本版本未就绪，`run` 默认只做预检与阻断记录，不会执行四例验收。
- **四例插件预检（显式 `--mode plugin`）**：本地编译插件后运行四例；结果始终标记“四例插件预检”，永远不构成内置验收。

## 执行

用户明确要求验证且给出精确 Git 提交时（不是分支名、不是源码或插件 SHA-256）：

```bash
python3 /home/fpga/fpga/pmux-opt/scripts/pmux_validation/validate.py plan <commit>
python3 /home/fpga/fpga/pmux-opt/scripts/pmux_validation/validate.py run <commit>
python3 /home/fpga/fpga/pmux-opt/scripts/pmux_validation/validate.py run <commit> --mode plugin
```

Windows PowerShell 用 `wsl.exe -d Ubuntu-24.04 -- python3 ...` 包装，不把 Bash 命令交给 PowerShell。

- `plan` 只读；`run` 按形态执行。讨论或编写文档时不得运行。
- 缺内置产物时简明报告缺项，不擅自开始 Yosys 集成开发。
- 工作区已有未提交改动不阻止提取精确提交；不 checkout/pull/reset/clean。

## 失败处理与汇报

- 失败与阻断记录保留；修复后新开轮次、不覆盖旧输出；不与其他性能实验并行。
- 缺失证据、工具错误、无效性能样本不会被判为通过；插件预检不输出内置验收完成。
- 最终中文汇报：实际模式与交付形态、四例 Comb/DFF 与平均缩减率、功能证明状态、逐例 CPU/内存开销与 5% 判定、缺项或未就绪清单、报告路径。
