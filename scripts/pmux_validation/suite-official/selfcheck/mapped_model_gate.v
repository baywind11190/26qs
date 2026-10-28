// official4-p2 形式化自检（gate 侧）：按映射端口模式实例化 dffeas / lcell。
// 模型由入口 runner/form_cells_cycloneiv.v（器件语义模型 v3）提供。
// 说明：lcell 实测端口 dataa/datab/datac/datad/combout 必需；cin 恒接 1'b0，
// cout 未使用（本套网表同此约定）。
module mac_init_ok (input clk, input d, output q);
   dffeas #(.power_up("low"), .is_wysiwyg("false")) u (
      .q(q), .d(d), .clk(clk), .clrn(1'b1), .prn(1'b1), .ena(1'b1),
      .asdata(1'b0), .aload(1'b0), .sclr(1'b0), .sload(1'b0));
endmodule

module mac_init_conflict (input clk, input d, output q);
   dffeas #(.power_up("low"), .is_wysiwyg("false")) u (
      .q(q), .d(d), .clk(clk), .clrn(1'b1), .prn(1'b1), .ena(1'b1),
      .asdata(1'b0), .aload(1'b0), .sclr(1'b0), .sload(1'b0));
endmodule

module mac_clr (input clk, input rst, input ena, input d, output q);
   dffeas #(.power_up("low"), .is_wysiwyg("false")) u (
      .q(q), .d(d), .clk(clk), .clrn(~rst), .prn(1'b1), .ena(ena),
      .asdata(1'b0), .aload(1'b0), .sclr(1'b0), .sload(1'b0));
endmodule

module mac_ena (input clk, input ena, input d, output q);
   dffeas #(.power_up("low"), .is_wysiwyg("false")) u (
      .q(q), .d(d), .clk(clk), .clrn(1'b1), .prn(1'b1), .ena(ena),
      .asdata(1'b0), .aload(1'b0), .sclr(1'b0), .sload(1'b0));
endmodule

module mac_lut_ok (input a, input b, output y);
   cycloneiv_lcell_comb #(.lut_mask(16'h0008), .sum_lutc_input("datac")) u (
      .dataa(a), .datab(b), .datac(1'b0), .datad(1'b0), .cin(1'b0), .combout(y));
endmodule

module mac_lut_bad (input a, input b, output y);
   cycloneiv_lcell_comb #(.lut_mask(16'h000E), .sum_lutc_input("datac")) u (
      .dataa(a), .datab(b), .datac(1'b0), .datad(1'b0), .cin(1'b0), .combout(y));
endmodule

module maskreg (input clk, input d, output q);
   dffeas #(.power_up("low"), .is_wysiwyg("false")) u (
      .q(q), .d(d), .clk(clk), .clrn(1'b1), .prn(1'b1), .ena(1'b1),
      .asdata(1'b0), .aload(1'b0), .sclr(1'b0), .sload(1'b0));
endmodule
