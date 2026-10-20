// Formal-only model for the explicitly checked ff_map.v configuration in
// Yosys 0.69 (9f75ca1f9). The mapper moves _TECHMAP_WIREINIT_Q_ into
// power_up and removes the wire init attribute. Model that parameter on the
// gate side; do not add initial/reset assumptions to the reference RTL.
module dffeas(output reg q, input d, clk, clrn, prn, ena,
              asdata, aload, sclr, sload);
parameter power_up="dontcare", is_wysiwyg="false";
initial begin
  if (power_up == "high") q = 1'b1;
  else if (power_up == "low") q = 1'b0;
end
always @(posedge clk or negedge clrn)
  if (!clrn) q <= 1'b0;
  else if (ena) q <= d;
endmodule
