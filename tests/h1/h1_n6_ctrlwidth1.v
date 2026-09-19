module h1_n6_ctrlwidth1(
    input [0:0] control,
    input [15:0] din,
    output reg [3:0] out_a,
    output reg [3:0] out_b
);

always @*
begin
    case (control)
        1'd0: out_a = din[3:0];
        1'd1: out_a = din[7:4];
        default: out_a = 4'bx;
    endcase
end

always @*
begin
    case (control)
        1'd0: out_b = din[7:4];
        1'd1: out_b = din[3:0];
        default: out_b = 4'bx;
    endcase
end

endmodule
