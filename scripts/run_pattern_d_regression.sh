#!/usr/bin/env bash
set -u

cd "$(dirname "$0")/.."

PLUGIN="$(pwd)/pmux_opt.so"
TEST_DIR="tests/pattern_d"
RESULT_DIR="results/pattern_d_regression"

mkdir -p "$RESULT_DIR"

declare -A EXPECTED_REWRITE=(
    [d1_positive_single]=0
    [d2_positive_pmux]=2
    [d3_direct_output]=0
    [d4_pmux_extra_user]=0
    [d5_no_guard]=0
    [d6_guard_mismatch]=0
    [d7_signed_eq]=0
    [d8_guard_zero]=0
)

fail=0

printf "%-24s %-8s %-8s %-8s %-8s\n" \
    "CASE" "REWRITE" "EQY" "BASE" "OPT"

for name in \
    d1_positive_single \
    d2_positive_pmux \
    d3_direct_output \
    d4_pmux_extra_user \
    d5_no_guard \
    d6_guard_mismatch \
    d7_signed_eq \
    d8_guard_zero
do
    src="$TEST_DIR/$name.v"
    out="$RESULT_DIR/$name"

    mkdir -p "$out"

    yosys -m "$PLUGIN" -p "
        read_verilog $src
        hierarchy -check -top top
        proc
        opt
        pmux_opt
        opt
    " > "$out/rewrite.log" 2>&1

    rewrite_count="$(
        grep -c 'GUARD-AWARE EQ REWRITE' \
            "$out/rewrite.log" || true
    )"

    expected="${EXPECTED_REWRITE[$name]}"

    if [[ "$rewrite_count" -ne "$expected" ]]; then
        rewrite_status="BAD:${rewrite_count}/${expected}"
        fail=1
    else
        rewrite_status="PASS:${rewrite_count}"
    fi

    cat > "$out/check.eqy" <<EQY
[gold]
read_verilog $src
hierarchy -check -top top
proc
opt
prep -top top

[gate]
plugin -i $PLUGIN
read_verilog $src
hierarchy -check -top top
proc
opt
pmux_opt
opt
prep -top top

[strategy simple]
use sat
depth 1
EQY

    rm -rf "$out/eqy"

    if timeout 60s eqy -j "$(nproc)" -f \
        -d "$out/eqy" \
        "$out/check.eqy" \
        > "$out/eqy.log" 2>&1
    then
        eqy_status="PASS"
    else
        eqy_status="FAIL"
        fail=1
    fi

    yosys -p "
        read_verilog $src
        hierarchy -check -top top
        proc
        opt
        synth_intel -family cycloneiv -top top
        stat
    " > "$out/base.log" 2>&1

    yosys -m "$PLUGIN" -p "
        read_verilog $src
        hierarchy -check -top top
        proc
        opt
        pmux_opt
        opt
        synth_intel -family cycloneiv -top top
        stat
    " > "$out/opt.log" 2>&1

    base_comb="$(
        awk '$2 == "cycloneiv_lcell_comb" {v=$1} END {print v+0}' \
            "$out/base.log"
    )"

    opt_comb="$(
        awk '$2 == "cycloneiv_lcell_comb" {v=$1} END {print v+0}' \
            "$out/opt.log"
    )"

    if [[ "$opt_comb" -gt "$base_comb" ]]; then
        fail=1
    fi

    printf "%-24s %-8s %-8s %-8s %-8s\n" \
        "$name" \
        "$rewrite_status" \
        "$eqy_status" \
        "$base_comb" \
        "$opt_comb"
done

echo

if [[ "$fail" -eq 0 ]]; then
    echo "PATTERN D REGRESSION: PASS"
    exit 0
else
    echo "PATTERN D REGRESSION: FAIL"
    exit 1
fi
