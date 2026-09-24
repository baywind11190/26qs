module b6_expression_only(
    input clk,
    input [3:0] control,
    output reg [3:0] y
);

always @(posedge clk) begin
    case (control)
        4'd3:
            y <= {
                ~control[0],
                control[1] ^ control[2],
                control[3] & control[0],
                |control
            };

        4'd12:
            y <= {
                ~control[3],
                control[2] ^ control[1],
                control[0] & control[3],
                &control
            };
    endcase
end

endmodule
