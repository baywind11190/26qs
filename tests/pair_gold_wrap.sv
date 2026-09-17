module pair_probe (
    input  [3:0]  state,
    input  [11:0] i0, i1, i2, i3, i4, i5, i6, i7,
    input  [11:0] q0, q1, q2, q3, q4, q5, q6, q7,
    input  [11:0] I0h,
    input  [11:0] Q0h,
    output [11:0] out_a,
    output [11:0] out_b
);

pair_baseline u_dut (
    .state(state),
    .i0(i0), .i1(i1), .i2(i2), .i3(i3),
    .i4(i4), .i5(i5), .i6(i6), .i7(i7),
    .q0(q0), .q1(q1), .q2(q2), .q3(q3),
    .q4(q4), .q5(q5), .q6(q6), .q7(q7),
    .I0h(I0h),
    .Q0h(Q0h),
    .out_a(out_a),
    .out_b(out_b)
);

endmodule
