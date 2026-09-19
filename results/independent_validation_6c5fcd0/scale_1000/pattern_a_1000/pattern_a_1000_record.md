# pattern_a_1000 独立验证记录（commit 6c5fcd052987206d9e117f518f1d98fc9046c72d；方案A：/tmp 独立工作区）

## 完成记录
Case: pattern_a_1000
Nodes: 996（target 1000；units=166，A=166，C=0，N=0）
Trigger: pair-swap candidate=166 / rebuilt=166；Pattern C 输出 0 行
EQY: PASS（gold=RTL --prep；gate=optimized_generic.il --prep；strategy simple/use sat/depth 5）
EQY 耗时: EQY 21:17:53 [verify] summary: Elapsed clock time [H:MM:SS (secs)]: 0:07:48 (468)
Total B/O: 4150 -> 2656（-36.00%）
Comb B/O: 4150 -> 2656（-36.00%）
DFF B/O: 0 -> 0
Time median B/O: 1.660s -> 1.080s
RSS max B/O: 95148 kB -> 77108 kB
Status: PASS
异常: 无（baseline/optimized 两侧出现相同 ABC 提示信息，rc 均 0）

## 判定
- EQY = PASS [OK]
- optimized runtime 1.080s <= 60s [OK]
- optimized peak RSS 77108 kB = 0.07 GB <= 2 GB [OK]
- 资源不回退: Total 4150->2656 (-36.00%), Comb 4150->2656 (-36.00%), DFF 0->0 [OK]

## 运行参数
- baseline: yosys-baseline -Q -p "read_verilog -sv design.v; hierarchy -check -top stress_top; proc; opt_clean; write_rtlil baseline_generic.il; synth_intel -family cycloneiv -top stress_top; stat -json; write_rtlil baseline_mapped.il"
- optimized: yosys-optimized(含 6c5fcd0 pmux_opt 内置) 同上但 proc 后执行 pmux_opt
- EQY: gold=原RTL / gate=optimized_generic.il
