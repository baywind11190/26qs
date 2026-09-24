module a5_one_special(
    input  [2:0] control,

    input  [7:0] d0, d1, d2,
    input  [7:0] e0, e1, e2,

    input  [7:0] special_a,
    input  [7:0] special_b,
    input  [7:0] special_c,
    input  [7:0] special_d,

    output reg [7:0] x,
    output reg [7:0] y
);

always @* begin
    x = 8'b0;
    y = 8'b0;

    case (control)
        // 唯一一个“不满足 pair-swap”的特殊 pair
        3'd0: begin x = special_a; y = special_b; end
        3'd1: begin x = special_c; y = special_d; end

        3'd2: begin x = d0; y = e0; end
        3'd3: begin x = e0; y = d0; end

        3'd4: begin x = d1; y = e1; end
        3'd5: begin x = e1; y = d1; end

        3'd6: begin x = d2; y = e2; end
        3'd7: begin x = e2; y = d2; end
    endcase
end

endmodule
