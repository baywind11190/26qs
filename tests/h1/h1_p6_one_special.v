module h1_p6_one_special(
    input [3:0] control,
    input [63:0] din,
    output reg [1:0] out_a,
    output reg [1:0] out_b
);

always @*
begin
    case (control)
        4'd0: out_a = din[1:0];
        4'd1: out_a = din[9:8];
        4'd2: out_a = din[3:2];
        4'd3: out_a = din[11:10];
        4'd4: out_a = din[17:16];
        4'd5: out_a = din[25:24];
        4'd6: out_a = din[19:18];
        4'd7: out_a = din[27:26];
        4'd8: out_a = din[33:32];
        4'd9: out_a = din[41:40];
        4'd10: out_a = din[37:36];
        4'd11: out_a = din[43:42];
        4'd12: out_a = din[49:48];
        4'd13: out_a = din[57:56];
        4'd14: out_a = din[51:50];
        4'd15: out_a = din[59:58];
        default: out_a = 2'bx;
    endcase
end

always @*
begin
    case (control)
        4'd0: out_b = din[3:2];
        4'd1: out_b = din[11:10];
        4'd2: out_b = din[1:0];
        4'd3: out_b = din[9:8];
        4'd4: out_b = din[19:18];
        4'd5: out_b = din[27:26];
        4'd6: out_b = din[17:16];
        4'd7: out_b = din[25:24];
        4'd8: out_b = din[35:34];
        4'd9: out_b = din[43:42];
        4'd10: out_b = din[39:38];
        4'd11: out_b = din[41:40];
        4'd12: out_b = din[51:50];
        4'd13: out_b = din[59:58];
        4'd14: out_b = din[49:48];
        4'd15: out_b = din[57:56];
        default: out_b = 2'bx;
    endcase
end

endmodule
