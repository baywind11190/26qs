// H2 用例（h2p_c4_lw8）——4 banks, lane=8
// 参考语义：phase = ctrl[1:0]，bank = ctrl[高位]；lane i 输出 = bank lane (i+phase)%4
// 生成器：gen_h2_cases.py（确定性，无随机）

module h2p_c4_lw8 (
    input  wire [3:0] ctrl,
    input  wire [127:0] d,
    output reg  [31:0] y
);
    wire [31:0] base0 = d[31:0];
    wire [31:0] base1 = d[63:32];
    wire [31:0] base2 = d[95:64];
    wire [31:0] base3 = d[127:96];
    wire [31:0] r0_0 = {base0[31:24], base0[23:16], base0[15:8], base0[7:0]};
    wire [31:0] r0_1 = {base0[7:0], base0[31:24], base0[23:16], base0[15:8]};
    wire [31:0] r0_2 = {base0[15:8], base0[7:0], base0[31:24], base0[23:16]};
    wire [31:0] r0_3 = {base0[23:16], base0[15:8], base0[7:0], base0[31:24]};
    wire [31:0] r1_0 = {base1[31:24], base1[23:16], base1[15:8], base1[7:0]};
    wire [31:0] r1_1 = {base1[7:0], base1[31:24], base1[23:16], base1[15:8]};
    wire [31:0] r1_2 = {base1[15:8], base1[7:0], base1[31:24], base1[23:16]};
    wire [31:0] r1_3 = {base1[23:16], base1[15:8], base1[7:0], base1[31:24]};
    wire [31:0] r2_0 = {base2[31:24], base2[23:16], base2[15:8], base2[7:0]};
    wire [31:0] r2_1 = {base2[7:0], base2[31:24], base2[23:16], base2[15:8]};
    wire [31:0] r2_2 = {base2[15:8], base2[7:0], base2[31:24], base2[23:16]};
    wire [31:0] r2_3 = {base2[23:16], base2[15:8], base2[7:0], base2[31:24]};
    wire [31:0] r3_0 = {base3[31:24], base3[23:16], base3[15:8], base3[7:0]};
    wire [31:0] r3_1 = {base3[7:0], base3[31:24], base3[23:16], base3[15:8]};
    wire [31:0] r3_2 = {base3[15:8], base3[7:0], base3[31:24], base3[23:16]};
    wire [31:0] r3_3 = {base3[23:16], base3[15:8], base3[7:0], base3[31:24]};
    always @* begin
        case (ctrl)
            4'd0: y = r0_0;
            4'd1: y = r0_1;
            4'd2: y = r0_2;
            4'd3: y = r0_3;
            4'd4: y = r1_0;
            4'd5: y = r1_1;
            4'd6: y = r1_2;
            4'd7: y = r1_3;
            4'd8: y = r2_0;
            4'd9: y = r2_1;
            4'd10: y = r2_2;
            4'd11: y = r2_3;
            4'd12: y = r3_0;
            4'd13: y = r3_1;
            4'd14: y = r3_2;
            4'd15: y = r3_3;
            default: y = 32'b0;
        endcase
    end
endmodule
