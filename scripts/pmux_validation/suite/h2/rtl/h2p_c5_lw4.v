// H2 用例（h2p_c5_lw4）——8 banks, lane=4
// 参考语义：phase = ctrl[1:0]，bank = ctrl[高位]；lane i 输出 = bank lane (i+phase)%4
// 生成器：gen_h2_cases.py（确定性，无随机）

module h2p_c5_lw4 (
    input  wire [4:0] ctrl,
    input  wire [127:0] d,
    output reg  [15:0] y
);
    wire [15:0] base0 = d[15:0];
    wire [15:0] base1 = d[31:16];
    wire [15:0] base2 = d[47:32];
    wire [15:0] base3 = d[63:48];
    wire [15:0] base4 = d[79:64];
    wire [15:0] base5 = d[95:80];
    wire [15:0] base6 = d[111:96];
    wire [15:0] base7 = d[127:112];
    wire [15:0] r0_0 = {base0[15:12], base0[11:8], base0[7:4], base0[3:0]};
    wire [15:0] r0_1 = {base0[3:0], base0[15:12], base0[11:8], base0[7:4]};
    wire [15:0] r0_2 = {base0[7:4], base0[3:0], base0[15:12], base0[11:8]};
    wire [15:0] r0_3 = {base0[11:8], base0[7:4], base0[3:0], base0[15:12]};
    wire [15:0] r1_0 = {base1[15:12], base1[11:8], base1[7:4], base1[3:0]};
    wire [15:0] r1_1 = {base1[3:0], base1[15:12], base1[11:8], base1[7:4]};
    wire [15:0] r1_2 = {base1[7:4], base1[3:0], base1[15:12], base1[11:8]};
    wire [15:0] r1_3 = {base1[11:8], base1[7:4], base1[3:0], base1[15:12]};
    wire [15:0] r2_0 = {base2[15:12], base2[11:8], base2[7:4], base2[3:0]};
    wire [15:0] r2_1 = {base2[3:0], base2[15:12], base2[11:8], base2[7:4]};
    wire [15:0] r2_2 = {base2[7:4], base2[3:0], base2[15:12], base2[11:8]};
    wire [15:0] r2_3 = {base2[11:8], base2[7:4], base2[3:0], base2[15:12]};
    wire [15:0] r3_0 = {base3[15:12], base3[11:8], base3[7:4], base3[3:0]};
    wire [15:0] r3_1 = {base3[3:0], base3[15:12], base3[11:8], base3[7:4]};
    wire [15:0] r3_2 = {base3[7:4], base3[3:0], base3[15:12], base3[11:8]};
    wire [15:0] r3_3 = {base3[11:8], base3[7:4], base3[3:0], base3[15:12]};
    wire [15:0] r4_0 = {base4[15:12], base4[11:8], base4[7:4], base4[3:0]};
    wire [15:0] r4_1 = {base4[3:0], base4[15:12], base4[11:8], base4[7:4]};
    wire [15:0] r4_2 = {base4[7:4], base4[3:0], base4[15:12], base4[11:8]};
    wire [15:0] r4_3 = {base4[11:8], base4[7:4], base4[3:0], base4[15:12]};
    wire [15:0] r5_0 = {base5[15:12], base5[11:8], base5[7:4], base5[3:0]};
    wire [15:0] r5_1 = {base5[3:0], base5[15:12], base5[11:8], base5[7:4]};
    wire [15:0] r5_2 = {base5[7:4], base5[3:0], base5[15:12], base5[11:8]};
    wire [15:0] r5_3 = {base5[11:8], base5[7:4], base5[3:0], base5[15:12]};
    wire [15:0] r6_0 = {base6[15:12], base6[11:8], base6[7:4], base6[3:0]};
    wire [15:0] r6_1 = {base6[3:0], base6[15:12], base6[11:8], base6[7:4]};
    wire [15:0] r6_2 = {base6[7:4], base6[3:0], base6[15:12], base6[11:8]};
    wire [15:0] r6_3 = {base6[11:8], base6[7:4], base6[3:0], base6[15:12]};
    wire [15:0] r7_0 = {base7[15:12], base7[11:8], base7[7:4], base7[3:0]};
    wire [15:0] r7_1 = {base7[3:0], base7[15:12], base7[11:8], base7[7:4]};
    wire [15:0] r7_2 = {base7[7:4], base7[3:0], base7[15:12], base7[11:8]};
    wire [15:0] r7_3 = {base7[11:8], base7[7:4], base7[3:0], base7[15:12]};
    always @* begin
        case (ctrl)
            5'd0: y = r0_0;
            5'd1: y = r0_1;
            5'd2: y = r0_2;
            5'd3: y = r0_3;
            5'd4: y = r1_0;
            5'd5: y = r1_1;
            5'd6: y = r1_2;
            5'd7: y = r1_3;
            5'd8: y = r2_0;
            5'd9: y = r2_1;
            5'd10: y = r2_2;
            5'd11: y = r2_3;
            5'd12: y = r3_0;
            5'd13: y = r3_1;
            5'd14: y = r3_2;
            5'd15: y = r3_3;
            5'd16: y = r4_0;
            5'd17: y = r4_1;
            5'd18: y = r4_2;
            5'd19: y = r4_3;
            5'd20: y = r5_0;
            5'd21: y = r5_1;
            5'd22: y = r5_2;
            5'd23: y = r5_3;
            5'd24: y = r6_0;
            5'd25: y = r6_1;
            5'd26: y = r6_2;
            5'd27: y = r6_3;
            5'd28: y = r7_0;
            5'd29: y = r7_1;
            5'd30: y = r7_2;
            5'd31: y = r7_3;
            default: y = 16'b0;
        endcase
    end
endmodule
