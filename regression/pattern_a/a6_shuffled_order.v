module a6_shuffled_order(
    input  [2:0] control,
    input  [7:0] d0, d1, d2, d3,
    input  [7:0] e0, e1, e2, e3,
    output reg [7:0] x,
    output reg [7:0] y
);
always @* begin
    x = 8'b0;
    y = 8'b0;
    case (control)
        3'd5: begin x = d3; y = e3; end
        3'd0: begin x = d0; y = e0; end
        3'd7: begin x = e3; y = d3; end
        3'd2: begin x = e0; y = d0; end
        3'd4: begin x = d2; y = e2; end
        3'd1: begin x = d1; y = e1; end
        3'd6: begin x = e2; y = d2; end
        3'd3: begin x = e1; y = d1; end
    endcase
end
endmodule
