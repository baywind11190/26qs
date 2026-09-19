# H1 开发侧冻结流程复测报告

日期：2026-09-19。结果目录：results/frozen_20260919_224357/。

此次为同一开发机器上的固定提交复测，不是队友独立验证。
算法源码未修改。stable=244baaf19c8abf62443aabfb5ff449ff535a447d；candidate=0c0ee40aabfaf62fad3ab7c04dd42d092d6ca483。

## 验证结果

- P：12 个 H1 案例 + 4 个公开案例，全部通过。
- R1：相同 16 个案例，全部通过。
- 共 80 次 EQY 正向检查 PASS：P 每例两组网表对比，R1 每例两组网表对比加原始 RTL 预处理参考对比。
- 故意不等价的最小负对照被拒绝（EQY rc=2），未计入正向检查。
- 32 个 case/flow 均无 Total 退化、综合超时或 RSS 超限。
- P 的 H1 触发次数符合预期；12 个 RTL 与历史案例逐字节一致。

## 公开资源

| 流程 | Total | Comb | DFF |
|---|---|---|---|
| P | 611→525（下降 14.08%） | 358→277 | 249→244 |
| R1 | 611→526（下降 13.91%） | 358→278 | 249→244 |

P test3：Total 30→23，Comb 12→10，DFF 17→12。
R1 test3：Total 30→24，Comb 12→11，DFF 17→12。
以上数字单独统计，两条流程不能混合计算。

## H1 对父提交的 P 流程 Total 收益

| case | stable | H1 |
|---|---:|---:|
| h1_p1_threshold | 104 | 84 |
| h1_p2_swapbit2 | 192 | 168 |
| h1_p3_shuffle | 60 | 46 |
| h1_p4_large | 797 | 355 |
| h1_p5_zero_special | 56 | 56 |
| h1_p6_one_special | 43 | 43 |

六个拒绝案例均没有 pair-swap rewrite，且相对 stable 无 Total 变化。

## 复现与待办

执行 `python3 scripts/run_frozen_validation.py --suite all`。
详细规范见 frozen_validation.md。原始日志、配置、网表、工具版本、源码/插件哈希见本次结果目录。
首次开发试跑 frozen_20260919_224119 因网表导出误用 design -push 导致空网表，不是有效验证；问题已修正为 design -push-copy。
随后 frozen_20260919_224211 全部通过；最终上述目录包含负对照及工具路径记录，是本次采用的版本。

未重跑 A/B/C/D 全回归和千节点压力测试；本次未更改算法。H1 专项输入也不等同于未经调参的隐藏测试。
仍需将新增验证文件提交并交队友在独立环境复现 P/R1，完成 H1 独立报告后再进入 H2。
