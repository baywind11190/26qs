// selfcheck negative gate: y = a | b（与 gold 不等价，期望 EQY 给出反例）
module selfcheck_neg (
    input  wire a,
    input  wire b,
    output wire y
);
    assign y = a | b;
endmodule
