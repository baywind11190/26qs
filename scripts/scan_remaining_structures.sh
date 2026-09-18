#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

mkdir -p results/remaining_scan

yosys-config --build pmux_opt.so src/pmux_opt.cc

for n in 1 2 3 4; do
    src=$(find ./pmux_case -path "*/test$n/test$n.v" | head -n 1)

    echo
    echo "========================================"
    echo "TEST$n"
    echo "========================================"

    yosys -m ./pmux_opt.so -p "
        read_verilog $src
        hierarchy -check -top test$n
        proc
        opt
        pmux_opt
        opt
        stat -width
        write_rtlil results/remaining_scan/test${n}_after_opt.il
    " > "results/remaining_scan/test${n}.log" 2>&1

    echo "--- Remaining cells ---"

    grep -E '^[[:space:]]+[0-9]+[[:space:]]+\$(pmux|mux|eq|logic_not|not|reduce_or|reduce_and|reduce_bool)_' \
        "results/remaining_scan/test${n}.log" || true

    echo
    echo "--- Remaining PMUX ---"

    awk '
    /^[[:space:]]*cell \$pmux / {
        p=1
        print
        next
    }

    p && /parameter \\WIDTH|parameter \\S_WIDTH|connect \\A|connect \\B|connect \\S|connect \\Y/ {
        print
    }

    p && /^[[:space:]]*end$/ {
        p=0
        print ""
    }
    ' "results/remaining_scan/test${n}_after_opt.il"
done
