/*
 * Cyclone IV 形式验证功能模型（本轮自建，仅用于 EQY 映射链）。
 *
 * 来源与依据：
 *   /home/fpga/eda/yosys-baseline/build/share/intel/cycloneiv/cells_sim.v
 *   （Yosys 0.69，源码提交 9f75ca1f9834a39a863915b5dae0c7b1e33533bc）
 *
 * 与 cells_sim.v 的差异（全部记录于本轮 10/REPORT，逐条对照）：
 *
 * 1) dffeas：原模型为 `always @(posedge clk, posedge aload)`，同一寄存器
 *    带两个边沿敏感事件，Yosys proc_dff 无法处理（报 "Multiple edge
 *    sensitive events found for this signal"）。原模型在两个边沿执行的
 *    赋值逻辑完全相同（if(reset) q_tmp<=0 else q_tmp<=d）。本设计中全部
 *    222/12/10 个 dffeas 实例的 aload 均连接常量 1'0（已统计验证），
 *    "aload 边沿永不发生"，因此去掉 aload 边沿是精确等价——假设 aload
 *    恒为 0，仅在该连接事实下成立。
 *
 * 2) cycloneiv_lcell_comb：以等价组合形式重建与原件 lut_data 完全相同的
 *    LUT 语义。原件行为（cells_sim.v:79-91）：
 *      s3 = datad ? mask[15:8] : mask[7:0]
 *      s2 = datac ? s3[7:4] : s3[3:0]
 *      s1 = datab ? s2[3:2] : s2[1:0]
 *      lut_data = dataa ? s1[1] : s1[0]
 *    即 lut_data(mask,a,b,c,d) = mask[{d,c,b,a}]（位索引高到低 d,c,b,a）。
 *    combout：sum_lutc_input=="cin" 时第三输入用 cin，否则用 datac；
 *    cout 固定用 {datad, cin, datab, dataa} 索引。
 *
 * 3) 去掉 initial、$error、$finish 等仿真控制语句（形式语义无关）。
 *
 * 4) VCC/GND 以行为级常量驱动重建（与 cells_sim.v 的 assign V=1'b1 一致）。
 */

module cycloneiv_lcell_comb
  (output combout,
   output cout,
   input dataa, datab, datac, datad, cin);

   parameter lut_mask = 16'hFFFF;
   parameter dont_touch = "off";
   parameter lpm_type = "cycloneiv_lcell_comb";
   parameter sum_lutc_input = "datac";

   function lut_bit;
      input [15:0] mask;
      input [3:0]  idx;
      begin
         lut_bit = mask[idx];
      end
   endfunction

   wire [3:0] comb_idx =
      (sum_lutc_input == "cin") ? {datad, cin, datab, dataa}
                                : {datad, datac, datab, dataa};
   wire [3:0] cout_idx = {datad, cin, datab, dataa};

   assign combout = lut_bit(lut_mask, comb_idx);
   assign cout    = lut_bit(lut_mask, cout_idx);

endmodule // cycloneiv_lcell_comb (formal functional model)


module dffeas
  (output q,
   input d, clk, clrn, prn, ena,
   input asdata, aload, sclr, sload);

   parameter power_up = "dontcare";
   parameter is_wysiwyg = "false";

   wire reset = (prn && sclr && ~clrn && ena);
   reg  q_tmp;

   always @(posedge clk) begin
      if (reset)
         q_tmp <= 1'b0;
      else
         q_tmp <= d;
   end

   assign q = q_tmp;

endmodule // dffeas (formal functional model, aload == 1'b0 assumption)


module VCC (output V);
   assign V = 1'b1;
endmodule

module GND (output G);
   assign G = 1'b0;
endmodule
