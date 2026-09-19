module h1_p2_swapbit2(
    input [3:0] control,
    input [255:0] din,
    output reg [7:0] out_a,
    output reg [7:0] out_b
);

always @*
begin
    case (control)
        4'd0: out_a = din[7:0];
        4'd1: out_a = din[39:32];
        4'd2: out_a = din[71:64];
        4'd3: out_a = din[103:96];
        4'd4: out_a = din[23:16];
        4'd5: out_a = din[47:40];
        4'd6: out_a = din[79:72];
        4'd7: out_a = din[111:104];
        4'd8: out_a = din[135:128];
        4'd9: out_a = din[167:160];
        4'd10: out_a = din[199:192];
        4'd11: out_a = din[231:224];
        4'd12: out_a = din[143:136];
        4'd13: out_a = din[175:168];
        4'd14: out_a = din[207:200];
        4'd15: out_a = din[247:240];
        default: out_a = 8'bx;
    endcase
end

always @*
begin
    case (control)
        4'd0: out_b = din[15:8];
        4'd1: out_b = din[47:40];
        4'd2: out_b = din[79:72];
        4'd3: out_b = din[111:104];
        4'd4: out_b = din[31:24];
        4'd5: out_b = din[39:32];
        4'd6: out_b = din[71:64];
        4'd7: out_b = din[103:96];
        4'd8: out_b = din[143:136];
        4'd9: out_b = din[175:168];
        4'd10: out_b = din[207:200];
        4'd11: out_b = din[239:232];
        4'd12: out_b = din[135:128];
        4'd13: out_b = din[167:160];
        4'd14: out_b = din[199:192];
        4'd15: out_b = din[255:248];
        default: out_b = 8'bx;
    endcase
end

endmodule
