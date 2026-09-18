module top(
    input clk,
    input cs,
    input [7:0] sr,
    output reg q
);

wire signed [7:0] signed_sr = sr;
wire hit = (signed_sr == -8'sd86);

always @(posedge clk)
begin
    if (cs && sr[7] && hit)
        q <= ~q;
end

endmodule
