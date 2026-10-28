// official4-p2 形式化自检（gold 侧 RTL 参考）。
// 移植自 2026-09-24「初值建模修正」06_器件语义模型_v3/03_模型检查/model_checks.v
// （origin sha256=4049c94e26352e23aa93aeebec2a41607fb8b3b70b4f5a32491f36f548e34842），
// 并新增 LUT 逻辑对照与未声明初值回归（maskreg）。gold/gate 两侧模块同名，
// 由 EQY 按名匹配比较（不手工构造比较器）。
module mac_init_ok (input clk, input d, output q);
   reg r;
   initial r = 1'b0;
   always @(posedge clk) r <= d;
   assign q = r;
endmodule

module mac_init_conflict (input clk, input d, output q);
   reg r;
   initial r = 1'b1;             // 与 gate 侧 power_up="low" 冲突：应被检出
   always @(posedge clk) r <= d;
   assign q = r;
endmodule

module mac_clr (input clk, input rst, input ena, input d, output q);
   reg r;
   initial r = 1'b0;
   always @(posedge clk or posedge rst)
      if (rst) r <= 1'b0;
      else if (ena) r <= d;
   assign q = r;
endmodule

module mac_ena (input clk, input ena, input d, output q);
   reg r;
   initial r = 1'b0;
   always @(posedge clk) if (ena) r <= d;
   assign q = r;
endmodule

module mac_lut_ok (input a, input b, output y);
   assign y = a & b;             // gate 侧为等价 AND LUT：应通过
endmodule

module mac_lut_bad (input a, input b, output y);
   assign y = a & b;             // gate 侧被替换为 OR 型 LUT：应被检出
endmodule

module maskreg (input clk, input d, output q);
   reg r;                        // 未声明初值（保持 x）：用于“矛盾前提回归”检查
   always @(posedge clk) r <= d;
   assign q = r;
endmodule
