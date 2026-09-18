module c7_external_dependency(
    input clk,
    input [3:0] control,
    input [3:0] data,
    output reg [3:0] y
);

always @(posedge clk) begin
    case (control)
        4'd3:
            y <= data ^ control;

        4'd12:
            y <= ~(data ^ control);
    endcase
end

endmodule
