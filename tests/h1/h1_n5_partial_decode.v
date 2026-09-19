module h1_n5_partial_decode(
    input [3:0] control,
    input [127:0] din,
    output reg [3:0] out_a,
    output reg [3:0] out_b
);

always @*
begin
    case (control)
        4'd0: out_a = din[3:0];
        4'd1: out_a = din[7:4];
        4'd2: out_a = din[19:16];
        4'd3: out_a = din[27:24];
        4'd4: out_a = din[35:32];
        4'd5: out_a = din[39:36];
        4'd6: out_a = din[51:48];
        4'd7: out_a = din[55:52];
        4'd8: out_a = din[67:64];
        4'd9: out_a = din[71:68];
        4'd10: out_a = din[83:80];
        4'd11: out_a = din[87:84];
        4'd12: out_a = din[99:96];
        4'd13: out_a = din[107:104];
        4'd14: out_a = din[115:112];
        default: out_a = 4'bx;
    endcase
end

always @*
begin
    case (control)
        4'd0: out_b = din[7:4];
        4'd1: out_b = din[3:0];
        4'd2: out_b = din[23:20];
        4'd3: out_b = din[31:28];
        4'd4: out_b = din[39:36];
        4'd5: out_b = din[35:32];
        4'd6: out_b = din[55:52];
        4'd7: out_b = din[51:48];
        4'd8: out_b = din[71:68];
        4'd9: out_b = din[67:64];
        4'd10: out_b = din[87:84];
        4'd11: out_b = din[83:80];
        4'd12: out_b = din[103:100];
        4'd13: out_b = din[111:108];
        4'd14: out_b = din[119:116];
        default: out_b = 4'bx;
    endcase
end

endmodule
