# H1 与公开案例冻结验证规范

这是团队评测流程，不是官方指定 pass 顺序。主面积指标为 Cyclone IV 映射后的 Total cells。

## 固定源码

- stable：244baaf19c8abf62443aabfb5ff449ff535a447d
- candidate：0c0ee40aabfaf62fad3ab7c04dd42d092d6ca483

脚本用 git show 提取两个提交的 src/pmux_opt.cc，分别新编译插件，不使用项目根目录旧 .so。
默认验证上述固定提交，修改工作区源码不会改变被测插件。将来验证新提交需明确传入 --candidate。

## 流程

共同前端：read_verilog -sv → hierarchy -check → proc。

P：baseline 执行 opt → opt；stable/candidate 执行 opt → pmux_opt → opt。
R1：baseline 执行 opt_clean；stable/candidate 执行 pmux_opt → opt_clean。

映射统一执行 synth_intel -family cycloneiv；统计 Total、cycloneiv_lcell_comb、dffeas。
P、R1 单独列出，不能混合汇总。

Formal：每个 case/flow 比较 baseline 与 candidate、stable 与 candidate 的 generic netlist。
R1 额外比较由原始 RTL 经 proc/memory_map/opt_clean 得到的参考网表与 candidate。
为支持 test4 的 memory，Formal 导出副本统一 memory_map/opt_clean，再由模板 prep。
保存副本使用 design -push-copy，导出后 design -pop 恢复映射输入，Formal 预处理不改变 QoR 流程。
EQY 使用 SAT depth 10；返回码为 0 且出现 DONE (PASS 才计 PASS。
返回码 2 记 FAIL_OR_UNKNOWN，不直接宣布真实非等价；其他错误与 TIMEOUT 分开。

## 运行

在 WSL 项目根目录执行：

```bash
python3 scripts/run_frozen_validation.py --suite all
```

只跑专项或公开测试：

```bash
python3 scripts/run_frozen_validation.py --suite h1
python3 scripts/run_frozen_validation.py --suite public
```

仅选流程可加 --flows P 或 --flows R1。
使用 --out 指定新的绝对输出目录；目录已存在时拒绝覆盖。
需要 Yosys、同版本 yosys-config、EQY、Z3、GNU time 和 Python 3。

每次保存源码/插件/RTL 哈希、工具版本、脚本哈希、完整命令脚本、构建日志、网表、stat、EQY 日志、summary.json/csv。
综合每次硬超时 60 秒，EQY 120 秒，构建 180 秒；超时终止对应进程组。
time/RSS 是 GNU time 对单次 Yosys 调用的统计，不含插件编译和 EQY，不宣称是并发进程树总内存。
这是单次运行，不是三次性能中位数，也不能代替队友独立验证或完整 A/B/C/D、千节点回归。

通过条件：所有 Formal PASS；candidate Total 不高于 baseline/stable；RSS 不超过 2,000,000 KB。
P 下另外检查 H1 预期触发次数，四个新增正例必须比 stable 严格降低 Total。

## 交接边界

H1 案例取自现存历史 RTL，原生成器没有恢复。
本脚本执行属于开发侧复测。队友须在自己的环境对同一提交重新编译运行，另行形成独立报告。
历史 run_full_regression.sh 保留原样；严格 P/R1 结果以本入口为准。

验证入口还会生成输出互为反相的最小负对照，要求 EQY 返回码 2（FAIL_OR_UNKNOWN），防止空验证被当成 PASS。
