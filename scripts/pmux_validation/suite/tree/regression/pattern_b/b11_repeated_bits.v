module b11_repeated_bits(
    input clk,
    input [3:0] control,
    input [3:0] data,
    output reg [11:0] y
);

always @(posedge clk) begin
    case (control)
        4'd3:
            y <= {
                control[3],
                control[3],
                control[2],
                data,
                control[1],
                control[1],
                control[0],
                control[0]
            };

        4'd12:
            y <= {
                control[0],
                control[0],
                control[1],
                data,
                control[2],
                control[2],
                control[3],
                control[3]
            };
    endcase
end

endmodule
