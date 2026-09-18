module a4_half_swap(
    input  [1:0] control,
    input  [3:0] d0, d1,
    input  [3:0] e0, e1,
    input  [3:0] p,
    input  [3:0] q,
    output reg [3:0] x,
    output reg [3:0] y
);
always @* begin
    x = 4'b0;
    y = 4'b0;
    case (control)
        2'd0: begin x = d0; y = e0; end
        2'd1: begin x = e0; y = d0; end
        2'd2: begin x = d1; y = e1; end
        2'd3: begin x = p;  y = q;  end
    endcase
end
endmodule
