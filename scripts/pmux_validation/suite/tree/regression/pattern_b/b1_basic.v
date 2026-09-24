module b1_basic(
    input clk,
    input [2:0] control,
    input [2:0] data,
    output reg [5:0] y
);

always @(posedge clk) begin
    case (control)
        3'd1: y <= {control[2:0], data};
        3'd4: y <= {data, control[2:0]};
        3'd7: y <= {control[0], data, control[2:1]};
    endcase
end

endmodule
