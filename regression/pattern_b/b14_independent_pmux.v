module b14_independent_pmux(
    input clk,
    input [2:0] control_a,
    input [2:0] control_b,
    input [4:0] data,
    output reg [7:0] x,
    output reg [7:0] y
);

always @(posedge clk) begin
    case (control_a)
        3'd1: x <= {control_a, data};
        3'd6: x <= {data, control_a};
    endcase
end

always @(posedge clk) begin
    case (control_b)
        3'd2: y <= {control_b, data};
        3'd5: y <= {data, control_b};
    endcase
end

endmodule
