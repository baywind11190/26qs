# 02 `-set-def-formal` 实际约束了什么（移除前的核对）

## 1. 官方帮助文本（Yosys 0.69，`passes/sat/sat.cc:963-964`）

```
-set-def-formal
    add -set-def constraints for formal $anyinit, $anyconst, $anyseq cells
```

## 2. 实现中的全部施加点（`kernel/satgen.cc`）

| 位置 | 对象 | 施加的约束 |
| --- | --- | --- |
| `satgen.cc:1217`（内置 FF 分支，t=1） | **所有内置触发器**（含 `$anyinit`） | `assume(NOT(any(undef_q)))` —— 初值“已定义”假设 |
| `satgen.cc:1289`（`$anyconst`，t<2） | `$anyconst` 输出 | 输出“已定义”假设 |
| `satgen.cc:1307`（`$anyseq`） | `$anyseq` 输出 | 输出位强制为已定义 |
| `satgen.cc:1320`（同族处理） | （形式单元） | “已定义”假设 |
| `sat.cc:265-271`（组合条件） | `$anyinit` | **仅当 `-set-init-undef` 且 `-set-def-formal` 同时启用**时，其 Q 加入 `forced_def`（从 Sx 初值集合剔除） |

## 3. 本套设计中的实际作用对象（实测）

- 全部 8 链 106 个分区的运行日志中 `anyinit/anyseq/anyconst` 提及次数 = **0**；`modules/test3.il` 中同类计数 = 0。
- ⇒ 在本套四例设计中，`-set-def-formal` 的**唯一实际作用**是 `satgen.cc:1217` 的“所有触发器初值已定义”假设；
  `$anyconst/$anyseq/$anyinit` 相关约束为真空（无实例）。

## 4. 与 `-set-init-undef` 的关系（矛盾的直接来源）

- `-set-init-undef`：未显式约束的初值位约束为 x（`sat.cc:337-344`；导入见 `sat.cc:357-359` 的 `signals_eq`，含 undef 标志比较）。
- `-set-def-formal`：对**同一批位**假设 undef=0。
- ⇒ 含“未声明初值普通 FF”的设计：前提约束 UNSAT（已逐分区证明，见 01 与 `audit_summary.csv`）。

## 5. 移除影响评估（对照实验前的结论，后经实测确认）

- **保持不变**：`-set-def-inputs`（模块输入仍“已定义”）、`-set-assumes`（assume 单元仍生效）、断言集合、
  设计与网表、链/策略/深度（`-tempinduct -maxsteps 5`）逐行一致。
- **被移除的仅两类“定义性”假设**：FF 初值“已定义”（唯一实际项）与形式单元输出“已定义”（本套无实例）。
- **是否引入新的空检查**：约束放松只能使前提更易满足，不会产生前提 UNSAT；实测 noDF 下 106/106 前提 SAT（01），
  且检出能力对照（03）通过。
- **语义对齐**：移除后，未声明初值以真正的 x（undef）参与，与流水线既有 `in_gold===1'bx` 容忍项的设计意图一致；
  而 DF 组合与该意图直接冲突。
- 补记（工具事实，供参考）：`$anyinit` 的“初值定义豁免”（`forced_def`）也只在 DF 组合下生效（`sat.cc:265-271`）；
  本套无 `$anyinit` 实例，不受影响。

## 6. 结论

在本套输入上，移除 `-set-def-formal` = **去掉一组与 `-set-init-undef` 直接矛盾的“初值已定义”假设**；
不改变必须保留的输入定义、assume、断言与结构条件；不引入空检查（前提审计与检出能力双重验证）。
