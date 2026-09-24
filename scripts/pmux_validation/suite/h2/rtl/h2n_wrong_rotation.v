// H2 用例（h2n_wrong_rotation）——phase=1 左旋（错误方向）
// 参考语义：phase = ctrl[1:0]，bank = ctrl[高位]；lane i 输出 = bank lane (i+phase)%4
// 生成器：gen_h2_cases.py（确定性，无随机）

module h2n_wrong_rotation (
    input  wire [3:0] ctrl,
    input  wire [31:0] d,
    output reg  [7:0] y
);
    wire [7:0] base0 = d[7:0];
    wire [7:0] base1 = d[15:8];
    wire [7:0] base2 = d[23:16];
    wire [7:0] base3 = d[31:24];
    wire [7:0] r0_0 = {base0[7:6], base0[5:4], base0[3:2], base0[1:0]};
    wire [7:0] r0_1 = {base0[1:0], base0[7:6], base0[5:4], base0[3:2]};
    wire [7:0] r0_2 = {base0[3:2], base0[1:0], base0[7:6], base0[5:4]};
    wire [7:0] r0_3 = {base0[5:4], base0[3:2], base0[1:0], base0[7:6]};
    wire [7:0] r1_0 = {base1[7:6], base1[5:4], base1[3:2], base1[1:0]};
    wire [7:0] r1_1 = {base1[1:0], base1[7:6], base1[5:4], base1[3:2]};
    wire [7:0] r1_2 = {base1[3:2], base1[1:0], base1[7:6], base1[5:4]};
    wire [7:0] r1_3 = {base1[5:4], base1[3:2], base1[1:0], base1[7:6]};
    wire [7:0] r2_0 = {base2[7:6], base2[5:4], base2[3:2], base2[1:0]};
    wire [7:0] r2_1 = {base2[1:0], base2[7:6], base2[5:4], base2[3:2]};
    wire [7:0] r2_2 = {base2[3:2], base2[1:0], base2[7:6], base2[5:4]};
    wire [7:0] r2_3 = {base2[5:4], base2[3:2], base2[1:0], base2[7:6]};
    wire [7:0] r3_0 = {base3[7:6], base3[5:4], base3[3:2], base3[1:0]};
    wire [7:0] r3_1 = {base3[1:0], base3[7:6], base3[5:4], base3[3:2]};
    wire [7:0] r3_2 = {base3[3:2], base3[1:0], base3[7:6], base3[5:4]};
    wire [7:0] r3_3 = {base3[5:4], base3[3:2], base3[1:0], base3[7:6]};
    always @* begin
        case (ctrl)
            4'd0: y = {base0[7:6], base0[5:4], base0[3:2], base0[1:0]};
            4'd1: y = {base0[5:4], base0[3:2], base0[1:0], base0[7:6]};
            4'd2: y = {base0[3:2], base0[1:0], base0[7:6], base0[5:4]};
            4'd3: y = {base0[5:4], base0[3:2], base0[1:0], base0[7:6]};
            4'd4: y = {base1[7:6], base1[5:4], base1[3:2], base1[1:0]};
            4'd5: y = {base1[5:4], base1[3:2], base1[1:0], base1[7:6]};
            4'd6: y = {base1[3:2], base1[1:0], base1[7:6], base1[5:4]};
            4'd7: y = {base1[5:4], base1[3:2], base1[1:0], base1[7:6]};
            4'd8: y = {base2[7:6], base2[5:4], base2[3:2], base2[1:0]};
            4'd9: y = {base2[5:4], base2[3:2], base2[1:0], base2[7:6]};
            4'd10: y = {base2[3:2], base2[1:0], base2[7:6], base2[5:4]};
            4'd11: y = {base2[5:4], base2[3:2], base2[1:0], base2[7:6]};
            4'd12: y = {base3[7:6], base3[5:4], base3[3:2], base3[1:0]};
            4'd13: y = {base3[5:4], base3[3:2], base3[1:0], base3[7:6]};
            4'd14: y = {base3[3:2], base3[1:0], base3[7:6], base3[5:4]};
            4'd15: y = {base3[5:4], base3[3:2], base3[1:0], base3[7:6]};
            default: y = 8'b0;
        endcase
    end
endmodule
