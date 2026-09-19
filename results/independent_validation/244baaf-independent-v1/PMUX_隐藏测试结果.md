# PMUX 隐藏测试结果

- Commit：`244baaf19c8abf62443aabfb5ff449ff535a447d`
- Run ID：`244baaf-independent-v1`

## Blind tests

| Case | 测试目的 | Trigger | EQY | Total | Comb | DFF | Time | RSS | Status |
|---|---|---|---|---:|---:|---:|---:|---:|---|
| blind01 | Selector order shuffled; one selector drives permuted case blocks (non-ascending case values). | True | PASS | 31→19 (+38.71%) | 31→19 | 0→0 | 0.0800→0.0800s | 29348→29552kB | PASS |
| blind02 | Partial decode; control width exceeds the set of present case values. | False | PASS | 45→45 (+0.00%) | 45→45 | 0→0 | 0.0800→0.0800s | 29568→29468kB | PASS |
| blind03 | Multiple independent control domains (ca/cb/cc) must not interfere. | True | PASS | 57→49 (+14.04%) | 56→48 | 0→0 | 0.0800→0.0800s | 29816→29564kB | PASS |
| blind04 | Branches mix control-derived expressions with external-data dependencies (no illegal constant folding). | True | PASS | 53→53 (+0.00%) | 53→53 | 0→0 | 0.0900→0.0900s | 29764→29828kB | PASS |
| blind05 | No optimizable structure; expect EQY PASS and no obvious resource regression. | False | PASS | 29→29 (+0.00%) | 29→29 | 0→0 | 0.0700→0.0800s | 29464→29636kB | PASS |
| blind06 | PMUX mixed with and/or/xor/not/reduce/ordinary mux logic. | True | PASS | 47→33 (+29.79%) | 47→33 | 0→0 | 0.0800→0.0800s | 29632→29716kB | PASS |
| blind07 | Boundary widths: 1,2,4,8,12,16. | True | PASS | 259→172 (+33.59%) | 259→172 | 0→0 | 0.1400→0.1100s | 30356→30104kB | PASS |
| blind08 | Multiple PMUX structures: optimizable, non-optimizable, shared and independent controls. | True | PASS | 52→42 (+19.23%) | 52→42 | 0→0 | 0.0800→0.0800s | 29496→29864kB | PASS |

## 判定

- 所有 blind case 首先要求 EQY PASS。
- 资源增加不使用自创百分比阈值；出现增加时标记 NEEDS_ANALYSIS。
- 发生 EQY FAIL / crash / runtime>60s / RSS>2GB 时属于硬失败。
