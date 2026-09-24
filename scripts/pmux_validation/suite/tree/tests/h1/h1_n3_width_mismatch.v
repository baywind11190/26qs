
module h1_n3_width_mismatch(
    input [3:0] control,
    input [255:0] din,
    output reg [3:0] out_a,
    output reg [7:0] out_b
);

always @*
begin
    case (control)
        0: out_a = din[3:0];
        1: out_a = din[7:4];
        2: out_a = din[11:8];
        3: out_a = din[15:12];
        4: out_a = din[19:16];
        5: out_a = din[23:20];
        6: out_a = din[27:24];
        7: out_a = din[31:28];
        8: out_a = din[35:32];
        9: out_a = din[39:36];
        10: out_a = din[43:40];
        11: out_a = din[47:44];
        12: out_a = din[51:48];
        13: out_a = din[55:52];
        14: out_a = din[59:56];
        15: out_a = din[63:60];
        default: out_a = 4'bx;
    endcase
end

always @*
begin
    case (control)
        0: out_b = din[71:64];
        1: out_b = din[79:72];
        2: out_b = din[87:80];
        3: out_b = din[95:88];
        4: out_b = din[103:96];
        5: out_b = din[111:104];
        6: out_b = din[119:112];
        7: out_b = din[127:120];
        8: out_b = din[135:128];
        9: out_b = din[143:136];
        10: out_b = din[151:144];
        11: out_b = din[159:152];
        12: out_b = din[167:160];
        13: out_b = din[175:168];
        14: out_b = din[183:176];
        15: out_b = din[191:184];
        default: out_b = 8'bx;
    endcase
end

endmodule
