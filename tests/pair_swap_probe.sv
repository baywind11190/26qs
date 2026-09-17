module pair_baseline (
    input  [3:0]  state,
    input  [11:0] i0, i1, i2, i3, i4, i5, i6, i7,
    input  [11:0] q0, q1, q2, q3, q4, q5, q6, q7,
    input  [11:0] I0h,
    input  [11:0] Q0h,
    output reg [11:0] out_a,
    output reg [11:0] out_b
);

always @* begin
    case (state)
        4'd0:  begin out_a = Q0h; out_b = I0h; end
        4'd1:  begin out_a = i0;  out_b = q0;  end
        4'd2:  begin out_a = q1;  out_b = i1;  end
        4'd3:  begin out_a = i1;  out_b = q1;  end
        4'd4:  begin out_a = q2;  out_b = i2;  end
        4'd5:  begin out_a = i2;  out_b = q2;  end
        4'd6:  begin out_a = q3;  out_b = i3;  end
        4'd7:  begin out_a = i3;  out_b = q3;  end
        4'd8:  begin out_a = q4;  out_b = i4;  end
        4'd9:  begin out_a = i4;  out_b = q4;  end
        4'd10: begin out_a = q5;  out_b = i5;  end
        4'd11: begin out_a = i5;  out_b = q5;  end
        4'd12: begin out_a = q6;  out_b = i6;  end
        4'd13: begin out_a = i6;  out_b = q6;  end
        4'd14: begin out_a = q7;  out_b = i7;  end
        4'd15: begin out_a = i7;  out_b = q7;  end
    endcase
end

endmodule


module pair_optimized (
    input  [3:0]  state,
    input  [11:0] i0, i1, i2, i3, i4, i5, i6, i7,
    input  [11:0] q0, q1, q2, q3, q4, q5, q6, q7,
    input  [11:0] I0h,
    input  [11:0] Q0h,
    output [11:0] out_a,
    output [11:0] out_b
);

reg [11:0] pair_i;
reg [11:0] pair_q;

always @* begin
    case (state[3:1])
        3'd0: begin pair_i = i0; pair_q = q0; end
        3'd1: begin pair_i = i1; pair_q = q1; end
        3'd2: begin pair_i = i2; pair_q = q2; end
        3'd3: begin pair_i = i3; pair_q = q3; end
        3'd4: begin pair_i = i4; pair_q = q4; end
        3'd5: begin pair_i = i5; pair_q = q5; end
        3'd6: begin pair_i = i6; pair_q = q6; end
        3'd7: begin pair_i = i7; pair_q = q7; end
    endcase
end

wire [11:0] normal_a =
    state[0] ? pair_i : pair_q;

wire [11:0] normal_b =
    state[0] ? pair_q : pair_i;

assign out_a =
    (state == 4'd0) ? Q0h : normal_a;

assign out_b =
    (state == 4'd0) ? I0h : normal_b;

endmodule
