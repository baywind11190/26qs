// H2 用例（h2p_c3_lw1）——2 banks, lane=1
// 参考语义：phase = ctrl[1:0]，bank = ctrl[高位]；lane i 输出 = bank lane (i+phase)%4
// 生成器：gen_h2_cases.py（确定性，无随机）

module h2p_c3_lw1 (
    input  wire [2:0] ctrl,
    input  wire [7:0] d,
    output reg  [3:0] y
);
    wire [3:0] base0 = d[3:0];
    wire [3:0] base1 = d[7:4];
    wire [3:0] r0_0 = {base0[3:3], base0[2:2], base0[1:1], base0[0:0]};
    wire [3:0] r0_1 = {base0[0:0], base0[3:3], base0[2:2], base0[1:1]};
    wire [3:0] r0_2 = {base0[1:1], base0[0:0], base0[3:3], base0[2:2]};
    wire [3:0] r0_3 = {base0[2:2], base0[1:1], base0[0:0], base0[3:3]};
    wire [3:0] r1_0 = {base1[3:3], base1[2:2], base1[1:1], base1[0:0]};
    wire [3:0] r1_1 = {base1[0:0], base1[3:3], base1[2:2], base1[1:1]};
    wire [3:0] r1_2 = {base1[1:1], base1[0:0], base1[3:3], base1[2:2]};
    wire [3:0] r1_3 = {base1[2:2], base1[1:1], base1[0:0], base1[3:3]};
    always @* begin
        case (ctrl)
            3'd0: y = r0_0;
            3'd1: y = r0_1;
            3'd2: y = r0_2;
            3'd3: y = r0_3;
            3'd4: y = r1_0;
            3'd5: y = r1_1;
            3'd6: y = r1_2;
            3'd7: y = r1_3;
            default: y = 4'b0;
        endcase
    end
endmodule
