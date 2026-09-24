// H2 拒绝例：不同控制（两个独立 pmux）
module h2n_diff_control (
    input  wire [3:0] ctrl_a,
    input  wire [3:0] ctrl_b,
    input  wire [7:0] d0, d1, d2, d3,
    output reg  [7:0] y_a,
    output reg  [7:0] y_b
);
    wire [7:0] r0 = d0, r1 = {d0[1:0], d0[7:2]}, r2 = {d0[3:0], d0[7:4]}, r3 = {d0[5:0], d0[7:6]};
    wire [7:0] r0e = d1, r1e = {d1[1:0], d1[7:2]}, r2e = {d1[3:0], d1[7:4]}, r3e = {d1[5:0], d1[7:6]};
    always @* begin
        case (ctrl_a)
            4'd0: y_a = r0;
            4'd1: y_a = r1;
            4'd2: y_a = r2;
            4'd3: y_a = r3;
            default: y_a = 8'b0;
        endcase
    end
    always @* begin
        case (ctrl_b)
            4'd0: y_b = r0e;
            4'd1: y_b = r1e;
            4'd2: y_b = r2e;
            4'd3: y_b = r3e;
            default: y_b = 8'b0;
        endcase
    end
endmodule
