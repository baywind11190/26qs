module h1_n1_three_special(
    input [3:0] control,
    input [127:0] din,
    output reg [3:0] out_a,
    output reg [3:0] out_b
);

always @*
begin
    case (control)
        4'd0: out_a = din[3:0];
        4'd1: out_a = din[11:8];
        4'd2: out_a = din[19:16];
        4'd3: out_a = din[23:20];
        4'd4: out_a = din[35:32];
        4'd5: out_a = din[39:36];
        4'd6: out_a = din[51:48];
        4'd7: out_a = din[59:56];
        4'd8: out_a = din[67:64];
        4'd9: out_a = din[71:68];
        4'd10: out_a = din[83:80];
        4'd11: out_a = din[87:84];
        4'd12: out_a = din[99:96];
        4'd13: out_a = din[103:100];
        4'd14: out_a = din[115:112];
        4'd15: out_a = din[123:120];
        default: out_a = 4'bx;
    endcase
end

always @*
begin
    case (control)
        4'd0: out_b = din[7:4];
        4'd1: out_b = din[15:12];
        4'd2: out_b = din[23:20];
        4'd3: out_b = din[19:16];
        4'd4: out_b = din[39:36];
        4'd5: out_b = din[35:32];
        4'd6: out_b = din[55:52];
        4'd7: out_b = din[63:60];
        4'd8: out_b = din[71:68];
        4'd9: out_b = din[67:64];
        4'd10: out_b = din[87:84];
        4'd11: out_b = din[83:80];
        4'd12: out_b = din[103:100];
        4'd13: out_b = din[99:96];
        4'd14: out_b = din[119:116];
        4'd15: out_b = din[127:124];
        default: out_b = 4'bx;
    endcase
end

endmodule
