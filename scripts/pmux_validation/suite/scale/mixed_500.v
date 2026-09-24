module stress_top(
    input [73:0] a_ctrl,
    input [591:0] a_data,
    output [295:0] a_out,
    input [87:0] c_ctrl,
    output [87:0] c_out,
    input [31:0] n_ctrl,
    input [255:0] n_data,
    output [63:0] n_out
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

endmodule
