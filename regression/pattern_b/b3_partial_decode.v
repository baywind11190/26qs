module b3_partial_decode(
    input clk,
    input [3:0] control,
    input [3:0] data,
    output reg [7:0] y
);

always @(posedge clk) begin
    case (control)
        4'd3:  y <= {control, data};
        4'd12: y <= {data, control};
    endcase
end

endmodule
