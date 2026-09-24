module c5_partial_decode(
    input clk,
    input [7:0] control,
    output reg [3:0] y
);

always @(posedge clk) begin
    case (control)
        8'h35:
            y <= {
                ~control[0],
                control[5] ^ control[2],
                |control[7:4],
                &control[3:0]
            };

        8'hA7:
            y <= {
                ~control[7],
                control[6] ^ control[1],
                |control[3:0],
                &control[7:4]
            };
    endcase
end

endmodule
