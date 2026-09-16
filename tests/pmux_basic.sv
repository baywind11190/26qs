module pmux_basic (
    input  wire [7:0] a,
    input  wire [7:0] b,
    input  wire [7:0] c,
    input  wire [1:0] sel,
    output reg  [7:0] y
);

always @* begin
    unique case (sel)
        2'b01:  y = b;
        2'b10:  y = c;
        default: y = a;
    endcase
end

endmodule
