#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

yosys-config --build pmux_opt.so src/pmux_opt.cc

cases=(
"c1_partial_bits:YES"
"c2_full_expression:YES"
"c3_nested_expression:YES"
"c4_reduction_ops:YES"
"c5_partial_decode:YES"
"c6_combinational:YES"
"c7_external_dependency:NO"
"c8_two_controls:YES"
)

printf "%-25s %-9s %-9s %-8s %-8s %-8s %-9s\n" \
       "CASE" "TRIGGER" "EQY" "BITS" "BEFORE" "AFTER" "RESOURCE"

printf "%-25s %-9s %-9s %-8s %-8s %-8s %-9s\n" \
       "-------------------------" \
       "---------" \
       "---------" \
       "--------" \
       "--------" \
       "--------" \
       "---------"

fail=0

for item in "${cases[@]}"; do

    top="${item%%:*}"
    expected="${item##*:}"

    src="$ROOT/regression/pattern_c/$top.v"
    out="$ROOT/results/pattern_c/$top"

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

    if grep -q "BRANCH-EXPR CONST FOLD" "$out/plugin.log"; then
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

    bits=$(
        awk '
            /BRANCH-EXPR CONST FOLD/ {
                active=1
                next
            }

            active && /replaced bits/ {
                sum += $4
                active=0
            }

            END {
                print sum + 0
            }
        ' "$out/plugin.log"
    )

    before=$(
        yosys -p "
            read_verilog $src
            hierarchy -check -top $top
            proc
            opt
            synth_intel -family cycloneiv -top $top
            stat
        " 2>&1 |
        awk '
            $2=="cycloneiv_lcell_comb" {
                v=$1
            }

            END {
                if (v=="")
                    print 0
                else
                    print v
            }
        '
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
        awk '
            $2=="cycloneiv_lcell_comb" {
                v=$1
            }

            END {
                if (v=="")
                    print 0
                else
                    print v
            }
        '
    )

    if [[ "$before" != "-" && "$after" != "-" ]]; then

        if (( after < before )); then
            resource_status="GAIN"

        elif (( after == before )); then
            resource_status="SAME"

        else
            resource_status="REGRESS"
            fail=1
        fi

    else
        resource_status="UNKNOWN"
    fi

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

    printf "%-25s %-9s %-9s %-8s %-8s %-8s %-9s\n" \
           "$top" \
           "$trigger_status" \
           "$eqy_status" \
           "$bits" \
           "$before" \
           "$after" \
           "$resource_status"
done

echo

if [[ "$fail" -eq 0 ]]; then
    echo "PATTERN C REGRESSION: PASS"
else
    echo "PATTERN C REGRESSION: FAIL"
    exit 1
fi
