#!/usr/bin/env bash
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

OUT="$ROOT/results/full_regression"
rm -rf "$OUT"
mkdir -p "$OUT"

fail=0

echo "========================================"
echo " PMUX OPT FULL REGRESSION"
echo "========================================"
echo

yosys-config --build pmux_opt.so src/pmux_opt.cc || exit 1

run_regression()
{
    name="$1"
    script="$2"

    echo
    echo "========== $name =========="

    if "$script" 2>&1 | tee "$OUT/${name}.log"; then
        echo "$name: PASS"
    else
        echo "$name: FAIL"
        fail=1
    fi
}

run_regression "pattern_a" "$ROOT/scripts/run_pattern_a_regression.sh"
run_regression "pattern_b" "$ROOT/scripts/run_pattern_b_regression.sh"
run_regression "pattern_c" "$ROOT/scripts/run_pattern_c_regression.sh"

echo
echo "========================================"
echo " PUBLIC TEST1-4 BENCHMARK"
echo "========================================"
echo

printf "%-6s %-6s %-8s %-8s %-9s %-9s %-7s %-7s %-8s %-8s %-9s %-9s %-9s\n" \
    "TEST" "EQY" \
    "COMB_B" "COMB_O" \
    "TOTAL_B" "TOTAL_O" \
    "DFF_B" "DFF_O" \
    "TIME_B" "TIME_O" \
    "RSS_B" "RSS_O" \
    "STATUS"

printf "%-6s %-6s %-8s %-8s %-9s %-9s %-7s %-7s %-8s %-8s %-9s %-9s %-9s\n" \
    "------" "------" \
    "--------" "--------" \
    "---------" "---------" \
    "-------" "-------" \
    "--------" "--------" \
    "---------" "---------" \
    "---------"

printf "test,eqy,comb_before,comb_after,total_before,total_after,dff_before,dff_after,time_before_s,time_after_s,rss_before_kb,rss_after_kb,status\n" \
    > "$OUT/public_benchmark.csv"

for n in 1 2 3 4; do

    top="test$n"
    src="$(find "$ROOT/pmux_case" -path "*/test$n/test$n.v" | head -n 1)"

    case_out="$OUT/test$n"
    mkdir -p "$case_out"

    if [[ -z "$src" ]]; then
        echo "ERROR: cannot find test$n.v"
        fail=1
        continue
    fi

    /usr/bin/time \
        -f "%e %M" \
        -o "$case_out/base.time" \
        yosys -p "
            read_verilog $src
            hierarchy -check -top $top
            proc
            opt
            synth_intel -family cycloneiv -top $top
            tee -o $case_out/base_stat.json stat -json
        " > "$case_out/base.log" 2>&1

    base_rc=$?

    /usr/bin/time \
        -f "%e %M" \
        -o "$case_out/opt.time" \
        yosys -m "$ROOT/pmux_opt.so" -p "
            read_verilog $src
            hierarchy -check -top $top
            proc
            opt
            pmux_opt
            opt
            synth_intel -family cycloneiv -top $top
            tee -o $case_out/opt_stat.json stat -json
        " > "$case_out/opt.log" 2>&1

    opt_rc=$?

    if [[ "$base_rc" -ne 0 || "$opt_rc" -ne 0 ]]; then
        echo "test$n synthesis FAIL"
        fail=1
        continue
    fi

    comb_b="$(
        awk '$2=="cycloneiv_lcell_comb"{v=$1} END{if(v=="") print 0; else print v}' \
            "$case_out/base.log"
    )"

    comb_o="$(
        awk '$2=="cycloneiv_lcell_comb"{v=$1} END{if(v=="") print 0; else print v}' \
            "$case_out/opt.log"
    )"

    dff_b="$(
        awk '$2=="dffeas"{v=$1} END{if(v=="") print 0; else print v}' \
            "$case_out/base.log"
    )"

    dff_o="$(
        awk '$2=="dffeas"{v=$1} END{if(v=="") print 0; else print v}' \
            "$case_out/opt.log"
    )"

    total_b="$(
        python3 - "$case_out/base_stat.json" "$top" <<'PY'
import json
import sys

path = sys.argv[1]
top = sys.argv[2]

with open(path, "r") as f:
    data = json.load(f)

modules = data.get("modules", {})

module = modules.get("\\" + top)

if module is None:
    module = modules.get(top)

if module is None:
    raise SystemExit("module not found: " + top)

print(module.get("num_cells", 0))
PY
    )"

    total_o="$(
        python3 - "$case_out/opt_stat.json" "$top" <<'PY'
import json
import sys

path = sys.argv[1]
top = sys.argv[2]

with open(path, "r") as f:
    data = json.load(f)

modules = data.get("modules", {})

module = modules.get("\\" + top)

if module is None:
    module = modules.get(top)

if module is None:
    raise SystemExit("module not found: " + top)

print(module.get("num_cells", 0))
PY
    )"

    read -r time_b rss_b < "$case_out/base.time"
    read -r time_o rss_o < "$case_out/opt.time"

    rm -rf "$case_out/eqy"

    if eqy -f \
        -d "$case_out/eqy" \
        "$ROOT/formal/test${n}_pairswap.eqy" \
        > "$case_out/eqy.log" 2>&1; then

        eqy_status="PASS"
    else
        eqy_status="FAIL"
        fail=1
    fi

    status="OK"

    if (( comb_o > comb_b || total_o > total_b )); then
        status="REGRESS"
        fail=1
    elif (( comb_o < comb_b || total_o < total_b )); then
        status="GAIN"
    fi

    printf "%-6s %-6s %-8s %-8s %-9s %-9s %-7s %-7s %-8s %-8s %-9s %-9s %-9s\n" \
        "test$n" "$eqy_status" \
        "$comb_b" "$comb_o" \
        "$total_b" "$total_o" \
        "$dff_b" "$dff_o" \
        "$time_b" "$time_o" \
        "$rss_b" "$rss_o" \
        "$status"

    printf "test%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" \
        "$n" "$eqy_status" \
        "$comb_b" "$comb_o" \
        "$total_b" "$total_o" \
        "$dff_b" "$dff_o" \
        "$time_b" "$time_o" \
        "$rss_b" "$rss_o" \
        "$status" \
        >> "$OUT/public_benchmark.csv"
done

echo
echo "========================================"

if [[ "$fail" -eq 0 ]]; then
    echo "FULL REGRESSION: PASS"
else
    echo "FULL REGRESSION: FAIL"
    exit 1
fi
