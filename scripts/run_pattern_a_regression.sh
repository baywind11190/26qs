#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

yosys-config --build pmux_opt.so src/pmux_opt.cc

cases=(
"a1_width4_bit0:YES"
"a2_width4_bit1:YES"
"a3_width8_bit2:YES"
"a4_half_swap:NO"
"a5_one_special:NO"
"a6_shuffled_order:YES"
"a7_partial_decode:NO"
"a8_false_positive:NO"
"a9_three_pmux:YES"
)

printf "%-24s %-9s %-9s %-8s %-8s\n" \
       "CASE" "TRIGGER" "EQY" "BEFORE" "AFTER"
printf "%-24s %-9s %-9s %-8s %-8s\n" \
       "------------------------" "---------" "---------" "--------" "--------"

fail=0

for item in "${cases[@]}"; do
    top="${item%%:*}"
    expected="${item##*:}"

    src="$ROOT/regression/pattern_a/$top.v"
    out="$ROOT/results/pattern_a/$top"

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

    if grep -q "PAIR-SWAP REBUILT" "$out/plugin.log"; then
        actual="YES"
    else
        actual="NO"
    fi

    if [[ "$actual" != "$expected" ]]; then
        trigger_status="FAIL"
        fail=1
    else
        trigger_status="PASS"
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

    if eqy -f "$out/check.eqy" >"$out/eqy.log" 2>&1; then
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
    echo "PATTERN A REGRESSION: PASS"
else
    echo "PATTERN A REGRESSION: FAIL"
    exit 1
fi
