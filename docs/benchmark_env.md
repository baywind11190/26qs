# PMUX Benchmark Environment

## 1. Operating System

- Platform: WSL2
- Distribution: Ubuntu 24.04.5 LTS
- Linux user: `fpga`

## 2. Yosys

Executable:

```text
/home/fpga/bin/yosys
```

Version:

```text
Yosys 0.69
git sha1 9f75ca1f9
GNU /usr/bin/c++ 13.3.0
```

Plugin build tool:

```text
/home/fpga/bin/yosys-config
```

Current plugin build command:

```bash
yosys-config --build build/pmux_opt.so src/pmux_opt.cc
```

## 3. EQY

Executable:

```text
/home/fpga/eda/eqy/install/bin/eqy
```

Version:

```text
EQY v0.69
```

The EQY verification chain has been confirmed operational with both:

- known-equivalent designs returning `PASS`
- intentionally non-equivalent designs returning `FAIL`

## 4. Z3

Executable:

```text
/usr/bin/z3
```

Version:

```text
Z3 version 4.8.12 - 64 bit
```

Ubuntu package:

```text
z3 4.8.12-3.1build1
```

The package version is currently held with:

```bash
sudo apt-mark hold z3
```

Verification command:

```bash
apt-mark showhold | grep '^z3$'
```

Expected output:

```text
z3
```

## 5. Performance Measurement

External performance measurement tool:

```text
/usr/bin/time
```

Measurements use:

```bash
/usr/bin/time -v
```

The primary recorded metrics are:

- Elapsed wall-clock time
- Maximum resident set size (RSS)
- Exit status

Each official case is currently measured three times.

For baseline reporting:

- execution time uses the median of three runs
- memory uses the maximum RSS observed across the three runs

## 6. Benchmark Comparison Principle

Baseline and optimized designs must use the same:

- physical machine
- WSL / Linux environment
- Yosys version
- EQY version
- solver environment
- input Verilog
- top module
- synthesis flow
- FPGA mapping target
- resource-statistics method
- performance-measurement method

Only the PMUX optimization step should differ between baseline and optimized flows.

## 7. FPGA Mapping Baseline

According to the current follow-up evaluation convention already confirmed for this project, the benchmark uses Cyclone IV mapping.

Current fixed Yosys mapping command:

```text
synth_intel -family cycloneiv
```

Yosys 0.69 reports that:

```text
-family <max10 | cyclone10lp | cycloneiv | cycloneive>
```

is supported by `synth_intel`.

The current project therefore uses:

```text
cycloneiv
```

as the fixed baseline mapping family.

The `synth_intel` command is marked experimental by Yosys 0.69. This warning is recorded as a tool limitation and is not treated as an execution failure.

## 8. Official Competition Cases

Official cases:

```text
pmux_case/competition_case/test1/test1.v
pmux_case/competition_case/test2/test2.v
pmux_case/competition_case/test3/test3.v
pmux_case/competition_case/test4/test4.v
```

Top modules:

```text
test1
test2
test3
test4
```

After:

```text
read_verilog
hierarchy -auto-top
proc
stat
```

the observed structures are:

```text
test1:
158 total cells
5  $pmux
36 $mux
75 $eq

test2:
4 total cells
0 $pmux
4 $mux

test3:
23 total cells
3 $pmux
9 $mux
7 $eq

test4:
18 total cells
0 $pmux
4 $mux
contains memory-related cells
```

Therefore the four official cases include both PMUX-producing cases and non-PMUX / mixed-logic control cases.

All four cases remain part of the benchmark.

## 9. EQY Baseline Verification

EQY configuration files:

```text
formal/competition/test1.eqy
formal/competition/test2.eqy
formal/competition/test3.eqy
formal/competition/test4.eqy
```

Current baseline identity-check results:

```text
test1: PASS, rc=0
test2: PASS, rc=0
test3: PASS, rc=0
test4: PASS, rc=0
```

For test1-test3, the current SAT strategy is:

```text
[strategy simple]
use sat
depth 5
```

### test4 memory handling

`test4` contains memory.

The original SAT-only configuration produced:

```text
Skipping strategy 'simple' ... as it contains memory.
ERROR: No configured strategy supports partition ...
```

Therefore `test4` applies:

```text
memory_map
```

to both gold and gate designs before the SAT strategy.

After `memory_map`, all test4 partitions successfully pass equivalence checking:

```text
Successfully proved designs equivalent
DONE (PASS, rc=0)
```

## 10. Negative EQY Self-Test

Negative test files:

```text
formal/negative/gold.v
formal/negative/gate.v
formal/negative/negative.eqy
```

The intentionally different logic is:

```text
gold:
y = a & b

gate:
y = a | b
```

These designs are intentionally not equivalent.

Observed EQY result:

```text
Failed to prove equivalence of partition negative_test.y
DONE (FAIL, rc=2)
```

Shell exit code:

```text
EQY_RC=2
```

This is the expected result.

The negative test is used only to prove that the verification infrastructure can reject an incorrect design. It is not included in optimization-rate statistics.

## 11. Cyclone IV Baseline Resource Results

The four official cases have been synthesized using:

```text
synth_intel -family cycloneiv
```

Current mapped resource results:

| Case | Total cells | cycloneiv_lcell_comb | dffeas | Other cells |
|---|---:|---:|---:|---:|
| test1 | 510 | 286 | 222 | 2 |
| test2 | 25 | 25 | 0 | 0 |
| test3 | 30 | 12 | 17 | 1 |
| test4 | 46 | 35 | 10 | 1 |

The current `other_cells` are:

```text
test1: 2 × $not
test2: none
test3: 1 × $not
test4: 1 × $not
```

These mapped cell counts are the current baseline values against which future optimized commits will be compared.

## 12. Baseline Performance Results

Each case was measured three times using:

```bash
/usr/bin/time -v
```

### test1

```text
Elapsed:
0.14 s
0.14 s
0.14 s

Maximum RSS:
33952 kB
33564 kB
33520 kB
```

Summary:

```text
Median time: 0.14 s
Maximum RSS: 33952 kB
```

### test2

```text
Elapsed:
0.05 s
0.05 s
0.05 s

Maximum RSS:
28632 kB
28824 kB
28956 kB
```

Summary:

```text
Median time: 0.05 s
Maximum RSS: 28956 kB
```

### test3

```text
Elapsed:
0.06 s
0.05 s
0.06 s

Maximum RSS:
29520 kB
29392 kB
28980 kB
```

Summary:

```text
Median time: 0.06 s
Maximum RSS: 29520 kB
```

### test4

```text
Elapsed:
0.07 s
0.07 s
0.07 s

Maximum RSS:
30056 kB
30104 kB
30028 kB
```

Summary:

```text
Median time: 0.07 s
Maximum RSS: 30104 kB
```

## 13. Baseline Summary

| Case | EQY | Total cells | Median time | Maximum RSS |
|---|---|---:|---:|---:|
| test1 | PASS | 510 | 0.14 s | 33952 kB |
| test2 | PASS | 25 | 0.05 s | 28956 kB |
| test3 | PASS | 30 | 0.06 s | 29520 kB |
| test4 | PASS | 46 | 0.07 s | 30104 kB |

All four official baseline identity checks currently pass.

## 14. Machine-Readable Baseline Summary

Automatic collection script:

```text
tools/collect_baseline.py
```

Run with:

```bash
python3 tools/collect_baseline.py
```

Generated CSV:

```text
results/baseline/baseline_summary.csv
```

Current summary values:

```text
test1: EQY=PASS, cells=510, time_median=0.1400 s, rss_max=33952 kB
test2: EQY=PASS, cells=25,  time_median=0.0500 s, rss_max=28956 kB
test3: EQY=PASS, cells=30,  time_median=0.0600 s, rss_max=29520 kB
test4: EQY=PASS, cells=46,  time_median=0.0700 s, rss_max=30104 kB
```

The CSV additionally records:

- case ID
- top module
- SHA-256 of each official Verilog input
- EQY status
- total mapped cells
- Cyclone IV combinational cells
- DFFEAS cells
- other cells
- all three timing measurements
- timing median
- all three RSS measurements
- maximum RSS

## 15. Current Benchmark Baseline Status

Completed:

```text
WSL2 environment fixed
Yosys 0.69 fixed
EQY v0.69 fixed
Z3 4.8.12-3.1build1 installed and held
GNU time available
4 official cases identified
Cyclone IV mapping flow fixed
4 baseline resource measurements complete
3-run performance measurements complete
4 official identity EQY checks PASS
negative EQY self-test correctly FAIL
baseline_summary.csv generated
```

The next integration stage is:

```text
receive a specific PMUX optimization commit
→ build pmux_opt plugin
→ generate optimized design
→ run EQY against baseline/golden design
→ map both flows using the same Cyclone IV process
→ compare mapped cell counts
→ measure optimized runtime and peak RSS
→ calculate optimization rate
→ report PASS / FAIL and reproducible logs
```

The validation side should not directly modify:

```text
src/pmux_opt.cc
```

unless the team explicitly changes the collaboration boundary.
