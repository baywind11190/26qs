module b8_control8(
    input clk,
    input [7:0] control,
    input [7:0] data,
    output reg [15:0] y
);

always @(posedge clk) begin
    case (control)
        8'h12: y <= {control, data};
        8'h5A: y <= {data, control};
        8'hC3: y <= {
            control[7:4],
            data,
            control[3:0]
        };
    endcase
end

endmodule
