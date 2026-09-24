// H2 用例（h2p_c4_lw1）——4 banks, lane=1
// 参考语义：phase = ctrl[1:0]，bank = ctrl[高位]；lane i 输出 = bank lane (i+phase)%4
// 生成器：gen_h2_cases.py（确定性，无随机）

module h2p_c4_lw1 (
    input  wire [3:0] ctrl,
    input  wire [15:0] d,
    output reg  [3:0] y
);
    wire [3:0] base0 = d[3:0];
    wire [3:0] base1 = d[7:4];
    wire [3:0] base2 = d[11:8];
    wire [3:0] base3 = d[15:12];
    wire [3:0] r0_0 = {base0[3:3], base0[2:2], base0[1:1], base0[0:0]};
    wire [3:0] r0_1 = {base0[0:0], base0[3:3], base0[2:2], base0[1:1]};
    wire [3:0] r0_2 = {base0[1:1], base0[0:0], base0[3:3], base0[2:2]};
    wire [3:0] r0_3 = {base0[2:2], base0[1:1], base0[0:0], base0[3:3]};
    wire [3:0] r1_0 = {base1[3:3], base1[2:2], base1[1:1], base1[0:0]};
    wire [3:0] r1_1 = {base1[0:0], base1[3:3], base1[2:2], base1[1:1]};
    wire [3:0] r1_2 = {base1[1:1], base1[0:0], base1[3:3], base1[2:2]};
    wire [3:0] r1_3 = {base1[2:2], base1[1:1], base1[0:0], base1[3:3]};
    wire [3:0] r2_0 = {base2[3:3], base2[2:2], base2[1:1], base2[0:0]};
    wire [3:0] r2_1 = {base2[0:0], base2[3:3], base2[2:2], base2[1:1]};
    wire [3:0] r2_2 = {base2[1:1], base2[0:0], base2[3:3], base2[2:2]};
    wire [3:0] r2_3 = {base2[2:2], base2[1:1], base2[0:0], base2[3:3]};
    wire [3:0] r3_0 = {base3[3:3], base3[2:2], base3[1:1], base3[0:0]};
    wire [3:0] r3_1 = {base3[0:0], base3[3:3], base3[2:2], base3[1:1]};
    wire [3:0] r3_2 = {base3[1:1], base3[0:0], base3[3:3], base3[2:2]};
    wire [3:0] r3_3 = {base3[2:2], base3[1:1], base3[0:0], base3[3:3]};
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
            default: y = 4'b0;
        endcase
    end
endmodule
