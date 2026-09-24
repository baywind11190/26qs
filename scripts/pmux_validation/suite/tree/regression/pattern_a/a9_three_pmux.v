module a9_three_pmux(
    input  [1:0] control,
    input  [7:0] d0, d1,
    input  [7:0] e0, e1,
    input  [3:0] z0, z1, z2, z3,
    output reg [7:0] x,
    output reg [7:0] y,
    output reg [3:0] z
);
always @* begin
    x = 8'b0;
    y = 8'b0;
    z = 4'b0;
    case (control)
        2'd0: begin x = d0; y = e0; z = z0; end
        2'd1: begin x = e0; y = d0; z = z1; end
        2'd2: begin x = d1; y = e1; z = z2; end
        2'd3: begin x = e1; y = d1; z = z3; end
    endcase
end
endmodule
