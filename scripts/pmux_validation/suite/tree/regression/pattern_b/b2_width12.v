module b2_width12(
    input clk,
    input [3:0] control,
    input [7:0] data,
    output reg [11:0] y
);

always @(posedge clk) begin
    case (control)
        4'd2:  y <= {control[3:0], data};
        4'd9:  y <= {data, control[3:0]};
        4'd13: y <= {control[3], data[7:4],
                     control[1], data[3:0],
                     control[2:0]};
    endcase
end

endmodule
