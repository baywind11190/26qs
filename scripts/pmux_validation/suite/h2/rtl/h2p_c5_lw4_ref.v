// 独立参考模型（移位表达）: phase=ctrl[1:0], bank=ctrl[4:2]
// 模块名与用例相同（EQY 要求 gold/gate 顶层同名）
module h2p_c5_lw4 (
    input  wire [4:0] ctrl,
    input  wire [127:0] d,
    output wire [15:0] y
);
    wire [15:0] pre = (ctrl[4:2] == 3'd0) ? d[15:0] : (ctrl[4:2] == 3'd1) ? d[31:16] : (ctrl[4:2] == 3'd2) ? d[47:32] : (ctrl[4:2] == 3'd3) ? d[63:48] : (ctrl[4:2] == 3'd4) ? d[79:64] : (ctrl[4:2] == 3'd5) ? d[95:80] : (ctrl[4:2] == 3'd6) ? d[111:96] : (ctrl[4:2] == 3'd7) ? d[127:112] : 16'b0;
    wire [1:0] phase = ctrl[1:0];
    wire [15:0] s_amt = phase * 4;  // 移位量（bit）
    wire [15:0] rot_r = pre >> s_amt;
    wire [15:0] rot_l = pre << (16 - s_amt);
    assign y = (phase == 2'd0) ? pre
                          : (rot_r | rot_l);
endmodule
