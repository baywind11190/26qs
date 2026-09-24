// H2 用例（h2n_xz_data）——末尾分支数据为常量 x
// 参考语义：phase = ctrl[1:0]，bank = ctrl[高位]；lane i 输出 = bank lane (i+phase)%4
// 生成器：gen_h2_cases.py（确定性，无随机）

module h2n_xz_data (
    input  wire [2:0] ctrl,
    input  wire [15:0] d,
    output reg  [7:0] y
);
    wire [7:0] base0 = d[7:0];
    wire [7:0] base1 = d[15:8];
    wire [7:0] r0_0 = {base0[7:6], base0[5:4], base0[3:2], base0[1:0]};
    wire [7:0] r0_1 = {base0[1:0], base0[7:6], base0[5:4], base0[3:2]};
    wire [7:0] r0_2 = {base0[3:2], base0[1:0], base0[7:6], base0[5:4]};
    wire [7:0] r0_3 = {base0[5:4], base0[3:2], base0[1:0], base0[7:6]};
    wire [7:0] r1_0 = {base1[7:6], base1[5:4], base1[3:2], base1[1:0]};
    wire [7:0] r1_1 = {base1[1:0], base1[7:6], base1[5:4], base1[3:2]};
    wire [7:0] r1_2 = {base1[3:2], base1[1:0], base1[7:6], base1[5:4]};
    wire [7:0] r1_3 = {base1[5:4], base1[3:2], base1[1:0], base1[7:6]};
    always @* begin
        case (ctrl)
            3'd0: y = r0_0;
            3'd1: y = r0_1;
            3'd2: y = r0_2;
            3'd3: y = r0_3;
            3'd4: y = r1_0;
            3'd5: y = r1_1;
            3'd6: y = r1_2;
            3'd7: y = 8'bx;
            default: y = 8'b0;
        endcase
    end
endmodule
