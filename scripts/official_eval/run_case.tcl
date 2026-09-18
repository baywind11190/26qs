yosys -import

# Required environment variables
foreach var {RTL_FILE TOP GENERIC_NETLIST MAPPED_NETLIST STAT_JSON} {
    if {![info exists ::env($var)] || $::env($var) eq ""} {
        error "Missing required environment variable: $var"
    }
}

set rtl_file       $::env(RTL_FILE)
set top            $::env(TOP)
set generic_netlist $::env(GENERIC_NETLIST)
set mapped_netlist  $::env(MAPPED_NETLIST)
set stat_json       $::env(STAT_JSON)

puts "\[official_eval\] RTL_FILE        = $rtl_file"
puts "\[official_eval\] TOP             = $top"
puts "\[official_eval\] GENERIC_NETLIST = $generic_netlist"
puts "\[official_eval\] MAPPED_NETLIST  = $mapped_netlist"
puts "\[official_eval\] STAT_JSON       = $stat_json"

# ------------------------------------------------------------
# Common front-end flow
# ------------------------------------------------------------

yosys read_verilog -sv $rtl_file
yosys hierarchy -check -top $top
yosys proc

# The baseline Yosys does not contain pmux_opt.
# The optimized Yosys will contain it after integration.
# Both executables still use this exact same Tcl script.
if {[llength [info commands pmux_opt]] > 0} {
    puts "\[official_eval\] pmux_opt detected: executing optimization pass"
    yosys pmux_opt
} else {
    puts "\[official_eval\] pmux_opt not present: continuing without PMUX optimization"
}

yosys opt_clean

# Generic Yosys netlist:
# used later for RTL vs optimized-netlist EQY.
yosys write_rtlil $generic_netlist

# ------------------------------------------------------------
# Common FPGA mapping flow
# ------------------------------------------------------------

yosys synth_intel -family cycloneiv -top $top

# Resource statistics after identical Cyclone IV mapping.
yosys tee -o $stat_json stat -json

# Preserve the mapped design as a reproducible artifact.
yosys write_rtlil $mapped_netlist
