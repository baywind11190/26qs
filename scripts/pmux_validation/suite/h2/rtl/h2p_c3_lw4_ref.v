// 独立参考模型（移位表达）: phase=ctrl[1:0], bank=ctrl[2:2]
// 模块名与用例相同（EQY 要求 gold/gate 顶层同名）
module h2p_c3_lw4 (
    input  wire [2:0] ctrl,
    input  wire [31:0] d,
    output wire [15:0] y
);
    wire [15:0] pre = (ctrl[2:2] == 1'b0) ? d[15:0] : (ctrl[2:2] == 1'b1) ? d[31:16] : 16'b0;
    wire [1:0] phase = ctrl[1:0];
    wire [15:0] s_amt = phase * 4;  // 移位量（bit）
    wire [15:0] rot_r = pre >> s_amt;
    wire [15:0] rot_l = pre << (16 - s_amt);
    assign y = (phase == 2'd0) ? pre
                          : (rot_r | rot_l);
endmodule
