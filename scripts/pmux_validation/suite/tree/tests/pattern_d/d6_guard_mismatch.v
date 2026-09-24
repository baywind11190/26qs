module top(
    input clk,
    input cs,
    input [7:0] sr,
    output reg q
);

wire hit = (sr == 8'hAA);

always @(posedge clk)
begin
    if (cs && sr[6] && hit)
        q <= ~q;
end

endmodule
