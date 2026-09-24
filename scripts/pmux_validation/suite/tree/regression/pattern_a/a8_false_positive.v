module a8_false_positive(
    input  [1:0] control,
    input  [7:0] d0, d1,
    input  [7:0] e0, e1,
    input  [7:0] f0, f1,
    output reg [7:0] x,
    output reg [7:0] y
);
always @* begin
    x = 8'b0;
    y = 8'b0;
    case (control)
        2'd0: begin x = d0; y = e0; end
        2'd1: begin x = e0; y = f0; end
        2'd2: begin x = d1; y = e1; end
        2'd3: begin x = e1; y = f1; end
    endcase
end
endmodule
