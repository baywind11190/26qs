module b12_zero_selector(
    input clk,
    input [3:0] control,
    input [3:0] data,
    output reg [7:0] y
);

always @(posedge clk) begin
    case (control)
        4'd0: y <= {control, data};
        4'd9: y <= {data, control};
    endcase
end

endmodule
