module h1_n2_small_two_special(
    input [2:0] control,
    input [63:0] din,
    output reg [3:0] out_a,
    output reg [3:0] out_b
);

always @*
begin
    case (control)
        3'd0: out_a = din[3:0];
        3'd1: out_a = din[11:8];
        3'd2: out_a = din[19:16];
        3'd3: out_a = din[23:20];
        3'd4: out_a = din[35:32];
        3'd5: out_a = din[39:36];
        3'd6: out_a = din[51:48];
        3'd7: out_a = din[59:56];
        default: out_a = 4'bx;
    endcase
end

always @*
begin
    case (control)
        3'd0: out_b = din[7:4];
        3'd1: out_b = din[15:12];
        3'd2: out_b = din[23:20];
        3'd3: out_b = din[19:16];
        3'd4: out_b = din[39:36];
        3'd5: out_b = din[35:32];
        3'd6: out_b = din[55:52];
        3'd7: out_b = din[63:60];
        default: out_b = 4'bx;
    endcase
end

endmodule
