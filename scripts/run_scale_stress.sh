#!/usr/bin/env bash
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

OUT="$ROOT/results/scale_stress"
rm -rf "$OUT"
mkdir -p "$OUT"

yosys-config --build pmux_opt.so src/pmux_opt.cc || exit 1

cases=(
    "mixed_100:mixed:100"
    "mixed_250:mixed:250"
    "mixed_500:mixed:500"
    "mixed_750:mixed:750"
    "mixed_1000:mixed:1000"
    "pattern_a_1000:pattern_a:1000"
    "expr_1000:expr:1000"
    "negative_1000:negative:1000"
)

printf "%-17s %-6s %-5s %-7s %-7s %-7s %-7s %-7s %-7s %-7s %-8s\n" \
    "CASE" "NODES" "EQY" \
    "COMB_B" "COMB_O" \
    "TOT_B" "TOT_O" \
    "T_B" "T_O" \
    "RSS_MB" "STATUS"

printf "%-17s %-6s %-5s %-7s %-7s %-7s %-7s %-7s %-7s %-7s %-8s\n" \
    "-----------------" "------" "-----" \
    "-------" "-------" \
    "-------" "-------" \
    "-------" "-------" \
    "-------" "--------"

echo "case,mode,target_nodes,actual_nodes,eqy,comb_before,comb_after,total_before,total_after,time_before_s,time_after_s,rss_after_kb,status" \
    > "$OUT/results.csv"

fail=0

for item in "${cases[@]}"; do

    name="${item%%:*}"
    rest="${item#*:}"
    mode="${rest%%:*}"
    target="${rest##*:}"

    case_out="$OUT/$name"
    mkdir -p "$case_out"

    src="$case_out/design.v"

    echo
    echo "[generate] $name"

    python3 "$ROOT/scripts/gen_scale_case.py" \
        --mode "$mode" \
        --target "$target" \
        --output "$src"

    nodes="$(
        python3 -c \
        'import json,sys; print(json.load(open(sys.argv[1]))["actual_nodes"])' \
        "$src.json"
    )"

    echo "[base synth] $name"

    /usr/bin/time \
        -f "%e %M" \
        -o "$case_out/base.time" \
        timeout 65s \
        yosys -p "
            read_verilog $src
            hierarchy -check -top stress_top
            proc
            opt
            synth_intel -family cycloneiv -top stress_top
            tee -o $case_out/base_stat.json stat -json
        " > "$case_out/base.log" 2>&1

    base_rc=$?

    echo "[optimized synth] $name"

    /usr/bin/time \
        -f "%e %M" \
        -o "$case_out/opt.time" \
        timeout 65s \
        yosys -m "$ROOT/pmux_opt.so" -p "
            read_verilog $src
            hierarchy -check -top stress_top
            proc
            opt
            pmux_opt
            opt
            synth_intel -family cycloneiv -top stress_top
            tee -o $case_out/opt_stat.json stat -json
        " > "$case_out/opt.log" 2>&1

    opt_rc=$?

    if [[ "$base_rc" -ne 0 || "$opt_rc" -ne 0 ]]; then
        printf "%-17s %-6s %-5s %-7s %-7s %-7s %-7s %-7s %-7s %-7s %-8s\n" \
            "$name" "$nodes" "-" "-" "-" "-" "-" "-" "-" "-" "SYNTH_FAIL"

        echo "$name,$mode,$target,$nodes,-,-,-,-,-,-,-,-,SYNTH_FAIL" \
            >> "$OUT/results.csv"

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

    total_b="$(
        python3 -c '
import json,sys
d=json.load(open(sys.argv[1]))
m=d["modules"].get("\\stress_top") or d["modules"].get("stress_top")
print(m["num_cells"])
' "$case_out/base_stat.json"
    )"

    total_o="$(
        python3 -c '
import json,sys
d=json.load(open(sys.argv[1]))
m=d["modules"].get("\\stress_top") or d["modules"].get("stress_top")
print(m["num_cells"])
' "$case_out/opt_stat.json"
    )"

    read -r time_b rss_b < "$case_out/base.time"
    read -r time_o rss_o < "$case_out/opt.time"

    rss_mb="$(
        awk -v x="$rss_o" 'BEGIN {printf "%.1f", x/1024}'
    )"

    echo "[eqy] $name"

    cat > "$case_out/check.eqy" <<EOF
[gold]
read_verilog $src
hierarchy -check -top stress_top
proc
opt
prep -top stress_top

[gate]
plugin -i $ROOT/pmux_opt.so
read_verilog $src
hierarchy -check -top stress_top
proc
opt
pmux_opt
opt
prep -top stress_top

[strategy simple]
use sat
depth 1
EOF

    rm -rf "$case_out/eqy"

    if eqy -f \
        -d "$case_out/eqy" \
        "$case_out/check.eqy" \
        > "$case_out/eqy.log" 2>&1; then
        eqy_status="PASS"
    else
        eqy_status="FAIL"
        fail=1
    fi

    status="PASS"

    if (( comb_o > comb_b || total_o > total_b )); then
        status="RESOURCE_REGRESS"
        fail=1
    fi

    time_ok="$(
        awk -v x="$time_o" 'BEGIN {print (x <= 60.0) ? 1 : 0}'
    )"

    rss_ok="$(
        awk -v x="$rss_o" 'BEGIN {print (x <= 2097152) ? 1 : 0}'
    )"

    if [[ "$time_ok" != "1" ]]; then
        status="TIME_FAIL"
        fail=1
    fi

    if [[ "$rss_ok" != "1" ]]; then
        status="MEM_FAIL"
        fail=1
    fi

    if [[ "$eqy_status" != "PASS" ]]; then
        status="EQY_FAIL"
    fi

    printf "%-17s %-6s %-5s %-7s %-7s %-7s %-7s %-7s %-7s %-7s %-8s\n" \
        "$name" "$nodes" "$eqy_status" \
        "$comb_b" "$comb_o" \
        "$total_b" "$total_o" \
        "$time_b" "$time_o" \
        "$rss_mb" "$status"

    echo "$name,$mode,$target,$nodes,$eqy_status,$comb_b,$comb_o,$total_b,$total_o,$time_b,$time_o,$rss_o,$status" \
        >> "$OUT/results.csv"

done

echo
echo "========================================"

if [[ "$fail" -eq 0 ]]; then
    echo "SCALE STRESS: PASS"
else
    echo "SCALE STRESS: FAIL"
    exit 1
fi
