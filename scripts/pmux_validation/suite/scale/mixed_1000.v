module stress_top(
    input [147:0] a_ctrl,
    input [1183:0] a_data,
    output [591:0] a_out,
    input [175:0] c_ctrl,
    output [175:0] c_out,
    input [61:0] n_ctrl,
    input [495:0] n_data,
    output [123:0] n_out
);

wire [1:0] a_ctrl_0 = a_ctrl[0 +: 2];
wire [15:0] a_data_0 = a_data[0 +: 16];
reg [3:0] a_x_0;
reg [3:0] a_y_0;

always @* begin
    a_x_0 = 4'b0;
    a_y_0 = 4'b0;
    case (a_ctrl_0)
        2'd0: begin a_x_0 = a_data_0[3:0];   a_y_0 = a_data_0[11:8];  end
        2'd1: begin a_x_0 = a_data_0[11:8];  a_y_0 = a_data_0[3:0];   end
        2'd2: begin a_x_0 = a_data_0[7:4];   a_y_0 = a_data_0[15:12]; end
        2'd3: begin a_x_0 = a_data_0[15:12]; a_y_0 = a_data_0[7:4];   end
    endcase
end
assign a_out[0 +: 4] = a_x_0;
assign a_out[4 +: 4] = a_y_0;

wire [1:0] a_ctrl_1 = a_ctrl[2 +: 2];
wire [15:0] a_data_1 = a_data[16 +: 16];
reg [3:0] a_x_1;
reg [3:0] a_y_1;

always @* begin
    a_x_1 = 4'b0;
    a_y_1 = 4'b0;
    case (a_ctrl_1)
        2'd0: begin a_x_1 = a_data_1[3:0];   a_y_1 = a_data_1[11:8];  end
        2'd1: begin a_x_1 = a_data_1[11:8];  a_y_1 = a_data_1[3:0];   end
        2'd2: begin a_x_1 = a_data_1[7:4];   a_y_1 = a_data_1[15:12]; end
        2'd3: begin a_x_1 = a_data_1[15:12]; a_y_1 = a_data_1[7:4];   end
    endcase
end
assign a_out[8 +: 4] = a_x_1;
assign a_out[12 +: 4] = a_y_1;

wire [1:0] a_ctrl_2 = a_ctrl[4 +: 2];
wire [15:0] a_data_2 = a_data[32 +: 16];
reg [3:0] a_x_2;
reg [3:0] a_y_2;

always @* begin
    a_x_2 = 4'b0;
    a_y_2 = 4'b0;
    case (a_ctrl_2)
        2'd0: begin a_x_2 = a_data_2[3:0];   a_y_2 = a_data_2[11:8];  end
        2'd1: begin a_x_2 = a_data_2[11:8];  a_y_2 = a_data_2[3:0];   end
        2'd2: begin a_x_2 = a_data_2[7:4];   a_y_2 = a_data_2[15:12]; end
        2'd3: begin a_x_2 = a_data_2[15:12]; a_y_2 = a_data_2[7:4];   end
    endcase
end
assign a_out[16 +: 4] = a_x_2;
assign a_out[20 +: 4] = a_y_2;

wire [1:0] a_ctrl_3 = a_ctrl[6 +: 2];
wire [15:0] a_data_3 = a_data[48 +: 16];
reg [3:0] a_x_3;
reg [3:0] a_y_3;

always @* begin
    a_x_3 = 4'b0;
    a_y_3 = 4'b0;
    case (a_ctrl_3)
        2'd0: begin a_x_3 = a_data_3[3:0];   a_y_3 = a_data_3[11:8];  end
        2'd1: begin a_x_3 = a_data_3[11:8];  a_y_3 = a_data_3[3:0];   end
        2'd2: begin a_x_3 = a_data_3[7:4];   a_y_3 = a_data_3[15:12]; end
        2'd3: begin a_x_3 = a_data_3[15:12]; a_y_3 = a_data_3[7:4];   end
    endcase
end
assign a_out[24 +: 4] = a_x_3;
assign a_out[28 +: 4] = a_y_3;

wire [1:0] a_ctrl_4 = a_ctrl[8 +: 2];
wire [15:0] a_data_4 = a_data[64 +: 16];
reg [3:0] a_x_4;
reg [3:0] a_y_4;

always @* begin
    a_x_4 = 4'b0;
    a_y_4 = 4'b0;
    case (a_ctrl_4)
        2'd0: begin a_x_4 = a_data_4[3:0];   a_y_4 = a_data_4[11:8];  end
        2'd1: begin a_x_4 = a_data_4[11:8];  a_y_4 = a_data_4[3:0];   end
        2'd2: begin a_x_4 = a_data_4[7:4];   a_y_4 = a_data_4[15:12]; end
        2'd3: begin a_x_4 = a_data_4[15:12]; a_y_4 = a_data_4[7:4];   end
    endcase
end
assign a_out[32 +: 4] = a_x_4;
assign a_out[36 +: 4] = a_y_4;

wire [1:0] a_ctrl_5 = a_ctrl[10 +: 2];
wire [15:0] a_data_5 = a_data[80 +: 16];
reg [3:0] a_x_5;
reg [3:0] a_y_5;

always @* begin
    a_x_5 = 4'b0;
    a_y_5 = 4'b0;
    case (a_ctrl_5)
        2'd0: begin a_x_5 = a_data_5[3:0];   a_y_5 = a_data_5[11:8];  end
        2'd1: begin a_x_5 = a_data_5[11:8];  a_y_5 = a_data_5[3:0];   end
        2'd2: begin a_x_5 = a_data_5[7:4];   a_y_5 = a_data_5[15:12]; end
        2'd3: begin a_x_5 = a_data_5[15:12]; a_y_5 = a_data_5[7:4];   end
    endcase
end
assign a_out[40 +: 4] = a_x_5;
assign a_out[44 +: 4] = a_y_5;

wire [1:0] a_ctrl_6 = a_ctrl[12 +: 2];
wire [15:0] a_data_6 = a_data[96 +: 16];
reg [3:0] a_x_6;
reg [3:0] a_y_6;

always @* begin
    a_x_6 = 4'b0;
    a_y_6 = 4'b0;
    case (a_ctrl_6)
        2'd0: begin a_x_6 = a_data_6[3:0];   a_y_6 = a_data_6[11:8];  end
        2'd1: begin a_x_6 = a_data_6[11:8];  a_y_6 = a_data_6[3:0];   end
        2'd2: begin a_x_6 = a_data_6[7:4];   a_y_6 = a_data_6[15:12]; end
        2'd3: begin a_x_6 = a_data_6[15:12]; a_y_6 = a_data_6[7:4];   end
    endcase
end
assign a_out[48 +: 4] = a_x_6;
assign a_out[52 +: 4] = a_y_6;

wire [1:0] a_ctrl_7 = a_ctrl[14 +: 2];
wire [15:0] a_data_7 = a_data[112 +: 16];
reg [3:0] a_x_7;
reg [3:0] a_y_7;

always @* begin
    a_x_7 = 4'b0;
    a_y_7 = 4'b0;
    case (a_ctrl_7)
        2'd0: begin a_x_7 = a_data_7[3:0];   a_y_7 = a_data_7[11:8];  end
        2'd1: begin a_x_7 = a_data_7[11:8];  a_y_7 = a_data_7[3:0];   end
        2'd2: begin a_x_7 = a_data_7[7:4];   a_y_7 = a_data_7[15:12]; end
        2'd3: begin a_x_7 = a_data_7[15:12]; a_y_7 = a_data_7[7:4];   end
    endcase
end
assign a_out[56 +: 4] = a_x_7;
assign a_out[60 +: 4] = a_y_7;

wire [1:0] a_ctrl_8 = a_ctrl[16 +: 2];
wire [15:0] a_data_8 = a_data[128 +: 16];
reg [3:0] a_x_8;
reg [3:0] a_y_8;

always @* begin
    a_x_8 = 4'b0;
    a_y_8 = 4'b0;
    case (a_ctrl_8)
        2'd0: begin a_x_8 = a_data_8[3:0];   a_y_8 = a_data_8[11:8];  end
        2'd1: begin a_x_8 = a_data_8[11:8];  a_y_8 = a_data_8[3:0];   end
        2'd2: begin a_x_8 = a_data_8[7:4];   a_y_8 = a_data_8[15:12]; end
        2'd3: begin a_x_8 = a_data_8[15:12]; a_y_8 = a_data_8[7:4];   end
    endcase
end
assign a_out[64 +: 4] = a_x_8;
assign a_out[68 +: 4] = a_y_8;

wire [1:0] a_ctrl_9 = a_ctrl[18 +: 2];
wire [15:0] a_data_9 = a_data[144 +: 16];
reg [3:0] a_x_9;
reg [3:0] a_y_9;

always @* begin
    a_x_9 = 4'b0;
    a_y_9 = 4'b0;
    case (a_ctrl_9)
        2'd0: begin a_x_9 = a_data_9[3:0];   a_y_9 = a_data_9[11:8];  end
        2'd1: begin a_x_9 = a_data_9[11:8];  a_y_9 = a_data_9[3:0];   end
        2'd2: begin a_x_9 = a_data_9[7:4];   a_y_9 = a_data_9[15:12]; end
        2'd3: begin a_x_9 = a_data_9[15:12]; a_y_9 = a_data_9[7:4];   end
    endcase
end
assign a_out[72 +: 4] = a_x_9;
assign a_out[76 +: 4] = a_y_9;

wire [1:0] a_ctrl_10 = a_ctrl[20 +: 2];
wire [15:0] a_data_10 = a_data[160 +: 16];
reg [3:0] a_x_10;
reg [3:0] a_y_10;

always @* begin
    a_x_10 = 4'b0;
    a_y_10 = 4'b0;
    case (a_ctrl_10)
        2'd0: begin a_x_10 = a_data_10[3:0];   a_y_10 = a_data_10[11:8];  end
        2'd1: begin a_x_10 = a_data_10[11:8];  a_y_10 = a_data_10[3:0];   end
        2'd2: begin a_x_10 = a_data_10[7:4];   a_y_10 = a_data_10[15:12]; end
        2'd3: begin a_x_10 = a_data_10[15:12]; a_y_10 = a_data_10[7:4];   end
    endcase
end
assign a_out[80 +: 4] = a_x_10;
assign a_out[84 +: 4] = a_y_10;

wire [1:0] a_ctrl_11 = a_ctrl[22 +: 2];
wire [15:0] a_data_11 = a_data[176 +: 16];
reg [3:0] a_x_11;
reg [3:0] a_y_11;

always @* begin
    a_x_11 = 4'b0;
    a_y_11 = 4'b0;
    case (a_ctrl_11)
        2'd0: begin a_x_11 = a_data_11[3:0];   a_y_11 = a_data_11[11:8];  end
        2'd1: begin a_x_11 = a_data_11[11:8];  a_y_11 = a_data_11[3:0];   end
        2'd2: begin a_x_11 = a_data_11[7:4];   a_y_11 = a_data_11[15:12]; end
        2'd3: begin a_x_11 = a_data_11[15:12]; a_y_11 = a_data_11[7:4];   end
    endcase
end
assign a_out[88 +: 4] = a_x_11;
assign a_out[92 +: 4] = a_y_11;

wire [1:0] a_ctrl_12 = a_ctrl[24 +: 2];
wire [15:0] a_data_12 = a_data[192 +: 16];
reg [3:0] a_x_12;
reg [3:0] a_y_12;

always @* begin
    a_x_12 = 4'b0;
    a_y_12 = 4'b0;
    case (a_ctrl_12)
        2'd0: begin a_x_12 = a_data_12[3:0];   a_y_12 = a_data_12[11:8];  end
        2'd1: begin a_x_12 = a_data_12[11:8];  a_y_12 = a_data_12[3:0];   end
        2'd2: begin a_x_12 = a_data_12[7:4];   a_y_12 = a_data_12[15:12]; end
        2'd3: begin a_x_12 = a_data_12[15:12]; a_y_12 = a_data_12[7:4];   end
    endcase
end
assign a_out[96 +: 4] = a_x_12;
assign a_out[100 +: 4] = a_y_12;

wire [1:0] a_ctrl_13 = a_ctrl[26 +: 2];
wire [15:0] a_data_13 = a_data[208 +: 16];
reg [3:0] a_x_13;
reg [3:0] a_y_13;

always @* begin
    a_x_13 = 4'b0;
    a_y_13 = 4'b0;
    case (a_ctrl_13)
        2'd0: begin a_x_13 = a_data_13[3:0];   a_y_13 = a_data_13[11:8];  end
        2'd1: begin a_x_13 = a_data_13[11:8];  a_y_13 = a_data_13[3:0];   end
        2'd2: begin a_x_13 = a_data_13[7:4];   a_y_13 = a_data_13[15:12]; end
        2'd3: begin a_x_13 = a_data_13[15:12]; a_y_13 = a_data_13[7:4];   end
    endcase
end
assign a_out[104 +: 4] = a_x_13;
assign a_out[108 +: 4] = a_y_13;

wire [1:0] a_ctrl_14 = a_ctrl[28 +: 2];
wire [15:0] a_data_14 = a_data[224 +: 16];
reg [3:0] a_x_14;
reg [3:0] a_y_14;

always @* begin
    a_x_14 = 4'b0;
    a_y_14 = 4'b0;
    case (a_ctrl_14)
        2'd0: begin a_x_14 = a_data_14[3:0];   a_y_14 = a_data_14[11:8];  end
        2'd1: begin a_x_14 = a_data_14[11:8];  a_y_14 = a_data_14[3:0];   end
        2'd2: begin a_x_14 = a_data_14[7:4];   a_y_14 = a_data_14[15:12]; end
        2'd3: begin a_x_14 = a_data_14[15:12]; a_y_14 = a_data_14[7:4];   end
    endcase
end
assign a_out[112 +: 4] = a_x_14;
assign a_out[116 +: 4] = a_y_14;

wire [1:0] a_ctrl_15 = a_ctrl[30 +: 2];
wire [15:0] a_data_15 = a_data[240 +: 16];
reg [3:0] a_x_15;
reg [3:0] a_y_15;

always @* begin
    a_x_15 = 4'b0;
    a_y_15 = 4'b0;
    case (a_ctrl_15)
        2'd0: begin a_x_15 = a_data_15[3:0];   a_y_15 = a_data_15[11:8];  end
        2'd1: begin a_x_15 = a_data_15[11:8];  a_y_15 = a_data_15[3:0];   end
        2'd2: begin a_x_15 = a_data_15[7:4];   a_y_15 = a_data_15[15:12]; end
        2'd3: begin a_x_15 = a_data_15[15:12]; a_y_15 = a_data_15[7:4];   end
    endcase
end
assign a_out[120 +: 4] = a_x_15;
assign a_out[124 +: 4] = a_y_15;

wire [1:0] a_ctrl_16 = a_ctrl[32 +: 2];
wire [15:0] a_data_16 = a_data[256 +: 16];
reg [3:0] a_x_16;
reg [3:0] a_y_16;

always @* begin
    a_x_16 = 4'b0;
    a_y_16 = 4'b0;
    case (a_ctrl_16)
        2'd0: begin a_x_16 = a_data_16[3:0];   a_y_16 = a_data_16[11:8];  end
        2'd1: begin a_x_16 = a_data_16[11:8];  a_y_16 = a_data_16[3:0];   end
        2'd2: begin a_x_16 = a_data_16[7:4];   a_y_16 = a_data_16[15:12]; end
        2'd3: begin a_x_16 = a_data_16[15:12]; a_y_16 = a_data_16[7:4];   end
    endcase
end
assign a_out[128 +: 4] = a_x_16;
assign a_out[132 +: 4] = a_y_16;

wire [1:0] a_ctrl_17 = a_ctrl[34 +: 2];
wire [15:0] a_data_17 = a_data[272 +: 16];
reg [3:0] a_x_17;
reg [3:0] a_y_17;

always @* begin
    a_x_17 = 4'b0;
    a_y_17 = 4'b0;
    case (a_ctrl_17)
        2'd0: begin a_x_17 = a_data_17[3:0];   a_y_17 = a_data_17[11:8];  end
        2'd1: begin a_x_17 = a_data_17[11:8];  a_y_17 = a_data_17[3:0];   end
        2'd2: begin a_x_17 = a_data_17[7:4];   a_y_17 = a_data_17[15:12]; end
        2'd3: begin a_x_17 = a_data_17[15:12]; a_y_17 = a_data_17[7:4];   end
    endcase
end
assign a_out[136 +: 4] = a_x_17;
assign a_out[140 +: 4] = a_y_17;

wire [1:0] a_ctrl_18 = a_ctrl[36 +: 2];
wire [15:0] a_data_18 = a_data[288 +: 16];
reg [3:0] a_x_18;
reg [3:0] a_y_18;

always @* begin
    a_x_18 = 4'b0;
    a_y_18 = 4'b0;
    case (a_ctrl_18)
        2'd0: begin a_x_18 = a_data_18[3:0];   a_y_18 = a_data_18[11:8];  end
        2'd1: begin a_x_18 = a_data_18[11:8];  a_y_18 = a_data_18[3:0];   end
        2'd2: begin a_x_18 = a_data_18[7:4];   a_y_18 = a_data_18[15:12]; end
        2'd3: begin a_x_18 = a_data_18[15:12]; a_y_18 = a_data_18[7:4];   end
    endcase
end
assign a_out[144 +: 4] = a_x_18;
assign a_out[148 +: 4] = a_y_18;

wire [1:0] a_ctrl_19 = a_ctrl[38 +: 2];
wire [15:0] a_data_19 = a_data[304 +: 16];
reg [3:0] a_x_19;
reg [3:0] a_y_19;

always @* begin
    a_x_19 = 4'b0;
    a_y_19 = 4'b0;
    case (a_ctrl_19)
        2'd0: begin a_x_19 = a_data_19[3:0];   a_y_19 = a_data_19[11:8];  end
        2'd1: begin a_x_19 = a_data_19[11:8];  a_y_19 = a_data_19[3:0];   end
        2'd2: begin a_x_19 = a_data_19[7:4];   a_y_19 = a_data_19[15:12]; end
        2'd3: begin a_x_19 = a_data_19[15:12]; a_y_19 = a_data_19[7:4];   end
    endcase
end
assign a_out[152 +: 4] = a_x_19;
assign a_out[156 +: 4] = a_y_19;

wire [1:0] a_ctrl_20 = a_ctrl[40 +: 2];
wire [15:0] a_data_20 = a_data[320 +: 16];
reg [3:0] a_x_20;
reg [3:0] a_y_20;

always @* begin
    a_x_20 = 4'b0;
    a_y_20 = 4'b0;
    case (a_ctrl_20)
        2'd0: begin a_x_20 = a_data_20[3:0];   a_y_20 = a_data_20[11:8];  end
        2'd1: begin a_x_20 = a_data_20[11:8];  a_y_20 = a_data_20[3:0];   end
        2'd2: begin a_x_20 = a_data_20[7:4];   a_y_20 = a_data_20[15:12]; end
        2'd3: begin a_x_20 = a_data_20[15:12]; a_y_20 = a_data_20[7:4];   end
    endcase
end
assign a_out[160 +: 4] = a_x_20;
assign a_out[164 +: 4] = a_y_20;

wire [1:0] a_ctrl_21 = a_ctrl[42 +: 2];
wire [15:0] a_data_21 = a_data[336 +: 16];
reg [3:0] a_x_21;
reg [3:0] a_y_21;

always @* begin
    a_x_21 = 4'b0;
    a_y_21 = 4'b0;
    case (a_ctrl_21)
        2'd0: begin a_x_21 = a_data_21[3:0];   a_y_21 = a_data_21[11:8];  end
        2'd1: begin a_x_21 = a_data_21[11:8];  a_y_21 = a_data_21[3:0];   end
        2'd2: begin a_x_21 = a_data_21[7:4];   a_y_21 = a_data_21[15:12]; end
        2'd3: begin a_x_21 = a_data_21[15:12]; a_y_21 = a_data_21[7:4];   end
    endcase
end
assign a_out[168 +: 4] = a_x_21;
assign a_out[172 +: 4] = a_y_21;

wire [1:0] a_ctrl_22 = a_ctrl[44 +: 2];
wire [15:0] a_data_22 = a_data[352 +: 16];
reg [3:0] a_x_22;
reg [3:0] a_y_22;

always @* begin
    a_x_22 = 4'b0;
    a_y_22 = 4'b0;
    case (a_ctrl_22)
        2'd0: begin a_x_22 = a_data_22[3:0];   a_y_22 = a_data_22[11:8];  end
        2'd1: begin a_x_22 = a_data_22[11:8];  a_y_22 = a_data_22[3:0];   end
        2'd2: begin a_x_22 = a_data_22[7:4];   a_y_22 = a_data_22[15:12]; end
        2'd3: begin a_x_22 = a_data_22[15:12]; a_y_22 = a_data_22[7:4];   end
    endcase
end
assign a_out[176 +: 4] = a_x_22;
assign a_out[180 +: 4] = a_y_22;

wire [1:0] a_ctrl_23 = a_ctrl[46 +: 2];
wire [15:0] a_data_23 = a_data[368 +: 16];
reg [3:0] a_x_23;
reg [3:0] a_y_23;

always @* begin
    a_x_23 = 4'b0;
    a_y_23 = 4'b0;
    case (a_ctrl_23)
        2'd0: begin a_x_23 = a_data_23[3:0];   a_y_23 = a_data_23[11:8];  end
        2'd1: begin a_x_23 = a_data_23[11:8];  a_y_23 = a_data_23[3:0];   end
        2'd2: begin a_x_23 = a_data_23[7:4];   a_y_23 = a_data_23[15:12]; end
        2'd3: begin a_x_23 = a_data_23[15:12]; a_y_23 = a_data_23[7:4];   end
    endcase
end
assign a_out[184 +: 4] = a_x_23;
assign a_out[188 +: 4] = a_y_23;

wire [1:0] a_ctrl_24 = a_ctrl[48 +: 2];
wire [15:0] a_data_24 = a_data[384 +: 16];
reg [3:0] a_x_24;
reg [3:0] a_y_24;

always @* begin
    a_x_24 = 4'b0;
    a_y_24 = 4'b0;
    case (a_ctrl_24)
        2'd0: begin a_x_24 = a_data_24[3:0];   a_y_24 = a_data_24[11:8];  end
        2'd1: begin a_x_24 = a_data_24[11:8];  a_y_24 = a_data_24[3:0];   end
        2'd2: begin a_x_24 = a_data_24[7:4];   a_y_24 = a_data_24[15:12]; end
        2'd3: begin a_x_24 = a_data_24[15:12]; a_y_24 = a_data_24[7:4];   end
    endcase
end
assign a_out[192 +: 4] = a_x_24;
assign a_out[196 +: 4] = a_y_24;

wire [1:0] a_ctrl_25 = a_ctrl[50 +: 2];
wire [15:0] a_data_25 = a_data[400 +: 16];
reg [3:0] a_x_25;
reg [3:0] a_y_25;

always @* begin
    a_x_25 = 4'b0;
    a_y_25 = 4'b0;
    case (a_ctrl_25)
        2'd0: begin a_x_25 = a_data_25[3:0];   a_y_25 = a_data_25[11:8];  end
        2'd1: begin a_x_25 = a_data_25[11:8];  a_y_25 = a_data_25[3:0];   end
        2'd2: begin a_x_25 = a_data_25[7:4];   a_y_25 = a_data_25[15:12]; end
        2'd3: begin a_x_25 = a_data_25[15:12]; a_y_25 = a_data_25[7:4];   end
    endcase
end
assign a_out[200 +: 4] = a_x_25;
assign a_out[204 +: 4] = a_y_25;

wire [1:0] a_ctrl_26 = a_ctrl[52 +: 2];
wire [15:0] a_data_26 = a_data[416 +: 16];
reg [3:0] a_x_26;
reg [3:0] a_y_26;

always @* begin
    a_x_26 = 4'b0;
    a_y_26 = 4'b0;
    case (a_ctrl_26)
        2'd0: begin a_x_26 = a_data_26[3:0];   a_y_26 = a_data_26[11:8];  end
        2'd1: begin a_x_26 = a_data_26[11:8];  a_y_26 = a_data_26[3:0];   end
        2'd2: begin a_x_26 = a_data_26[7:4];   a_y_26 = a_data_26[15:12]; end
        2'd3: begin a_x_26 = a_data_26[15:12]; a_y_26 = a_data_26[7:4];   end
    endcase
end
assign a_out[208 +: 4] = a_x_26;
assign a_out[212 +: 4] = a_y_26;

wire [1:0] a_ctrl_27 = a_ctrl[54 +: 2];
wire [15:0] a_data_27 = a_data[432 +: 16];
reg [3:0] a_x_27;
reg [3:0] a_y_27;

always @* begin
    a_x_27 = 4'b0;
    a_y_27 = 4'b0;
    case (a_ctrl_27)
        2'd0: begin a_x_27 = a_data_27[3:0];   a_y_27 = a_data_27[11:8];  end
        2'd1: begin a_x_27 = a_data_27[11:8];  a_y_27 = a_data_27[3:0];   end
        2'd2: begin a_x_27 = a_data_27[7:4];   a_y_27 = a_data_27[15:12]; end
        2'd3: begin a_x_27 = a_data_27[15:12]; a_y_27 = a_data_27[7:4];   end
    endcase
end
assign a_out[216 +: 4] = a_x_27;
assign a_out[220 +: 4] = a_y_27;

wire [1:0] a_ctrl_28 = a_ctrl[56 +: 2];
wire [15:0] a_data_28 = a_data[448 +: 16];
reg [3:0] a_x_28;
reg [3:0] a_y_28;

always @* begin
    a_x_28 = 4'b0;
    a_y_28 = 4'b0;
    case (a_ctrl_28)
        2'd0: begin a_x_28 = a_data_28[3:0];   a_y_28 = a_data_28[11:8];  end
        2'd1: begin a_x_28 = a_data_28[11:8];  a_y_28 = a_data_28[3:0];   end
        2'd2: begin a_x_28 = a_data_28[7:4];   a_y_28 = a_data_28[15:12]; end
        2'd3: begin a_x_28 = a_data_28[15:12]; a_y_28 = a_data_28[7:4];   end
    endcase
end
assign a_out[224 +: 4] = a_x_28;
assign a_out[228 +: 4] = a_y_28;

wire [1:0] a_ctrl_29 = a_ctrl[58 +: 2];
wire [15:0] a_data_29 = a_data[464 +: 16];
reg [3:0] a_x_29;
reg [3:0] a_y_29;

always @* begin
    a_x_29 = 4'b0;
    a_y_29 = 4'b0;
    case (a_ctrl_29)
        2'd0: begin a_x_29 = a_data_29[3:0];   a_y_29 = a_data_29[11:8];  end
        2'd1: begin a_x_29 = a_data_29[11:8];  a_y_29 = a_data_29[3:0];   end
        2'd2: begin a_x_29 = a_data_29[7:4];   a_y_29 = a_data_29[15:12]; end
        2'd3: begin a_x_29 = a_data_29[15:12]; a_y_29 = a_data_29[7:4];   end
    endcase
end
assign a_out[232 +: 4] = a_x_29;
assign a_out[236 +: 4] = a_y_29;

wire [1:0] a_ctrl_30 = a_ctrl[60 +: 2];
wire [15:0] a_data_30 = a_data[480 +: 16];
reg [3:0] a_x_30;
reg [3:0] a_y_30;

always @* begin
    a_x_30 = 4'b0;
    a_y_30 = 4'b0;
    case (a_ctrl_30)
        2'd0: begin a_x_30 = a_data_30[3:0];   a_y_30 = a_data_30[11:8];  end
        2'd1: begin a_x_30 = a_data_30[11:8];  a_y_30 = a_data_30[3:0];   end
        2'd2: begin a_x_30 = a_data_30[7:4];   a_y_30 = a_data_30[15:12]; end
        2'd3: begin a_x_30 = a_data_30[15:12]; a_y_30 = a_data_30[7:4];   end
    endcase
end
assign a_out[240 +: 4] = a_x_30;
assign a_out[244 +: 4] = a_y_30;

wire [1:0] a_ctrl_31 = a_ctrl[62 +: 2];
wire [15:0] a_data_31 = a_data[496 +: 16];
reg [3:0] a_x_31;
reg [3:0] a_y_31;

always @* begin
    a_x_31 = 4'b0;
    a_y_31 = 4'b0;
    case (a_ctrl_31)
        2'd0: begin a_x_31 = a_data_31[3:0];   a_y_31 = a_data_31[11:8];  end
        2'd1: begin a_x_31 = a_data_31[11:8];  a_y_31 = a_data_31[3:0];   end
        2'd2: begin a_x_31 = a_data_31[7:4];   a_y_31 = a_data_31[15:12]; end
        2'd3: begin a_x_31 = a_data_31[15:12]; a_y_31 = a_data_31[7:4];   end
    endcase
end
assign a_out[248 +: 4] = a_x_31;
assign a_out[252 +: 4] = a_y_31;

wire [1:0] a_ctrl_32 = a_ctrl[64 +: 2];
wire [15:0] a_data_32 = a_data[512 +: 16];
reg [3:0] a_x_32;
reg [3:0] a_y_32;

always @* begin
    a_x_32 = 4'b0;
    a_y_32 = 4'b0;
    case (a_ctrl_32)
        2'd0: begin a_x_32 = a_data_32[3:0];   a_y_32 = a_data_32[11:8];  end
        2'd1: begin a_x_32 = a_data_32[11:8];  a_y_32 = a_data_32[3:0];   end
        2'd2: begin a_x_32 = a_data_32[7:4];   a_y_32 = a_data_32[15:12]; end
        2'd3: begin a_x_32 = a_data_32[15:12]; a_y_32 = a_data_32[7:4];   end
    endcase
end
assign a_out[256 +: 4] = a_x_32;
assign a_out[260 +: 4] = a_y_32;

wire [1:0] a_ctrl_33 = a_ctrl[66 +: 2];
wire [15:0] a_data_33 = a_data[528 +: 16];
reg [3:0] a_x_33;
reg [3:0] a_y_33;

always @* begin
    a_x_33 = 4'b0;
    a_y_33 = 4'b0;
    case (a_ctrl_33)
        2'd0: begin a_x_33 = a_data_33[3:0];   a_y_33 = a_data_33[11:8];  end
        2'd1: begin a_x_33 = a_data_33[11:8];  a_y_33 = a_data_33[3:0];   end
        2'd2: begin a_x_33 = a_data_33[7:4];   a_y_33 = a_data_33[15:12]; end
        2'd3: begin a_x_33 = a_data_33[15:12]; a_y_33 = a_data_33[7:4];   end
    endcase
end
assign a_out[264 +: 4] = a_x_33;
assign a_out[268 +: 4] = a_y_33;

wire [1:0] a_ctrl_34 = a_ctrl[68 +: 2];
wire [15:0] a_data_34 = a_data[544 +: 16];
reg [3:0] a_x_34;
reg [3:0] a_y_34;

always @* begin
    a_x_34 = 4'b0;
    a_y_34 = 4'b0;
    case (a_ctrl_34)
        2'd0: begin a_x_34 = a_data_34[3:0];   a_y_34 = a_data_34[11:8];  end
        2'd1: begin a_x_34 = a_data_34[11:8];  a_y_34 = a_data_34[3:0];   end
        2'd2: begin a_x_34 = a_data_34[7:4];   a_y_34 = a_data_34[15:12]; end
        2'd3: begin a_x_34 = a_data_34[15:12]; a_y_34 = a_data_34[7:4];   end
    endcase
end
assign a_out[272 +: 4] = a_x_34;
assign a_out[276 +: 4] = a_y_34;

wire [1:0] a_ctrl_35 = a_ctrl[70 +: 2];
wire [15:0] a_data_35 = a_data[560 +: 16];
reg [3:0] a_x_35;
reg [3:0] a_y_35;

always @* begin
    a_x_35 = 4'b0;
    a_y_35 = 4'b0;
    case (a_ctrl_35)
        2'd0: begin a_x_35 = a_data_35[3:0];   a_y_35 = a_data_35[11:8];  end
        2'd1: begin a_x_35 = a_data_35[11:8];  a_y_35 = a_data_35[3:0];   end
        2'd2: begin a_x_35 = a_data_35[7:4];   a_y_35 = a_data_35[15:12]; end
        2'd3: begin a_x_35 = a_data_35[15:12]; a_y_35 = a_data_35[7:4];   end
    endcase
end
assign a_out[280 +: 4] = a_x_35;
assign a_out[284 +: 4] = a_y_35;

wire [1:0] a_ctrl_36 = a_ctrl[72 +: 2];
wire [15:0] a_data_36 = a_data[576 +: 16];
reg [3:0] a_x_36;
reg [3:0] a_y_36;

always @* begin
    a_x_36 = 4'b0;
    a_y_36 = 4'b0;
    case (a_ctrl_36)
        2'd0: begin a_x_36 = a_data_36[3:0];   a_y_36 = a_data_36[11:8];  end
        2'd1: begin a_x_36 = a_data_36[11:8];  a_y_36 = a_data_36[3:0];   end
        2'd2: begin a_x_36 = a_data_36[7:4];   a_y_36 = a_data_36[15:12]; end
        2'd3: begin a_x_36 = a_data_36[15:12]; a_y_36 = a_data_36[7:4];   end
    endcase
end
assign a_out[288 +: 4] = a_x_36;
assign a_out[292 +: 4] = a_y_36;

wire [1:0] a_ctrl_37 = a_ctrl[74 +: 2];
wire [15:0] a_data_37 = a_data[592 +: 16];
reg [3:0] a_x_37;
reg [3:0] a_y_37;

always @* begin
    a_x_37 = 4'b0;
    a_y_37 = 4'b0;
    case (a_ctrl_37)
        2'd0: begin a_x_37 = a_data_37[3:0];   a_y_37 = a_data_37[11:8];  end
        2'd1: begin a_x_37 = a_data_37[11:8];  a_y_37 = a_data_37[3:0];   end
        2'd2: begin a_x_37 = a_data_37[7:4];   a_y_37 = a_data_37[15:12]; end
        2'd3: begin a_x_37 = a_data_37[15:12]; a_y_37 = a_data_37[7:4];   end
    endcase
end
assign a_out[296 +: 4] = a_x_37;
assign a_out[300 +: 4] = a_y_37;

wire [1:0] a_ctrl_38 = a_ctrl[76 +: 2];
wire [15:0] a_data_38 = a_data[608 +: 16];
reg [3:0] a_x_38;
reg [3:0] a_y_38;

always @* begin
    a_x_38 = 4'b0;
    a_y_38 = 4'b0;
    case (a_ctrl_38)
        2'd0: begin a_x_38 = a_data_38[3:0];   a_y_38 = a_data_38[11:8];  end
        2'd1: begin a_x_38 = a_data_38[11:8];  a_y_38 = a_data_38[3:0];   end
        2'd2: begin a_x_38 = a_data_38[7:4];   a_y_38 = a_data_38[15:12]; end
        2'd3: begin a_x_38 = a_data_38[15:12]; a_y_38 = a_data_38[7:4];   end
    endcase
end
assign a_out[304 +: 4] = a_x_38;
assign a_out[308 +: 4] = a_y_38;

wire [1:0] a_ctrl_39 = a_ctrl[78 +: 2];
wire [15:0] a_data_39 = a_data[624 +: 16];
reg [3:0] a_x_39;
reg [3:0] a_y_39;

always @* begin
    a_x_39 = 4'b0;
    a_y_39 = 4'b0;
    case (a_ctrl_39)
        2'd0: begin a_x_39 = a_data_39[3:0];   a_y_39 = a_data_39[11:8];  end
        2'd1: begin a_x_39 = a_data_39[11:8];  a_y_39 = a_data_39[3:0];   end
        2'd2: begin a_x_39 = a_data_39[7:4];   a_y_39 = a_data_39[15:12]; end
        2'd3: begin a_x_39 = a_data_39[15:12]; a_y_39 = a_data_39[7:4];   end
    endcase
end
assign a_out[312 +: 4] = a_x_39;
assign a_out[316 +: 4] = a_y_39;

wire [1:0] a_ctrl_40 = a_ctrl[80 +: 2];
wire [15:0] a_data_40 = a_data[640 +: 16];
reg [3:0] a_x_40;
reg [3:0] a_y_40;

always @* begin
    a_x_40 = 4'b0;
    a_y_40 = 4'b0;
    case (a_ctrl_40)
        2'd0: begin a_x_40 = a_data_40[3:0];   a_y_40 = a_data_40[11:8];  end
        2'd1: begin a_x_40 = a_data_40[11:8];  a_y_40 = a_data_40[3:0];   end
        2'd2: begin a_x_40 = a_data_40[7:4];   a_y_40 = a_data_40[15:12]; end
        2'd3: begin a_x_40 = a_data_40[15:12]; a_y_40 = a_data_40[7:4];   end
    endcase
end
assign a_out[320 +: 4] = a_x_40;
assign a_out[324 +: 4] = a_y_40;

wire [1:0] a_ctrl_41 = a_ctrl[82 +: 2];
wire [15:0] a_data_41 = a_data[656 +: 16];
reg [3:0] a_x_41;
reg [3:0] a_y_41;

always @* begin
    a_x_41 = 4'b0;
    a_y_41 = 4'b0;
    case (a_ctrl_41)
        2'd0: begin a_x_41 = a_data_41[3:0];   a_y_41 = a_data_41[11:8];  end
        2'd1: begin a_x_41 = a_data_41[11:8];  a_y_41 = a_data_41[3:0];   end
        2'd2: begin a_x_41 = a_data_41[7:4];   a_y_41 = a_data_41[15:12]; end
        2'd3: begin a_x_41 = a_data_41[15:12]; a_y_41 = a_data_41[7:4];   end
    endcase
end
assign a_out[328 +: 4] = a_x_41;
assign a_out[332 +: 4] = a_y_41;

wire [1:0] a_ctrl_42 = a_ctrl[84 +: 2];
wire [15:0] a_data_42 = a_data[672 +: 16];
reg [3:0] a_x_42;
reg [3:0] a_y_42;

always @* begin
    a_x_42 = 4'b0;
    a_y_42 = 4'b0;
    case (a_ctrl_42)
        2'd0: begin a_x_42 = a_data_42[3:0];   a_y_42 = a_data_42[11:8];  end
        2'd1: begin a_x_42 = a_data_42[11:8];  a_y_42 = a_data_42[3:0];   end
        2'd2: begin a_x_42 = a_data_42[7:4];   a_y_42 = a_data_42[15:12]; end
        2'd3: begin a_x_42 = a_data_42[15:12]; a_y_42 = a_data_42[7:4];   end
    endcase
end
assign a_out[336 +: 4] = a_x_42;
assign a_out[340 +: 4] = a_y_42;

wire [1:0] a_ctrl_43 = a_ctrl[86 +: 2];
wire [15:0] a_data_43 = a_data[688 +: 16];
reg [3:0] a_x_43;
reg [3:0] a_y_43;

always @* begin
    a_x_43 = 4'b0;
    a_y_43 = 4'b0;
    case (a_ctrl_43)
        2'd0: begin a_x_43 = a_data_43[3:0];   a_y_43 = a_data_43[11:8];  end
        2'd1: begin a_x_43 = a_data_43[11:8];  a_y_43 = a_data_43[3:0];   end
        2'd2: begin a_x_43 = a_data_43[7:4];   a_y_43 = a_data_43[15:12]; end
        2'd3: begin a_x_43 = a_data_43[15:12]; a_y_43 = a_data_43[7:4];   end
    endcase
end
assign a_out[344 +: 4] = a_x_43;
assign a_out[348 +: 4] = a_y_43;

wire [1:0] a_ctrl_44 = a_ctrl[88 +: 2];
wire [15:0] a_data_44 = a_data[704 +: 16];
reg [3:0] a_x_44;
reg [3:0] a_y_44;

always @* begin
    a_x_44 = 4'b0;
    a_y_44 = 4'b0;
    case (a_ctrl_44)
        2'd0: begin a_x_44 = a_data_44[3:0];   a_y_44 = a_data_44[11:8];  end
        2'd1: begin a_x_44 = a_data_44[11:8];  a_y_44 = a_data_44[3:0];   end
        2'd2: begin a_x_44 = a_data_44[7:4];   a_y_44 = a_data_44[15:12]; end
        2'd3: begin a_x_44 = a_data_44[15:12]; a_y_44 = a_data_44[7:4];   end
    endcase
end
assign a_out[352 +: 4] = a_x_44;
assign a_out[356 +: 4] = a_y_44;

wire [1:0] a_ctrl_45 = a_ctrl[90 +: 2];
wire [15:0] a_data_45 = a_data[720 +: 16];
reg [3:0] a_x_45;
reg [3:0] a_y_45;

always @* begin
    a_x_45 = 4'b0;
    a_y_45 = 4'b0;
    case (a_ctrl_45)
        2'd0: begin a_x_45 = a_data_45[3:0];   a_y_45 = a_data_45[11:8];  end
        2'd1: begin a_x_45 = a_data_45[11:8];  a_y_45 = a_data_45[3:0];   end
        2'd2: begin a_x_45 = a_data_45[7:4];   a_y_45 = a_data_45[15:12]; end
        2'd3: begin a_x_45 = a_data_45[15:12]; a_y_45 = a_data_45[7:4];   end
    endcase
end
assign a_out[360 +: 4] = a_x_45;
assign a_out[364 +: 4] = a_y_45;

wire [1:0] a_ctrl_46 = a_ctrl[92 +: 2];
wire [15:0] a_data_46 = a_data[736 +: 16];
reg [3:0] a_x_46;
reg [3:0] a_y_46;

always @* begin
    a_x_46 = 4'b0;
    a_y_46 = 4'b0;
    case (a_ctrl_46)
        2'd0: begin a_x_46 = a_data_46[3:0];   a_y_46 = a_data_46[11:8];  end
        2'd1: begin a_x_46 = a_data_46[11:8];  a_y_46 = a_data_46[3:0];   end
        2'd2: begin a_x_46 = a_data_46[7:4];   a_y_46 = a_data_46[15:12]; end
        2'd3: begin a_x_46 = a_data_46[15:12]; a_y_46 = a_data_46[7:4];   end
    endcase
end
assign a_out[368 +: 4] = a_x_46;
assign a_out[372 +: 4] = a_y_46;

wire [1:0] a_ctrl_47 = a_ctrl[94 +: 2];
wire [15:0] a_data_47 = a_data[752 +: 16];
reg [3:0] a_x_47;
reg [3:0] a_y_47;

always @* begin
    a_x_47 = 4'b0;
    a_y_47 = 4'b0;
    case (a_ctrl_47)
        2'd0: begin a_x_47 = a_data_47[3:0];   a_y_47 = a_data_47[11:8];  end
        2'd1: begin a_x_47 = a_data_47[11:8];  a_y_47 = a_data_47[3:0];   end
        2'd2: begin a_x_47 = a_data_47[7:4];   a_y_47 = a_data_47[15:12]; end
        2'd3: begin a_x_47 = a_data_47[15:12]; a_y_47 = a_data_47[7:4];   end
    endcase
end
assign a_out[376 +: 4] = a_x_47;
assign a_out[380 +: 4] = a_y_47;

wire [1:0] a_ctrl_48 = a_ctrl[96 +: 2];
wire [15:0] a_data_48 = a_data[768 +: 16];
reg [3:0] a_x_48;
reg [3:0] a_y_48;

always @* begin
    a_x_48 = 4'b0;
    a_y_48 = 4'b0;
    case (a_ctrl_48)
        2'd0: begin a_x_48 = a_data_48[3:0];   a_y_48 = a_data_48[11:8];  end
        2'd1: begin a_x_48 = a_data_48[11:8];  a_y_48 = a_data_48[3:0];   end
        2'd2: begin a_x_48 = a_data_48[7:4];   a_y_48 = a_data_48[15:12]; end
        2'd3: begin a_x_48 = a_data_48[15:12]; a_y_48 = a_data_48[7:4];   end
    endcase
end
assign a_out[384 +: 4] = a_x_48;
assign a_out[388 +: 4] = a_y_48;

wire [1:0] a_ctrl_49 = a_ctrl[98 +: 2];
wire [15:0] a_data_49 = a_data[784 +: 16];
reg [3:0] a_x_49;
reg [3:0] a_y_49;

always @* begin
    a_x_49 = 4'b0;
    a_y_49 = 4'b0;
    case (a_ctrl_49)
        2'd0: begin a_x_49 = a_data_49[3:0];   a_y_49 = a_data_49[11:8];  end
        2'd1: begin a_x_49 = a_data_49[11:8];  a_y_49 = a_data_49[3:0];   end
        2'd2: begin a_x_49 = a_data_49[7:4];   a_y_49 = a_data_49[15:12]; end
        2'd3: begin a_x_49 = a_data_49[15:12]; a_y_49 = a_data_49[7:4];   end
    endcase
end
assign a_out[392 +: 4] = a_x_49;
assign a_out[396 +: 4] = a_y_49;

wire [1:0] a_ctrl_50 = a_ctrl[100 +: 2];
wire [15:0] a_data_50 = a_data[800 +: 16];
reg [3:0] a_x_50;
reg [3:0] a_y_50;

always @* begin
    a_x_50 = 4'b0;
    a_y_50 = 4'b0;
    case (a_ctrl_50)
        2'd0: begin a_x_50 = a_data_50[3:0];   a_y_50 = a_data_50[11:8];  end
        2'd1: begin a_x_50 = a_data_50[11:8];  a_y_50 = a_data_50[3:0];   end
        2'd2: begin a_x_50 = a_data_50[7:4];   a_y_50 = a_data_50[15:12]; end
        2'd3: begin a_x_50 = a_data_50[15:12]; a_y_50 = a_data_50[7:4];   end
    endcase
end
assign a_out[400 +: 4] = a_x_50;
assign a_out[404 +: 4] = a_y_50;

wire [1:0] a_ctrl_51 = a_ctrl[102 +: 2];
wire [15:0] a_data_51 = a_data[816 +: 16];
reg [3:0] a_x_51;
reg [3:0] a_y_51;

always @* begin
    a_x_51 = 4'b0;
    a_y_51 = 4'b0;
    case (a_ctrl_51)
        2'd0: begin a_x_51 = a_data_51[3:0];   a_y_51 = a_data_51[11:8];  end
        2'd1: begin a_x_51 = a_data_51[11:8];  a_y_51 = a_data_51[3:0];   end
        2'd2: begin a_x_51 = a_data_51[7:4];   a_y_51 = a_data_51[15:12]; end
        2'd3: begin a_x_51 = a_data_51[15:12]; a_y_51 = a_data_51[7:4];   end
    endcase
end
assign a_out[408 +: 4] = a_x_51;
assign a_out[412 +: 4] = a_y_51;

wire [1:0] a_ctrl_52 = a_ctrl[104 +: 2];
wire [15:0] a_data_52 = a_data[832 +: 16];
reg [3:0] a_x_52;
reg [3:0] a_y_52;

always @* begin
    a_x_52 = 4'b0;
    a_y_52 = 4'b0;
    case (a_ctrl_52)
        2'd0: begin a_x_52 = a_data_52[3:0];   a_y_52 = a_data_52[11:8];  end
        2'd1: begin a_x_52 = a_data_52[11:8];  a_y_52 = a_data_52[3:0];   end
        2'd2: begin a_x_52 = a_data_52[7:4];   a_y_52 = a_data_52[15:12]; end
        2'd3: begin a_x_52 = a_data_52[15:12]; a_y_52 = a_data_52[7:4];   end
    endcase
end
assign a_out[416 +: 4] = a_x_52;
assign a_out[420 +: 4] = a_y_52;

wire [1:0] a_ctrl_53 = a_ctrl[106 +: 2];
wire [15:0] a_data_53 = a_data[848 +: 16];
reg [3:0] a_x_53;
reg [3:0] a_y_53;

always @* begin
    a_x_53 = 4'b0;
    a_y_53 = 4'b0;
    case (a_ctrl_53)
        2'd0: begin a_x_53 = a_data_53[3:0];   a_y_53 = a_data_53[11:8];  end
        2'd1: begin a_x_53 = a_data_53[11:8];  a_y_53 = a_data_53[3:0];   end
        2'd2: begin a_x_53 = a_data_53[7:4];   a_y_53 = a_data_53[15:12]; end
        2'd3: begin a_x_53 = a_data_53[15:12]; a_y_53 = a_data_53[7:4];   end
    endcase
end
assign a_out[424 +: 4] = a_x_53;
assign a_out[428 +: 4] = a_y_53;

wire [1:0] a_ctrl_54 = a_ctrl[108 +: 2];
wire [15:0] a_data_54 = a_data[864 +: 16];
reg [3:0] a_x_54;
reg [3:0] a_y_54;

always @* begin
    a_x_54 = 4'b0;
    a_y_54 = 4'b0;
    case (a_ctrl_54)
        2'd0: begin a_x_54 = a_data_54[3:0];   a_y_54 = a_data_54[11:8];  end
        2'd1: begin a_x_54 = a_data_54[11:8];  a_y_54 = a_data_54[3:0];   end
        2'd2: begin a_x_54 = a_data_54[7:4];   a_y_54 = a_data_54[15:12]; end
        2'd3: begin a_x_54 = a_data_54[15:12]; a_y_54 = a_data_54[7:4];   end
    endcase
end
assign a_out[432 +: 4] = a_x_54;
assign a_out[436 +: 4] = a_y_54;

wire [1:0] a_ctrl_55 = a_ctrl[110 +: 2];
wire [15:0] a_data_55 = a_data[880 +: 16];
reg [3:0] a_x_55;
reg [3:0] a_y_55;

always @* begin
    a_x_55 = 4'b0;
    a_y_55 = 4'b0;
    case (a_ctrl_55)
        2'd0: begin a_x_55 = a_data_55[3:0];   a_y_55 = a_data_55[11:8];  end
        2'd1: begin a_x_55 = a_data_55[11:8];  a_y_55 = a_data_55[3:0];   end
        2'd2: begin a_x_55 = a_data_55[7:4];   a_y_55 = a_data_55[15:12]; end
        2'd3: begin a_x_55 = a_data_55[15:12]; a_y_55 = a_data_55[7:4];   end
    endcase
end
assign a_out[440 +: 4] = a_x_55;
assign a_out[444 +: 4] = a_y_55;

wire [1:0] a_ctrl_56 = a_ctrl[112 +: 2];
wire [15:0] a_data_56 = a_data[896 +: 16];
reg [3:0] a_x_56;
reg [3:0] a_y_56;

always @* begin
    a_x_56 = 4'b0;
    a_y_56 = 4'b0;
    case (a_ctrl_56)
        2'd0: begin a_x_56 = a_data_56[3:0];   a_y_56 = a_data_56[11:8];  end
        2'd1: begin a_x_56 = a_data_56[11:8];  a_y_56 = a_data_56[3:0];   end
        2'd2: begin a_x_56 = a_data_56[7:4];   a_y_56 = a_data_56[15:12]; end
        2'd3: begin a_x_56 = a_data_56[15:12]; a_y_56 = a_data_56[7:4];   end
    endcase
end
assign a_out[448 +: 4] = a_x_56;
assign a_out[452 +: 4] = a_y_56;

wire [1:0] a_ctrl_57 = a_ctrl[114 +: 2];
wire [15:0] a_data_57 = a_data[912 +: 16];
reg [3:0] a_x_57;
reg [3:0] a_y_57;

always @* begin
    a_x_57 = 4'b0;
    a_y_57 = 4'b0;
    case (a_ctrl_57)
        2'd0: begin a_x_57 = a_data_57[3:0];   a_y_57 = a_data_57[11:8];  end
        2'd1: begin a_x_57 = a_data_57[11:8];  a_y_57 = a_data_57[3:0];   end
        2'd2: begin a_x_57 = a_data_57[7:4];   a_y_57 = a_data_57[15:12]; end
        2'd3: begin a_x_57 = a_data_57[15:12]; a_y_57 = a_data_57[7:4];   end
    endcase
end
assign a_out[456 +: 4] = a_x_57;
assign a_out[460 +: 4] = a_y_57;

wire [1:0] a_ctrl_58 = a_ctrl[116 +: 2];
wire [15:0] a_data_58 = a_data[928 +: 16];
reg [3:0] a_x_58;
reg [3:0] a_y_58;

always @* begin
    a_x_58 = 4'b0;
    a_y_58 = 4'b0;
    case (a_ctrl_58)
        2'd0: begin a_x_58 = a_data_58[3:0];   a_y_58 = a_data_58[11:8];  end
        2'd1: begin a_x_58 = a_data_58[11:8];  a_y_58 = a_data_58[3:0];   end
        2'd2: begin a_x_58 = a_data_58[7:4];   a_y_58 = a_data_58[15:12]; end
        2'd3: begin a_x_58 = a_data_58[15:12]; a_y_58 = a_data_58[7:4];   end
    endcase
end
assign a_out[464 +: 4] = a_x_58;
assign a_out[468 +: 4] = a_y_58;

wire [1:0] a_ctrl_59 = a_ctrl[118 +: 2];
wire [15:0] a_data_59 = a_data[944 +: 16];
reg [3:0] a_x_59;
reg [3:0] a_y_59;

always @* begin
    a_x_59 = 4'b0;
    a_y_59 = 4'b0;
    case (a_ctrl_59)
        2'd0: begin a_x_59 = a_data_59[3:0];   a_y_59 = a_data_59[11:8];  end
        2'd1: begin a_x_59 = a_data_59[11:8];  a_y_59 = a_data_59[3:0];   end
        2'd2: begin a_x_59 = a_data_59[7:4];   a_y_59 = a_data_59[15:12]; end
        2'd3: begin a_x_59 = a_data_59[15:12]; a_y_59 = a_data_59[7:4];   end
    endcase
end
assign a_out[472 +: 4] = a_x_59;
assign a_out[476 +: 4] = a_y_59;

wire [1:0] a_ctrl_60 = a_ctrl[120 +: 2];
wire [15:0] a_data_60 = a_data[960 +: 16];
reg [3:0] a_x_60;
reg [3:0] a_y_60;

always @* begin
    a_x_60 = 4'b0;
    a_y_60 = 4'b0;
    case (a_ctrl_60)
        2'd0: begin a_x_60 = a_data_60[3:0];   a_y_60 = a_data_60[11:8];  end
        2'd1: begin a_x_60 = a_data_60[11:8];  a_y_60 = a_data_60[3:0];   end
        2'd2: begin a_x_60 = a_data_60[7:4];   a_y_60 = a_data_60[15:12]; end
        2'd3: begin a_x_60 = a_data_60[15:12]; a_y_60 = a_data_60[7:4];   end
    endcase
end
assign a_out[480 +: 4] = a_x_60;
assign a_out[484 +: 4] = a_y_60;

wire [1:0] a_ctrl_61 = a_ctrl[122 +: 2];
wire [15:0] a_data_61 = a_data[976 +: 16];
reg [3:0] a_x_61;
reg [3:0] a_y_61;

always @* begin
    a_x_61 = 4'b0;
    a_y_61 = 4'b0;
    case (a_ctrl_61)
        2'd0: begin a_x_61 = a_data_61[3:0];   a_y_61 = a_data_61[11:8];  end
        2'd1: begin a_x_61 = a_data_61[11:8];  a_y_61 = a_data_61[3:0];   end
        2'd2: begin a_x_61 = a_data_61[7:4];   a_y_61 = a_data_61[15:12]; end
        2'd3: begin a_x_61 = a_data_61[15:12]; a_y_61 = a_data_61[7:4];   end
    endcase
end
assign a_out[488 +: 4] = a_x_61;
assign a_out[492 +: 4] = a_y_61;

wire [1:0] a_ctrl_62 = a_ctrl[124 +: 2];
wire [15:0] a_data_62 = a_data[992 +: 16];
reg [3:0] a_x_62;
reg [3:0] a_y_62;

always @* begin
    a_x_62 = 4'b0;
    a_y_62 = 4'b0;
    case (a_ctrl_62)
        2'd0: begin a_x_62 = a_data_62[3:0];   a_y_62 = a_data_62[11:8];  end
        2'd1: begin a_x_62 = a_data_62[11:8];  a_y_62 = a_data_62[3:0];   end
        2'd2: begin a_x_62 = a_data_62[7:4];   a_y_62 = a_data_62[15:12]; end
        2'd3: begin a_x_62 = a_data_62[15:12]; a_y_62 = a_data_62[7:4];   end
    endcase
end
assign a_out[496 +: 4] = a_x_62;
assign a_out[500 +: 4] = a_y_62;

wire [1:0] a_ctrl_63 = a_ctrl[126 +: 2];
wire [15:0] a_data_63 = a_data[1008 +: 16];
reg [3:0] a_x_63;
reg [3:0] a_y_63;

always @* begin
    a_x_63 = 4'b0;
    a_y_63 = 4'b0;
    case (a_ctrl_63)
        2'd0: begin a_x_63 = a_data_63[3:0];   a_y_63 = a_data_63[11:8];  end
        2'd1: begin a_x_63 = a_data_63[11:8];  a_y_63 = a_data_63[3:0];   end
        2'd2: begin a_x_63 = a_data_63[7:4];   a_y_63 = a_data_63[15:12]; end
        2'd3: begin a_x_63 = a_data_63[15:12]; a_y_63 = a_data_63[7:4];   end
    endcase
end
assign a_out[504 +: 4] = a_x_63;
assign a_out[508 +: 4] = a_y_63;

wire [1:0] a_ctrl_64 = a_ctrl[128 +: 2];
wire [15:0] a_data_64 = a_data[1024 +: 16];
reg [3:0] a_x_64;
reg [3:0] a_y_64;

always @* begin
    a_x_64 = 4'b0;
    a_y_64 = 4'b0;
    case (a_ctrl_64)
        2'd0: begin a_x_64 = a_data_64[3:0];   a_y_64 = a_data_64[11:8];  end
        2'd1: begin a_x_64 = a_data_64[11:8];  a_y_64 = a_data_64[3:0];   end
        2'd2: begin a_x_64 = a_data_64[7:4];   a_y_64 = a_data_64[15:12]; end
        2'd3: begin a_x_64 = a_data_64[15:12]; a_y_64 = a_data_64[7:4];   end
    endcase
end
assign a_out[512 +: 4] = a_x_64;
assign a_out[516 +: 4] = a_y_64;

wire [1:0] a_ctrl_65 = a_ctrl[130 +: 2];
wire [15:0] a_data_65 = a_data[1040 +: 16];
reg [3:0] a_x_65;
reg [3:0] a_y_65;

always @* begin
    a_x_65 = 4'b0;
    a_y_65 = 4'b0;
    case (a_ctrl_65)
        2'd0: begin a_x_65 = a_data_65[3:0];   a_y_65 = a_data_65[11:8];  end
        2'd1: begin a_x_65 = a_data_65[11:8];  a_y_65 = a_data_65[3:0];   end
        2'd2: begin a_x_65 = a_data_65[7:4];   a_y_65 = a_data_65[15:12]; end
        2'd3: begin a_x_65 = a_data_65[15:12]; a_y_65 = a_data_65[7:4];   end
    endcase
end
assign a_out[520 +: 4] = a_x_65;
assign a_out[524 +: 4] = a_y_65;

wire [1:0] a_ctrl_66 = a_ctrl[132 +: 2];
wire [15:0] a_data_66 = a_data[1056 +: 16];
reg [3:0] a_x_66;
reg [3:0] a_y_66;

always @* begin
    a_x_66 = 4'b0;
    a_y_66 = 4'b0;
    case (a_ctrl_66)
        2'd0: begin a_x_66 = a_data_66[3:0];   a_y_66 = a_data_66[11:8];  end
        2'd1: begin a_x_66 = a_data_66[11:8];  a_y_66 = a_data_66[3:0];   end
        2'd2: begin a_x_66 = a_data_66[7:4];   a_y_66 = a_data_66[15:12]; end
        2'd3: begin a_x_66 = a_data_66[15:12]; a_y_66 = a_data_66[7:4];   end
    endcase
end
assign a_out[528 +: 4] = a_x_66;
assign a_out[532 +: 4] = a_y_66;

wire [1:0] a_ctrl_67 = a_ctrl[134 +: 2];
wire [15:0] a_data_67 = a_data[1072 +: 16];
reg [3:0] a_x_67;
reg [3:0] a_y_67;

always @* begin
    a_x_67 = 4'b0;
    a_y_67 = 4'b0;
    case (a_ctrl_67)
        2'd0: begin a_x_67 = a_data_67[3:0];   a_y_67 = a_data_67[11:8];  end
        2'd1: begin a_x_67 = a_data_67[11:8];  a_y_67 = a_data_67[3:0];   end
        2'd2: begin a_x_67 = a_data_67[7:4];   a_y_67 = a_data_67[15:12]; end
        2'd3: begin a_x_67 = a_data_67[15:12]; a_y_67 = a_data_67[7:4];   end
    endcase
end
assign a_out[536 +: 4] = a_x_67;
assign a_out[540 +: 4] = a_y_67;

wire [1:0] a_ctrl_68 = a_ctrl[136 +: 2];
wire [15:0] a_data_68 = a_data[1088 +: 16];
reg [3:0] a_x_68;
reg [3:0] a_y_68;

always @* begin
    a_x_68 = 4'b0;
    a_y_68 = 4'b0;
    case (a_ctrl_68)
        2'd0: begin a_x_68 = a_data_68[3:0];   a_y_68 = a_data_68[11:8];  end
        2'd1: begin a_x_68 = a_data_68[11:8];  a_y_68 = a_data_68[3:0];   end
        2'd2: begin a_x_68 = a_data_68[7:4];   a_y_68 = a_data_68[15:12]; end
        2'd3: begin a_x_68 = a_data_68[15:12]; a_y_68 = a_data_68[7:4];   end
    endcase
end
assign a_out[544 +: 4] = a_x_68;
assign a_out[548 +: 4] = a_y_68;

wire [1:0] a_ctrl_69 = a_ctrl[138 +: 2];
wire [15:0] a_data_69 = a_data[1104 +: 16];
reg [3:0] a_x_69;
reg [3:0] a_y_69;

always @* begin
    a_x_69 = 4'b0;
    a_y_69 = 4'b0;
    case (a_ctrl_69)
        2'd0: begin a_x_69 = a_data_69[3:0];   a_y_69 = a_data_69[11:8];  end
        2'd1: begin a_x_69 = a_data_69[11:8];  a_y_69 = a_data_69[3:0];   end
        2'd2: begin a_x_69 = a_data_69[7:4];   a_y_69 = a_data_69[15:12]; end
        2'd3: begin a_x_69 = a_data_69[15:12]; a_y_69 = a_data_69[7:4];   end
    endcase
end
assign a_out[552 +: 4] = a_x_69;
assign a_out[556 +: 4] = a_y_69;

wire [1:0] a_ctrl_70 = a_ctrl[140 +: 2];
wire [15:0] a_data_70 = a_data[1120 +: 16];
reg [3:0] a_x_70;
reg [3:0] a_y_70;

always @* begin
    a_x_70 = 4'b0;
    a_y_70 = 4'b0;
    case (a_ctrl_70)
        2'd0: begin a_x_70 = a_data_70[3:0];   a_y_70 = a_data_70[11:8];  end
        2'd1: begin a_x_70 = a_data_70[11:8];  a_y_70 = a_data_70[3:0];   end
        2'd2: begin a_x_70 = a_data_70[7:4];   a_y_70 = a_data_70[15:12]; end
        2'd3: begin a_x_70 = a_data_70[15:12]; a_y_70 = a_data_70[7:4];   end
    endcase
end
assign a_out[560 +: 4] = a_x_70;
assign a_out[564 +: 4] = a_y_70;

wire [1:0] a_ctrl_71 = a_ctrl[142 +: 2];
wire [15:0] a_data_71 = a_data[1136 +: 16];
reg [3:0] a_x_71;
reg [3:0] a_y_71;

always @* begin
    a_x_71 = 4'b0;
    a_y_71 = 4'b0;
    case (a_ctrl_71)
        2'd0: begin a_x_71 = a_data_71[3:0];   a_y_71 = a_data_71[11:8];  end
        2'd1: begin a_x_71 = a_data_71[11:8];  a_y_71 = a_data_71[3:0];   end
        2'd2: begin a_x_71 = a_data_71[7:4];   a_y_71 = a_data_71[15:12]; end
        2'd3: begin a_x_71 = a_data_71[15:12]; a_y_71 = a_data_71[7:4];   end
    endcase
end
assign a_out[568 +: 4] = a_x_71;
assign a_out[572 +: 4] = a_y_71;

wire [1:0] a_ctrl_72 = a_ctrl[144 +: 2];
wire [15:0] a_data_72 = a_data[1152 +: 16];
reg [3:0] a_x_72;
reg [3:0] a_y_72;

always @* begin
    a_x_72 = 4'b0;
    a_y_72 = 4'b0;
    case (a_ctrl_72)
        2'd0: begin a_x_72 = a_data_72[3:0];   a_y_72 = a_data_72[11:8];  end
        2'd1: begin a_x_72 = a_data_72[11:8];  a_y_72 = a_data_72[3:0];   end
        2'd2: begin a_x_72 = a_data_72[7:4];   a_y_72 = a_data_72[15:12]; end
        2'd3: begin a_x_72 = a_data_72[15:12]; a_y_72 = a_data_72[7:4];   end
    endcase
end
assign a_out[576 +: 4] = a_x_72;
assign a_out[580 +: 4] = a_y_72;

wire [1:0] a_ctrl_73 = a_ctrl[146 +: 2];
wire [15:0] a_data_73 = a_data[1168 +: 16];
reg [3:0] a_x_73;
reg [3:0] a_y_73;

always @* begin
    a_x_73 = 4'b0;
    a_y_73 = 4'b0;
    case (a_ctrl_73)
        2'd0: begin a_x_73 = a_data_73[3:0];   a_y_73 = a_data_73[11:8];  end
        2'd1: begin a_x_73 = a_data_73[11:8];  a_y_73 = a_data_73[3:0];   end
        2'd2: begin a_x_73 = a_data_73[7:4];   a_y_73 = a_data_73[15:12]; end
        2'd3: begin a_x_73 = a_data_73[15:12]; a_y_73 = a_data_73[7:4];   end
    endcase
end
assign a_out[584 +: 4] = a_x_73;
assign a_out[588 +: 4] = a_y_73;

wire [3:0] c_ctrl_0 = c_ctrl[0 +: 4];
reg [3:0] c_y_0;

always @* begin
    c_y_0 = 4'b0000;
    case (c_ctrl_0)
        4'd3:
            c_y_0 = {
                ~c_ctrl_0[0],
                c_ctrl_0[1] ^ c_ctrl_0[2],
                c_ctrl_0[3] & c_ctrl_0[0],
                |c_ctrl_0
            };
        4'd12:
            c_y_0 = {
                ~c_ctrl_0[3],
                c_ctrl_0[2] ^ c_ctrl_0[1],
                c_ctrl_0[0] & c_ctrl_0[3],
                &c_ctrl_0
            };
    endcase
end
assign c_out[0 +: 4] = c_y_0;

wire [3:0] c_ctrl_1 = c_ctrl[4 +: 4];
reg [3:0] c_y_1;

always @* begin
    c_y_1 = 4'b0000;
    case (c_ctrl_1)
        4'd3:
            c_y_1 = {
                ~c_ctrl_1[0],
                c_ctrl_1[1] ^ c_ctrl_1[2],
                c_ctrl_1[3] & c_ctrl_1[0],
                |c_ctrl_1
            };
        4'd12:
            c_y_1 = {
                ~c_ctrl_1[3],
                c_ctrl_1[2] ^ c_ctrl_1[1],
                c_ctrl_1[0] & c_ctrl_1[3],
                &c_ctrl_1
            };
    endcase
end
assign c_out[4 +: 4] = c_y_1;

wire [3:0] c_ctrl_2 = c_ctrl[8 +: 4];
reg [3:0] c_y_2;

always @* begin
    c_y_2 = 4'b0000;
    case (c_ctrl_2)
        4'd3:
            c_y_2 = {
                ~c_ctrl_2[0],
                c_ctrl_2[1] ^ c_ctrl_2[2],
                c_ctrl_2[3] & c_ctrl_2[0],
                |c_ctrl_2
            };
        4'd12:
            c_y_2 = {
                ~c_ctrl_2[3],
                c_ctrl_2[2] ^ c_ctrl_2[1],
                c_ctrl_2[0] & c_ctrl_2[3],
                &c_ctrl_2
            };
    endcase
end
assign c_out[8 +: 4] = c_y_2;

wire [3:0] c_ctrl_3 = c_ctrl[12 +: 4];
reg [3:0] c_y_3;

always @* begin
    c_y_3 = 4'b0000;
    case (c_ctrl_3)
        4'd3:
            c_y_3 = {
                ~c_ctrl_3[0],
                c_ctrl_3[1] ^ c_ctrl_3[2],
                c_ctrl_3[3] & c_ctrl_3[0],
                |c_ctrl_3
            };
        4'd12:
            c_y_3 = {
                ~c_ctrl_3[3],
                c_ctrl_3[2] ^ c_ctrl_3[1],
                c_ctrl_3[0] & c_ctrl_3[3],
                &c_ctrl_3
            };
    endcase
end
assign c_out[12 +: 4] = c_y_3;

wire [3:0] c_ctrl_4 = c_ctrl[16 +: 4];
reg [3:0] c_y_4;

always @* begin
    c_y_4 = 4'b0000;
    case (c_ctrl_4)
        4'd3:
            c_y_4 = {
                ~c_ctrl_4[0],
                c_ctrl_4[1] ^ c_ctrl_4[2],
                c_ctrl_4[3] & c_ctrl_4[0],
                |c_ctrl_4
            };
        4'd12:
            c_y_4 = {
                ~c_ctrl_4[3],
                c_ctrl_4[2] ^ c_ctrl_4[1],
                c_ctrl_4[0] & c_ctrl_4[3],
                &c_ctrl_4
            };
    endcase
end
assign c_out[16 +: 4] = c_y_4;

wire [3:0] c_ctrl_5 = c_ctrl[20 +: 4];
reg [3:0] c_y_5;

always @* begin
    c_y_5 = 4'b0000;
    case (c_ctrl_5)
        4'd3:
            c_y_5 = {
                ~c_ctrl_5[0],
                c_ctrl_5[1] ^ c_ctrl_5[2],
                c_ctrl_5[3] & c_ctrl_5[0],
                |c_ctrl_5
            };
        4'd12:
            c_y_5 = {
                ~c_ctrl_5[3],
                c_ctrl_5[2] ^ c_ctrl_5[1],
                c_ctrl_5[0] & c_ctrl_5[3],
                &c_ctrl_5
            };
    endcase
end
assign c_out[20 +: 4] = c_y_5;

wire [3:0] c_ctrl_6 = c_ctrl[24 +: 4];
reg [3:0] c_y_6;

always @* begin
    c_y_6 = 4'b0000;
    case (c_ctrl_6)
        4'd3:
            c_y_6 = {
                ~c_ctrl_6[0],
                c_ctrl_6[1] ^ c_ctrl_6[2],
                c_ctrl_6[3] & c_ctrl_6[0],
                |c_ctrl_6
            };
        4'd12:
            c_y_6 = {
                ~c_ctrl_6[3],
                c_ctrl_6[2] ^ c_ctrl_6[1],
                c_ctrl_6[0] & c_ctrl_6[3],
                &c_ctrl_6
            };
    endcase
end
assign c_out[24 +: 4] = c_y_6;

wire [3:0] c_ctrl_7 = c_ctrl[28 +: 4];
reg [3:0] c_y_7;

always @* begin
    c_y_7 = 4'b0000;
    case (c_ctrl_7)
        4'd3:
            c_y_7 = {
                ~c_ctrl_7[0],
                c_ctrl_7[1] ^ c_ctrl_7[2],
                c_ctrl_7[3] & c_ctrl_7[0],
                |c_ctrl_7
            };
        4'd12:
            c_y_7 = {
                ~c_ctrl_7[3],
                c_ctrl_7[2] ^ c_ctrl_7[1],
                c_ctrl_7[0] & c_ctrl_7[3],
                &c_ctrl_7
            };
    endcase
end
assign c_out[28 +: 4] = c_y_7;

wire [3:0] c_ctrl_8 = c_ctrl[32 +: 4];
reg [3:0] c_y_8;

always @* begin
    c_y_8 = 4'b0000;
    case (c_ctrl_8)
        4'd3:
            c_y_8 = {
                ~c_ctrl_8[0],
                c_ctrl_8[1] ^ c_ctrl_8[2],
                c_ctrl_8[3] & c_ctrl_8[0],
                |c_ctrl_8
            };
        4'd12:
            c_y_8 = {
                ~c_ctrl_8[3],
                c_ctrl_8[2] ^ c_ctrl_8[1],
                c_ctrl_8[0] & c_ctrl_8[3],
                &c_ctrl_8
            };
    endcase
end
assign c_out[32 +: 4] = c_y_8;

wire [3:0] c_ctrl_9 = c_ctrl[36 +: 4];
reg [3:0] c_y_9;

always @* begin
    c_y_9 = 4'b0000;
    case (c_ctrl_9)
        4'd3:
            c_y_9 = {
                ~c_ctrl_9[0],
                c_ctrl_9[1] ^ c_ctrl_9[2],
                c_ctrl_9[3] & c_ctrl_9[0],
                |c_ctrl_9
            };
        4'd12:
            c_y_9 = {
                ~c_ctrl_9[3],
                c_ctrl_9[2] ^ c_ctrl_9[1],
                c_ctrl_9[0] & c_ctrl_9[3],
                &c_ctrl_9
            };
    endcase
end
assign c_out[36 +: 4] = c_y_9;

wire [3:0] c_ctrl_10 = c_ctrl[40 +: 4];
reg [3:0] c_y_10;

always @* begin
    c_y_10 = 4'b0000;
    case (c_ctrl_10)
        4'd3:
            c_y_10 = {
                ~c_ctrl_10[0],
                c_ctrl_10[1] ^ c_ctrl_10[2],
                c_ctrl_10[3] & c_ctrl_10[0],
                |c_ctrl_10
            };
        4'd12:
            c_y_10 = {
                ~c_ctrl_10[3],
                c_ctrl_10[2] ^ c_ctrl_10[1],
                c_ctrl_10[0] & c_ctrl_10[3],
                &c_ctrl_10
            };
    endcase
end
assign c_out[40 +: 4] = c_y_10;

wire [3:0] c_ctrl_11 = c_ctrl[44 +: 4];
reg [3:0] c_y_11;

always @* begin
    c_y_11 = 4'b0000;
    case (c_ctrl_11)
        4'd3:
            c_y_11 = {
                ~c_ctrl_11[0],
                c_ctrl_11[1] ^ c_ctrl_11[2],
                c_ctrl_11[3] & c_ctrl_11[0],
                |c_ctrl_11
            };
        4'd12:
            c_y_11 = {
                ~c_ctrl_11[3],
                c_ctrl_11[2] ^ c_ctrl_11[1],
                c_ctrl_11[0] & c_ctrl_11[3],
                &c_ctrl_11
            };
    endcase
end
assign c_out[44 +: 4] = c_y_11;

wire [3:0] c_ctrl_12 = c_ctrl[48 +: 4];
reg [3:0] c_y_12;

always @* begin
    c_y_12 = 4'b0000;
    case (c_ctrl_12)
        4'd3:
            c_y_12 = {
                ~c_ctrl_12[0],
                c_ctrl_12[1] ^ c_ctrl_12[2],
                c_ctrl_12[3] & c_ctrl_12[0],
                |c_ctrl_12
            };
        4'd12:
            c_y_12 = {
                ~c_ctrl_12[3],
                c_ctrl_12[2] ^ c_ctrl_12[1],
                c_ctrl_12[0] & c_ctrl_12[3],
                &c_ctrl_12
            };
    endcase
end
assign c_out[48 +: 4] = c_y_12;

wire [3:0] c_ctrl_13 = c_ctrl[52 +: 4];
reg [3:0] c_y_13;

always @* begin
    c_y_13 = 4'b0000;
    case (c_ctrl_13)
        4'd3:
            c_y_13 = {
                ~c_ctrl_13[0],
                c_ctrl_13[1] ^ c_ctrl_13[2],
                c_ctrl_13[3] & c_ctrl_13[0],
                |c_ctrl_13
            };
        4'd12:
            c_y_13 = {
                ~c_ctrl_13[3],
                c_ctrl_13[2] ^ c_ctrl_13[1],
                c_ctrl_13[0] & c_ctrl_13[3],
                &c_ctrl_13
            };
    endcase
end
assign c_out[52 +: 4] = c_y_13;

wire [3:0] c_ctrl_14 = c_ctrl[56 +: 4];
reg [3:0] c_y_14;

always @* begin
    c_y_14 = 4'b0000;
    case (c_ctrl_14)
        4'd3:
            c_y_14 = {
                ~c_ctrl_14[0],
                c_ctrl_14[1] ^ c_ctrl_14[2],
                c_ctrl_14[3] & c_ctrl_14[0],
                |c_ctrl_14
            };
        4'd12:
            c_y_14 = {
                ~c_ctrl_14[3],
                c_ctrl_14[2] ^ c_ctrl_14[1],
                c_ctrl_14[0] & c_ctrl_14[3],
                &c_ctrl_14
            };
    endcase
end
assign c_out[56 +: 4] = c_y_14;

wire [3:0] c_ctrl_15 = c_ctrl[60 +: 4];
reg [3:0] c_y_15;

always @* begin
    c_y_15 = 4'b0000;
    case (c_ctrl_15)
        4'd3:
            c_y_15 = {
                ~c_ctrl_15[0],
                c_ctrl_15[1] ^ c_ctrl_15[2],
                c_ctrl_15[3] & c_ctrl_15[0],
                |c_ctrl_15
            };
        4'd12:
            c_y_15 = {
                ~c_ctrl_15[3],
                c_ctrl_15[2] ^ c_ctrl_15[1],
                c_ctrl_15[0] & c_ctrl_15[3],
                &c_ctrl_15
            };
    endcase
end
assign c_out[60 +: 4] = c_y_15;

wire [3:0] c_ctrl_16 = c_ctrl[64 +: 4];
reg [3:0] c_y_16;

always @* begin
    c_y_16 = 4'b0000;
    case (c_ctrl_16)
        4'd3:
            c_y_16 = {
                ~c_ctrl_16[0],
                c_ctrl_16[1] ^ c_ctrl_16[2],
                c_ctrl_16[3] & c_ctrl_16[0],
                |c_ctrl_16
            };
        4'd12:
            c_y_16 = {
                ~c_ctrl_16[3],
                c_ctrl_16[2] ^ c_ctrl_16[1],
                c_ctrl_16[0] & c_ctrl_16[3],
                &c_ctrl_16
            };
    endcase
end
assign c_out[64 +: 4] = c_y_16;

wire [3:0] c_ctrl_17 = c_ctrl[68 +: 4];
reg [3:0] c_y_17;

always @* begin
    c_y_17 = 4'b0000;
    case (c_ctrl_17)
        4'd3:
            c_y_17 = {
                ~c_ctrl_17[0],
                c_ctrl_17[1] ^ c_ctrl_17[2],
                c_ctrl_17[3] & c_ctrl_17[0],
                |c_ctrl_17
            };
        4'd12:
            c_y_17 = {
                ~c_ctrl_17[3],
                c_ctrl_17[2] ^ c_ctrl_17[1],
                c_ctrl_17[0] & c_ctrl_17[3],
                &c_ctrl_17
            };
    endcase
end
assign c_out[68 +: 4] = c_y_17;

wire [3:0] c_ctrl_18 = c_ctrl[72 +: 4];
reg [3:0] c_y_18;

always @* begin
    c_y_18 = 4'b0000;
    case (c_ctrl_18)
        4'd3:
            c_y_18 = {
                ~c_ctrl_18[0],
                c_ctrl_18[1] ^ c_ctrl_18[2],
                c_ctrl_18[3] & c_ctrl_18[0],
                |c_ctrl_18
            };
        4'd12:
            c_y_18 = {
                ~c_ctrl_18[3],
                c_ctrl_18[2] ^ c_ctrl_18[1],
                c_ctrl_18[0] & c_ctrl_18[3],
                &c_ctrl_18
            };
    endcase
end
assign c_out[72 +: 4] = c_y_18;

wire [3:0] c_ctrl_19 = c_ctrl[76 +: 4];
reg [3:0] c_y_19;

always @* begin
    c_y_19 = 4'b0000;
    case (c_ctrl_19)
        4'd3:
            c_y_19 = {
                ~c_ctrl_19[0],
                c_ctrl_19[1] ^ c_ctrl_19[2],
                c_ctrl_19[3] & c_ctrl_19[0],
                |c_ctrl_19
            };
        4'd12:
            c_y_19 = {
                ~c_ctrl_19[3],
                c_ctrl_19[2] ^ c_ctrl_19[1],
                c_ctrl_19[0] & c_ctrl_19[3],
                &c_ctrl_19
            };
    endcase
end
assign c_out[76 +: 4] = c_y_19;

wire [3:0] c_ctrl_20 = c_ctrl[80 +: 4];
reg [3:0] c_y_20;

always @* begin
    c_y_20 = 4'b0000;
    case (c_ctrl_20)
        4'd3:
            c_y_20 = {
                ~c_ctrl_20[0],
                c_ctrl_20[1] ^ c_ctrl_20[2],
                c_ctrl_20[3] & c_ctrl_20[0],
                |c_ctrl_20
            };
        4'd12:
            c_y_20 = {
                ~c_ctrl_20[3],
                c_ctrl_20[2] ^ c_ctrl_20[1],
                c_ctrl_20[0] & c_ctrl_20[3],
                &c_ctrl_20
            };
    endcase
end
assign c_out[80 +: 4] = c_y_20;

wire [3:0] c_ctrl_21 = c_ctrl[84 +: 4];
reg [3:0] c_y_21;

always @* begin
    c_y_21 = 4'b0000;
    case (c_ctrl_21)
        4'd3:
            c_y_21 = {
                ~c_ctrl_21[0],
                c_ctrl_21[1] ^ c_ctrl_21[2],
                c_ctrl_21[3] & c_ctrl_21[0],
                |c_ctrl_21
            };
        4'd12:
            c_y_21 = {
                ~c_ctrl_21[3],
                c_ctrl_21[2] ^ c_ctrl_21[1],
                c_ctrl_21[0] & c_ctrl_21[3],
                &c_ctrl_21
            };
    endcase
end
assign c_out[84 +: 4] = c_y_21;

wire [3:0] c_ctrl_22 = c_ctrl[88 +: 4];
reg [3:0] c_y_22;

always @* begin
    c_y_22 = 4'b0000;
    case (c_ctrl_22)
        4'd3:
            c_y_22 = {
                ~c_ctrl_22[0],
                c_ctrl_22[1] ^ c_ctrl_22[2],
                c_ctrl_22[3] & c_ctrl_22[0],
                |c_ctrl_22
            };
        4'd12:
            c_y_22 = {
                ~c_ctrl_22[3],
                c_ctrl_22[2] ^ c_ctrl_22[1],
                c_ctrl_22[0] & c_ctrl_22[3],
                &c_ctrl_22
            };
    endcase
end
assign c_out[88 +: 4] = c_y_22;

wire [3:0] c_ctrl_23 = c_ctrl[92 +: 4];
reg [3:0] c_y_23;

always @* begin
    c_y_23 = 4'b0000;
    case (c_ctrl_23)
        4'd3:
            c_y_23 = {
                ~c_ctrl_23[0],
                c_ctrl_23[1] ^ c_ctrl_23[2],
                c_ctrl_23[3] & c_ctrl_23[0],
                |c_ctrl_23
            };
        4'd12:
            c_y_23 = {
                ~c_ctrl_23[3],
                c_ctrl_23[2] ^ c_ctrl_23[1],
                c_ctrl_23[0] & c_ctrl_23[3],
                &c_ctrl_23
            };
    endcase
end
assign c_out[92 +: 4] = c_y_23;

wire [3:0] c_ctrl_24 = c_ctrl[96 +: 4];
reg [3:0] c_y_24;

always @* begin
    c_y_24 = 4'b0000;
    case (c_ctrl_24)
        4'd3:
            c_y_24 = {
                ~c_ctrl_24[0],
                c_ctrl_24[1] ^ c_ctrl_24[2],
                c_ctrl_24[3] & c_ctrl_24[0],
                |c_ctrl_24
            };
        4'd12:
            c_y_24 = {
                ~c_ctrl_24[3],
                c_ctrl_24[2] ^ c_ctrl_24[1],
                c_ctrl_24[0] & c_ctrl_24[3],
                &c_ctrl_24
            };
    endcase
end
assign c_out[96 +: 4] = c_y_24;

wire [3:0] c_ctrl_25 = c_ctrl[100 +: 4];
reg [3:0] c_y_25;

always @* begin
    c_y_25 = 4'b0000;
    case (c_ctrl_25)
        4'd3:
            c_y_25 = {
                ~c_ctrl_25[0],
                c_ctrl_25[1] ^ c_ctrl_25[2],
                c_ctrl_25[3] & c_ctrl_25[0],
                |c_ctrl_25
            };
        4'd12:
            c_y_25 = {
                ~c_ctrl_25[3],
                c_ctrl_25[2] ^ c_ctrl_25[1],
                c_ctrl_25[0] & c_ctrl_25[3],
                &c_ctrl_25
            };
    endcase
end
assign c_out[100 +: 4] = c_y_25;

wire [3:0] c_ctrl_26 = c_ctrl[104 +: 4];
reg [3:0] c_y_26;

always @* begin
    c_y_26 = 4'b0000;
    case (c_ctrl_26)
        4'd3:
            c_y_26 = {
                ~c_ctrl_26[0],
                c_ctrl_26[1] ^ c_ctrl_26[2],
                c_ctrl_26[3] & c_ctrl_26[0],
                |c_ctrl_26
            };
        4'd12:
            c_y_26 = {
                ~c_ctrl_26[3],
                c_ctrl_26[2] ^ c_ctrl_26[1],
                c_ctrl_26[0] & c_ctrl_26[3],
                &c_ctrl_26
            };
    endcase
end
assign c_out[104 +: 4] = c_y_26;

wire [3:0] c_ctrl_27 = c_ctrl[108 +: 4];
reg [3:0] c_y_27;

always @* begin
    c_y_27 = 4'b0000;
    case (c_ctrl_27)
        4'd3:
            c_y_27 = {
                ~c_ctrl_27[0],
                c_ctrl_27[1] ^ c_ctrl_27[2],
                c_ctrl_27[3] & c_ctrl_27[0],
                |c_ctrl_27
            };
        4'd12:
            c_y_27 = {
                ~c_ctrl_27[3],
                c_ctrl_27[2] ^ c_ctrl_27[1],
                c_ctrl_27[0] & c_ctrl_27[3],
                &c_ctrl_27
            };
    endcase
end
assign c_out[108 +: 4] = c_y_27;

wire [3:0] c_ctrl_28 = c_ctrl[112 +: 4];
reg [3:0] c_y_28;

always @* begin
    c_y_28 = 4'b0000;
    case (c_ctrl_28)
        4'd3:
            c_y_28 = {
                ~c_ctrl_28[0],
                c_ctrl_28[1] ^ c_ctrl_28[2],
                c_ctrl_28[3] & c_ctrl_28[0],
                |c_ctrl_28
            };
        4'd12:
            c_y_28 = {
                ~c_ctrl_28[3],
                c_ctrl_28[2] ^ c_ctrl_28[1],
                c_ctrl_28[0] & c_ctrl_28[3],
                &c_ctrl_28
            };
    endcase
end
assign c_out[112 +: 4] = c_y_28;

wire [3:0] c_ctrl_29 = c_ctrl[116 +: 4];
reg [3:0] c_y_29;

always @* begin
    c_y_29 = 4'b0000;
    case (c_ctrl_29)
        4'd3:
            c_y_29 = {
                ~c_ctrl_29[0],
                c_ctrl_29[1] ^ c_ctrl_29[2],
                c_ctrl_29[3] & c_ctrl_29[0],
                |c_ctrl_29
            };
        4'd12:
            c_y_29 = {
                ~c_ctrl_29[3],
                c_ctrl_29[2] ^ c_ctrl_29[1],
                c_ctrl_29[0] & c_ctrl_29[3],
                &c_ctrl_29
            };
    endcase
end
assign c_out[116 +: 4] = c_y_29;

wire [3:0] c_ctrl_30 = c_ctrl[120 +: 4];
reg [3:0] c_y_30;

always @* begin
    c_y_30 = 4'b0000;
    case (c_ctrl_30)
        4'd3:
            c_y_30 = {
                ~c_ctrl_30[0],
                c_ctrl_30[1] ^ c_ctrl_30[2],
                c_ctrl_30[3] & c_ctrl_30[0],
                |c_ctrl_30
            };
        4'd12:
            c_y_30 = {
                ~c_ctrl_30[3],
                c_ctrl_30[2] ^ c_ctrl_30[1],
                c_ctrl_30[0] & c_ctrl_30[3],
                &c_ctrl_30
            };
    endcase
end
assign c_out[120 +: 4] = c_y_30;

wire [3:0] c_ctrl_31 = c_ctrl[124 +: 4];
reg [3:0] c_y_31;

always @* begin
    c_y_31 = 4'b0000;
    case (c_ctrl_31)
        4'd3:
            c_y_31 = {
                ~c_ctrl_31[0],
                c_ctrl_31[1] ^ c_ctrl_31[2],
                c_ctrl_31[3] & c_ctrl_31[0],
                |c_ctrl_31
            };
        4'd12:
            c_y_31 = {
                ~c_ctrl_31[3],
                c_ctrl_31[2] ^ c_ctrl_31[1],
                c_ctrl_31[0] & c_ctrl_31[3],
                &c_ctrl_31
            };
    endcase
end
assign c_out[124 +: 4] = c_y_31;

wire [3:0] c_ctrl_32 = c_ctrl[128 +: 4];
reg [3:0] c_y_32;

always @* begin
    c_y_32 = 4'b0000;
    case (c_ctrl_32)
        4'd3:
            c_y_32 = {
                ~c_ctrl_32[0],
                c_ctrl_32[1] ^ c_ctrl_32[2],
                c_ctrl_32[3] & c_ctrl_32[0],
                |c_ctrl_32
            };
        4'd12:
            c_y_32 = {
                ~c_ctrl_32[3],
                c_ctrl_32[2] ^ c_ctrl_32[1],
                c_ctrl_32[0] & c_ctrl_32[3],
                &c_ctrl_32
            };
    endcase
end
assign c_out[128 +: 4] = c_y_32;

wire [3:0] c_ctrl_33 = c_ctrl[132 +: 4];
reg [3:0] c_y_33;

always @* begin
    c_y_33 = 4'b0000;
    case (c_ctrl_33)
        4'd3:
            c_y_33 = {
                ~c_ctrl_33[0],
                c_ctrl_33[1] ^ c_ctrl_33[2],
                c_ctrl_33[3] & c_ctrl_33[0],
                |c_ctrl_33
            };
        4'd12:
            c_y_33 = {
                ~c_ctrl_33[3],
                c_ctrl_33[2] ^ c_ctrl_33[1],
                c_ctrl_33[0] & c_ctrl_33[3],
                &c_ctrl_33
            };
    endcase
end
assign c_out[132 +: 4] = c_y_33;

wire [3:0] c_ctrl_34 = c_ctrl[136 +: 4];
reg [3:0] c_y_34;

always @* begin
    c_y_34 = 4'b0000;
    case (c_ctrl_34)
        4'd3:
            c_y_34 = {
                ~c_ctrl_34[0],
                c_ctrl_34[1] ^ c_ctrl_34[2],
                c_ctrl_34[3] & c_ctrl_34[0],
                |c_ctrl_34
            };
        4'd12:
            c_y_34 = {
                ~c_ctrl_34[3],
                c_ctrl_34[2] ^ c_ctrl_34[1],
                c_ctrl_34[0] & c_ctrl_34[3],
                &c_ctrl_34
            };
    endcase
end
assign c_out[136 +: 4] = c_y_34;

wire [3:0] c_ctrl_35 = c_ctrl[140 +: 4];
reg [3:0] c_y_35;

always @* begin
    c_y_35 = 4'b0000;
    case (c_ctrl_35)
        4'd3:
            c_y_35 = {
                ~c_ctrl_35[0],
                c_ctrl_35[1] ^ c_ctrl_35[2],
                c_ctrl_35[3] & c_ctrl_35[0],
                |c_ctrl_35
            };
        4'd12:
            c_y_35 = {
                ~c_ctrl_35[3],
                c_ctrl_35[2] ^ c_ctrl_35[1],
                c_ctrl_35[0] & c_ctrl_35[3],
                &c_ctrl_35
            };
    endcase
end
assign c_out[140 +: 4] = c_y_35;

wire [3:0] c_ctrl_36 = c_ctrl[144 +: 4];
reg [3:0] c_y_36;

always @* begin
    c_y_36 = 4'b0000;
    case (c_ctrl_36)
        4'd3:
            c_y_36 = {
                ~c_ctrl_36[0],
                c_ctrl_36[1] ^ c_ctrl_36[2],
                c_ctrl_36[3] & c_ctrl_36[0],
                |c_ctrl_36
            };
        4'd12:
            c_y_36 = {
                ~c_ctrl_36[3],
                c_ctrl_36[2] ^ c_ctrl_36[1],
                c_ctrl_36[0] & c_ctrl_36[3],
                &c_ctrl_36
            };
    endcase
end
assign c_out[144 +: 4] = c_y_36;

wire [3:0] c_ctrl_37 = c_ctrl[148 +: 4];
reg [3:0] c_y_37;

always @* begin
    c_y_37 = 4'b0000;
    case (c_ctrl_37)
        4'd3:
            c_y_37 = {
                ~c_ctrl_37[0],
                c_ctrl_37[1] ^ c_ctrl_37[2],
                c_ctrl_37[3] & c_ctrl_37[0],
                |c_ctrl_37
            };
        4'd12:
            c_y_37 = {
                ~c_ctrl_37[3],
                c_ctrl_37[2] ^ c_ctrl_37[1],
                c_ctrl_37[0] & c_ctrl_37[3],
                &c_ctrl_37
            };
    endcase
end
assign c_out[148 +: 4] = c_y_37;

wire [3:0] c_ctrl_38 = c_ctrl[152 +: 4];
reg [3:0] c_y_38;

always @* begin
    c_y_38 = 4'b0000;
    case (c_ctrl_38)
        4'd3:
            c_y_38 = {
                ~c_ctrl_38[0],
                c_ctrl_38[1] ^ c_ctrl_38[2],
                c_ctrl_38[3] & c_ctrl_38[0],
                |c_ctrl_38
            };
        4'd12:
            c_y_38 = {
                ~c_ctrl_38[3],
                c_ctrl_38[2] ^ c_ctrl_38[1],
                c_ctrl_38[0] & c_ctrl_38[3],
                &c_ctrl_38
            };
    endcase
end
assign c_out[152 +: 4] = c_y_38;

wire [3:0] c_ctrl_39 = c_ctrl[156 +: 4];
reg [3:0] c_y_39;

always @* begin
    c_y_39 = 4'b0000;
    case (c_ctrl_39)
        4'd3:
            c_y_39 = {
                ~c_ctrl_39[0],
                c_ctrl_39[1] ^ c_ctrl_39[2],
                c_ctrl_39[3] & c_ctrl_39[0],
                |c_ctrl_39
            };
        4'd12:
            c_y_39 = {
                ~c_ctrl_39[3],
                c_ctrl_39[2] ^ c_ctrl_39[1],
                c_ctrl_39[0] & c_ctrl_39[3],
                &c_ctrl_39
            };
    endcase
end
assign c_out[156 +: 4] = c_y_39;

wire [3:0] c_ctrl_40 = c_ctrl[160 +: 4];
reg [3:0] c_y_40;

always @* begin
    c_y_40 = 4'b0000;
    case (c_ctrl_40)
        4'd3:
            c_y_40 = {
                ~c_ctrl_40[0],
                c_ctrl_40[1] ^ c_ctrl_40[2],
                c_ctrl_40[3] & c_ctrl_40[0],
                |c_ctrl_40
            };
        4'd12:
            c_y_40 = {
                ~c_ctrl_40[3],
                c_ctrl_40[2] ^ c_ctrl_40[1],
                c_ctrl_40[0] & c_ctrl_40[3],
                &c_ctrl_40
            };
    endcase
end
assign c_out[160 +: 4] = c_y_40;

wire [3:0] c_ctrl_41 = c_ctrl[164 +: 4];
reg [3:0] c_y_41;

always @* begin
    c_y_41 = 4'b0000;
    case (c_ctrl_41)
        4'd3:
            c_y_41 = {
                ~c_ctrl_41[0],
                c_ctrl_41[1] ^ c_ctrl_41[2],
                c_ctrl_41[3] & c_ctrl_41[0],
                |c_ctrl_41
            };
        4'd12:
            c_y_41 = {
                ~c_ctrl_41[3],
                c_ctrl_41[2] ^ c_ctrl_41[1],
                c_ctrl_41[0] & c_ctrl_41[3],
                &c_ctrl_41
            };
    endcase
end
assign c_out[164 +: 4] = c_y_41;

wire [3:0] c_ctrl_42 = c_ctrl[168 +: 4];
reg [3:0] c_y_42;

always @* begin
    c_y_42 = 4'b0000;
    case (c_ctrl_42)
        4'd3:
            c_y_42 = {
                ~c_ctrl_42[0],
                c_ctrl_42[1] ^ c_ctrl_42[2],
                c_ctrl_42[3] & c_ctrl_42[0],
                |c_ctrl_42
            };
        4'd12:
            c_y_42 = {
                ~c_ctrl_42[3],
                c_ctrl_42[2] ^ c_ctrl_42[1],
                c_ctrl_42[0] & c_ctrl_42[3],
                &c_ctrl_42
            };
    endcase
end
assign c_out[168 +: 4] = c_y_42;

wire [3:0] c_ctrl_43 = c_ctrl[172 +: 4];
reg [3:0] c_y_43;

always @* begin
    c_y_43 = 4'b0000;
    case (c_ctrl_43)
        4'd3:
            c_y_43 = {
                ~c_ctrl_43[0],
                c_ctrl_43[1] ^ c_ctrl_43[2],
                c_ctrl_43[3] & c_ctrl_43[0],
                |c_ctrl_43
            };
        4'd12:
            c_y_43 = {
                ~c_ctrl_43[3],
                c_ctrl_43[2] ^ c_ctrl_43[1],
                c_ctrl_43[0] & c_ctrl_43[3],
                &c_ctrl_43
            };
    endcase
end
assign c_out[172 +: 4] = c_y_43;

wire [1:0] n_ctrl_0 = n_ctrl[0 +: 2];
wire [15:0] n_data_0 = n_data[0 +: 16];
reg [3:0] n_y_0;

always @* begin
    n_y_0 = n_data_0[3:0];
    case (n_ctrl_0)
        2'd0: n_y_0 = n_data_0[3:0];
        2'd1: n_y_0 = n_data_0[7:4];
        2'd2: n_y_0 = n_data_0[11:8];
        2'd3: n_y_0 = n_data_0[15:12];
    endcase
end
assign n_out[0 +: 4] = n_y_0;

wire [1:0] n_ctrl_1 = n_ctrl[2 +: 2];
wire [15:0] n_data_1 = n_data[16 +: 16];
reg [3:0] n_y_1;

always @* begin
    n_y_1 = n_data_1[3:0];
    case (n_ctrl_1)
        2'd0: n_y_1 = n_data_1[3:0];
        2'd1: n_y_1 = n_data_1[7:4];
        2'd2: n_y_1 = n_data_1[11:8];
        2'd3: n_y_1 = n_data_1[15:12];
    endcase
end
assign n_out[4 +: 4] = n_y_1;

wire [1:0] n_ctrl_2 = n_ctrl[4 +: 2];
wire [15:0] n_data_2 = n_data[32 +: 16];
reg [3:0] n_y_2;

always @* begin
    n_y_2 = n_data_2[3:0];
    case (n_ctrl_2)
        2'd0: n_y_2 = n_data_2[3:0];
        2'd1: n_y_2 = n_data_2[7:4];
        2'd2: n_y_2 = n_data_2[11:8];
        2'd3: n_y_2 = n_data_2[15:12];
    endcase
end
assign n_out[8 +: 4] = n_y_2;

wire [1:0] n_ctrl_3 = n_ctrl[6 +: 2];
wire [15:0] n_data_3 = n_data[48 +: 16];
reg [3:0] n_y_3;

always @* begin
    n_y_3 = n_data_3[3:0];
    case (n_ctrl_3)
        2'd0: n_y_3 = n_data_3[3:0];
        2'd1: n_y_3 = n_data_3[7:4];
        2'd2: n_y_3 = n_data_3[11:8];
        2'd3: n_y_3 = n_data_3[15:12];
    endcase
end
assign n_out[12 +: 4] = n_y_3;

wire [1:0] n_ctrl_4 = n_ctrl[8 +: 2];
wire [15:0] n_data_4 = n_data[64 +: 16];
reg [3:0] n_y_4;

always @* begin
    n_y_4 = n_data_4[3:0];
    case (n_ctrl_4)
        2'd0: n_y_4 = n_data_4[3:0];
        2'd1: n_y_4 = n_data_4[7:4];
        2'd2: n_y_4 = n_data_4[11:8];
        2'd3: n_y_4 = n_data_4[15:12];
    endcase
end
assign n_out[16 +: 4] = n_y_4;

wire [1:0] n_ctrl_5 = n_ctrl[10 +: 2];
wire [15:0] n_data_5 = n_data[80 +: 16];
reg [3:0] n_y_5;

always @* begin
    n_y_5 = n_data_5[3:0];
    case (n_ctrl_5)
        2'd0: n_y_5 = n_data_5[3:0];
        2'd1: n_y_5 = n_data_5[7:4];
        2'd2: n_y_5 = n_data_5[11:8];
        2'd3: n_y_5 = n_data_5[15:12];
    endcase
end
assign n_out[20 +: 4] = n_y_5;

wire [1:0] n_ctrl_6 = n_ctrl[12 +: 2];
wire [15:0] n_data_6 = n_data[96 +: 16];
reg [3:0] n_y_6;

always @* begin
    n_y_6 = n_data_6[3:0];
    case (n_ctrl_6)
        2'd0: n_y_6 = n_data_6[3:0];
        2'd1: n_y_6 = n_data_6[7:4];
        2'd2: n_y_6 = n_data_6[11:8];
        2'd3: n_y_6 = n_data_6[15:12];
    endcase
end
assign n_out[24 +: 4] = n_y_6;

wire [1:0] n_ctrl_7 = n_ctrl[14 +: 2];
wire [15:0] n_data_7 = n_data[112 +: 16];
reg [3:0] n_y_7;

always @* begin
    n_y_7 = n_data_7[3:0];
    case (n_ctrl_7)
        2'd0: n_y_7 = n_data_7[3:0];
        2'd1: n_y_7 = n_data_7[7:4];
        2'd2: n_y_7 = n_data_7[11:8];
        2'd3: n_y_7 = n_data_7[15:12];
    endcase
end
assign n_out[28 +: 4] = n_y_7;

wire [1:0] n_ctrl_8 = n_ctrl[16 +: 2];
wire [15:0] n_data_8 = n_data[128 +: 16];
reg [3:0] n_y_8;

always @* begin
    n_y_8 = n_data_8[3:0];
    case (n_ctrl_8)
        2'd0: n_y_8 = n_data_8[3:0];
        2'd1: n_y_8 = n_data_8[7:4];
        2'd2: n_y_8 = n_data_8[11:8];
        2'd3: n_y_8 = n_data_8[15:12];
    endcase
end
assign n_out[32 +: 4] = n_y_8;

wire [1:0] n_ctrl_9 = n_ctrl[18 +: 2];
wire [15:0] n_data_9 = n_data[144 +: 16];
reg [3:0] n_y_9;

always @* begin
    n_y_9 = n_data_9[3:0];
    case (n_ctrl_9)
        2'd0: n_y_9 = n_data_9[3:0];
        2'd1: n_y_9 = n_data_9[7:4];
        2'd2: n_y_9 = n_data_9[11:8];
        2'd3: n_y_9 = n_data_9[15:12];
    endcase
end
assign n_out[36 +: 4] = n_y_9;

wire [1:0] n_ctrl_10 = n_ctrl[20 +: 2];
wire [15:0] n_data_10 = n_data[160 +: 16];
reg [3:0] n_y_10;

always @* begin
    n_y_10 = n_data_10[3:0];
    case (n_ctrl_10)
        2'd0: n_y_10 = n_data_10[3:0];
        2'd1: n_y_10 = n_data_10[7:4];
        2'd2: n_y_10 = n_data_10[11:8];
        2'd3: n_y_10 = n_data_10[15:12];
    endcase
end
assign n_out[40 +: 4] = n_y_10;

wire [1:0] n_ctrl_11 = n_ctrl[22 +: 2];
wire [15:0] n_data_11 = n_data[176 +: 16];
reg [3:0] n_y_11;

always @* begin
    n_y_11 = n_data_11[3:0];
    case (n_ctrl_11)
        2'd0: n_y_11 = n_data_11[3:0];
        2'd1: n_y_11 = n_data_11[7:4];
        2'd2: n_y_11 = n_data_11[11:8];
        2'd3: n_y_11 = n_data_11[15:12];
    endcase
end
assign n_out[44 +: 4] = n_y_11;

wire [1:0] n_ctrl_12 = n_ctrl[24 +: 2];
wire [15:0] n_data_12 = n_data[192 +: 16];
reg [3:0] n_y_12;

always @* begin
    n_y_12 = n_data_12[3:0];
    case (n_ctrl_12)
        2'd0: n_y_12 = n_data_12[3:0];
        2'd1: n_y_12 = n_data_12[7:4];
        2'd2: n_y_12 = n_data_12[11:8];
        2'd3: n_y_12 = n_data_12[15:12];
    endcase
end
assign n_out[48 +: 4] = n_y_12;

wire [1:0] n_ctrl_13 = n_ctrl[26 +: 2];
wire [15:0] n_data_13 = n_data[208 +: 16];
reg [3:0] n_y_13;

always @* begin
    n_y_13 = n_data_13[3:0];
    case (n_ctrl_13)
        2'd0: n_y_13 = n_data_13[3:0];
        2'd1: n_y_13 = n_data_13[7:4];
        2'd2: n_y_13 = n_data_13[11:8];
        2'd3: n_y_13 = n_data_13[15:12];
    endcase
end
assign n_out[52 +: 4] = n_y_13;

wire [1:0] n_ctrl_14 = n_ctrl[28 +: 2];
wire [15:0] n_data_14 = n_data[224 +: 16];
reg [3:0] n_y_14;

always @* begin
    n_y_14 = n_data_14[3:0];
    case (n_ctrl_14)
        2'd0: n_y_14 = n_data_14[3:0];
        2'd1: n_y_14 = n_data_14[7:4];
        2'd2: n_y_14 = n_data_14[11:8];
        2'd3: n_y_14 = n_data_14[15:12];
    endcase
end
assign n_out[56 +: 4] = n_y_14;

wire [1:0] n_ctrl_15 = n_ctrl[30 +: 2];
wire [15:0] n_data_15 = n_data[240 +: 16];
reg [3:0] n_y_15;

always @* begin
    n_y_15 = n_data_15[3:0];
    case (n_ctrl_15)
        2'd0: n_y_15 = n_data_15[3:0];
        2'd1: n_y_15 = n_data_15[7:4];
        2'd2: n_y_15 = n_data_15[11:8];
        2'd3: n_y_15 = n_data_15[15:12];
    endcase
end
assign n_out[60 +: 4] = n_y_15;

wire [1:0] n_ctrl_16 = n_ctrl[32 +: 2];
wire [15:0] n_data_16 = n_data[256 +: 16];
reg [3:0] n_y_16;

always @* begin
    n_y_16 = n_data_16[3:0];
    case (n_ctrl_16)
        2'd0: n_y_16 = n_data_16[3:0];
        2'd1: n_y_16 = n_data_16[7:4];
        2'd2: n_y_16 = n_data_16[11:8];
        2'd3: n_y_16 = n_data_16[15:12];
    endcase
end
assign n_out[64 +: 4] = n_y_16;

wire [1:0] n_ctrl_17 = n_ctrl[34 +: 2];
wire [15:0] n_data_17 = n_data[272 +: 16];
reg [3:0] n_y_17;

always @* begin
    n_y_17 = n_data_17[3:0];
    case (n_ctrl_17)
        2'd0: n_y_17 = n_data_17[3:0];
        2'd1: n_y_17 = n_data_17[7:4];
        2'd2: n_y_17 = n_data_17[11:8];
        2'd3: n_y_17 = n_data_17[15:12];
    endcase
end
assign n_out[68 +: 4] = n_y_17;

wire [1:0] n_ctrl_18 = n_ctrl[36 +: 2];
wire [15:0] n_data_18 = n_data[288 +: 16];
reg [3:0] n_y_18;

always @* begin
    n_y_18 = n_data_18[3:0];
    case (n_ctrl_18)
        2'd0: n_y_18 = n_data_18[3:0];
        2'd1: n_y_18 = n_data_18[7:4];
        2'd2: n_y_18 = n_data_18[11:8];
        2'd3: n_y_18 = n_data_18[15:12];
    endcase
end
assign n_out[72 +: 4] = n_y_18;

wire [1:0] n_ctrl_19 = n_ctrl[38 +: 2];
wire [15:0] n_data_19 = n_data[304 +: 16];
reg [3:0] n_y_19;

always @* begin
    n_y_19 = n_data_19[3:0];
    case (n_ctrl_19)
        2'd0: n_y_19 = n_data_19[3:0];
        2'd1: n_y_19 = n_data_19[7:4];
        2'd2: n_y_19 = n_data_19[11:8];
        2'd3: n_y_19 = n_data_19[15:12];
    endcase
end
assign n_out[76 +: 4] = n_y_19;

wire [1:0] n_ctrl_20 = n_ctrl[40 +: 2];
wire [15:0] n_data_20 = n_data[320 +: 16];
reg [3:0] n_y_20;

always @* begin
    n_y_20 = n_data_20[3:0];
    case (n_ctrl_20)
        2'd0: n_y_20 = n_data_20[3:0];
        2'd1: n_y_20 = n_data_20[7:4];
        2'd2: n_y_20 = n_data_20[11:8];
        2'd3: n_y_20 = n_data_20[15:12];
    endcase
end
assign n_out[80 +: 4] = n_y_20;

wire [1:0] n_ctrl_21 = n_ctrl[42 +: 2];
wire [15:0] n_data_21 = n_data[336 +: 16];
reg [3:0] n_y_21;

always @* begin
    n_y_21 = n_data_21[3:0];
    case (n_ctrl_21)
        2'd0: n_y_21 = n_data_21[3:0];
        2'd1: n_y_21 = n_data_21[7:4];
        2'd2: n_y_21 = n_data_21[11:8];
        2'd3: n_y_21 = n_data_21[15:12];
    endcase
end
assign n_out[84 +: 4] = n_y_21;

wire [1:0] n_ctrl_22 = n_ctrl[44 +: 2];
wire [15:0] n_data_22 = n_data[352 +: 16];
reg [3:0] n_y_22;

always @* begin
    n_y_22 = n_data_22[3:0];
    case (n_ctrl_22)
        2'd0: n_y_22 = n_data_22[3:0];
        2'd1: n_y_22 = n_data_22[7:4];
        2'd2: n_y_22 = n_data_22[11:8];
        2'd3: n_y_22 = n_data_22[15:12];
    endcase
end
assign n_out[88 +: 4] = n_y_22;

wire [1:0] n_ctrl_23 = n_ctrl[46 +: 2];
wire [15:0] n_data_23 = n_data[368 +: 16];
reg [3:0] n_y_23;

always @* begin
    n_y_23 = n_data_23[3:0];
    case (n_ctrl_23)
        2'd0: n_y_23 = n_data_23[3:0];
        2'd1: n_y_23 = n_data_23[7:4];
        2'd2: n_y_23 = n_data_23[11:8];
        2'd3: n_y_23 = n_data_23[15:12];
    endcase
end
assign n_out[92 +: 4] = n_y_23;

wire [1:0] n_ctrl_24 = n_ctrl[48 +: 2];
wire [15:0] n_data_24 = n_data[384 +: 16];
reg [3:0] n_y_24;

always @* begin
    n_y_24 = n_data_24[3:0];
    case (n_ctrl_24)
        2'd0: n_y_24 = n_data_24[3:0];
        2'd1: n_y_24 = n_data_24[7:4];
        2'd2: n_y_24 = n_data_24[11:8];
        2'd3: n_y_24 = n_data_24[15:12];
    endcase
end
assign n_out[96 +: 4] = n_y_24;

wire [1:0] n_ctrl_25 = n_ctrl[50 +: 2];
wire [15:0] n_data_25 = n_data[400 +: 16];
reg [3:0] n_y_25;

always @* begin
    n_y_25 = n_data_25[3:0];
    case (n_ctrl_25)
        2'd0: n_y_25 = n_data_25[3:0];
        2'd1: n_y_25 = n_data_25[7:4];
        2'd2: n_y_25 = n_data_25[11:8];
        2'd3: n_y_25 = n_data_25[15:12];
    endcase
end
assign n_out[100 +: 4] = n_y_25;

wire [1:0] n_ctrl_26 = n_ctrl[52 +: 2];
wire [15:0] n_data_26 = n_data[416 +: 16];
reg [3:0] n_y_26;

always @* begin
    n_y_26 = n_data_26[3:0];
    case (n_ctrl_26)
        2'd0: n_y_26 = n_data_26[3:0];
        2'd1: n_y_26 = n_data_26[7:4];
        2'd2: n_y_26 = n_data_26[11:8];
        2'd3: n_y_26 = n_data_26[15:12];
    endcase
end
assign n_out[104 +: 4] = n_y_26;

wire [1:0] n_ctrl_27 = n_ctrl[54 +: 2];
wire [15:0] n_data_27 = n_data[432 +: 16];
reg [3:0] n_y_27;

always @* begin
    n_y_27 = n_data_27[3:0];
    case (n_ctrl_27)
        2'd0: n_y_27 = n_data_27[3:0];
        2'd1: n_y_27 = n_data_27[7:4];
        2'd2: n_y_27 = n_data_27[11:8];
        2'd3: n_y_27 = n_data_27[15:12];
    endcase
end
assign n_out[108 +: 4] = n_y_27;

wire [1:0] n_ctrl_28 = n_ctrl[56 +: 2];
wire [15:0] n_data_28 = n_data[448 +: 16];
reg [3:0] n_y_28;

always @* begin
    n_y_28 = n_data_28[3:0];
    case (n_ctrl_28)
        2'd0: n_y_28 = n_data_28[3:0];
        2'd1: n_y_28 = n_data_28[7:4];
        2'd2: n_y_28 = n_data_28[11:8];
        2'd3: n_y_28 = n_data_28[15:12];
    endcase
end
assign n_out[112 +: 4] = n_y_28;

wire [1:0] n_ctrl_29 = n_ctrl[58 +: 2];
wire [15:0] n_data_29 = n_data[464 +: 16];
reg [3:0] n_y_29;

always @* begin
    n_y_29 = n_data_29[3:0];
    case (n_ctrl_29)
        2'd0: n_y_29 = n_data_29[3:0];
        2'd1: n_y_29 = n_data_29[7:4];
        2'd2: n_y_29 = n_data_29[11:8];
        2'd3: n_y_29 = n_data_29[15:12];
    endcase
end
assign n_out[116 +: 4] = n_y_29;

wire [1:0] n_ctrl_30 = n_ctrl[60 +: 2];
wire [15:0] n_data_30 = n_data[480 +: 16];
reg [3:0] n_y_30;

always @* begin
    n_y_30 = n_data_30[3:0];
    case (n_ctrl_30)
        2'd0: n_y_30 = n_data_30[3:0];
        2'd1: n_y_30 = n_data_30[7:4];
        2'd2: n_y_30 = n_data_30[11:8];
        2'd3: n_y_30 = n_data_30[15:12];
    endcase
end
assign n_out[120 +: 4] = n_y_30;

endmodule
