// selfcheck negative gold: y = a & b（期望被 EQY 拒绝当 gate 为 OR）
module selfcheck_neg (
    input  wire a,
    input  wire b,
    output wire y
);
    assign y = a & b;
endmodule
