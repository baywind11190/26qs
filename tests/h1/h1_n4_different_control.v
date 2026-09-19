
module h1_n4_different_control(
    input [3:0] control_a,
    input [3:0] control_b,
    input [127:0] din,
    output reg [3:0] out_a,
    output reg [3:0] out_b
);

always @*
begin
    case (control_a)
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
    case (control_b)
        0: out_b = din[67:64];
        1: out_b = din[71:68];
        2: out_b = din[75:72];
        3: out_b = din[79:76];
        4: out_b = din[83:80];
        5: out_b = din[87:84];
        6: out_b = din[91:88];
        7: out_b = din[95:92];
        8: out_b = din[99:96];
        9: out_b = din[103:100];
        10: out_b = din[107:104];
        11: out_b = din[111:108];
        12: out_b = din[115:112];
        13: out_b = din[119:116];
        14: out_b = din[123:120];
        15: out_b = din[127:124];
        default: out_b = 4'bx;
    endcase
end

endmodule
