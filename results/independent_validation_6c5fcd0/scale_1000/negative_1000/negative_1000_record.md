# negative_1000 独立验证记录（commit 6c5fcd052987206d9e117f518f1d98fc9046c72d；方案A：/tmp 独立工作区）

## 完成记录
Case: negative_1000
Nodes: 1000（target 1000；units=200，A=0，C=0，N=200）
Trigger: pair-swap candidate=0 / rebuilt=0；Pattern C 输出 0 行
EQY: PASS（gold=RTL --prep；gate=optimized_generic.il --prep；strategy simple/use sat/depth 5）
EQY 耗时: EQY 21:41:12 [verify] summary: Elapsed clock time [H:MM:SS (secs)]: 0:07:53 (473)
Total B/O: 2600 -> 2600（-0.00%）
Comb B/O: 2600 -> 2600（-0.00%）
DFF B/O: 0 -> 0
Time median B/O: 1.150s -> 1.160s
RSS max B/O: 74088 kB -> 74184 kB
Status: PASS
异常: 无（baseline/optimized 两侧出现相同 ABC 提示信息，rc 均 0）

## 判定
- EQY = PASS [OK]
- optimized runtime 1.160s <= 60s [OK]
- optimized peak RSS 74184 kB = 0.07 GB <= 2 GB [OK]
- 资源不回退: Total 2600->2600 (-0.00%), Comb 2600->2600 (-0.00%), DFF 0->0 [OK]

## 运行参数
- baseline: yosys-baseline -Q -p "read_verilog -sv design.v; hierarchy -check -top stress_top; proc; opt_clean; write_rtlil baseline_generic.il; synth_intel -family cycloneiv -top stress_top; stat -json; write_rtlil baseline_mapped.il"
- optimized: yosys-optimized(含 6c5fcd0 pmux_opt 内置) 同上但 proc 后执行 pmux_opt
- EQY: gold=原RTL / gate=optimized_generic.il

## 负控制专项核验（独立验证重点）
- 测试语义（前置确认，与算法负责人脚本一致）：negative_1000 = 无优化结构负控制组（普通 PMUX：n_ctrl 选 n_data nibble），
  与“Negative EQY 故障设计自测”完全不同；预期：不触发优化、EQY PASS、资源不回退。
- 触发核验：pmux_opt 扫描 200 个 $pmux：shared-selector groups=0，candidates=0，rebuilt=0（3 次运行一致）
  → Trigger = NO（符合预期，未误触发）。
- 网表影响核验：generic.il 原始 diff=4 行（仅 Yosys 版本注释行：9f75ca1f9 vs 9f75ca1f9-dirty）；
  归一化（统一安装路径/版本字符串）后完全一致（cmp 通过）。
  mapped.il 原始 diff=10780 行（全部为 \src 属性中的安装路径 yosys-baseline vs yosys-optimized + 版本注释）；
  归一化后完全一致（cmp 通过）。cell 数：generic 1000=1000；mapped 2600=2600。
- 结论：负控制组通过——插件在无可优化结构时不改动网表、不产生资源回退。
