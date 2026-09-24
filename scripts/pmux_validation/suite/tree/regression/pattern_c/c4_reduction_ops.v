module c4_reduction_ops(
    input clk,
    input [3:0] control,
    output reg [3:0] y
);

always @(posedge clk) begin
    case (control)
        4'd3:
            y <= {
                |control,
                &control,
                ^control,
                ~^control
            };

        4'd12:
            y <= {
                |control[3:2],
                &control[3:2],
                ^control[1:0],
                ~^control[1:0]
            };
    endcase
end

endmodule
