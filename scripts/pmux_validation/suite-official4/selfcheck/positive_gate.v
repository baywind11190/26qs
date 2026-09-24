// selfcheck positive gate: 布尔等价改写
// y = ab ^ cd ^ (ab&cd)  ==  (ab) | (cd)
module selfcheck_pos (
    input  wire a,
    input  wire b,
    input  wire c,
    input  wire d,
    output wire y
);
    wire ab = a & b;
    wire cd = c & d;
    assign y = ab ^ cd ^ (ab & cd);
endmodule
