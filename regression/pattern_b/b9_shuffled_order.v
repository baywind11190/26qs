module b9_shuffled_order(
    input clk,
    input [3:0] control,
    input [7:0] data,
    output reg [11:0] y
);

always @(posedge clk) begin
    case (control)
        4'd13: y <= {control, data};
        4'd2:  y <= {data, control};
        4'd9:  y <= {
            control[3:2],
            data,
            control[1:0]
        };
    endcase
end

endmodule
