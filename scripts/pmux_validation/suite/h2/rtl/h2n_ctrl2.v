// H2 用例（h2n_ctrl2）——控制宽度 2（低于 H2 下限 3）
// 参考语义：phase = ctrl[1:0]，bank = ctrl[高位]；lane i 输出 = bank lane (i+phase)%4
// 生成器：gen_h2_cases.py（确定性，无随机）

module h2n_ctrl2 (
    input  wire [1:0] ctrl,
    input  wire [7:0] d,
    output reg  [7:0] y
);
    wire [7:0] base0 = d;
    wire [7:0] r0_0 = {base0[7:6], base0[5:4], base0[3:2], base0[1:0]};
    wire [7:0] r0_1 = {base0[1:0], base0[7:6], base0[5:4], base0[3:2]};
    wire [7:0] r0_2 = {base0[3:2], base0[1:0], base0[7:6], base0[5:4]};
    wire [7:0] r0_3 = {base0[5:4], base0[3:2], base0[1:0], base0[7:6]};
    always @* begin
        case (ctrl)
            2'd0: y = base0;
            2'd1: y = base0;
            2'd2: y = base0;
            2'd3: y = base0;
            default: y = 8'b0;
        endcase
    end
endmodule
