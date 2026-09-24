// H2 拒绝例：非目标结构（普通 mux，非 pmux）
module h2n_non_target (
    input  wire sel,
    input  wire [7:0] a, b_out,
    output wire [7:0] y
);
    assign y = sel ? a : b_out;
endmodule
