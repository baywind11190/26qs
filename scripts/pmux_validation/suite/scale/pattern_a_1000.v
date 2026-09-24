module stress_top(
    input [331:0] a_ctrl,
    input [2655:0] a_data,
    output [1327:0] a_out
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

wire [1:0] a_ctrl_74 = a_ctrl[148 +: 2];
wire [15:0] a_data_74 = a_data[1184 +: 16];
reg [3:0] a_x_74;
reg [3:0] a_y_74;

always @* begin
    a_x_74 = 4'b0;
    a_y_74 = 4'b0;
    case (a_ctrl_74)
        2'd0: begin a_x_74 = a_data_74[3:0];   a_y_74 = a_data_74[11:8];  end
        2'd1: begin a_x_74 = a_data_74[11:8];  a_y_74 = a_data_74[3:0];   end
        2'd2: begin a_x_74 = a_data_74[7:4];   a_y_74 = a_data_74[15:12]; end
        2'd3: begin a_x_74 = a_data_74[15:12]; a_y_74 = a_data_74[7:4];   end
    endcase
end
assign a_out[592 +: 4] = a_x_74;
assign a_out[596 +: 4] = a_y_74;

wire [1:0] a_ctrl_75 = a_ctrl[150 +: 2];
wire [15:0] a_data_75 = a_data[1200 +: 16];
reg [3:0] a_x_75;
reg [3:0] a_y_75;

always @* begin
    a_x_75 = 4'b0;
    a_y_75 = 4'b0;
    case (a_ctrl_75)
        2'd0: begin a_x_75 = a_data_75[3:0];   a_y_75 = a_data_75[11:8];  end
        2'd1: begin a_x_75 = a_data_75[11:8];  a_y_75 = a_data_75[3:0];   end
        2'd2: begin a_x_75 = a_data_75[7:4];   a_y_75 = a_data_75[15:12]; end
        2'd3: begin a_x_75 = a_data_75[15:12]; a_y_75 = a_data_75[7:4];   end
    endcase
end
assign a_out[600 +: 4] = a_x_75;
assign a_out[604 +: 4] = a_y_75;

wire [1:0] a_ctrl_76 = a_ctrl[152 +: 2];
wire [15:0] a_data_76 = a_data[1216 +: 16];
reg [3:0] a_x_76;
reg [3:0] a_y_76;

always @* begin
    a_x_76 = 4'b0;
    a_y_76 = 4'b0;
    case (a_ctrl_76)
        2'd0: begin a_x_76 = a_data_76[3:0];   a_y_76 = a_data_76[11:8];  end
        2'd1: begin a_x_76 = a_data_76[11:8];  a_y_76 = a_data_76[3:0];   end
        2'd2: begin a_x_76 = a_data_76[7:4];   a_y_76 = a_data_76[15:12]; end
        2'd3: begin a_x_76 = a_data_76[15:12]; a_y_76 = a_data_76[7:4];   end
    endcase
end
assign a_out[608 +: 4] = a_x_76;
assign a_out[612 +: 4] = a_y_76;

wire [1:0] a_ctrl_77 = a_ctrl[154 +: 2];
wire [15:0] a_data_77 = a_data[1232 +: 16];
reg [3:0] a_x_77;
reg [3:0] a_y_77;

always @* begin
    a_x_77 = 4'b0;
    a_y_77 = 4'b0;
    case (a_ctrl_77)
        2'd0: begin a_x_77 = a_data_77[3:0];   a_y_77 = a_data_77[11:8];  end
        2'd1: begin a_x_77 = a_data_77[11:8];  a_y_77 = a_data_77[3:0];   end
        2'd2: begin a_x_77 = a_data_77[7:4];   a_y_77 = a_data_77[15:12]; end
        2'd3: begin a_x_77 = a_data_77[15:12]; a_y_77 = a_data_77[7:4];   end
    endcase
end
assign a_out[616 +: 4] = a_x_77;
assign a_out[620 +: 4] = a_y_77;

wire [1:0] a_ctrl_78 = a_ctrl[156 +: 2];
wire [15:0] a_data_78 = a_data[1248 +: 16];
reg [3:0] a_x_78;
reg [3:0] a_y_78;

always @* begin
    a_x_78 = 4'b0;
    a_y_78 = 4'b0;
    case (a_ctrl_78)
        2'd0: begin a_x_78 = a_data_78[3:0];   a_y_78 = a_data_78[11:8];  end
        2'd1: begin a_x_78 = a_data_78[11:8];  a_y_78 = a_data_78[3:0];   end
        2'd2: begin a_x_78 = a_data_78[7:4];   a_y_78 = a_data_78[15:12]; end
        2'd3: begin a_x_78 = a_data_78[15:12]; a_y_78 = a_data_78[7:4];   end
    endcase
end
assign a_out[624 +: 4] = a_x_78;
assign a_out[628 +: 4] = a_y_78;

wire [1:0] a_ctrl_79 = a_ctrl[158 +: 2];
wire [15:0] a_data_79 = a_data[1264 +: 16];
reg [3:0] a_x_79;
reg [3:0] a_y_79;

always @* begin
    a_x_79 = 4'b0;
    a_y_79 = 4'b0;
    case (a_ctrl_79)
        2'd0: begin a_x_79 = a_data_79[3:0];   a_y_79 = a_data_79[11:8];  end
        2'd1: begin a_x_79 = a_data_79[11:8];  a_y_79 = a_data_79[3:0];   end
        2'd2: begin a_x_79 = a_data_79[7:4];   a_y_79 = a_data_79[15:12]; end
        2'd3: begin a_x_79 = a_data_79[15:12]; a_y_79 = a_data_79[7:4];   end
    endcase
end
assign a_out[632 +: 4] = a_x_79;
assign a_out[636 +: 4] = a_y_79;

wire [1:0] a_ctrl_80 = a_ctrl[160 +: 2];
wire [15:0] a_data_80 = a_data[1280 +: 16];
reg [3:0] a_x_80;
reg [3:0] a_y_80;

always @* begin
    a_x_80 = 4'b0;
    a_y_80 = 4'b0;
    case (a_ctrl_80)
        2'd0: begin a_x_80 = a_data_80[3:0];   a_y_80 = a_data_80[11:8];  end
        2'd1: begin a_x_80 = a_data_80[11:8];  a_y_80 = a_data_80[3:0];   end
        2'd2: begin a_x_80 = a_data_80[7:4];   a_y_80 = a_data_80[15:12]; end
        2'd3: begin a_x_80 = a_data_80[15:12]; a_y_80 = a_data_80[7:4];   end
    endcase
end
assign a_out[640 +: 4] = a_x_80;
assign a_out[644 +: 4] = a_y_80;

wire [1:0] a_ctrl_81 = a_ctrl[162 +: 2];
wire [15:0] a_data_81 = a_data[1296 +: 16];
reg [3:0] a_x_81;
reg [3:0] a_y_81;

always @* begin
    a_x_81 = 4'b0;
    a_y_81 = 4'b0;
    case (a_ctrl_81)
        2'd0: begin a_x_81 = a_data_81[3:0];   a_y_81 = a_data_81[11:8];  end
        2'd1: begin a_x_81 = a_data_81[11:8];  a_y_81 = a_data_81[3:0];   end
        2'd2: begin a_x_81 = a_data_81[7:4];   a_y_81 = a_data_81[15:12]; end
        2'd3: begin a_x_81 = a_data_81[15:12]; a_y_81 = a_data_81[7:4];   end
    endcase
end
assign a_out[648 +: 4] = a_x_81;
assign a_out[652 +: 4] = a_y_81;

wire [1:0] a_ctrl_82 = a_ctrl[164 +: 2];
wire [15:0] a_data_82 = a_data[1312 +: 16];
reg [3:0] a_x_82;
reg [3:0] a_y_82;

always @* begin
    a_x_82 = 4'b0;
    a_y_82 = 4'b0;
    case (a_ctrl_82)
        2'd0: begin a_x_82 = a_data_82[3:0];   a_y_82 = a_data_82[11:8];  end
        2'd1: begin a_x_82 = a_data_82[11:8];  a_y_82 = a_data_82[3:0];   end
        2'd2: begin a_x_82 = a_data_82[7:4];   a_y_82 = a_data_82[15:12]; end
        2'd3: begin a_x_82 = a_data_82[15:12]; a_y_82 = a_data_82[7:4];   end
    endcase
end
assign a_out[656 +: 4] = a_x_82;
assign a_out[660 +: 4] = a_y_82;

wire [1:0] a_ctrl_83 = a_ctrl[166 +: 2];
wire [15:0] a_data_83 = a_data[1328 +: 16];
reg [3:0] a_x_83;
reg [3:0] a_y_83;

always @* begin
    a_x_83 = 4'b0;
    a_y_83 = 4'b0;
    case (a_ctrl_83)
        2'd0: begin a_x_83 = a_data_83[3:0];   a_y_83 = a_data_83[11:8];  end
        2'd1: begin a_x_83 = a_data_83[11:8];  a_y_83 = a_data_83[3:0];   end
        2'd2: begin a_x_83 = a_data_83[7:4];   a_y_83 = a_data_83[15:12]; end
        2'd3: begin a_x_83 = a_data_83[15:12]; a_y_83 = a_data_83[7:4];   end
    endcase
end
assign a_out[664 +: 4] = a_x_83;
assign a_out[668 +: 4] = a_y_83;

wire [1:0] a_ctrl_84 = a_ctrl[168 +: 2];
wire [15:0] a_data_84 = a_data[1344 +: 16];
reg [3:0] a_x_84;
reg [3:0] a_y_84;

always @* begin
    a_x_84 = 4'b0;
    a_y_84 = 4'b0;
    case (a_ctrl_84)
        2'd0: begin a_x_84 = a_data_84[3:0];   a_y_84 = a_data_84[11:8];  end
        2'd1: begin a_x_84 = a_data_84[11:8];  a_y_84 = a_data_84[3:0];   end
        2'd2: begin a_x_84 = a_data_84[7:4];   a_y_84 = a_data_84[15:12]; end
        2'd3: begin a_x_84 = a_data_84[15:12]; a_y_84 = a_data_84[7:4];   end
    endcase
end
assign a_out[672 +: 4] = a_x_84;
assign a_out[676 +: 4] = a_y_84;

wire [1:0] a_ctrl_85 = a_ctrl[170 +: 2];
wire [15:0] a_data_85 = a_data[1360 +: 16];
reg [3:0] a_x_85;
reg [3:0] a_y_85;

always @* begin
    a_x_85 = 4'b0;
    a_y_85 = 4'b0;
    case (a_ctrl_85)
        2'd0: begin a_x_85 = a_data_85[3:0];   a_y_85 = a_data_85[11:8];  end
        2'd1: begin a_x_85 = a_data_85[11:8];  a_y_85 = a_data_85[3:0];   end
        2'd2: begin a_x_85 = a_data_85[7:4];   a_y_85 = a_data_85[15:12]; end
        2'd3: begin a_x_85 = a_data_85[15:12]; a_y_85 = a_data_85[7:4];   end
    endcase
end
assign a_out[680 +: 4] = a_x_85;
assign a_out[684 +: 4] = a_y_85;

wire [1:0] a_ctrl_86 = a_ctrl[172 +: 2];
wire [15:0] a_data_86 = a_data[1376 +: 16];
reg [3:0] a_x_86;
reg [3:0] a_y_86;

always @* begin
    a_x_86 = 4'b0;
    a_y_86 = 4'b0;
    case (a_ctrl_86)
        2'd0: begin a_x_86 = a_data_86[3:0];   a_y_86 = a_data_86[11:8];  end
        2'd1: begin a_x_86 = a_data_86[11:8];  a_y_86 = a_data_86[3:0];   end
        2'd2: begin a_x_86 = a_data_86[7:4];   a_y_86 = a_data_86[15:12]; end
        2'd3: begin a_x_86 = a_data_86[15:12]; a_y_86 = a_data_86[7:4];   end
    endcase
end
assign a_out[688 +: 4] = a_x_86;
assign a_out[692 +: 4] = a_y_86;

wire [1:0] a_ctrl_87 = a_ctrl[174 +: 2];
wire [15:0] a_data_87 = a_data[1392 +: 16];
reg [3:0] a_x_87;
reg [3:0] a_y_87;

always @* begin
    a_x_87 = 4'b0;
    a_y_87 = 4'b0;
    case (a_ctrl_87)
        2'd0: begin a_x_87 = a_data_87[3:0];   a_y_87 = a_data_87[11:8];  end
        2'd1: begin a_x_87 = a_data_87[11:8];  a_y_87 = a_data_87[3:0];   end
        2'd2: begin a_x_87 = a_data_87[7:4];   a_y_87 = a_data_87[15:12]; end
        2'd3: begin a_x_87 = a_data_87[15:12]; a_y_87 = a_data_87[7:4];   end
    endcase
end
assign a_out[696 +: 4] = a_x_87;
assign a_out[700 +: 4] = a_y_87;

wire [1:0] a_ctrl_88 = a_ctrl[176 +: 2];
wire [15:0] a_data_88 = a_data[1408 +: 16];
reg [3:0] a_x_88;
reg [3:0] a_y_88;

always @* begin
    a_x_88 = 4'b0;
    a_y_88 = 4'b0;
    case (a_ctrl_88)
        2'd0: begin a_x_88 = a_data_88[3:0];   a_y_88 = a_data_88[11:8];  end
        2'd1: begin a_x_88 = a_data_88[11:8];  a_y_88 = a_data_88[3:0];   end
        2'd2: begin a_x_88 = a_data_88[7:4];   a_y_88 = a_data_88[15:12]; end
        2'd3: begin a_x_88 = a_data_88[15:12]; a_y_88 = a_data_88[7:4];   end
    endcase
end
assign a_out[704 +: 4] = a_x_88;
assign a_out[708 +: 4] = a_y_88;

wire [1:0] a_ctrl_89 = a_ctrl[178 +: 2];
wire [15:0] a_data_89 = a_data[1424 +: 16];
reg [3:0] a_x_89;
reg [3:0] a_y_89;

always @* begin
    a_x_89 = 4'b0;
    a_y_89 = 4'b0;
    case (a_ctrl_89)
        2'd0: begin a_x_89 = a_data_89[3:0];   a_y_89 = a_data_89[11:8];  end
        2'd1: begin a_x_89 = a_data_89[11:8];  a_y_89 = a_data_89[3:0];   end
        2'd2: begin a_x_89 = a_data_89[7:4];   a_y_89 = a_data_89[15:12]; end
        2'd3: begin a_x_89 = a_data_89[15:12]; a_y_89 = a_data_89[7:4];   end
    endcase
end
assign a_out[712 +: 4] = a_x_89;
assign a_out[716 +: 4] = a_y_89;

wire [1:0] a_ctrl_90 = a_ctrl[180 +: 2];
wire [15:0] a_data_90 = a_data[1440 +: 16];
reg [3:0] a_x_90;
reg [3:0] a_y_90;

always @* begin
    a_x_90 = 4'b0;
    a_y_90 = 4'b0;
    case (a_ctrl_90)
        2'd0: begin a_x_90 = a_data_90[3:0];   a_y_90 = a_data_90[11:8];  end
        2'd1: begin a_x_90 = a_data_90[11:8];  a_y_90 = a_data_90[3:0];   end
        2'd2: begin a_x_90 = a_data_90[7:4];   a_y_90 = a_data_90[15:12]; end
        2'd3: begin a_x_90 = a_data_90[15:12]; a_y_90 = a_data_90[7:4];   end
    endcase
end
assign a_out[720 +: 4] = a_x_90;
assign a_out[724 +: 4] = a_y_90;

wire [1:0] a_ctrl_91 = a_ctrl[182 +: 2];
wire [15:0] a_data_91 = a_data[1456 +: 16];
reg [3:0] a_x_91;
reg [3:0] a_y_91;

always @* begin
    a_x_91 = 4'b0;
    a_y_91 = 4'b0;
    case (a_ctrl_91)
        2'd0: begin a_x_91 = a_data_91[3:0];   a_y_91 = a_data_91[11:8];  end
        2'd1: begin a_x_91 = a_data_91[11:8];  a_y_91 = a_data_91[3:0];   end
        2'd2: begin a_x_91 = a_data_91[7:4];   a_y_91 = a_data_91[15:12]; end
        2'd3: begin a_x_91 = a_data_91[15:12]; a_y_91 = a_data_91[7:4];   end
    endcase
end
assign a_out[728 +: 4] = a_x_91;
assign a_out[732 +: 4] = a_y_91;

wire [1:0] a_ctrl_92 = a_ctrl[184 +: 2];
wire [15:0] a_data_92 = a_data[1472 +: 16];
reg [3:0] a_x_92;
reg [3:0] a_y_92;

always @* begin
    a_x_92 = 4'b0;
    a_y_92 = 4'b0;
    case (a_ctrl_92)
        2'd0: begin a_x_92 = a_data_92[3:0];   a_y_92 = a_data_92[11:8];  end
        2'd1: begin a_x_92 = a_data_92[11:8];  a_y_92 = a_data_92[3:0];   end
        2'd2: begin a_x_92 = a_data_92[7:4];   a_y_92 = a_data_92[15:12]; end
        2'd3: begin a_x_92 = a_data_92[15:12]; a_y_92 = a_data_92[7:4];   end
    endcase
end
assign a_out[736 +: 4] = a_x_92;
assign a_out[740 +: 4] = a_y_92;

wire [1:0] a_ctrl_93 = a_ctrl[186 +: 2];
wire [15:0] a_data_93 = a_data[1488 +: 16];
reg [3:0] a_x_93;
reg [3:0] a_y_93;

always @* begin
    a_x_93 = 4'b0;
    a_y_93 = 4'b0;
    case (a_ctrl_93)
        2'd0: begin a_x_93 = a_data_93[3:0];   a_y_93 = a_data_93[11:8];  end
        2'd1: begin a_x_93 = a_data_93[11:8];  a_y_93 = a_data_93[3:0];   end
        2'd2: begin a_x_93 = a_data_93[7:4];   a_y_93 = a_data_93[15:12]; end
        2'd3: begin a_x_93 = a_data_93[15:12]; a_y_93 = a_data_93[7:4];   end
    endcase
end
assign a_out[744 +: 4] = a_x_93;
assign a_out[748 +: 4] = a_y_93;

wire [1:0] a_ctrl_94 = a_ctrl[188 +: 2];
wire [15:0] a_data_94 = a_data[1504 +: 16];
reg [3:0] a_x_94;
reg [3:0] a_y_94;

always @* begin
    a_x_94 = 4'b0;
    a_y_94 = 4'b0;
    case (a_ctrl_94)
        2'd0: begin a_x_94 = a_data_94[3:0];   a_y_94 = a_data_94[11:8];  end
        2'd1: begin a_x_94 = a_data_94[11:8];  a_y_94 = a_data_94[3:0];   end
        2'd2: begin a_x_94 = a_data_94[7:4];   a_y_94 = a_data_94[15:12]; end
        2'd3: begin a_x_94 = a_data_94[15:12]; a_y_94 = a_data_94[7:4];   end
    endcase
end
assign a_out[752 +: 4] = a_x_94;
assign a_out[756 +: 4] = a_y_94;

wire [1:0] a_ctrl_95 = a_ctrl[190 +: 2];
wire [15:0] a_data_95 = a_data[1520 +: 16];
reg [3:0] a_x_95;
reg [3:0] a_y_95;

always @* begin
    a_x_95 = 4'b0;
    a_y_95 = 4'b0;
    case (a_ctrl_95)
        2'd0: begin a_x_95 = a_data_95[3:0];   a_y_95 = a_data_95[11:8];  end
        2'd1: begin a_x_95 = a_data_95[11:8];  a_y_95 = a_data_95[3:0];   end
        2'd2: begin a_x_95 = a_data_95[7:4];   a_y_95 = a_data_95[15:12]; end
        2'd3: begin a_x_95 = a_data_95[15:12]; a_y_95 = a_data_95[7:4];   end
    endcase
end
assign a_out[760 +: 4] = a_x_95;
assign a_out[764 +: 4] = a_y_95;

wire [1:0] a_ctrl_96 = a_ctrl[192 +: 2];
wire [15:0] a_data_96 = a_data[1536 +: 16];
reg [3:0] a_x_96;
reg [3:0] a_y_96;

always @* begin
    a_x_96 = 4'b0;
    a_y_96 = 4'b0;
    case (a_ctrl_96)
        2'd0: begin a_x_96 = a_data_96[3:0];   a_y_96 = a_data_96[11:8];  end
        2'd1: begin a_x_96 = a_data_96[11:8];  a_y_96 = a_data_96[3:0];   end
        2'd2: begin a_x_96 = a_data_96[7:4];   a_y_96 = a_data_96[15:12]; end
        2'd3: begin a_x_96 = a_data_96[15:12]; a_y_96 = a_data_96[7:4];   end
    endcase
end
assign a_out[768 +: 4] = a_x_96;
assign a_out[772 +: 4] = a_y_96;

wire [1:0] a_ctrl_97 = a_ctrl[194 +: 2];
wire [15:0] a_data_97 = a_data[1552 +: 16];
reg [3:0] a_x_97;
reg [3:0] a_y_97;

always @* begin
    a_x_97 = 4'b0;
    a_y_97 = 4'b0;
    case (a_ctrl_97)
        2'd0: begin a_x_97 = a_data_97[3:0];   a_y_97 = a_data_97[11:8];  end
        2'd1: begin a_x_97 = a_data_97[11:8];  a_y_97 = a_data_97[3:0];   end
        2'd2: begin a_x_97 = a_data_97[7:4];   a_y_97 = a_data_97[15:12]; end
        2'd3: begin a_x_97 = a_data_97[15:12]; a_y_97 = a_data_97[7:4];   end
    endcase
end
assign a_out[776 +: 4] = a_x_97;
assign a_out[780 +: 4] = a_y_97;

wire [1:0] a_ctrl_98 = a_ctrl[196 +: 2];
wire [15:0] a_data_98 = a_data[1568 +: 16];
reg [3:0] a_x_98;
reg [3:0] a_y_98;

always @* begin
    a_x_98 = 4'b0;
    a_y_98 = 4'b0;
    case (a_ctrl_98)
        2'd0: begin a_x_98 = a_data_98[3:0];   a_y_98 = a_data_98[11:8];  end
        2'd1: begin a_x_98 = a_data_98[11:8];  a_y_98 = a_data_98[3:0];   end
        2'd2: begin a_x_98 = a_data_98[7:4];   a_y_98 = a_data_98[15:12]; end
        2'd3: begin a_x_98 = a_data_98[15:12]; a_y_98 = a_data_98[7:4];   end
    endcase
end
assign a_out[784 +: 4] = a_x_98;
assign a_out[788 +: 4] = a_y_98;

wire [1:0] a_ctrl_99 = a_ctrl[198 +: 2];
wire [15:0] a_data_99 = a_data[1584 +: 16];
reg [3:0] a_x_99;
reg [3:0] a_y_99;

always @* begin
    a_x_99 = 4'b0;
    a_y_99 = 4'b0;
    case (a_ctrl_99)
        2'd0: begin a_x_99 = a_data_99[3:0];   a_y_99 = a_data_99[11:8];  end
        2'd1: begin a_x_99 = a_data_99[11:8];  a_y_99 = a_data_99[3:0];   end
        2'd2: begin a_x_99 = a_data_99[7:4];   a_y_99 = a_data_99[15:12]; end
        2'd3: begin a_x_99 = a_data_99[15:12]; a_y_99 = a_data_99[7:4];   end
    endcase
end
assign a_out[792 +: 4] = a_x_99;
assign a_out[796 +: 4] = a_y_99;

wire [1:0] a_ctrl_100 = a_ctrl[200 +: 2];
wire [15:0] a_data_100 = a_data[1600 +: 16];
reg [3:0] a_x_100;
reg [3:0] a_y_100;

always @* begin
    a_x_100 = 4'b0;
    a_y_100 = 4'b0;
    case (a_ctrl_100)
        2'd0: begin a_x_100 = a_data_100[3:0];   a_y_100 = a_data_100[11:8];  end
        2'd1: begin a_x_100 = a_data_100[11:8];  a_y_100 = a_data_100[3:0];   end
        2'd2: begin a_x_100 = a_data_100[7:4];   a_y_100 = a_data_100[15:12]; end
        2'd3: begin a_x_100 = a_data_100[15:12]; a_y_100 = a_data_100[7:4];   end
    endcase
end
assign a_out[800 +: 4] = a_x_100;
assign a_out[804 +: 4] = a_y_100;

wire [1:0] a_ctrl_101 = a_ctrl[202 +: 2];
wire [15:0] a_data_101 = a_data[1616 +: 16];
reg [3:0] a_x_101;
reg [3:0] a_y_101;

always @* begin
    a_x_101 = 4'b0;
    a_y_101 = 4'b0;
    case (a_ctrl_101)
        2'd0: begin a_x_101 = a_data_101[3:0];   a_y_101 = a_data_101[11:8];  end
        2'd1: begin a_x_101 = a_data_101[11:8];  a_y_101 = a_data_101[3:0];   end
        2'd2: begin a_x_101 = a_data_101[7:4];   a_y_101 = a_data_101[15:12]; end
        2'd3: begin a_x_101 = a_data_101[15:12]; a_y_101 = a_data_101[7:4];   end
    endcase
end
assign a_out[808 +: 4] = a_x_101;
assign a_out[812 +: 4] = a_y_101;

wire [1:0] a_ctrl_102 = a_ctrl[204 +: 2];
wire [15:0] a_data_102 = a_data[1632 +: 16];
reg [3:0] a_x_102;
reg [3:0] a_y_102;

always @* begin
    a_x_102 = 4'b0;
    a_y_102 = 4'b0;
    case (a_ctrl_102)
        2'd0: begin a_x_102 = a_data_102[3:0];   a_y_102 = a_data_102[11:8];  end
        2'd1: begin a_x_102 = a_data_102[11:8];  a_y_102 = a_data_102[3:0];   end
        2'd2: begin a_x_102 = a_data_102[7:4];   a_y_102 = a_data_102[15:12]; end
        2'd3: begin a_x_102 = a_data_102[15:12]; a_y_102 = a_data_102[7:4];   end
    endcase
end
assign a_out[816 +: 4] = a_x_102;
assign a_out[820 +: 4] = a_y_102;

wire [1:0] a_ctrl_103 = a_ctrl[206 +: 2];
wire [15:0] a_data_103 = a_data[1648 +: 16];
reg [3:0] a_x_103;
reg [3:0] a_y_103;

always @* begin
    a_x_103 = 4'b0;
    a_y_103 = 4'b0;
    case (a_ctrl_103)
        2'd0: begin a_x_103 = a_data_103[3:0];   a_y_103 = a_data_103[11:8];  end
        2'd1: begin a_x_103 = a_data_103[11:8];  a_y_103 = a_data_103[3:0];   end
        2'd2: begin a_x_103 = a_data_103[7:4];   a_y_103 = a_data_103[15:12]; end
        2'd3: begin a_x_103 = a_data_103[15:12]; a_y_103 = a_data_103[7:4];   end
    endcase
end
assign a_out[824 +: 4] = a_x_103;
assign a_out[828 +: 4] = a_y_103;

wire [1:0] a_ctrl_104 = a_ctrl[208 +: 2];
wire [15:0] a_data_104 = a_data[1664 +: 16];
reg [3:0] a_x_104;
reg [3:0] a_y_104;

always @* begin
    a_x_104 = 4'b0;
    a_y_104 = 4'b0;
    case (a_ctrl_104)
        2'd0: begin a_x_104 = a_data_104[3:0];   a_y_104 = a_data_104[11:8];  end
        2'd1: begin a_x_104 = a_data_104[11:8];  a_y_104 = a_data_104[3:0];   end
        2'd2: begin a_x_104 = a_data_104[7:4];   a_y_104 = a_data_104[15:12]; end
        2'd3: begin a_x_104 = a_data_104[15:12]; a_y_104 = a_data_104[7:4];   end
    endcase
end
assign a_out[832 +: 4] = a_x_104;
assign a_out[836 +: 4] = a_y_104;

wire [1:0] a_ctrl_105 = a_ctrl[210 +: 2];
wire [15:0] a_data_105 = a_data[1680 +: 16];
reg [3:0] a_x_105;
reg [3:0] a_y_105;

always @* begin
    a_x_105 = 4'b0;
    a_y_105 = 4'b0;
    case (a_ctrl_105)
        2'd0: begin a_x_105 = a_data_105[3:0];   a_y_105 = a_data_105[11:8];  end
        2'd1: begin a_x_105 = a_data_105[11:8];  a_y_105 = a_data_105[3:0];   end
        2'd2: begin a_x_105 = a_data_105[7:4];   a_y_105 = a_data_105[15:12]; end
        2'd3: begin a_x_105 = a_data_105[15:12]; a_y_105 = a_data_105[7:4];   end
    endcase
end
assign a_out[840 +: 4] = a_x_105;
assign a_out[844 +: 4] = a_y_105;

wire [1:0] a_ctrl_106 = a_ctrl[212 +: 2];
wire [15:0] a_data_106 = a_data[1696 +: 16];
reg [3:0] a_x_106;
reg [3:0] a_y_106;

always @* begin
    a_x_106 = 4'b0;
    a_y_106 = 4'b0;
    case (a_ctrl_106)
        2'd0: begin a_x_106 = a_data_106[3:0];   a_y_106 = a_data_106[11:8];  end
        2'd1: begin a_x_106 = a_data_106[11:8];  a_y_106 = a_data_106[3:0];   end
        2'd2: begin a_x_106 = a_data_106[7:4];   a_y_106 = a_data_106[15:12]; end
        2'd3: begin a_x_106 = a_data_106[15:12]; a_y_106 = a_data_106[7:4];   end
    endcase
end
assign a_out[848 +: 4] = a_x_106;
assign a_out[852 +: 4] = a_y_106;

wire [1:0] a_ctrl_107 = a_ctrl[214 +: 2];
wire [15:0] a_data_107 = a_data[1712 +: 16];
reg [3:0] a_x_107;
reg [3:0] a_y_107;

always @* begin
    a_x_107 = 4'b0;
    a_y_107 = 4'b0;
    case (a_ctrl_107)
        2'd0: begin a_x_107 = a_data_107[3:0];   a_y_107 = a_data_107[11:8];  end
        2'd1: begin a_x_107 = a_data_107[11:8];  a_y_107 = a_data_107[3:0];   end
        2'd2: begin a_x_107 = a_data_107[7:4];   a_y_107 = a_data_107[15:12]; end
        2'd3: begin a_x_107 = a_data_107[15:12]; a_y_107 = a_data_107[7:4];   end
    endcase
end
assign a_out[856 +: 4] = a_x_107;
assign a_out[860 +: 4] = a_y_107;

wire [1:0] a_ctrl_108 = a_ctrl[216 +: 2];
wire [15:0] a_data_108 = a_data[1728 +: 16];
reg [3:0] a_x_108;
reg [3:0] a_y_108;

always @* begin
    a_x_108 = 4'b0;
    a_y_108 = 4'b0;
    case (a_ctrl_108)
        2'd0: begin a_x_108 = a_data_108[3:0];   a_y_108 = a_data_108[11:8];  end
        2'd1: begin a_x_108 = a_data_108[11:8];  a_y_108 = a_data_108[3:0];   end
        2'd2: begin a_x_108 = a_data_108[7:4];   a_y_108 = a_data_108[15:12]; end
        2'd3: begin a_x_108 = a_data_108[15:12]; a_y_108 = a_data_108[7:4];   end
    endcase
end
assign a_out[864 +: 4] = a_x_108;
assign a_out[868 +: 4] = a_y_108;

wire [1:0] a_ctrl_109 = a_ctrl[218 +: 2];
wire [15:0] a_data_109 = a_data[1744 +: 16];
reg [3:0] a_x_109;
reg [3:0] a_y_109;

always @* begin
    a_x_109 = 4'b0;
    a_y_109 = 4'b0;
    case (a_ctrl_109)
        2'd0: begin a_x_109 = a_data_109[3:0];   a_y_109 = a_data_109[11:8];  end
        2'd1: begin a_x_109 = a_data_109[11:8];  a_y_109 = a_data_109[3:0];   end
        2'd2: begin a_x_109 = a_data_109[7:4];   a_y_109 = a_data_109[15:12]; end
        2'd3: begin a_x_109 = a_data_109[15:12]; a_y_109 = a_data_109[7:4];   end
    endcase
end
assign a_out[872 +: 4] = a_x_109;
assign a_out[876 +: 4] = a_y_109;

wire [1:0] a_ctrl_110 = a_ctrl[220 +: 2];
wire [15:0] a_data_110 = a_data[1760 +: 16];
reg [3:0] a_x_110;
reg [3:0] a_y_110;

always @* begin
    a_x_110 = 4'b0;
    a_y_110 = 4'b0;
    case (a_ctrl_110)
        2'd0: begin a_x_110 = a_data_110[3:0];   a_y_110 = a_data_110[11:8];  end
        2'd1: begin a_x_110 = a_data_110[11:8];  a_y_110 = a_data_110[3:0];   end
        2'd2: begin a_x_110 = a_data_110[7:4];   a_y_110 = a_data_110[15:12]; end
        2'd3: begin a_x_110 = a_data_110[15:12]; a_y_110 = a_data_110[7:4];   end
    endcase
end
assign a_out[880 +: 4] = a_x_110;
assign a_out[884 +: 4] = a_y_110;

wire [1:0] a_ctrl_111 = a_ctrl[222 +: 2];
wire [15:0] a_data_111 = a_data[1776 +: 16];
reg [3:0] a_x_111;
reg [3:0] a_y_111;

always @* begin
    a_x_111 = 4'b0;
    a_y_111 = 4'b0;
    case (a_ctrl_111)
        2'd0: begin a_x_111 = a_data_111[3:0];   a_y_111 = a_data_111[11:8];  end
        2'd1: begin a_x_111 = a_data_111[11:8];  a_y_111 = a_data_111[3:0];   end
        2'd2: begin a_x_111 = a_data_111[7:4];   a_y_111 = a_data_111[15:12]; end
        2'd3: begin a_x_111 = a_data_111[15:12]; a_y_111 = a_data_111[7:4];   end
    endcase
end
assign a_out[888 +: 4] = a_x_111;
assign a_out[892 +: 4] = a_y_111;

wire [1:0] a_ctrl_112 = a_ctrl[224 +: 2];
wire [15:0] a_data_112 = a_data[1792 +: 16];
reg [3:0] a_x_112;
reg [3:0] a_y_112;

always @* begin
    a_x_112 = 4'b0;
    a_y_112 = 4'b0;
    case (a_ctrl_112)
        2'd0: begin a_x_112 = a_data_112[3:0];   a_y_112 = a_data_112[11:8];  end
        2'd1: begin a_x_112 = a_data_112[11:8];  a_y_112 = a_data_112[3:0];   end
        2'd2: begin a_x_112 = a_data_112[7:4];   a_y_112 = a_data_112[15:12]; end
        2'd3: begin a_x_112 = a_data_112[15:12]; a_y_112 = a_data_112[7:4];   end
    endcase
end
assign a_out[896 +: 4] = a_x_112;
assign a_out[900 +: 4] = a_y_112;

wire [1:0] a_ctrl_113 = a_ctrl[226 +: 2];
wire [15:0] a_data_113 = a_data[1808 +: 16];
reg [3:0] a_x_113;
reg [3:0] a_y_113;

always @* begin
    a_x_113 = 4'b0;
    a_y_113 = 4'b0;
    case (a_ctrl_113)
        2'd0: begin a_x_113 = a_data_113[3:0];   a_y_113 = a_data_113[11:8];  end
        2'd1: begin a_x_113 = a_data_113[11:8];  a_y_113 = a_data_113[3:0];   end
        2'd2: begin a_x_113 = a_data_113[7:4];   a_y_113 = a_data_113[15:12]; end
        2'd3: begin a_x_113 = a_data_113[15:12]; a_y_113 = a_data_113[7:4];   end
    endcase
end
assign a_out[904 +: 4] = a_x_113;
assign a_out[908 +: 4] = a_y_113;

wire [1:0] a_ctrl_114 = a_ctrl[228 +: 2];
wire [15:0] a_data_114 = a_data[1824 +: 16];
reg [3:0] a_x_114;
reg [3:0] a_y_114;

always @* begin
    a_x_114 = 4'b0;
    a_y_114 = 4'b0;
    case (a_ctrl_114)
        2'd0: begin a_x_114 = a_data_114[3:0];   a_y_114 = a_data_114[11:8];  end
        2'd1: begin a_x_114 = a_data_114[11:8];  a_y_114 = a_data_114[3:0];   end
        2'd2: begin a_x_114 = a_data_114[7:4];   a_y_114 = a_data_114[15:12]; end
        2'd3: begin a_x_114 = a_data_114[15:12]; a_y_114 = a_data_114[7:4];   end
    endcase
end
assign a_out[912 +: 4] = a_x_114;
assign a_out[916 +: 4] = a_y_114;

wire [1:0] a_ctrl_115 = a_ctrl[230 +: 2];
wire [15:0] a_data_115 = a_data[1840 +: 16];
reg [3:0] a_x_115;
reg [3:0] a_y_115;

always @* begin
    a_x_115 = 4'b0;
    a_y_115 = 4'b0;
    case (a_ctrl_115)
        2'd0: begin a_x_115 = a_data_115[3:0];   a_y_115 = a_data_115[11:8];  end
        2'd1: begin a_x_115 = a_data_115[11:8];  a_y_115 = a_data_115[3:0];   end
        2'd2: begin a_x_115 = a_data_115[7:4];   a_y_115 = a_data_115[15:12]; end
        2'd3: begin a_x_115 = a_data_115[15:12]; a_y_115 = a_data_115[7:4];   end
    endcase
end
assign a_out[920 +: 4] = a_x_115;
assign a_out[924 +: 4] = a_y_115;

wire [1:0] a_ctrl_116 = a_ctrl[232 +: 2];
wire [15:0] a_data_116 = a_data[1856 +: 16];
reg [3:0] a_x_116;
reg [3:0] a_y_116;

always @* begin
    a_x_116 = 4'b0;
    a_y_116 = 4'b0;
    case (a_ctrl_116)
        2'd0: begin a_x_116 = a_data_116[3:0];   a_y_116 = a_data_116[11:8];  end
        2'd1: begin a_x_116 = a_data_116[11:8];  a_y_116 = a_data_116[3:0];   end
        2'd2: begin a_x_116 = a_data_116[7:4];   a_y_116 = a_data_116[15:12]; end
        2'd3: begin a_x_116 = a_data_116[15:12]; a_y_116 = a_data_116[7:4];   end
    endcase
end
assign a_out[928 +: 4] = a_x_116;
assign a_out[932 +: 4] = a_y_116;

wire [1:0] a_ctrl_117 = a_ctrl[234 +: 2];
wire [15:0] a_data_117 = a_data[1872 +: 16];
reg [3:0] a_x_117;
reg [3:0] a_y_117;

always @* begin
    a_x_117 = 4'b0;
    a_y_117 = 4'b0;
    case (a_ctrl_117)
        2'd0: begin a_x_117 = a_data_117[3:0];   a_y_117 = a_data_117[11:8];  end
        2'd1: begin a_x_117 = a_data_117[11:8];  a_y_117 = a_data_117[3:0];   end
        2'd2: begin a_x_117 = a_data_117[7:4];   a_y_117 = a_data_117[15:12]; end
        2'd3: begin a_x_117 = a_data_117[15:12]; a_y_117 = a_data_117[7:4];   end
    endcase
end
assign a_out[936 +: 4] = a_x_117;
assign a_out[940 +: 4] = a_y_117;

wire [1:0] a_ctrl_118 = a_ctrl[236 +: 2];
wire [15:0] a_data_118 = a_data[1888 +: 16];
reg [3:0] a_x_118;
reg [3:0] a_y_118;

always @* begin
    a_x_118 = 4'b0;
    a_y_118 = 4'b0;
    case (a_ctrl_118)
        2'd0: begin a_x_118 = a_data_118[3:0];   a_y_118 = a_data_118[11:8];  end
        2'd1: begin a_x_118 = a_data_118[11:8];  a_y_118 = a_data_118[3:0];   end
        2'd2: begin a_x_118 = a_data_118[7:4];   a_y_118 = a_data_118[15:12]; end
        2'd3: begin a_x_118 = a_data_118[15:12]; a_y_118 = a_data_118[7:4];   end
    endcase
end
assign a_out[944 +: 4] = a_x_118;
assign a_out[948 +: 4] = a_y_118;

wire [1:0] a_ctrl_119 = a_ctrl[238 +: 2];
wire [15:0] a_data_119 = a_data[1904 +: 16];
reg [3:0] a_x_119;
reg [3:0] a_y_119;

always @* begin
    a_x_119 = 4'b0;
    a_y_119 = 4'b0;
    case (a_ctrl_119)
        2'd0: begin a_x_119 = a_data_119[3:0];   a_y_119 = a_data_119[11:8];  end
        2'd1: begin a_x_119 = a_data_119[11:8];  a_y_119 = a_data_119[3:0];   end
        2'd2: begin a_x_119 = a_data_119[7:4];   a_y_119 = a_data_119[15:12]; end
        2'd3: begin a_x_119 = a_data_119[15:12]; a_y_119 = a_data_119[7:4];   end
    endcase
end
assign a_out[952 +: 4] = a_x_119;
assign a_out[956 +: 4] = a_y_119;

wire [1:0] a_ctrl_120 = a_ctrl[240 +: 2];
wire [15:0] a_data_120 = a_data[1920 +: 16];
reg [3:0] a_x_120;
reg [3:0] a_y_120;

always @* begin
    a_x_120 = 4'b0;
    a_y_120 = 4'b0;
    case (a_ctrl_120)
        2'd0: begin a_x_120 = a_data_120[3:0];   a_y_120 = a_data_120[11:8];  end
        2'd1: begin a_x_120 = a_data_120[11:8];  a_y_120 = a_data_120[3:0];   end
        2'd2: begin a_x_120 = a_data_120[7:4];   a_y_120 = a_data_120[15:12]; end
        2'd3: begin a_x_120 = a_data_120[15:12]; a_y_120 = a_data_120[7:4];   end
    endcase
end
assign a_out[960 +: 4] = a_x_120;
assign a_out[964 +: 4] = a_y_120;

wire [1:0] a_ctrl_121 = a_ctrl[242 +: 2];
wire [15:0] a_data_121 = a_data[1936 +: 16];
reg [3:0] a_x_121;
reg [3:0] a_y_121;

always @* begin
    a_x_121 = 4'b0;
    a_y_121 = 4'b0;
    case (a_ctrl_121)
        2'd0: begin a_x_121 = a_data_121[3:0];   a_y_121 = a_data_121[11:8];  end
        2'd1: begin a_x_121 = a_data_121[11:8];  a_y_121 = a_data_121[3:0];   end
        2'd2: begin a_x_121 = a_data_121[7:4];   a_y_121 = a_data_121[15:12]; end
        2'd3: begin a_x_121 = a_data_121[15:12]; a_y_121 = a_data_121[7:4];   end
    endcase
end
assign a_out[968 +: 4] = a_x_121;
assign a_out[972 +: 4] = a_y_121;

wire [1:0] a_ctrl_122 = a_ctrl[244 +: 2];
wire [15:0] a_data_122 = a_data[1952 +: 16];
reg [3:0] a_x_122;
reg [3:0] a_y_122;

always @* begin
    a_x_122 = 4'b0;
    a_y_122 = 4'b0;
    case (a_ctrl_122)
        2'd0: begin a_x_122 = a_data_122[3:0];   a_y_122 = a_data_122[11:8];  end
        2'd1: begin a_x_122 = a_data_122[11:8];  a_y_122 = a_data_122[3:0];   end
        2'd2: begin a_x_122 = a_data_122[7:4];   a_y_122 = a_data_122[15:12]; end
        2'd3: begin a_x_122 = a_data_122[15:12]; a_y_122 = a_data_122[7:4];   end
    endcase
end
assign a_out[976 +: 4] = a_x_122;
assign a_out[980 +: 4] = a_y_122;

wire [1:0] a_ctrl_123 = a_ctrl[246 +: 2];
wire [15:0] a_data_123 = a_data[1968 +: 16];
reg [3:0] a_x_123;
reg [3:0] a_y_123;

always @* begin
    a_x_123 = 4'b0;
    a_y_123 = 4'b0;
    case (a_ctrl_123)
        2'd0: begin a_x_123 = a_data_123[3:0];   a_y_123 = a_data_123[11:8];  end
        2'd1: begin a_x_123 = a_data_123[11:8];  a_y_123 = a_data_123[3:0];   end
        2'd2: begin a_x_123 = a_data_123[7:4];   a_y_123 = a_data_123[15:12]; end
        2'd3: begin a_x_123 = a_data_123[15:12]; a_y_123 = a_data_123[7:4];   end
    endcase
end
assign a_out[984 +: 4] = a_x_123;
assign a_out[988 +: 4] = a_y_123;

wire [1:0] a_ctrl_124 = a_ctrl[248 +: 2];
wire [15:0] a_data_124 = a_data[1984 +: 16];
reg [3:0] a_x_124;
reg [3:0] a_y_124;

always @* begin
    a_x_124 = 4'b0;
    a_y_124 = 4'b0;
    case (a_ctrl_124)
        2'd0: begin a_x_124 = a_data_124[3:0];   a_y_124 = a_data_124[11:8];  end
        2'd1: begin a_x_124 = a_data_124[11:8];  a_y_124 = a_data_124[3:0];   end
        2'd2: begin a_x_124 = a_data_124[7:4];   a_y_124 = a_data_124[15:12]; end
        2'd3: begin a_x_124 = a_data_124[15:12]; a_y_124 = a_data_124[7:4];   end
    endcase
end
assign a_out[992 +: 4] = a_x_124;
assign a_out[996 +: 4] = a_y_124;

wire [1:0] a_ctrl_125 = a_ctrl[250 +: 2];
wire [15:0] a_data_125 = a_data[2000 +: 16];
reg [3:0] a_x_125;
reg [3:0] a_y_125;

always @* begin
    a_x_125 = 4'b0;
    a_y_125 = 4'b0;
    case (a_ctrl_125)
        2'd0: begin a_x_125 = a_data_125[3:0];   a_y_125 = a_data_125[11:8];  end
        2'd1: begin a_x_125 = a_data_125[11:8];  a_y_125 = a_data_125[3:0];   end
        2'd2: begin a_x_125 = a_data_125[7:4];   a_y_125 = a_data_125[15:12]; end
        2'd3: begin a_x_125 = a_data_125[15:12]; a_y_125 = a_data_125[7:4];   end
    endcase
end
assign a_out[1000 +: 4] = a_x_125;
assign a_out[1004 +: 4] = a_y_125;

wire [1:0] a_ctrl_126 = a_ctrl[252 +: 2];
wire [15:0] a_data_126 = a_data[2016 +: 16];
reg [3:0] a_x_126;
reg [3:0] a_y_126;

always @* begin
    a_x_126 = 4'b0;
    a_y_126 = 4'b0;
    case (a_ctrl_126)
        2'd0: begin a_x_126 = a_data_126[3:0];   a_y_126 = a_data_126[11:8];  end
        2'd1: begin a_x_126 = a_data_126[11:8];  a_y_126 = a_data_126[3:0];   end
        2'd2: begin a_x_126 = a_data_126[7:4];   a_y_126 = a_data_126[15:12]; end
        2'd3: begin a_x_126 = a_data_126[15:12]; a_y_126 = a_data_126[7:4];   end
    endcase
end
assign a_out[1008 +: 4] = a_x_126;
assign a_out[1012 +: 4] = a_y_126;

wire [1:0] a_ctrl_127 = a_ctrl[254 +: 2];
wire [15:0] a_data_127 = a_data[2032 +: 16];
reg [3:0] a_x_127;
reg [3:0] a_y_127;

always @* begin
    a_x_127 = 4'b0;
    a_y_127 = 4'b0;
    case (a_ctrl_127)
        2'd0: begin a_x_127 = a_data_127[3:0];   a_y_127 = a_data_127[11:8];  end
        2'd1: begin a_x_127 = a_data_127[11:8];  a_y_127 = a_data_127[3:0];   end
        2'd2: begin a_x_127 = a_data_127[7:4];   a_y_127 = a_data_127[15:12]; end
        2'd3: begin a_x_127 = a_data_127[15:12]; a_y_127 = a_data_127[7:4];   end
    endcase
end
assign a_out[1016 +: 4] = a_x_127;
assign a_out[1020 +: 4] = a_y_127;

wire [1:0] a_ctrl_128 = a_ctrl[256 +: 2];
wire [15:0] a_data_128 = a_data[2048 +: 16];
reg [3:0] a_x_128;
reg [3:0] a_y_128;

always @* begin
    a_x_128 = 4'b0;
    a_y_128 = 4'b0;
    case (a_ctrl_128)
        2'd0: begin a_x_128 = a_data_128[3:0];   a_y_128 = a_data_128[11:8];  end
        2'd1: begin a_x_128 = a_data_128[11:8];  a_y_128 = a_data_128[3:0];   end
        2'd2: begin a_x_128 = a_data_128[7:4];   a_y_128 = a_data_128[15:12]; end
        2'd3: begin a_x_128 = a_data_128[15:12]; a_y_128 = a_data_128[7:4];   end
    endcase
end
assign a_out[1024 +: 4] = a_x_128;
assign a_out[1028 +: 4] = a_y_128;

wire [1:0] a_ctrl_129 = a_ctrl[258 +: 2];
wire [15:0] a_data_129 = a_data[2064 +: 16];
reg [3:0] a_x_129;
reg [3:0] a_y_129;

always @* begin
    a_x_129 = 4'b0;
    a_y_129 = 4'b0;
    case (a_ctrl_129)
        2'd0: begin a_x_129 = a_data_129[3:0];   a_y_129 = a_data_129[11:8];  end
        2'd1: begin a_x_129 = a_data_129[11:8];  a_y_129 = a_data_129[3:0];   end
        2'd2: begin a_x_129 = a_data_129[7:4];   a_y_129 = a_data_129[15:12]; end
        2'd3: begin a_x_129 = a_data_129[15:12]; a_y_129 = a_data_129[7:4];   end
    endcase
end
assign a_out[1032 +: 4] = a_x_129;
assign a_out[1036 +: 4] = a_y_129;

wire [1:0] a_ctrl_130 = a_ctrl[260 +: 2];
wire [15:0] a_data_130 = a_data[2080 +: 16];
reg [3:0] a_x_130;
reg [3:0] a_y_130;

always @* begin
    a_x_130 = 4'b0;
    a_y_130 = 4'b0;
    case (a_ctrl_130)
        2'd0: begin a_x_130 = a_data_130[3:0];   a_y_130 = a_data_130[11:8];  end
        2'd1: begin a_x_130 = a_data_130[11:8];  a_y_130 = a_data_130[3:0];   end
        2'd2: begin a_x_130 = a_data_130[7:4];   a_y_130 = a_data_130[15:12]; end
        2'd3: begin a_x_130 = a_data_130[15:12]; a_y_130 = a_data_130[7:4];   end
    endcase
end
assign a_out[1040 +: 4] = a_x_130;
assign a_out[1044 +: 4] = a_y_130;

wire [1:0] a_ctrl_131 = a_ctrl[262 +: 2];
wire [15:0] a_data_131 = a_data[2096 +: 16];
reg [3:0] a_x_131;
reg [3:0] a_y_131;

always @* begin
    a_x_131 = 4'b0;
    a_y_131 = 4'b0;
    case (a_ctrl_131)
        2'd0: begin a_x_131 = a_data_131[3:0];   a_y_131 = a_data_131[11:8];  end
        2'd1: begin a_x_131 = a_data_131[11:8];  a_y_131 = a_data_131[3:0];   end
        2'd2: begin a_x_131 = a_data_131[7:4];   a_y_131 = a_data_131[15:12]; end
        2'd3: begin a_x_131 = a_data_131[15:12]; a_y_131 = a_data_131[7:4];   end
    endcase
end
assign a_out[1048 +: 4] = a_x_131;
assign a_out[1052 +: 4] = a_y_131;

wire [1:0] a_ctrl_132 = a_ctrl[264 +: 2];
wire [15:0] a_data_132 = a_data[2112 +: 16];
reg [3:0] a_x_132;
reg [3:0] a_y_132;

always @* begin
    a_x_132 = 4'b0;
    a_y_132 = 4'b0;
    case (a_ctrl_132)
        2'd0: begin a_x_132 = a_data_132[3:0];   a_y_132 = a_data_132[11:8];  end
        2'd1: begin a_x_132 = a_data_132[11:8];  a_y_132 = a_data_132[3:0];   end
        2'd2: begin a_x_132 = a_data_132[7:4];   a_y_132 = a_data_132[15:12]; end
        2'd3: begin a_x_132 = a_data_132[15:12]; a_y_132 = a_data_132[7:4];   end
    endcase
end
assign a_out[1056 +: 4] = a_x_132;
assign a_out[1060 +: 4] = a_y_132;

wire [1:0] a_ctrl_133 = a_ctrl[266 +: 2];
wire [15:0] a_data_133 = a_data[2128 +: 16];
reg [3:0] a_x_133;
reg [3:0] a_y_133;

always @* begin
    a_x_133 = 4'b0;
    a_y_133 = 4'b0;
    case (a_ctrl_133)
        2'd0: begin a_x_133 = a_data_133[3:0];   a_y_133 = a_data_133[11:8];  end
        2'd1: begin a_x_133 = a_data_133[11:8];  a_y_133 = a_data_133[3:0];   end
        2'd2: begin a_x_133 = a_data_133[7:4];   a_y_133 = a_data_133[15:12]; end
        2'd3: begin a_x_133 = a_data_133[15:12]; a_y_133 = a_data_133[7:4];   end
    endcase
end
assign a_out[1064 +: 4] = a_x_133;
assign a_out[1068 +: 4] = a_y_133;

wire [1:0] a_ctrl_134 = a_ctrl[268 +: 2];
wire [15:0] a_data_134 = a_data[2144 +: 16];
reg [3:0] a_x_134;
reg [3:0] a_y_134;

always @* begin
    a_x_134 = 4'b0;
    a_y_134 = 4'b0;
    case (a_ctrl_134)
        2'd0: begin a_x_134 = a_data_134[3:0];   a_y_134 = a_data_134[11:8];  end
        2'd1: begin a_x_134 = a_data_134[11:8];  a_y_134 = a_data_134[3:0];   end
        2'd2: begin a_x_134 = a_data_134[7:4];   a_y_134 = a_data_134[15:12]; end
        2'd3: begin a_x_134 = a_data_134[15:12]; a_y_134 = a_data_134[7:4];   end
    endcase
end
assign a_out[1072 +: 4] = a_x_134;
assign a_out[1076 +: 4] = a_y_134;

wire [1:0] a_ctrl_135 = a_ctrl[270 +: 2];
wire [15:0] a_data_135 = a_data[2160 +: 16];
reg [3:0] a_x_135;
reg [3:0] a_y_135;

always @* begin
    a_x_135 = 4'b0;
    a_y_135 = 4'b0;
    case (a_ctrl_135)
        2'd0: begin a_x_135 = a_data_135[3:0];   a_y_135 = a_data_135[11:8];  end
        2'd1: begin a_x_135 = a_data_135[11:8];  a_y_135 = a_data_135[3:0];   end
        2'd2: begin a_x_135 = a_data_135[7:4];   a_y_135 = a_data_135[15:12]; end
        2'd3: begin a_x_135 = a_data_135[15:12]; a_y_135 = a_data_135[7:4];   end
    endcase
end
assign a_out[1080 +: 4] = a_x_135;
assign a_out[1084 +: 4] = a_y_135;

wire [1:0] a_ctrl_136 = a_ctrl[272 +: 2];
wire [15:0] a_data_136 = a_data[2176 +: 16];
reg [3:0] a_x_136;
reg [3:0] a_y_136;

always @* begin
    a_x_136 = 4'b0;
    a_y_136 = 4'b0;
    case (a_ctrl_136)
        2'd0: begin a_x_136 = a_data_136[3:0];   a_y_136 = a_data_136[11:8];  end
        2'd1: begin a_x_136 = a_data_136[11:8];  a_y_136 = a_data_136[3:0];   end
        2'd2: begin a_x_136 = a_data_136[7:4];   a_y_136 = a_data_136[15:12]; end
        2'd3: begin a_x_136 = a_data_136[15:12]; a_y_136 = a_data_136[7:4];   end
    endcase
end
assign a_out[1088 +: 4] = a_x_136;
assign a_out[1092 +: 4] = a_y_136;

wire [1:0] a_ctrl_137 = a_ctrl[274 +: 2];
wire [15:0] a_data_137 = a_data[2192 +: 16];
reg [3:0] a_x_137;
reg [3:0] a_y_137;

always @* begin
    a_x_137 = 4'b0;
    a_y_137 = 4'b0;
    case (a_ctrl_137)
        2'd0: begin a_x_137 = a_data_137[3:0];   a_y_137 = a_data_137[11:8];  end
        2'd1: begin a_x_137 = a_data_137[11:8];  a_y_137 = a_data_137[3:0];   end
        2'd2: begin a_x_137 = a_data_137[7:4];   a_y_137 = a_data_137[15:12]; end
        2'd3: begin a_x_137 = a_data_137[15:12]; a_y_137 = a_data_137[7:4];   end
    endcase
end
assign a_out[1096 +: 4] = a_x_137;
assign a_out[1100 +: 4] = a_y_137;

wire [1:0] a_ctrl_138 = a_ctrl[276 +: 2];
wire [15:0] a_data_138 = a_data[2208 +: 16];
reg [3:0] a_x_138;
reg [3:0] a_y_138;

always @* begin
    a_x_138 = 4'b0;
    a_y_138 = 4'b0;
    case (a_ctrl_138)
        2'd0: begin a_x_138 = a_data_138[3:0];   a_y_138 = a_data_138[11:8];  end
        2'd1: begin a_x_138 = a_data_138[11:8];  a_y_138 = a_data_138[3:0];   end
        2'd2: begin a_x_138 = a_data_138[7:4];   a_y_138 = a_data_138[15:12]; end
        2'd3: begin a_x_138 = a_data_138[15:12]; a_y_138 = a_data_138[7:4];   end
    endcase
end
assign a_out[1104 +: 4] = a_x_138;
assign a_out[1108 +: 4] = a_y_138;

wire [1:0] a_ctrl_139 = a_ctrl[278 +: 2];
wire [15:0] a_data_139 = a_data[2224 +: 16];
reg [3:0] a_x_139;
reg [3:0] a_y_139;

always @* begin
    a_x_139 = 4'b0;
    a_y_139 = 4'b0;
    case (a_ctrl_139)
        2'd0: begin a_x_139 = a_data_139[3:0];   a_y_139 = a_data_139[11:8];  end
        2'd1: begin a_x_139 = a_data_139[11:8];  a_y_139 = a_data_139[3:0];   end
        2'd2: begin a_x_139 = a_data_139[7:4];   a_y_139 = a_data_139[15:12]; end
        2'd3: begin a_x_139 = a_data_139[15:12]; a_y_139 = a_data_139[7:4];   end
    endcase
end
assign a_out[1112 +: 4] = a_x_139;
assign a_out[1116 +: 4] = a_y_139;

wire [1:0] a_ctrl_140 = a_ctrl[280 +: 2];
wire [15:0] a_data_140 = a_data[2240 +: 16];
reg [3:0] a_x_140;
reg [3:0] a_y_140;

always @* begin
    a_x_140 = 4'b0;
    a_y_140 = 4'b0;
    case (a_ctrl_140)
        2'd0: begin a_x_140 = a_data_140[3:0];   a_y_140 = a_data_140[11:8];  end
        2'd1: begin a_x_140 = a_data_140[11:8];  a_y_140 = a_data_140[3:0];   end
        2'd2: begin a_x_140 = a_data_140[7:4];   a_y_140 = a_data_140[15:12]; end
        2'd3: begin a_x_140 = a_data_140[15:12]; a_y_140 = a_data_140[7:4];   end
    endcase
end
assign a_out[1120 +: 4] = a_x_140;
assign a_out[1124 +: 4] = a_y_140;

wire [1:0] a_ctrl_141 = a_ctrl[282 +: 2];
wire [15:0] a_data_141 = a_data[2256 +: 16];
reg [3:0] a_x_141;
reg [3:0] a_y_141;

always @* begin
    a_x_141 = 4'b0;
    a_y_141 = 4'b0;
    case (a_ctrl_141)
        2'd0: begin a_x_141 = a_data_141[3:0];   a_y_141 = a_data_141[11:8];  end
        2'd1: begin a_x_141 = a_data_141[11:8];  a_y_141 = a_data_141[3:0];   end
        2'd2: begin a_x_141 = a_data_141[7:4];   a_y_141 = a_data_141[15:12]; end
        2'd3: begin a_x_141 = a_data_141[15:12]; a_y_141 = a_data_141[7:4];   end
    endcase
end
assign a_out[1128 +: 4] = a_x_141;
assign a_out[1132 +: 4] = a_y_141;

wire [1:0] a_ctrl_142 = a_ctrl[284 +: 2];
wire [15:0] a_data_142 = a_data[2272 +: 16];
reg [3:0] a_x_142;
reg [3:0] a_y_142;

always @* begin
    a_x_142 = 4'b0;
    a_y_142 = 4'b0;
    case (a_ctrl_142)
        2'd0: begin a_x_142 = a_data_142[3:0];   a_y_142 = a_data_142[11:8];  end
        2'd1: begin a_x_142 = a_data_142[11:8];  a_y_142 = a_data_142[3:0];   end
        2'd2: begin a_x_142 = a_data_142[7:4];   a_y_142 = a_data_142[15:12]; end
        2'd3: begin a_x_142 = a_data_142[15:12]; a_y_142 = a_data_142[7:4];   end
    endcase
end
assign a_out[1136 +: 4] = a_x_142;
assign a_out[1140 +: 4] = a_y_142;

wire [1:0] a_ctrl_143 = a_ctrl[286 +: 2];
wire [15:0] a_data_143 = a_data[2288 +: 16];
reg [3:0] a_x_143;
reg [3:0] a_y_143;

always @* begin
    a_x_143 = 4'b0;
    a_y_143 = 4'b0;
    case (a_ctrl_143)
        2'd0: begin a_x_143 = a_data_143[3:0];   a_y_143 = a_data_143[11:8];  end
        2'd1: begin a_x_143 = a_data_143[11:8];  a_y_143 = a_data_143[3:0];   end
        2'd2: begin a_x_143 = a_data_143[7:4];   a_y_143 = a_data_143[15:12]; end
        2'd3: begin a_x_143 = a_data_143[15:12]; a_y_143 = a_data_143[7:4];   end
    endcase
end
assign a_out[1144 +: 4] = a_x_143;
assign a_out[1148 +: 4] = a_y_143;

wire [1:0] a_ctrl_144 = a_ctrl[288 +: 2];
wire [15:0] a_data_144 = a_data[2304 +: 16];
reg [3:0] a_x_144;
reg [3:0] a_y_144;

always @* begin
    a_x_144 = 4'b0;
    a_y_144 = 4'b0;
    case (a_ctrl_144)
        2'd0: begin a_x_144 = a_data_144[3:0];   a_y_144 = a_data_144[11:8];  end
        2'd1: begin a_x_144 = a_data_144[11:8];  a_y_144 = a_data_144[3:0];   end
        2'd2: begin a_x_144 = a_data_144[7:4];   a_y_144 = a_data_144[15:12]; end
        2'd3: begin a_x_144 = a_data_144[15:12]; a_y_144 = a_data_144[7:4];   end
    endcase
end
assign a_out[1152 +: 4] = a_x_144;
assign a_out[1156 +: 4] = a_y_144;

wire [1:0] a_ctrl_145 = a_ctrl[290 +: 2];
wire [15:0] a_data_145 = a_data[2320 +: 16];
reg [3:0] a_x_145;
reg [3:0] a_y_145;

always @* begin
    a_x_145 = 4'b0;
    a_y_145 = 4'b0;
    case (a_ctrl_145)
        2'd0: begin a_x_145 = a_data_145[3:0];   a_y_145 = a_data_145[11:8];  end
        2'd1: begin a_x_145 = a_data_145[11:8];  a_y_145 = a_data_145[3:0];   end
        2'd2: begin a_x_145 = a_data_145[7:4];   a_y_145 = a_data_145[15:12]; end
        2'd3: begin a_x_145 = a_data_145[15:12]; a_y_145 = a_data_145[7:4];   end
    endcase
end
assign a_out[1160 +: 4] = a_x_145;
assign a_out[1164 +: 4] = a_y_145;

wire [1:0] a_ctrl_146 = a_ctrl[292 +: 2];
wire [15:0] a_data_146 = a_data[2336 +: 16];
reg [3:0] a_x_146;
reg [3:0] a_y_146;

always @* begin
    a_x_146 = 4'b0;
    a_y_146 = 4'b0;
    case (a_ctrl_146)
        2'd0: begin a_x_146 = a_data_146[3:0];   a_y_146 = a_data_146[11:8];  end
        2'd1: begin a_x_146 = a_data_146[11:8];  a_y_146 = a_data_146[3:0];   end
        2'd2: begin a_x_146 = a_data_146[7:4];   a_y_146 = a_data_146[15:12]; end
        2'd3: begin a_x_146 = a_data_146[15:12]; a_y_146 = a_data_146[7:4];   end
    endcase
end
assign a_out[1168 +: 4] = a_x_146;
assign a_out[1172 +: 4] = a_y_146;

wire [1:0] a_ctrl_147 = a_ctrl[294 +: 2];
wire [15:0] a_data_147 = a_data[2352 +: 16];
reg [3:0] a_x_147;
reg [3:0] a_y_147;

always @* begin
    a_x_147 = 4'b0;
    a_y_147 = 4'b0;
    case (a_ctrl_147)
        2'd0: begin a_x_147 = a_data_147[3:0];   a_y_147 = a_data_147[11:8];  end
        2'd1: begin a_x_147 = a_data_147[11:8];  a_y_147 = a_data_147[3:0];   end
        2'd2: begin a_x_147 = a_data_147[7:4];   a_y_147 = a_data_147[15:12]; end
        2'd3: begin a_x_147 = a_data_147[15:12]; a_y_147 = a_data_147[7:4];   end
    endcase
end
assign a_out[1176 +: 4] = a_x_147;
assign a_out[1180 +: 4] = a_y_147;

wire [1:0] a_ctrl_148 = a_ctrl[296 +: 2];
wire [15:0] a_data_148 = a_data[2368 +: 16];
reg [3:0] a_x_148;
reg [3:0] a_y_148;

always @* begin
    a_x_148 = 4'b0;
    a_y_148 = 4'b0;
    case (a_ctrl_148)
        2'd0: begin a_x_148 = a_data_148[3:0];   a_y_148 = a_data_148[11:8];  end
        2'd1: begin a_x_148 = a_data_148[11:8];  a_y_148 = a_data_148[3:0];   end
        2'd2: begin a_x_148 = a_data_148[7:4];   a_y_148 = a_data_148[15:12]; end
        2'd3: begin a_x_148 = a_data_148[15:12]; a_y_148 = a_data_148[7:4];   end
    endcase
end
assign a_out[1184 +: 4] = a_x_148;
assign a_out[1188 +: 4] = a_y_148;

wire [1:0] a_ctrl_149 = a_ctrl[298 +: 2];
wire [15:0] a_data_149 = a_data[2384 +: 16];
reg [3:0] a_x_149;
reg [3:0] a_y_149;

always @* begin
    a_x_149 = 4'b0;
    a_y_149 = 4'b0;
    case (a_ctrl_149)
        2'd0: begin a_x_149 = a_data_149[3:0];   a_y_149 = a_data_149[11:8];  end
        2'd1: begin a_x_149 = a_data_149[11:8];  a_y_149 = a_data_149[3:0];   end
        2'd2: begin a_x_149 = a_data_149[7:4];   a_y_149 = a_data_149[15:12]; end
        2'd3: begin a_x_149 = a_data_149[15:12]; a_y_149 = a_data_149[7:4];   end
    endcase
end
assign a_out[1192 +: 4] = a_x_149;
assign a_out[1196 +: 4] = a_y_149;

wire [1:0] a_ctrl_150 = a_ctrl[300 +: 2];
wire [15:0] a_data_150 = a_data[2400 +: 16];
reg [3:0] a_x_150;
reg [3:0] a_y_150;

always @* begin
    a_x_150 = 4'b0;
    a_y_150 = 4'b0;
    case (a_ctrl_150)
        2'd0: begin a_x_150 = a_data_150[3:0];   a_y_150 = a_data_150[11:8];  end
        2'd1: begin a_x_150 = a_data_150[11:8];  a_y_150 = a_data_150[3:0];   end
        2'd2: begin a_x_150 = a_data_150[7:4];   a_y_150 = a_data_150[15:12]; end
        2'd3: begin a_x_150 = a_data_150[15:12]; a_y_150 = a_data_150[7:4];   end
    endcase
end
assign a_out[1200 +: 4] = a_x_150;
assign a_out[1204 +: 4] = a_y_150;

wire [1:0] a_ctrl_151 = a_ctrl[302 +: 2];
wire [15:0] a_data_151 = a_data[2416 +: 16];
reg [3:0] a_x_151;
reg [3:0] a_y_151;

always @* begin
    a_x_151 = 4'b0;
    a_y_151 = 4'b0;
    case (a_ctrl_151)
        2'd0: begin a_x_151 = a_data_151[3:0];   a_y_151 = a_data_151[11:8];  end
        2'd1: begin a_x_151 = a_data_151[11:8];  a_y_151 = a_data_151[3:0];   end
        2'd2: begin a_x_151 = a_data_151[7:4];   a_y_151 = a_data_151[15:12]; end
        2'd3: begin a_x_151 = a_data_151[15:12]; a_y_151 = a_data_151[7:4];   end
    endcase
end
assign a_out[1208 +: 4] = a_x_151;
assign a_out[1212 +: 4] = a_y_151;

wire [1:0] a_ctrl_152 = a_ctrl[304 +: 2];
wire [15:0] a_data_152 = a_data[2432 +: 16];
reg [3:0] a_x_152;
reg [3:0] a_y_152;

always @* begin
    a_x_152 = 4'b0;
    a_y_152 = 4'b0;
    case (a_ctrl_152)
        2'd0: begin a_x_152 = a_data_152[3:0];   a_y_152 = a_data_152[11:8];  end
        2'd1: begin a_x_152 = a_data_152[11:8];  a_y_152 = a_data_152[3:0];   end
        2'd2: begin a_x_152 = a_data_152[7:4];   a_y_152 = a_data_152[15:12]; end
        2'd3: begin a_x_152 = a_data_152[15:12]; a_y_152 = a_data_152[7:4];   end
    endcase
end
assign a_out[1216 +: 4] = a_x_152;
assign a_out[1220 +: 4] = a_y_152;

wire [1:0] a_ctrl_153 = a_ctrl[306 +: 2];
wire [15:0] a_data_153 = a_data[2448 +: 16];
reg [3:0] a_x_153;
reg [3:0] a_y_153;

always @* begin
    a_x_153 = 4'b0;
    a_y_153 = 4'b0;
    case (a_ctrl_153)
        2'd0: begin a_x_153 = a_data_153[3:0];   a_y_153 = a_data_153[11:8];  end
        2'd1: begin a_x_153 = a_data_153[11:8];  a_y_153 = a_data_153[3:0];   end
        2'd2: begin a_x_153 = a_data_153[7:4];   a_y_153 = a_data_153[15:12]; end
        2'd3: begin a_x_153 = a_data_153[15:12]; a_y_153 = a_data_153[7:4];   end
    endcase
end
assign a_out[1224 +: 4] = a_x_153;
assign a_out[1228 +: 4] = a_y_153;

wire [1:0] a_ctrl_154 = a_ctrl[308 +: 2];
wire [15:0] a_data_154 = a_data[2464 +: 16];
reg [3:0] a_x_154;
reg [3:0] a_y_154;

always @* begin
    a_x_154 = 4'b0;
    a_y_154 = 4'b0;
    case (a_ctrl_154)
        2'd0: begin a_x_154 = a_data_154[3:0];   a_y_154 = a_data_154[11:8];  end
        2'd1: begin a_x_154 = a_data_154[11:8];  a_y_154 = a_data_154[3:0];   end
        2'd2: begin a_x_154 = a_data_154[7:4];   a_y_154 = a_data_154[15:12]; end
        2'd3: begin a_x_154 = a_data_154[15:12]; a_y_154 = a_data_154[7:4];   end
    endcase
end
assign a_out[1232 +: 4] = a_x_154;
assign a_out[1236 +: 4] = a_y_154;

wire [1:0] a_ctrl_155 = a_ctrl[310 +: 2];
wire [15:0] a_data_155 = a_data[2480 +: 16];
reg [3:0] a_x_155;
reg [3:0] a_y_155;

always @* begin
    a_x_155 = 4'b0;
    a_y_155 = 4'b0;
    case (a_ctrl_155)
        2'd0: begin a_x_155 = a_data_155[3:0];   a_y_155 = a_data_155[11:8];  end
        2'd1: begin a_x_155 = a_data_155[11:8];  a_y_155 = a_data_155[3:0];   end
        2'd2: begin a_x_155 = a_data_155[7:4];   a_y_155 = a_data_155[15:12]; end
        2'd3: begin a_x_155 = a_data_155[15:12]; a_y_155 = a_data_155[7:4];   end
    endcase
end
assign a_out[1240 +: 4] = a_x_155;
assign a_out[1244 +: 4] = a_y_155;

wire [1:0] a_ctrl_156 = a_ctrl[312 +: 2];
wire [15:0] a_data_156 = a_data[2496 +: 16];
reg [3:0] a_x_156;
reg [3:0] a_y_156;

always @* begin
    a_x_156 = 4'b0;
    a_y_156 = 4'b0;
    case (a_ctrl_156)
        2'd0: begin a_x_156 = a_data_156[3:0];   a_y_156 = a_data_156[11:8];  end
        2'd1: begin a_x_156 = a_data_156[11:8];  a_y_156 = a_data_156[3:0];   end
        2'd2: begin a_x_156 = a_data_156[7:4];   a_y_156 = a_data_156[15:12]; end
        2'd3: begin a_x_156 = a_data_156[15:12]; a_y_156 = a_data_156[7:4];   end
    endcase
end
assign a_out[1248 +: 4] = a_x_156;
assign a_out[1252 +: 4] = a_y_156;

wire [1:0] a_ctrl_157 = a_ctrl[314 +: 2];
wire [15:0] a_data_157 = a_data[2512 +: 16];
reg [3:0] a_x_157;
reg [3:0] a_y_157;

always @* begin
    a_x_157 = 4'b0;
    a_y_157 = 4'b0;
    case (a_ctrl_157)
        2'd0: begin a_x_157 = a_data_157[3:0];   a_y_157 = a_data_157[11:8];  end
        2'd1: begin a_x_157 = a_data_157[11:8];  a_y_157 = a_data_157[3:0];   end
        2'd2: begin a_x_157 = a_data_157[7:4];   a_y_157 = a_data_157[15:12]; end
        2'd3: begin a_x_157 = a_data_157[15:12]; a_y_157 = a_data_157[7:4];   end
    endcase
end
assign a_out[1256 +: 4] = a_x_157;
assign a_out[1260 +: 4] = a_y_157;

wire [1:0] a_ctrl_158 = a_ctrl[316 +: 2];
wire [15:0] a_data_158 = a_data[2528 +: 16];
reg [3:0] a_x_158;
reg [3:0] a_y_158;

always @* begin
    a_x_158 = 4'b0;
    a_y_158 = 4'b0;
    case (a_ctrl_158)
        2'd0: begin a_x_158 = a_data_158[3:0];   a_y_158 = a_data_158[11:8];  end
        2'd1: begin a_x_158 = a_data_158[11:8];  a_y_158 = a_data_158[3:0];   end
        2'd2: begin a_x_158 = a_data_158[7:4];   a_y_158 = a_data_158[15:12]; end
        2'd3: begin a_x_158 = a_data_158[15:12]; a_y_158 = a_data_158[7:4];   end
    endcase
end
assign a_out[1264 +: 4] = a_x_158;
assign a_out[1268 +: 4] = a_y_158;

wire [1:0] a_ctrl_159 = a_ctrl[318 +: 2];
wire [15:0] a_data_159 = a_data[2544 +: 16];
reg [3:0] a_x_159;
reg [3:0] a_y_159;

always @* begin
    a_x_159 = 4'b0;
    a_y_159 = 4'b0;
    case (a_ctrl_159)
        2'd0: begin a_x_159 = a_data_159[3:0];   a_y_159 = a_data_159[11:8];  end
        2'd1: begin a_x_159 = a_data_159[11:8];  a_y_159 = a_data_159[3:0];   end
        2'd2: begin a_x_159 = a_data_159[7:4];   a_y_159 = a_data_159[15:12]; end
        2'd3: begin a_x_159 = a_data_159[15:12]; a_y_159 = a_data_159[7:4];   end
    endcase
end
assign a_out[1272 +: 4] = a_x_159;
assign a_out[1276 +: 4] = a_y_159;

wire [1:0] a_ctrl_160 = a_ctrl[320 +: 2];
wire [15:0] a_data_160 = a_data[2560 +: 16];
reg [3:0] a_x_160;
reg [3:0] a_y_160;

always @* begin
    a_x_160 = 4'b0;
    a_y_160 = 4'b0;
    case (a_ctrl_160)
        2'd0: begin a_x_160 = a_data_160[3:0];   a_y_160 = a_data_160[11:8];  end
        2'd1: begin a_x_160 = a_data_160[11:8];  a_y_160 = a_data_160[3:0];   end
        2'd2: begin a_x_160 = a_data_160[7:4];   a_y_160 = a_data_160[15:12]; end
        2'd3: begin a_x_160 = a_data_160[15:12]; a_y_160 = a_data_160[7:4];   end
    endcase
end
assign a_out[1280 +: 4] = a_x_160;
assign a_out[1284 +: 4] = a_y_160;

wire [1:0] a_ctrl_161 = a_ctrl[322 +: 2];
wire [15:0] a_data_161 = a_data[2576 +: 16];
reg [3:0] a_x_161;
reg [3:0] a_y_161;

always @* begin
    a_x_161 = 4'b0;
    a_y_161 = 4'b0;
    case (a_ctrl_161)
        2'd0: begin a_x_161 = a_data_161[3:0];   a_y_161 = a_data_161[11:8];  end
        2'd1: begin a_x_161 = a_data_161[11:8];  a_y_161 = a_data_161[3:0];   end
        2'd2: begin a_x_161 = a_data_161[7:4];   a_y_161 = a_data_161[15:12]; end
        2'd3: begin a_x_161 = a_data_161[15:12]; a_y_161 = a_data_161[7:4];   end
    endcase
end
assign a_out[1288 +: 4] = a_x_161;
assign a_out[1292 +: 4] = a_y_161;

wire [1:0] a_ctrl_162 = a_ctrl[324 +: 2];
wire [15:0] a_data_162 = a_data[2592 +: 16];
reg [3:0] a_x_162;
reg [3:0] a_y_162;

always @* begin
    a_x_162 = 4'b0;
    a_y_162 = 4'b0;
    case (a_ctrl_162)
        2'd0: begin a_x_162 = a_data_162[3:0];   a_y_162 = a_data_162[11:8];  end
        2'd1: begin a_x_162 = a_data_162[11:8];  a_y_162 = a_data_162[3:0];   end
        2'd2: begin a_x_162 = a_data_162[7:4];   a_y_162 = a_data_162[15:12]; end
        2'd3: begin a_x_162 = a_data_162[15:12]; a_y_162 = a_data_162[7:4];   end
    endcase
end
assign a_out[1296 +: 4] = a_x_162;
assign a_out[1300 +: 4] = a_y_162;

wire [1:0] a_ctrl_163 = a_ctrl[326 +: 2];
wire [15:0] a_data_163 = a_data[2608 +: 16];
reg [3:0] a_x_163;
reg [3:0] a_y_163;

always @* begin
    a_x_163 = 4'b0;
    a_y_163 = 4'b0;
    case (a_ctrl_163)
        2'd0: begin a_x_163 = a_data_163[3:0];   a_y_163 = a_data_163[11:8];  end
        2'd1: begin a_x_163 = a_data_163[11:8];  a_y_163 = a_data_163[3:0];   end
        2'd2: begin a_x_163 = a_data_163[7:4];   a_y_163 = a_data_163[15:12]; end
        2'd3: begin a_x_163 = a_data_163[15:12]; a_y_163 = a_data_163[7:4];   end
    endcase
end
assign a_out[1304 +: 4] = a_x_163;
assign a_out[1308 +: 4] = a_y_163;

wire [1:0] a_ctrl_164 = a_ctrl[328 +: 2];
wire [15:0] a_data_164 = a_data[2624 +: 16];
reg [3:0] a_x_164;
reg [3:0] a_y_164;

always @* begin
    a_x_164 = 4'b0;
    a_y_164 = 4'b0;
    case (a_ctrl_164)
        2'd0: begin a_x_164 = a_data_164[3:0];   a_y_164 = a_data_164[11:8];  end
        2'd1: begin a_x_164 = a_data_164[11:8];  a_y_164 = a_data_164[3:0];   end
        2'd2: begin a_x_164 = a_data_164[7:4];   a_y_164 = a_data_164[15:12]; end
        2'd3: begin a_x_164 = a_data_164[15:12]; a_y_164 = a_data_164[7:4];   end
    endcase
end
assign a_out[1312 +: 4] = a_x_164;
assign a_out[1316 +: 4] = a_y_164;

wire [1:0] a_ctrl_165 = a_ctrl[330 +: 2];
wire [15:0] a_data_165 = a_data[2640 +: 16];
reg [3:0] a_x_165;
reg [3:0] a_y_165;

always @* begin
    a_x_165 = 4'b0;
    a_y_165 = 4'b0;
    case (a_ctrl_165)
        2'd0: begin a_x_165 = a_data_165[3:0];   a_y_165 = a_data_165[11:8];  end
        2'd1: begin a_x_165 = a_data_165[11:8];  a_y_165 = a_data_165[3:0];   end
        2'd2: begin a_x_165 = a_data_165[7:4];   a_y_165 = a_data_165[15:12]; end
        2'd3: begin a_x_165 = a_data_165[15:12]; a_y_165 = a_data_165[7:4];   end
    endcase
end
assign a_out[1320 +: 4] = a_x_165;
assign a_out[1324 +: 4] = a_y_165;

endmodule
