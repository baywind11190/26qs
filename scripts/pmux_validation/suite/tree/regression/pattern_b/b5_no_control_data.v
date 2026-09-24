module b5_no_control_data(
    input clk,
    input [2:0] control,
    input [7:0] d0,
    input [7:0] d1,
    input [7:0] d2,
    output reg [7:0] y
);

always @(posedge clk) begin
    case (control)
        3'd1: y <= d0;
        3'd4: y <= d1;
        3'd7: y <= d2;
    endcase
end

endmodule
