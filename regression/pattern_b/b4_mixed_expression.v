module b4_mixed_expression(
    input clk,
    input [3:0] control,
    input [5:0] data,
    output reg [9:0] y
);

always @(posedge clk) begin
    case (control)
        4'd5:
            y <= {
                control[3],
                ~control[2],
                control[1],
                data,
                control[0]
            };

        4'd10:
            y <= {
                control[0],
                data,
                control[2],
                ~control[1],
                control[3]
            };
    endcase
end

endmodule
