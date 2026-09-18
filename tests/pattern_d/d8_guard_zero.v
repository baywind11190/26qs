module top(
    input clk,
    input cs,
    input [7:0] sr,
    output reg q
);

wire hit = (sr == 8'h2A);

always @(posedge clk)
begin
    if (cs && !sr[7] && hit)
        q <= ~q;
end

endmodule
