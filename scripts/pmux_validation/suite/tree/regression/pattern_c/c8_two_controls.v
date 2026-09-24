module c8_two_controls(
    input clk,
    input [3:0] control_a,
    input [3:0] control_b,
    input [3:0] data_a,
    input [3:0] data_b,
    output reg [3:0] y_a,
    output reg [3:0] y_b
);

always @(posedge clk) begin
    y_a <= data_a;

    case (control_a)
        4'd3:
            y_a <= {
                data_a[3],
                ~control_a[0],
                control_a[1] ^ control_a[2],
                data_a[0]
            };

        4'd12:
            y_a <= {
                data_a[2],
                ~control_a[3],
                |control_a,
                data_a[1]
            };
    endcase
end

always @(posedge clk) begin
    y_b <= data_b;

    case (control_b)
        4'd5:
            y_b <= {
                data_b[3],
                ~control_b[0],
                control_b[3] ^ control_b[1],
                data_b[0]
            };

        4'd10:
            y_b <= {
                data_b[2],
                ~control_b[3],
                |control_b,
                data_b[1]
            };
    endcase
end

endmodule
