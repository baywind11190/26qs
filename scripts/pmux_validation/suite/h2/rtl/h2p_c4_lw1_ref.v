// 独立参考模型（移位表达）: phase=ctrl[1:0], bank=ctrl[3:2]
// 模块名与用例相同（EQY 要求 gold/gate 顶层同名）
module h2p_c4_lw1 (
    input  wire [3:0] ctrl,
    input  wire [15:0] d,
    output wire [3:0] y
);
    wire [3:0] pre = (ctrl[3:2] == 2'd0) ? d[3:0] : (ctrl[3:2] == 2'd1) ? d[7:4] : (ctrl[3:2] == 2'd2) ? d[11:8] : (ctrl[3:2] == 2'd3) ? d[15:12] : 4'b0;
    wire [1:0] phase = ctrl[1:0];
    wire [3:0] s_amt = phase * 1;  // 移位量（bit）
    wire [3:0] rot_r = pre >> s_amt;
    wire [3:0] rot_l = pre << (4 - s_amt);
    assign y = (phase == 2'd0) ? pre
                          : (rot_r | rot_l);
endmodule
