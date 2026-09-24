module top(
    input clk,
    input cs,
    input [7:0] sr,
    output reg q,
    output leak
);

wire hit = (sr == 8'hAA);

assign leak = hit;

always @(posedge clk)
begin
    if (cs && sr[7] && hit)
        q <= ~q;
end

endmodule
