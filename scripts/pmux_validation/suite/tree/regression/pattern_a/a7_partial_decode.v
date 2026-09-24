module a7_partial_decode(
    input  [2:0] control,
    input  [7:0] d0, d1,
    input  [7:0] e0, e1,
    output reg [7:0] x,
    output reg [7:0] y
);
always @* begin
    x = 8'b0;
    y = 8'b0;
    case (control)
        3'd0: begin x = d0; y = e0; end
        3'd1: begin x = e0; y = d0; end
        3'd4: begin x = d1; y = e1; end
        3'd5: begin x = e1; y = d1; end
    endcase
end
endmodule
