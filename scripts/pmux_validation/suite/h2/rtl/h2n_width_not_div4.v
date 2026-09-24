// H2 拒绝例：数据宽度 6 不能整除 4
module h2n_width_not_div4 (
    input  wire [3:0] ctrl,
    input  wire [5:0] d0, d1, d2, d3,
    output reg  [5:0] y
);
    always @* begin
        case (ctrl)
            4'd0:  y = d0;
            4'd1:  y = {d0[0], d0[5:1]};
            4'd2:  y = {d0[1:0], d0[5:2]};
            4'd3:  y = {d0[2:0], d0[5:3]};
            4'd4:  y = d1;
            4'd5:  y = {d1[0], d1[5:1]};
            4'd6:  y = {d1[1:0], d1[5:2]};
            4'd7:  y = {d1[2:0], d1[5:3]};
            4'd8:  y = d2;
            4'd9:  y = {d2[0], d2[5:1]};
            4'd10: y = {d2[1:0], d2[5:2]};
            4'd11: y = {d2[2:0], d2[5:3]};
            4'd12: y = d3;
            4'd13: y = {d3[0], d3[5:1]};
            4'd14: y = {d3[1:0], d3[5:2]};
            4'd15: y = {d3[2:0], d3[5:3]};
            default: y = 6'b0;
        endcase
    end
endmodule
