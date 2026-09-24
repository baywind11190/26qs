module b10_two_controls(
    input clk,
    input [3:0] control_a,
    input [3:0] control_b,
    input [3:0] data_a,
    input [3:0] data_b,
    output reg [7:0] y_a,
    output reg [7:0] y_b
);

always @(posedge clk) begin
    case (control_a)
        4'd2:  y_a <= {control_a, data_a};
        4'd11: y_a <= {data_a, control_a};
    endcase
end

always @(posedge clk) begin
    case (control_b)
        4'd5:  y_b <= {control_b, data_b};
        4'd14: y_b <= {data_b, control_b};
    endcase
end

endmodule
