# 隐藏测试风格盲测汇总（commit 6c5fcd0；方案A /tmp 工作区）

| Case | 测试目的 | Trigger | EQY | Resource | 结论 |
|---|---|---|---|---|---|
| blind01 | selector 乱序（case 非升序+切片乱序） | YES（pair-swap candidate=1 / rebuilt=1；Pattern C 输出 0 行） | PASS | Total 26→16; Comb 26→16 | PASS（EQY 正确；资源无负优化） |
| blind02 | partial decode（4bit 控制仅 2 个 case value） | YES（pair-swap candidate=0 / rebuilt=0；Pattern C 输出 2 行） | PASS | Total 3→3; Comb 3→3 | PASS（EQY 正确；资源无负优化） |
| blind03 | 多个独立 control 域（ca/cb/cc） | YES（pair-swap candidate=1 / rebuilt=1；Pattern C 输出 1 行） | PASS | Total 56→47; Comb 56→47 | PASS（EQY 正确；资源无负优化） |
| blind04 | external data 依赖（混合 ctl 表达式与 ext） | YES（pair-swap candidate=0 / rebuilt=0；Pattern C 输出 1 行） | PASS | Total 10→10; Comb 10→10 | PASS（EQY 正确；资源无负优化） |
| blind05 | 无可优化结构负例 | NO（pair-swap candidate=0 / rebuilt=0；Pattern C 输出 0 行） | PASS | Total 72→72; Comb 72→72 | PASS（EQY 正确；资源无负优化） |
| blind06 | PMUX + 混合组合逻辑 | YES（pair-swap candidate=1 / rebuilt=1；Pattern C 输出 0 行） | PASS | Total 44→31; Comb 44→31 | PASS（EQY 正确；资源无负优化） |
| blind07 | 边界位宽 W=1/2/4/8/12/16 | YES（pair-swap candidate=6 / rebuilt=6；Pattern C 输出 0 行） | PASS | Total 259→172; Comb 259→172 | PASS（EQY 正确；资源无负优化） |
| blind08 | 多 PMUX 混放（可优化/不可优化/多 control） | YES（pair-swap candidate=1 / rebuilt=1；Pattern C 输出 1 行） | PASS | Total 51→42; Comb 51→42 | PASS（EQY 正确；资源无负优化） |

## 完成标准核对
- 8 类盲测各至少 1 个测试：通过（blind01–blind08）
- blind07 覆盖 WIDTH=1/2/4/8/12/16：通过（6 个参数化实例）
- 每个 case 有测试目的 / EQY / 资源 before-after / Trigger：通过
- 异常：无（8/8 EQY PASS；无 crash / timeout / RSS 异常）
