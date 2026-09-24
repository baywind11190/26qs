# mixed_1000 独立验证记录（commit 6c5fcd0；方案A：/tmp 独立工作区）

## 完成记录
Case: mixed_1000
Nodes: 995（target 1000；units=149，A=74，C=44，N=31）
EQY: PASS（rc=0；wall 5:27；gold=RTL --prep；gate=optimized_generic.il --prep；strategy simple/use sat/depth 5）
Total B/O: 2341 -> 1675（-28.45%）
Comb B/O: 2341 -> 1675（-28.45%）
DFF B/O: 0 -> 0
Time median B/O: 1.110s -> 0.960s
RSS max B/O: 70120 kB -> 62236 kB
Status: PASS
异常: 无（baseline/optimized 两侧均出现相同 ABC 提示信息，全部 rc=0）

## 触发情况
PAIR-SWAP CANDIDATE=74 / REBUILT=74（74 个 pattern_a 单元全部重建）
Pattern C（BRANCH-EXPR CONST FOLD）有触发输出

## 判定
- EQY = PASS  [OK]
- optimized runtime 0.960s <= 60s  [OK]
- optimized peak RSS 62236 kB = 0.06 GB <= 2 GB  [OK]
- 无资源负优化：Total -28.45%  [OK]
=> mixed_1000 判定: PASS

## 运行参数
- baseline: yosys-baseline -Q -p "read_verilog -sv design.v; hierarchy -check -top stress_top; proc; opt_clean; write_rtlil baseline_generic.il; synth_intel -family cycloneiv -top stress_top; stat -json; write_rtlil baseline_mapped.il"
- optimized: yosys-optimized(含6c5fcd0 pmux_opt内置) 同上但 proc 后执行 pmux_opt
- EQY: gold=原RTL / gate=optimized_generic.il
