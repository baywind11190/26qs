/*
 * Cyclone IV 形式验证功能模型（器件语义核对版 v3）——独立实验模型
 * 生成于：2026-09-24 初值建模修正 第01轮 · 06_器件语义模型_v3（固定提交 5c44e87…）
 *
 * 设计依据（均已核对，见 06 目录 00_README 与 04/05 证据文档）：
 *   1) Quartus 官方形式验证库 fv_lib/verilog/dffeas.v：
 *        actual_d = sclr ? 1'b0 : (sload ? asdata : d);
 *        arst = ~clrn | (clrn & aload & ~asdata);
 *        aset = ~prn  | (clrn & aload &  asdata);
 *        异步优先级 arst > aset > 时钟路径；ena 为时钟使能。
 *   2) Quartus 官方仿真原语 sim_lib/altera_primitives.v：
 *        清零 = clrn 有效（低）；置位 = prn 有效（低）；
 *        initial: power_up == "high" ? 1 : 0（非 high 一律 0）。
 *   3) Yosys 0.69 映射规则 techlibs/intel/common/ff_map.v 与本轮 8 个 mapped 网表统计：
 *        prn=1'b1、sclr=sload=aload=asdata=1'b0 恒为常量；clrn 为常量 1 或信号；
 *        ena 大多为信号驱动；power_up 全部 "low"。
 *
 * 本轮支持配置（其余由 02_model_v3/precheck_supported_config.py 明确阻断，不静默建模）：
 *      power_up ∈ {"low","high"}; prn=1'b1; sclr=sload=aload=asdata=1'b0;
 *      clrn、ena 可为常量或信号。
 *
 * 与 v2 的差异（dffeas 功能语义，唯一变量）：
 *   a) 清零路径：clrn 低 = 异步清零（v2 未实现；最小复现已证实其为独立反例来源）；
 *   b) 时钟使能：ena=0 时保持（v2 未实现；本轮网表 200+ 实例 ena 为信号驱动）；
 *   c) 初值：power_up=="high"→1、=="low"→0（与 v2 相同）；其他取值不在支持集，
 *      由预检阻断（模型侧不为其静默选择语义）。
 *   d) 数据路径限制为受支持配置（sclr/sload/aload/asdata 常量 0 时 actual_d = d）。
 * VCC/GND 与 cycloneiv_lcell_comb 与 v2 逐字节相同，保证与 v2 对照时唯一变量是 dffeas。
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

   reg q_tmp;

   // 上电初值（器件语义：high→1、low→0；其他取值由预检阻断，不应出现）
   initial begin
      if (power_up == "high")
         q_tmp = 1'b1;
      else if (power_up == "low")
         q_tmp = 1'b0;
   end

   // 器件语义（受支持配置）：
   //   clrn 低 = 异步清零（优先级高于时钟路径）；
   //   ena = 时钟使能（ena=0 时保持，不装载）。
   //   prn/sclr/sload/aload/asdata 由预检确认为无效常量，未建模其路径。
   always @(posedge clk or negedge clrn) begin
      if (!clrn)
         q_tmp <= 1'b0;
      else if (ena)
         q_tmp <= d;
   end

   assign q = q_tmp;

endmodule // dffeas (device-semantics model v3, supported configuration only)


module VCC (output V);
   assign V = 1'b1;
endmodule

module GND (output G);
   assign G = 1'b0;
endmodule
