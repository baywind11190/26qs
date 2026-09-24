module top(
    input clk,
    input cs,
    input [7:0] sr,
    output reg [3:0] q
);

always @(posedge clk)
begin
    if (cs && sr[7])
    begin
        case (sr)
            8'hAA: q <= 4'hA;
            8'hFF: q <= 4'hF;
            default: q <= 4'h0;
        endcase
    end
end

endmodule
