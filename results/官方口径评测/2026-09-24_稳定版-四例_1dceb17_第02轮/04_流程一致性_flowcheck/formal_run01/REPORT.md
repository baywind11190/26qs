# 04 流程一致性检查（原生 vs 拆分 baseline）

- 工具: /home/fpga/eda/yosys-baseline/build/yosys（Yosys 0.69 / 源码提交 9f75ca1f9834a39a863915b5dae0c7b1e33533bc）
- 输入树: results/官方口径评测/2026-09-24_稳定版-四例_1dceb17_第02轮/02_冻结源码与输入_assets/tree
- 拆分流程: `synth_intel -run begin:coarse` + 手工展开 coarse 21 条命令 + `synth_intel -run map_bram:`
- 两侧命令均与 techlibs/intel/synth_intel.cc (9f75ca1f9) 源码逐条一致；baseline 侧无 pmux_opt。

| case | native rc | split rc | netlist | nl_sha_equal | stat_total | stat_comb | stat_dff | check_assert(split) |
|---|---|---|---|---|---|---|---|---|
| test1 | 0 | 0 | 逐字节相等 | True | 510 | 286 | 222 | True |
| test2 | 0 | 0 | 逐字节相等 | True | 25 | 25 | 0 | True |
| test3 | 0 | 0 | 逐字节相等 | True | 30 | 12 | 17 | True |
| test4 | 0 | 0 | 逐字节相等 | True | 46 | 35 | 10 | True |

## 结论

- 逐例网表、资源和检查结果见上表；全部满足：True。
- **流程一致性: PASS**

说明：拆分侧日志中的 `synth_intel` 启动次数为 3 次（原生 1 次）、并额外包含对称的 `check -assert` 与 `write_rtlil` dump 命令；
coarse 阶段的 21 条命令与原生源码逐条一致（见 command_sequence_*.txt）。
