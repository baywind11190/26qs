module b13_combinational(
    input [3:0] control,
    input [3:0] data,
    output reg [7:0] y
);

always @* begin
    y = 8'h00;

    case (control)
        4'd1:  y = {control, data};
        4'd6:  y = {data, control};
        4'd14: y = {
            control[3:2],
            data,
            control[1:0]
        };
    endcase
end

endmodule
