#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

yosys-config --build pmux_opt.so src/pmux_opt.cc

cases=(
"b1_basic:YES"
"b2_width12:YES"
"b3_partial_decode:YES"
"b4_mixed_expression:YES"
"b5_no_control_data:NO"
"b6_expression_only:NO"
"b7_control1_boundary:NO"
"b8_control8:YES"
"b9_shuffled_order:YES"
"b10_two_controls:YES"
"b11_repeated_bits:YES"
"b12_zero_selector:YES"
"b13_combinational:YES"
"b14_independent_pmux:YES"
)

printf "%-24s %-9s %-9s %-8s %-8s\n" \
       "CASE" "TRIGGER" "EQY" "BEFORE" "AFTER"

printf "%-24s %-9s %-9s %-8s %-8s\n" \
       "------------------------" "---------" "---------" "--------" "--------"

fail=0

for item in "${cases[@]}"; do
    top="${item%%:*}"
    expected="${item##*:}"

    src="$ROOT/regression/pattern_b/$top.v"
    out="$ROOT/results/pattern_b/$top"

    rm -rf "$out"
    mkdir -p "$out"

    yosys -m "$ROOT/pmux_opt.so" -p "
        read_verilog $src
        hierarchy -check -top $top
        proc
        opt
        pmux_opt
        opt
        stat -width
    " >"$out/plugin.log" 2>&1

    if grep -q "BRANCH-CONST FOLD" "$out/plugin.log"; then
        actual="YES"
    else
        actual="NO"
    fi

    if [[ "$actual" == "$expected" ]]; then
        trigger_status="PASS"
    else
        trigger_status="FAIL"
        fail=1
    fi

    before=$(
        yosys -p "
            read_verilog $src
            hierarchy -check -top $top
            proc
            opt
            synth_intel -family cycloneiv -top $top
            stat
        " 2>&1 |
        awk '$2=="cycloneiv_lcell_comb"{v=$1} END{if(v=="") print "-"; else print v}'
    )

    after=$(
        yosys -m "$ROOT/pmux_opt.so" -p "
            read_verilog $src
            hierarchy -check -top $top
            proc
            opt
            pmux_opt
            opt
            synth_intel -family cycloneiv -top $top
            stat
        " 2>&1 |
        awk '$2=="cycloneiv_lcell_comb"{v=$1} END{if(v=="") print "-"; else print v}'
    )

    cat >"$out/check.eqy" <<EQY
[gold]
read_verilog $src
hierarchy -check -top $top
proc
opt
prep -top $top

[gate]
plugin -i $ROOT/pmux_opt.so
read_verilog $src
hierarchy -check -top $top
proc
opt
pmux_opt
opt
prep -top $top

[strategy simple]
use sat
depth 5
EQY

    if (
        cd "$out"
        eqy -f -d eqy check.eqy >eqy.log 2>&1
    ); then
        eqy_status="PASS"
    else
        eqy_status="FAIL"
        fail=1
    fi

    printf "%-24s %-9s %-9s %-8s %-8s\n" \
           "$top" "$trigger_status" "$eqy_status" "$before" "$after"
done

echo

if [[ "$fail" -eq 0 ]]; then
    echo "PATTERN B REGRESSION: PASS"
else
    echo "PATTERN B REGRESSION: FAIL"
    exit 1
fi
