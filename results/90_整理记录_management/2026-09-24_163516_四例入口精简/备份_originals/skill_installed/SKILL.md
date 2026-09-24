---
name: pmux-stable-validation
description: 验证 PMUX 稳定 Git 提交，调用 WSL 共享 P3 插件版完整评测脚本，核对公开资源、功能回归、H2 边界、规模及时间内存证据并中文汇报。用于用户要求评测稳定版本或提供算法提交号要求验证时；不用于算法开发或最终内置 Yosys 集成。
---

# PMUX 稳定版本完整评测

用户主要验证队友交付的稳定版本，默认完整评测。DeepSeek 与 Codex 使用同一份仓库脚本，不临时重新编写综合或判定流程。

## 唯一执行入口

- WSL 发行版：Ubuntu-24.04；用户 fpga。
- 工程：`/home/fpga/fpga/pmux-opt`。
- 共用脚本：`/home/fpga/fpga/pmux-opt/scripts/pmux_validation/validate.py`。
- 规则：先读同目录 `POLICY.md`，按需读 `config.json` 与 `suite/manifest.json`。从 Windows 可通过 `\\wsl.localhost\Ubuntu-24.04\home\fpga\fpga\pmux-opt\scripts\pmux_validation` 读取。
- 结果：工程的 `results/官方口径评测/日期_版本名_提交短号_第NN轮`。

本 Skill 替代旧 pmux-commit-validation、pmux-independent-validation 的默认稳定版本验证入口。旧记录仅用于查阅，不调用它们的旧内置构建/Total 判定流程。

## 执行

用户要求实际验证并给出提交时，先检查 Git 状态及提交是否可解析；项目工作区有未提交改动并不要求清理。输入应为算法 Git commit，不是源码或插件 SHA-256。若哈希含义不明或缺失，仅补问缺项。不要把用户给的“最新分支”自动替代精确提交。

在 WSL Bash 中，先执行只读预检（把 `<commit>` 换成用户给的提交）：

```bash
python3 /home/fpga/fpga/pmux-opt/scripts/pmux_validation/validate.py plan <commit>
```

预检成功且用户要求运行验证时，执行：

```bash
python3 /home/fpga/fpga/pmux-opt/scripts/pmux_validation/validate.py run <commit>
```

在 Windows PowerShell 中使用以下入口，不把 Bash 命令交给 PowerShell：

```powershell
wsl.exe -d Ubuntu-24.04 -- python3 /home/fpga/fpga/pmux-opt/scripts/pmux_validation/validate.py plan <commit>
wsl.exe -d Ubuntu-24.04 -- python3 /home/fpga/fpga/pmux-opt/scripts/pmux_validation/validate.py run <commit>
```

脚本默认完整执行，没有隐式快速模式。可用 `--label` 指定已确认的版本名，默认“稳定版-P3”。对象缺失时查明提交来源，在用户授权范围内 fetch；不得 checkout/pull/reset/clean。只讨论或生成执行文档时不运行评测。

运行中使用工具返回的进程会话和本轮 `01_来源与环境_meta/stages.json` 跟进。阶段日志同目录；长耗时期间给用户简短中文进度。不要并行启动另一轮综合/性能实验。过程退出码和算法判定不同：阶段进程成功仍可能产生未证明或失败结果。

## 版本和范围

工具、数据文件与固定输入指纹变化时预检停止，不自动刷新指纹继续跑。先确认变化原因，需要时升级流程/套件并重新验收。未知新优化类型先了解其预期行为，保留通用回归，并增加独立专项；固定 H1/H2 套件不能代表所有未来算法均被覆盖。

不得修改 `src/pmux_opt.cc`、Yosys 实现或官方输入以通过验证；不自动提交、推送、安装依赖或清理旧结果。新插件从精确提交全新构建，源树 HEAD、算法提交、源码 SHA-256、插件 SHA-256 各自记录。编译入口目前支持单个 pmux_opt.cc；新增本地依赖须审核构建配置。

## 结论与失败处理

先读 `00_本轮验证结论.md`、`11_汇总与证据_summary/manifest.json` 和阶段退出码；对异常核对原始日志，不只读 PASS 标题。

- `LOCAL_PLUGIN_CHECKS_COMPLETE` 只表示本地核心检查完整，不等于 RTL 到映射网表全部证明或官方验收。
- `NEEDS_REVIEW` 表示至少一项失败、缺测或需复核，报告具体项目。
- EQY 超时、未证明、工具错误和分区反例分开汇报；反例复核前不认定算法错误，也不因 baseline 同样失败就豁免。
- c1/c2 不能代替 RTL 全链。映射模型适用条件不满足时保留 MODEL_UNSUPPORTED，不删条件强行证明。
- 最终内置 Yosys 验收本阶段仍为 NOT_RUN，不擅自扩展。
- 失败记录保留。修复工具封装后开新轮次；不要覆写旧输出或临时放宽判定。

最终中文汇报：算法版本、实际执行范围、公开 Comb/DFF 与时间内存结果、通过/未闭合/缺失项及报告路径。说明测试套件版本和新增算法覆盖限制。给用户操作说明时输出到 Windows `D:/codex/02_嵌赛/deepseek执行文件` 的 `.md`；实际工具执行不要求用户手工输入长命令。
