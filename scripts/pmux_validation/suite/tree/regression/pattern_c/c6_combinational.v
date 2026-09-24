module c6_combinational(
    input [3:0] control,
    input [1:0] data,
    output reg [3:0] y
);

always @* begin
    y = {
        data[1],
        data[0],
        data[1],
        data[0]
    };

    case (control)
        4'd3:
            y = {
                data[1],
                control[1] ^ control[2],
                data[0],
                ~control[0]
            };

        4'd12:
            y = {
                data[1],
                control[2] ^ control[1],
                data[0],
                ~control[3]
            };
    endcase
end

endmodule
