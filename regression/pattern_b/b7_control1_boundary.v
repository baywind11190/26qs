module b7_control1_boundary(
    input clk,
    input control,
    input [2:0] data,
    output reg [3:0] y
);

always @(posedge clk) begin
    case (control)
        1'b0: y <= {control, data};
        1'b1: y <= {data, control};
    endcase
end

endmodule
