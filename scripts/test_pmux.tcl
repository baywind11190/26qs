cd /home/fpga/fpga/pmux-opt

yosys -import

read_verilog -sv tests/pmux_basic.sv
hierarchy -check -top pmux_basic

yosys proc

pmux_opt

stat
