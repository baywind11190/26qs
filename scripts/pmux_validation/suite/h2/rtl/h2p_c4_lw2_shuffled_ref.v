// 独立参考模型（移位表达）: phase=ctrl[1:0], bank=ctrl[3:2]
// 模块名与用例相同（EQY 要求 gold/gate 顶层同名）
module h2p_c4_lw2_shuffled (
    input  wire [3:0] ctrl,
    input  wire [31:0] d,
    output wire [7:0] y
);
    wire [7:0] pre = (ctrl[3:2] == 2'd0) ? d[7:0] : (ctrl[3:2] == 2'd1) ? d[15:8] : (ctrl[3:2] == 2'd2) ? d[23:16] : (ctrl[3:2] == 2'd3) ? d[31:24] : 8'b0;
    wire [1:0] phase = ctrl[1:0];
    wire [7:0] s_amt = phase * 2;  // 移位量（bit）
    wire [7:0] rot_r = pre >> s_amt;
    wire [7:0] rot_l = pre << (8 - s_amt);
    assign y = (phase == 2'd0) ? pre
                          : (rot_r | rot_l);
endmodule
