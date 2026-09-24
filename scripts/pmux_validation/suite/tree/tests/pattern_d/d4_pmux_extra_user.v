module top(
    input clk,
    input cs,
    input [7:0] sr,
    output reg [3:0] q,
    output leak
);

reg [3:0] selected;

always @*
begin
    case (sr)
        8'hAA: selected = 4'hA;
        8'hFF: selected = 4'hF;
        default: selected = 4'h0;
    endcase
end

always @(posedge clk)
begin
    if (cs && sr[7])
        q <= selected;
end

assign leak = ^selected;

endmodule
