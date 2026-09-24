module stress_top(
    input [55:0] a_ctrl,
    input [447:0] a_data,
    output [223:0] a_out,
    input [147:0] c_ctrl,
    output [147:0] c_out,
    input [33:0] n_ctrl,
    input [271:0] n_data,
    output [67:0] n_out,
    input [35:0] h2_ctrl,
    input [767:0] h2_data,
    output [47:0] h2_out
);

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

wire [5:0] h2_ctrl_1 = h2_ctrl[6 +: 6];
wire [127:0] h2_data_1 = h2_data[128 +: 128];
reg [7:0] h2_y_1;

wire [7:0] h2_base0_1 = h2_data_1[7:0];
wire [7:0] h2_base1_1 = h2_data_1[15:8];
wire [7:0] h2_base2_1 = h2_data_1[23:16];
wire [7:0] h2_base3_1 = h2_data_1[31:24];
wire [7:0] h2_base4_1 = h2_data_1[39:32];
wire [7:0] h2_base5_1 = h2_data_1[47:40];
wire [7:0] h2_base6_1 = h2_data_1[55:48];
wire [7:0] h2_base7_1 = h2_data_1[63:56];
wire [7:0] h2_base8_1 = h2_data_1[71:64];
wire [7:0] h2_base9_1 = h2_data_1[79:72];
wire [7:0] h2_base10_1 = h2_data_1[87:80];
wire [7:0] h2_base11_1 = h2_data_1[95:88];
wire [7:0] h2_base12_1 = h2_data_1[103:96];
wire [7:0] h2_base13_1 = h2_data_1[111:104];
wire [7:0] h2_base14_1 = h2_data_1[119:112];
wire [7:0] h2_base15_1 = h2_data_1[127:120];
wire [7:0] h2_r0_0_1 = {h2_base0_1[7:6], h2_base0_1[5:4], h2_base0_1[3:2], h2_base0_1[1:0]};
wire [7:0] h2_r0_1_1 = {h2_base0_1[1:0], h2_base0_1[7:6], h2_base0_1[5:4], h2_base0_1[3:2]};
wire [7:0] h2_r0_2_1 = {h2_base0_1[3:2], h2_base0_1[1:0], h2_base0_1[7:6], h2_base0_1[5:4]};
wire [7:0] h2_r0_3_1 = {h2_base0_1[5:4], h2_base0_1[3:2], h2_base0_1[1:0], h2_base0_1[7:6]};
wire [7:0] h2_r1_0_1 = {h2_base1_1[7:6], h2_base1_1[5:4], h2_base1_1[3:2], h2_base1_1[1:0]};
wire [7:0] h2_r1_1_1 = {h2_base1_1[1:0], h2_base1_1[7:6], h2_base1_1[5:4], h2_base1_1[3:2]};
wire [7:0] h2_r1_2_1 = {h2_base1_1[3:2], h2_base1_1[1:0], h2_base1_1[7:6], h2_base1_1[5:4]};
wire [7:0] h2_r1_3_1 = {h2_base1_1[5:4], h2_base1_1[3:2], h2_base1_1[1:0], h2_base1_1[7:6]};
wire [7:0] h2_r2_0_1 = {h2_base2_1[7:6], h2_base2_1[5:4], h2_base2_1[3:2], h2_base2_1[1:0]};
wire [7:0] h2_r2_1_1 = {h2_base2_1[1:0], h2_base2_1[7:6], h2_base2_1[5:4], h2_base2_1[3:2]};
wire [7:0] h2_r2_2_1 = {h2_base2_1[3:2], h2_base2_1[1:0], h2_base2_1[7:6], h2_base2_1[5:4]};
wire [7:0] h2_r2_3_1 = {h2_base2_1[5:4], h2_base2_1[3:2], h2_base2_1[1:0], h2_base2_1[7:6]};
wire [7:0] h2_r3_0_1 = {h2_base3_1[7:6], h2_base3_1[5:4], h2_base3_1[3:2], h2_base3_1[1:0]};
wire [7:0] h2_r3_1_1 = {h2_base3_1[1:0], h2_base3_1[7:6], h2_base3_1[5:4], h2_base3_1[3:2]};
wire [7:0] h2_r3_2_1 = {h2_base3_1[3:2], h2_base3_1[1:0], h2_base3_1[7:6], h2_base3_1[5:4]};
wire [7:0] h2_r3_3_1 = {h2_base3_1[5:4], h2_base3_1[3:2], h2_base3_1[1:0], h2_base3_1[7:6]};
wire [7:0] h2_r4_0_1 = {h2_base4_1[7:6], h2_base4_1[5:4], h2_base4_1[3:2], h2_base4_1[1:0]};
wire [7:0] h2_r4_1_1 = {h2_base4_1[1:0], h2_base4_1[7:6], h2_base4_1[5:4], h2_base4_1[3:2]};
wire [7:0] h2_r4_2_1 = {h2_base4_1[3:2], h2_base4_1[1:0], h2_base4_1[7:6], h2_base4_1[5:4]};
wire [7:0] h2_r4_3_1 = {h2_base4_1[5:4], h2_base4_1[3:2], h2_base4_1[1:0], h2_base4_1[7:6]};
wire [7:0] h2_r5_0_1 = {h2_base5_1[7:6], h2_base5_1[5:4], h2_base5_1[3:2], h2_base5_1[1:0]};
wire [7:0] h2_r5_1_1 = {h2_base5_1[1:0], h2_base5_1[7:6], h2_base5_1[5:4], h2_base5_1[3:2]};
wire [7:0] h2_r5_2_1 = {h2_base5_1[3:2], h2_base5_1[1:0], h2_base5_1[7:6], h2_base5_1[5:4]};
wire [7:0] h2_r5_3_1 = {h2_base5_1[5:4], h2_base5_1[3:2], h2_base5_1[1:0], h2_base5_1[7:6]};
wire [7:0] h2_r6_0_1 = {h2_base6_1[7:6], h2_base6_1[5:4], h2_base6_1[3:2], h2_base6_1[1:0]};
wire [7:0] h2_r6_1_1 = {h2_base6_1[1:0], h2_base6_1[7:6], h2_base6_1[5:4], h2_base6_1[3:2]};
wire [7:0] h2_r6_2_1 = {h2_base6_1[3:2], h2_base6_1[1:0], h2_base6_1[7:6], h2_base6_1[5:4]};
wire [7:0] h2_r6_3_1 = {h2_base6_1[5:4], h2_base6_1[3:2], h2_base6_1[1:0], h2_base6_1[7:6]};
wire [7:0] h2_r7_0_1 = {h2_base7_1[7:6], h2_base7_1[5:4], h2_base7_1[3:2], h2_base7_1[1:0]};
wire [7:0] h2_r7_1_1 = {h2_base7_1[1:0], h2_base7_1[7:6], h2_base7_1[5:4], h2_base7_1[3:2]};
wire [7:0] h2_r7_2_1 = {h2_base7_1[3:2], h2_base7_1[1:0], h2_base7_1[7:6], h2_base7_1[5:4]};
wire [7:0] h2_r7_3_1 = {h2_base7_1[5:4], h2_base7_1[3:2], h2_base7_1[1:0], h2_base7_1[7:6]};
wire [7:0] h2_r8_0_1 = {h2_base8_1[7:6], h2_base8_1[5:4], h2_base8_1[3:2], h2_base8_1[1:0]};
wire [7:0] h2_r8_1_1 = {h2_base8_1[1:0], h2_base8_1[7:6], h2_base8_1[5:4], h2_base8_1[3:2]};
wire [7:0] h2_r8_2_1 = {h2_base8_1[3:2], h2_base8_1[1:0], h2_base8_1[7:6], h2_base8_1[5:4]};
wire [7:0] h2_r8_3_1 = {h2_base8_1[5:4], h2_base8_1[3:2], h2_base8_1[1:0], h2_base8_1[7:6]};
wire [7:0] h2_r9_0_1 = {h2_base9_1[7:6], h2_base9_1[5:4], h2_base9_1[3:2], h2_base9_1[1:0]};
wire [7:0] h2_r9_1_1 = {h2_base9_1[1:0], h2_base9_1[7:6], h2_base9_1[5:4], h2_base9_1[3:2]};
wire [7:0] h2_r9_2_1 = {h2_base9_1[3:2], h2_base9_1[1:0], h2_base9_1[7:6], h2_base9_1[5:4]};
wire [7:0] h2_r9_3_1 = {h2_base9_1[5:4], h2_base9_1[3:2], h2_base9_1[1:0], h2_base9_1[7:6]};
wire [7:0] h2_r10_0_1 = {h2_base10_1[7:6], h2_base10_1[5:4], h2_base10_1[3:2], h2_base10_1[1:0]};
wire [7:0] h2_r10_1_1 = {h2_base10_1[1:0], h2_base10_1[7:6], h2_base10_1[5:4], h2_base10_1[3:2]};
wire [7:0] h2_r10_2_1 = {h2_base10_1[3:2], h2_base10_1[1:0], h2_base10_1[7:6], h2_base10_1[5:4]};
wire [7:0] h2_r10_3_1 = {h2_base10_1[5:4], h2_base10_1[3:2], h2_base10_1[1:0], h2_base10_1[7:6]};
wire [7:0] h2_r11_0_1 = {h2_base11_1[7:6], h2_base11_1[5:4], h2_base11_1[3:2], h2_base11_1[1:0]};
wire [7:0] h2_r11_1_1 = {h2_base11_1[1:0], h2_base11_1[7:6], h2_base11_1[5:4], h2_base11_1[3:2]};
wire [7:0] h2_r11_2_1 = {h2_base11_1[3:2], h2_base11_1[1:0], h2_base11_1[7:6], h2_base11_1[5:4]};
wire [7:0] h2_r11_3_1 = {h2_base11_1[5:4], h2_base11_1[3:2], h2_base11_1[1:0], h2_base11_1[7:6]};
wire [7:0] h2_r12_0_1 = {h2_base12_1[7:6], h2_base12_1[5:4], h2_base12_1[3:2], h2_base12_1[1:0]};
wire [7:0] h2_r12_1_1 = {h2_base12_1[1:0], h2_base12_1[7:6], h2_base12_1[5:4], h2_base12_1[3:2]};
wire [7:0] h2_r12_2_1 = {h2_base12_1[3:2], h2_base12_1[1:0], h2_base12_1[7:6], h2_base12_1[5:4]};
wire [7:0] h2_r12_3_1 = {h2_base12_1[5:4], h2_base12_1[3:2], h2_base12_1[1:0], h2_base12_1[7:6]};
wire [7:0] h2_r13_0_1 = {h2_base13_1[7:6], h2_base13_1[5:4], h2_base13_1[3:2], h2_base13_1[1:0]};
wire [7:0] h2_r13_1_1 = {h2_base13_1[1:0], h2_base13_1[7:6], h2_base13_1[5:4], h2_base13_1[3:2]};
wire [7:0] h2_r13_2_1 = {h2_base13_1[3:2], h2_base13_1[1:0], h2_base13_1[7:6], h2_base13_1[5:4]};
wire [7:0] h2_r13_3_1 = {h2_base13_1[5:4], h2_base13_1[3:2], h2_base13_1[1:0], h2_base13_1[7:6]};
wire [7:0] h2_r14_0_1 = {h2_base14_1[7:6], h2_base14_1[5:4], h2_base14_1[3:2], h2_base14_1[1:0]};
wire [7:0] h2_r14_1_1 = {h2_base14_1[1:0], h2_base14_1[7:6], h2_base14_1[5:4], h2_base14_1[3:2]};
wire [7:0] h2_r14_2_1 = {h2_base14_1[3:2], h2_base14_1[1:0], h2_base14_1[7:6], h2_base14_1[5:4]};
wire [7:0] h2_r14_3_1 = {h2_base14_1[5:4], h2_base14_1[3:2], h2_base14_1[1:0], h2_base14_1[7:6]};
wire [7:0] h2_r15_0_1 = {h2_base15_1[7:6], h2_base15_1[5:4], h2_base15_1[3:2], h2_base15_1[1:0]};
wire [7:0] h2_r15_1_1 = {h2_base15_1[1:0], h2_base15_1[7:6], h2_base15_1[5:4], h2_base15_1[3:2]};
wire [7:0] h2_r15_2_1 = {h2_base15_1[3:2], h2_base15_1[1:0], h2_base15_1[7:6], h2_base15_1[5:4]};
wire [7:0] h2_r15_3_1 = {h2_base15_1[5:4], h2_base15_1[3:2], h2_base15_1[1:0], h2_base15_1[7:6]};
always @* begin
    case (h2_ctrl_1)
        6'd0: h2_y_1 = h2_r0_0_1;
        6'd1: h2_y_1 = h2_r0_1_1;
        6'd2: h2_y_1 = h2_r0_2_1;
        6'd3: h2_y_1 = h2_r0_3_1;
        6'd4: h2_y_1 = h2_r1_0_1;
        6'd5: h2_y_1 = h2_r1_1_1;
        6'd6: h2_y_1 = h2_r1_2_1;
        6'd7: h2_y_1 = h2_r1_3_1;
        6'd8: h2_y_1 = h2_r2_0_1;
        6'd9: h2_y_1 = h2_r2_1_1;
        6'd10: h2_y_1 = h2_r2_2_1;
        6'd11: h2_y_1 = h2_r2_3_1;
        6'd12: h2_y_1 = h2_r3_0_1;
        6'd13: h2_y_1 = h2_r3_1_1;
        6'd14: h2_y_1 = h2_r3_2_1;
        6'd15: h2_y_1 = h2_r3_3_1;
        6'd16: h2_y_1 = h2_r4_0_1;
        6'd17: h2_y_1 = h2_r4_1_1;
        6'd18: h2_y_1 = h2_r4_2_1;
        6'd19: h2_y_1 = h2_r4_3_1;
        6'd20: h2_y_1 = h2_r5_0_1;
        6'd21: h2_y_1 = h2_r5_1_1;
        6'd22: h2_y_1 = h2_r5_2_1;
        6'd23: h2_y_1 = h2_r5_3_1;
        6'd24: h2_y_1 = h2_r6_0_1;
        6'd25: h2_y_1 = h2_r6_1_1;
        6'd26: h2_y_1 = h2_r6_2_1;
        6'd27: h2_y_1 = h2_r6_3_1;
        6'd28: h2_y_1 = h2_r7_0_1;
        6'd29: h2_y_1 = h2_r7_1_1;
        6'd30: h2_y_1 = h2_r7_2_1;
        6'd31: h2_y_1 = h2_r7_3_1;
        6'd32: h2_y_1 = h2_r8_0_1;
        6'd33: h2_y_1 = h2_r8_1_1;
        6'd34: h2_y_1 = h2_r8_2_1;
        6'd35: h2_y_1 = h2_r8_3_1;
        6'd36: h2_y_1 = h2_r9_0_1;
        6'd37: h2_y_1 = h2_r9_1_1;
        6'd38: h2_y_1 = h2_r9_2_1;
        6'd39: h2_y_1 = h2_r9_3_1;
        6'd40: h2_y_1 = h2_r10_0_1;
        6'd41: h2_y_1 = h2_r10_1_1;
        6'd42: h2_y_1 = h2_r10_2_1;
        6'd43: h2_y_1 = h2_r10_3_1;
        6'd44: h2_y_1 = h2_r11_0_1;
        6'd45: h2_y_1 = h2_r11_1_1;
        6'd46: h2_y_1 = h2_r11_2_1;
        6'd47: h2_y_1 = h2_r11_3_1;
        6'd48: h2_y_1 = h2_r12_0_1;
        6'd49: h2_y_1 = h2_r12_1_1;
        6'd50: h2_y_1 = h2_r12_2_1;
        6'd51: h2_y_1 = h2_r12_3_1;
        6'd52: h2_y_1 = h2_r13_0_1;
        6'd53: h2_y_1 = h2_r13_1_1;
        6'd54: h2_y_1 = h2_r13_2_1;
        6'd55: h2_y_1 = h2_r13_3_1;
        6'd56: h2_y_1 = h2_r14_0_1;
        6'd57: h2_y_1 = h2_r14_1_1;
        6'd58: h2_y_1 = h2_r14_2_1;
        6'd59: h2_y_1 = h2_r14_3_1;
        6'd60: h2_y_1 = h2_r15_0_1;
        6'd61: h2_y_1 = h2_r15_1_1;
        6'd62: h2_y_1 = h2_r15_2_1;
        6'd63: h2_y_1 = h2_r15_3_1;
        default: h2_y_1 = 8'b0;
    endcase
end
assign h2_out[8 +: 8] = h2_y_1;

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

wire [5:0] h2_ctrl_4 = h2_ctrl[24 +: 6];
wire [127:0] h2_data_4 = h2_data[512 +: 128];
reg [7:0] h2_y_4;

wire [7:0] h2_base0_4 = h2_data_4[7:0];
wire [7:0] h2_base1_4 = h2_data_4[15:8];
wire [7:0] h2_base2_4 = h2_data_4[23:16];
wire [7:0] h2_base3_4 = h2_data_4[31:24];
wire [7:0] h2_base4_4 = h2_data_4[39:32];
wire [7:0] h2_base5_4 = h2_data_4[47:40];
wire [7:0] h2_base6_4 = h2_data_4[55:48];
wire [7:0] h2_base7_4 = h2_data_4[63:56];
wire [7:0] h2_base8_4 = h2_data_4[71:64];
wire [7:0] h2_base9_4 = h2_data_4[79:72];
wire [7:0] h2_base10_4 = h2_data_4[87:80];
wire [7:0] h2_base11_4 = h2_data_4[95:88];
wire [7:0] h2_base12_4 = h2_data_4[103:96];
wire [7:0] h2_base13_4 = h2_data_4[111:104];
wire [7:0] h2_base14_4 = h2_data_4[119:112];
wire [7:0] h2_base15_4 = h2_data_4[127:120];
wire [7:0] h2_r0_0_4 = {h2_base0_4[7:6], h2_base0_4[5:4], h2_base0_4[3:2], h2_base0_4[1:0]};
wire [7:0] h2_r0_1_4 = {h2_base0_4[1:0], h2_base0_4[7:6], h2_base0_4[5:4], h2_base0_4[3:2]};
wire [7:0] h2_r0_2_4 = {h2_base0_4[3:2], h2_base0_4[1:0], h2_base0_4[7:6], h2_base0_4[5:4]};
wire [7:0] h2_r0_3_4 = {h2_base0_4[5:4], h2_base0_4[3:2], h2_base0_4[1:0], h2_base0_4[7:6]};
wire [7:0] h2_r1_0_4 = {h2_base1_4[7:6], h2_base1_4[5:4], h2_base1_4[3:2], h2_base1_4[1:0]};
wire [7:0] h2_r1_1_4 = {h2_base1_4[1:0], h2_base1_4[7:6], h2_base1_4[5:4], h2_base1_4[3:2]};
wire [7:0] h2_r1_2_4 = {h2_base1_4[3:2], h2_base1_4[1:0], h2_base1_4[7:6], h2_base1_4[5:4]};
wire [7:0] h2_r1_3_4 = {h2_base1_4[5:4], h2_base1_4[3:2], h2_base1_4[1:0], h2_base1_4[7:6]};
wire [7:0] h2_r2_0_4 = {h2_base2_4[7:6], h2_base2_4[5:4], h2_base2_4[3:2], h2_base2_4[1:0]};
wire [7:0] h2_r2_1_4 = {h2_base2_4[1:0], h2_base2_4[7:6], h2_base2_4[5:4], h2_base2_4[3:2]};
wire [7:0] h2_r2_2_4 = {h2_base2_4[3:2], h2_base2_4[1:0], h2_base2_4[7:6], h2_base2_4[5:4]};
wire [7:0] h2_r2_3_4 = {h2_base2_4[5:4], h2_base2_4[3:2], h2_base2_4[1:0], h2_base2_4[7:6]};
wire [7:0] h2_r3_0_4 = {h2_base3_4[7:6], h2_base3_4[5:4], h2_base3_4[3:2], h2_base3_4[1:0]};
wire [7:0] h2_r3_1_4 = {h2_base3_4[1:0], h2_base3_4[7:6], h2_base3_4[5:4], h2_base3_4[3:2]};
wire [7:0] h2_r3_2_4 = {h2_base3_4[3:2], h2_base3_4[1:0], h2_base3_4[7:6], h2_base3_4[5:4]};
wire [7:0] h2_r3_3_4 = {h2_base3_4[5:4], h2_base3_4[3:2], h2_base3_4[1:0], h2_base3_4[7:6]};
wire [7:0] h2_r4_0_4 = {h2_base4_4[7:6], h2_base4_4[5:4], h2_base4_4[3:2], h2_base4_4[1:0]};
wire [7:0] h2_r4_1_4 = {h2_base4_4[1:0], h2_base4_4[7:6], h2_base4_4[5:4], h2_base4_4[3:2]};
wire [7:0] h2_r4_2_4 = {h2_base4_4[3:2], h2_base4_4[1:0], h2_base4_4[7:6], h2_base4_4[5:4]};
wire [7:0] h2_r4_3_4 = {h2_base4_4[5:4], h2_base4_4[3:2], h2_base4_4[1:0], h2_base4_4[7:6]};
wire [7:0] h2_r5_0_4 = {h2_base5_4[7:6], h2_base5_4[5:4], h2_base5_4[3:2], h2_base5_4[1:0]};
wire [7:0] h2_r5_1_4 = {h2_base5_4[1:0], h2_base5_4[7:6], h2_base5_4[5:4], h2_base5_4[3:2]};
wire [7:0] h2_r5_2_4 = {h2_base5_4[3:2], h2_base5_4[1:0], h2_base5_4[7:6], h2_base5_4[5:4]};
wire [7:0] h2_r5_3_4 = {h2_base5_4[5:4], h2_base5_4[3:2], h2_base5_4[1:0], h2_base5_4[7:6]};
wire [7:0] h2_r6_0_4 = {h2_base6_4[7:6], h2_base6_4[5:4], h2_base6_4[3:2], h2_base6_4[1:0]};
wire [7:0] h2_r6_1_4 = {h2_base6_4[1:0], h2_base6_4[7:6], h2_base6_4[5:4], h2_base6_4[3:2]};
wire [7:0] h2_r6_2_4 = {h2_base6_4[3:2], h2_base6_4[1:0], h2_base6_4[7:6], h2_base6_4[5:4]};
wire [7:0] h2_r6_3_4 = {h2_base6_4[5:4], h2_base6_4[3:2], h2_base6_4[1:0], h2_base6_4[7:6]};
wire [7:0] h2_r7_0_4 = {h2_base7_4[7:6], h2_base7_4[5:4], h2_base7_4[3:2], h2_base7_4[1:0]};
wire [7:0] h2_r7_1_4 = {h2_base7_4[1:0], h2_base7_4[7:6], h2_base7_4[5:4], h2_base7_4[3:2]};
wire [7:0] h2_r7_2_4 = {h2_base7_4[3:2], h2_base7_4[1:0], h2_base7_4[7:6], h2_base7_4[5:4]};
wire [7:0] h2_r7_3_4 = {h2_base7_4[5:4], h2_base7_4[3:2], h2_base7_4[1:0], h2_base7_4[7:6]};
wire [7:0] h2_r8_0_4 = {h2_base8_4[7:6], h2_base8_4[5:4], h2_base8_4[3:2], h2_base8_4[1:0]};
wire [7:0] h2_r8_1_4 = {h2_base8_4[1:0], h2_base8_4[7:6], h2_base8_4[5:4], h2_base8_4[3:2]};
wire [7:0] h2_r8_2_4 = {h2_base8_4[3:2], h2_base8_4[1:0], h2_base8_4[7:6], h2_base8_4[5:4]};
wire [7:0] h2_r8_3_4 = {h2_base8_4[5:4], h2_base8_4[3:2], h2_base8_4[1:0], h2_base8_4[7:6]};
wire [7:0] h2_r9_0_4 = {h2_base9_4[7:6], h2_base9_4[5:4], h2_base9_4[3:2], h2_base9_4[1:0]};
wire [7:0] h2_r9_1_4 = {h2_base9_4[1:0], h2_base9_4[7:6], h2_base9_4[5:4], h2_base9_4[3:2]};
wire [7:0] h2_r9_2_4 = {h2_base9_4[3:2], h2_base9_4[1:0], h2_base9_4[7:6], h2_base9_4[5:4]};
wire [7:0] h2_r9_3_4 = {h2_base9_4[5:4], h2_base9_4[3:2], h2_base9_4[1:0], h2_base9_4[7:6]};
wire [7:0] h2_r10_0_4 = {h2_base10_4[7:6], h2_base10_4[5:4], h2_base10_4[3:2], h2_base10_4[1:0]};
wire [7:0] h2_r10_1_4 = {h2_base10_4[1:0], h2_base10_4[7:6], h2_base10_4[5:4], h2_base10_4[3:2]};
wire [7:0] h2_r10_2_4 = {h2_base10_4[3:2], h2_base10_4[1:0], h2_base10_4[7:6], h2_base10_4[5:4]};
wire [7:0] h2_r10_3_4 = {h2_base10_4[5:4], h2_base10_4[3:2], h2_base10_4[1:0], h2_base10_4[7:6]};
wire [7:0] h2_r11_0_4 = {h2_base11_4[7:6], h2_base11_4[5:4], h2_base11_4[3:2], h2_base11_4[1:0]};
wire [7:0] h2_r11_1_4 = {h2_base11_4[1:0], h2_base11_4[7:6], h2_base11_4[5:4], h2_base11_4[3:2]};
wire [7:0] h2_r11_2_4 = {h2_base11_4[3:2], h2_base11_4[1:0], h2_base11_4[7:6], h2_base11_4[5:4]};
wire [7:0] h2_r11_3_4 = {h2_base11_4[5:4], h2_base11_4[3:2], h2_base11_4[1:0], h2_base11_4[7:6]};
wire [7:0] h2_r12_0_4 = {h2_base12_4[7:6], h2_base12_4[5:4], h2_base12_4[3:2], h2_base12_4[1:0]};
wire [7:0] h2_r12_1_4 = {h2_base12_4[1:0], h2_base12_4[7:6], h2_base12_4[5:4], h2_base12_4[3:2]};
wire [7:0] h2_r12_2_4 = {h2_base12_4[3:2], h2_base12_4[1:0], h2_base12_4[7:6], h2_base12_4[5:4]};
wire [7:0] h2_r12_3_4 = {h2_base12_4[5:4], h2_base12_4[3:2], h2_base12_4[1:0], h2_base12_4[7:6]};
wire [7:0] h2_r13_0_4 = {h2_base13_4[7:6], h2_base13_4[5:4], h2_base13_4[3:2], h2_base13_4[1:0]};
wire [7:0] h2_r13_1_4 = {h2_base13_4[1:0], h2_base13_4[7:6], h2_base13_4[5:4], h2_base13_4[3:2]};
wire [7:0] h2_r13_2_4 = {h2_base13_4[3:2], h2_base13_4[1:0], h2_base13_4[7:6], h2_base13_4[5:4]};
wire [7:0] h2_r13_3_4 = {h2_base13_4[5:4], h2_base13_4[3:2], h2_base13_4[1:0], h2_base13_4[7:6]};
wire [7:0] h2_r14_0_4 = {h2_base14_4[7:6], h2_base14_4[5:4], h2_base14_4[3:2], h2_base14_4[1:0]};
wire [7:0] h2_r14_1_4 = {h2_base14_4[1:0], h2_base14_4[7:6], h2_base14_4[5:4], h2_base14_4[3:2]};
wire [7:0] h2_r14_2_4 = {h2_base14_4[3:2], h2_base14_4[1:0], h2_base14_4[7:6], h2_base14_4[5:4]};
wire [7:0] h2_r14_3_4 = {h2_base14_4[5:4], h2_base14_4[3:2], h2_base14_4[1:0], h2_base14_4[7:6]};
wire [7:0] h2_r15_0_4 = {h2_base15_4[7:6], h2_base15_4[5:4], h2_base15_4[3:2], h2_base15_4[1:0]};
wire [7:0] h2_r15_1_4 = {h2_base15_4[1:0], h2_base15_4[7:6], h2_base15_4[5:4], h2_base15_4[3:2]};
wire [7:0] h2_r15_2_4 = {h2_base15_4[3:2], h2_base15_4[1:0], h2_base15_4[7:6], h2_base15_4[5:4]};
wire [7:0] h2_r15_3_4 = {h2_base15_4[5:4], h2_base15_4[3:2], h2_base15_4[1:0], h2_base15_4[7:6]};
always @* begin
    case (h2_ctrl_4)
        6'd0: h2_y_4 = h2_r0_0_4;
        6'd1: h2_y_4 = h2_r0_1_4;
        6'd2: h2_y_4 = h2_r0_2_4;
        6'd3: h2_y_4 = h2_r0_3_4;
        6'd4: h2_y_4 = h2_r1_0_4;
        6'd5: h2_y_4 = h2_r1_1_4;
        6'd6: h2_y_4 = h2_r1_2_4;
        6'd7: h2_y_4 = h2_r1_3_4;
        6'd8: h2_y_4 = h2_r2_0_4;
        6'd9: h2_y_4 = h2_r2_1_4;
        6'd10: h2_y_4 = h2_r2_2_4;
        6'd11: h2_y_4 = h2_r2_3_4;
        6'd12: h2_y_4 = h2_r3_0_4;
        6'd13: h2_y_4 = h2_r3_1_4;
        6'd14: h2_y_4 = h2_r3_2_4;
        6'd15: h2_y_4 = h2_r3_3_4;
        6'd16: h2_y_4 = h2_r4_0_4;
        6'd17: h2_y_4 = h2_r4_1_4;
        6'd18: h2_y_4 = h2_r4_2_4;
        6'd19: h2_y_4 = h2_r4_3_4;
        6'd20: h2_y_4 = h2_r5_0_4;
        6'd21: h2_y_4 = h2_r5_1_4;
        6'd22: h2_y_4 = h2_r5_2_4;
        6'd23: h2_y_4 = h2_r5_3_4;
        6'd24: h2_y_4 = h2_r6_0_4;
        6'd25: h2_y_4 = h2_r6_1_4;
        6'd26: h2_y_4 = h2_r6_2_4;
        6'd27: h2_y_4 = h2_r6_3_4;
        6'd28: h2_y_4 = h2_r7_0_4;
        6'd29: h2_y_4 = h2_r7_1_4;
        6'd30: h2_y_4 = h2_r7_2_4;
        6'd31: h2_y_4 = h2_r7_3_4;
        6'd32: h2_y_4 = h2_r8_0_4;
        6'd33: h2_y_4 = h2_r8_1_4;
        6'd34: h2_y_4 = h2_r8_2_4;
        6'd35: h2_y_4 = h2_r8_3_4;
        6'd36: h2_y_4 = h2_r9_0_4;
        6'd37: h2_y_4 = h2_r9_1_4;
        6'd38: h2_y_4 = h2_r9_2_4;
        6'd39: h2_y_4 = h2_r9_3_4;
        6'd40: h2_y_4 = h2_r10_0_4;
        6'd41: h2_y_4 = h2_r10_1_4;
        6'd42: h2_y_4 = h2_r10_2_4;
        6'd43: h2_y_4 = h2_r10_3_4;
        6'd44: h2_y_4 = h2_r11_0_4;
        6'd45: h2_y_4 = h2_r11_1_4;
        6'd46: h2_y_4 = h2_r11_2_4;
        6'd47: h2_y_4 = h2_r11_3_4;
        6'd48: h2_y_4 = h2_r12_0_4;
        6'd49: h2_y_4 = h2_r12_1_4;
        6'd50: h2_y_4 = h2_r12_2_4;
        6'd51: h2_y_4 = h2_r12_3_4;
        6'd52: h2_y_4 = h2_r13_0_4;
        6'd53: h2_y_4 = h2_r13_1_4;
        6'd54: h2_y_4 = h2_r13_2_4;
        6'd55: h2_y_4 = h2_r13_3_4;
        6'd56: h2_y_4 = h2_r14_0_4;
        6'd57: h2_y_4 = h2_r14_1_4;
        6'd58: h2_y_4 = h2_r14_2_4;
        6'd59: h2_y_4 = h2_r14_3_4;
        6'd60: h2_y_4 = h2_r15_0_4;
        6'd61: h2_y_4 = h2_r15_1_4;
        6'd62: h2_y_4 = h2_r15_2_4;
        6'd63: h2_y_4 = h2_r15_3_4;
        default: h2_y_4 = 8'b0;
    endcase
end
assign h2_out[32 +: 8] = h2_y_4;

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

wire [5:0] h2_ctrl_5 = h2_ctrl[30 +: 6];
wire [127:0] h2_data_5 = h2_data[640 +: 128];
reg [7:0] h2_y_5;

wire [7:0] h2_base0_5 = h2_data_5[7:0];
wire [7:0] h2_base1_5 = h2_data_5[15:8];
wire [7:0] h2_base2_5 = h2_data_5[23:16];
wire [7:0] h2_base3_5 = h2_data_5[31:24];
wire [7:0] h2_base4_5 = h2_data_5[39:32];
wire [7:0] h2_base5_5 = h2_data_5[47:40];
wire [7:0] h2_base6_5 = h2_data_5[55:48];
wire [7:0] h2_base7_5 = h2_data_5[63:56];
wire [7:0] h2_base8_5 = h2_data_5[71:64];
wire [7:0] h2_base9_5 = h2_data_5[79:72];
wire [7:0] h2_base10_5 = h2_data_5[87:80];
wire [7:0] h2_base11_5 = h2_data_5[95:88];
wire [7:0] h2_base12_5 = h2_data_5[103:96];
wire [7:0] h2_base13_5 = h2_data_5[111:104];
wire [7:0] h2_base14_5 = h2_data_5[119:112];
wire [7:0] h2_base15_5 = h2_data_5[127:120];
wire [7:0] h2_r0_0_5 = {h2_base0_5[7:6], h2_base0_5[5:4], h2_base0_5[3:2], h2_base0_5[1:0]};
wire [7:0] h2_r0_1_5 = {h2_base0_5[1:0], h2_base0_5[7:6], h2_base0_5[5:4], h2_base0_5[3:2]};
wire [7:0] h2_r0_2_5 = {h2_base0_5[3:2], h2_base0_5[1:0], h2_base0_5[7:6], h2_base0_5[5:4]};
wire [7:0] h2_r0_3_5 = {h2_base0_5[5:4], h2_base0_5[3:2], h2_base0_5[1:0], h2_base0_5[7:6]};
wire [7:0] h2_r1_0_5 = {h2_base1_5[7:6], h2_base1_5[5:4], h2_base1_5[3:2], h2_base1_5[1:0]};
wire [7:0] h2_r1_1_5 = {h2_base1_5[1:0], h2_base1_5[7:6], h2_base1_5[5:4], h2_base1_5[3:2]};
wire [7:0] h2_r1_2_5 = {h2_base1_5[3:2], h2_base1_5[1:0], h2_base1_5[7:6], h2_base1_5[5:4]};
wire [7:0] h2_r1_3_5 = {h2_base1_5[5:4], h2_base1_5[3:2], h2_base1_5[1:0], h2_base1_5[7:6]};
wire [7:0] h2_r2_0_5 = {h2_base2_5[7:6], h2_base2_5[5:4], h2_base2_5[3:2], h2_base2_5[1:0]};
wire [7:0] h2_r2_1_5 = {h2_base2_5[1:0], h2_base2_5[7:6], h2_base2_5[5:4], h2_base2_5[3:2]};
wire [7:0] h2_r2_2_5 = {h2_base2_5[3:2], h2_base2_5[1:0], h2_base2_5[7:6], h2_base2_5[5:4]};
wire [7:0] h2_r2_3_5 = {h2_base2_5[5:4], h2_base2_5[3:2], h2_base2_5[1:0], h2_base2_5[7:6]};
wire [7:0] h2_r3_0_5 = {h2_base3_5[7:6], h2_base3_5[5:4], h2_base3_5[3:2], h2_base3_5[1:0]};
wire [7:0] h2_r3_1_5 = {h2_base3_5[1:0], h2_base3_5[7:6], h2_base3_5[5:4], h2_base3_5[3:2]};
wire [7:0] h2_r3_2_5 = {h2_base3_5[3:2], h2_base3_5[1:0], h2_base3_5[7:6], h2_base3_5[5:4]};
wire [7:0] h2_r3_3_5 = {h2_base3_5[5:4], h2_base3_5[3:2], h2_base3_5[1:0], h2_base3_5[7:6]};
wire [7:0] h2_r4_0_5 = {h2_base4_5[7:6], h2_base4_5[5:4], h2_base4_5[3:2], h2_base4_5[1:0]};
wire [7:0] h2_r4_1_5 = {h2_base4_5[1:0], h2_base4_5[7:6], h2_base4_5[5:4], h2_base4_5[3:2]};
wire [7:0] h2_r4_2_5 = {h2_base4_5[3:2], h2_base4_5[1:0], h2_base4_5[7:6], h2_base4_5[5:4]};
wire [7:0] h2_r4_3_5 = {h2_base4_5[5:4], h2_base4_5[3:2], h2_base4_5[1:0], h2_base4_5[7:6]};
wire [7:0] h2_r5_0_5 = {h2_base5_5[7:6], h2_base5_5[5:4], h2_base5_5[3:2], h2_base5_5[1:0]};
wire [7:0] h2_r5_1_5 = {h2_base5_5[1:0], h2_base5_5[7:6], h2_base5_5[5:4], h2_base5_5[3:2]};
wire [7:0] h2_r5_2_5 = {h2_base5_5[3:2], h2_base5_5[1:0], h2_base5_5[7:6], h2_base5_5[5:4]};
wire [7:0] h2_r5_3_5 = {h2_base5_5[5:4], h2_base5_5[3:2], h2_base5_5[1:0], h2_base5_5[7:6]};
wire [7:0] h2_r6_0_5 = {h2_base6_5[7:6], h2_base6_5[5:4], h2_base6_5[3:2], h2_base6_5[1:0]};
wire [7:0] h2_r6_1_5 = {h2_base6_5[1:0], h2_base6_5[7:6], h2_base6_5[5:4], h2_base6_5[3:2]};
wire [7:0] h2_r6_2_5 = {h2_base6_5[3:2], h2_base6_5[1:0], h2_base6_5[7:6], h2_base6_5[5:4]};
wire [7:0] h2_r6_3_5 = {h2_base6_5[5:4], h2_base6_5[3:2], h2_base6_5[1:0], h2_base6_5[7:6]};
wire [7:0] h2_r7_0_5 = {h2_base7_5[7:6], h2_base7_5[5:4], h2_base7_5[3:2], h2_base7_5[1:0]};
wire [7:0] h2_r7_1_5 = {h2_base7_5[1:0], h2_base7_5[7:6], h2_base7_5[5:4], h2_base7_5[3:2]};
wire [7:0] h2_r7_2_5 = {h2_base7_5[3:2], h2_base7_5[1:0], h2_base7_5[7:6], h2_base7_5[5:4]};
wire [7:0] h2_r7_3_5 = {h2_base7_5[5:4], h2_base7_5[3:2], h2_base7_5[1:0], h2_base7_5[7:6]};
wire [7:0] h2_r8_0_5 = {h2_base8_5[7:6], h2_base8_5[5:4], h2_base8_5[3:2], h2_base8_5[1:0]};
wire [7:0] h2_r8_1_5 = {h2_base8_5[1:0], h2_base8_5[7:6], h2_base8_5[5:4], h2_base8_5[3:2]};
wire [7:0] h2_r8_2_5 = {h2_base8_5[3:2], h2_base8_5[1:0], h2_base8_5[7:6], h2_base8_5[5:4]};
wire [7:0] h2_r8_3_5 = {h2_base8_5[5:4], h2_base8_5[3:2], h2_base8_5[1:0], h2_base8_5[7:6]};
wire [7:0] h2_r9_0_5 = {h2_base9_5[7:6], h2_base9_5[5:4], h2_base9_5[3:2], h2_base9_5[1:0]};
wire [7:0] h2_r9_1_5 = {h2_base9_5[1:0], h2_base9_5[7:6], h2_base9_5[5:4], h2_base9_5[3:2]};
wire [7:0] h2_r9_2_5 = {h2_base9_5[3:2], h2_base9_5[1:0], h2_base9_5[7:6], h2_base9_5[5:4]};
wire [7:0] h2_r9_3_5 = {h2_base9_5[5:4], h2_base9_5[3:2], h2_base9_5[1:0], h2_base9_5[7:6]};
wire [7:0] h2_r10_0_5 = {h2_base10_5[7:6], h2_base10_5[5:4], h2_base10_5[3:2], h2_base10_5[1:0]};
wire [7:0] h2_r10_1_5 = {h2_base10_5[1:0], h2_base10_5[7:6], h2_base10_5[5:4], h2_base10_5[3:2]};
wire [7:0] h2_r10_2_5 = {h2_base10_5[3:2], h2_base10_5[1:0], h2_base10_5[7:6], h2_base10_5[5:4]};
wire [7:0] h2_r10_3_5 = {h2_base10_5[5:4], h2_base10_5[3:2], h2_base10_5[1:0], h2_base10_5[7:6]};
wire [7:0] h2_r11_0_5 = {h2_base11_5[7:6], h2_base11_5[5:4], h2_base11_5[3:2], h2_base11_5[1:0]};
wire [7:0] h2_r11_1_5 = {h2_base11_5[1:0], h2_base11_5[7:6], h2_base11_5[5:4], h2_base11_5[3:2]};
wire [7:0] h2_r11_2_5 = {h2_base11_5[3:2], h2_base11_5[1:0], h2_base11_5[7:6], h2_base11_5[5:4]};
wire [7:0] h2_r11_3_5 = {h2_base11_5[5:4], h2_base11_5[3:2], h2_base11_5[1:0], h2_base11_5[7:6]};
wire [7:0] h2_r12_0_5 = {h2_base12_5[7:6], h2_base12_5[5:4], h2_base12_5[3:2], h2_base12_5[1:0]};
wire [7:0] h2_r12_1_5 = {h2_base12_5[1:0], h2_base12_5[7:6], h2_base12_5[5:4], h2_base12_5[3:2]};
wire [7:0] h2_r12_2_5 = {h2_base12_5[3:2], h2_base12_5[1:0], h2_base12_5[7:6], h2_base12_5[5:4]};
wire [7:0] h2_r12_3_5 = {h2_base12_5[5:4], h2_base12_5[3:2], h2_base12_5[1:0], h2_base12_5[7:6]};
wire [7:0] h2_r13_0_5 = {h2_base13_5[7:6], h2_base13_5[5:4], h2_base13_5[3:2], h2_base13_5[1:0]};
wire [7:0] h2_r13_1_5 = {h2_base13_5[1:0], h2_base13_5[7:6], h2_base13_5[5:4], h2_base13_5[3:2]};
wire [7:0] h2_r13_2_5 = {h2_base13_5[3:2], h2_base13_5[1:0], h2_base13_5[7:6], h2_base13_5[5:4]};
wire [7:0] h2_r13_3_5 = {h2_base13_5[5:4], h2_base13_5[3:2], h2_base13_5[1:0], h2_base13_5[7:6]};
wire [7:0] h2_r14_0_5 = {h2_base14_5[7:6], h2_base14_5[5:4], h2_base14_5[3:2], h2_base14_5[1:0]};
wire [7:0] h2_r14_1_5 = {h2_base14_5[1:0], h2_base14_5[7:6], h2_base14_5[5:4], h2_base14_5[3:2]};
wire [7:0] h2_r14_2_5 = {h2_base14_5[3:2], h2_base14_5[1:0], h2_base14_5[7:6], h2_base14_5[5:4]};
wire [7:0] h2_r14_3_5 = {h2_base14_5[5:4], h2_base14_5[3:2], h2_base14_5[1:0], h2_base14_5[7:6]};
wire [7:0] h2_r15_0_5 = {h2_base15_5[7:6], h2_base15_5[5:4], h2_base15_5[3:2], h2_base15_5[1:0]};
wire [7:0] h2_r15_1_5 = {h2_base15_5[1:0], h2_base15_5[7:6], h2_base15_5[5:4], h2_base15_5[3:2]};
wire [7:0] h2_r15_2_5 = {h2_base15_5[3:2], h2_base15_5[1:0], h2_base15_5[7:6], h2_base15_5[5:4]};
wire [7:0] h2_r15_3_5 = {h2_base15_5[5:4], h2_base15_5[3:2], h2_base15_5[1:0], h2_base15_5[7:6]};
always @* begin
    case (h2_ctrl_5)
        6'd0: h2_y_5 = h2_r0_0_5;
        6'd1: h2_y_5 = h2_r0_1_5;
        6'd2: h2_y_5 = h2_r0_2_5;
        6'd3: h2_y_5 = h2_r0_3_5;
        6'd4: h2_y_5 = h2_r1_0_5;
        6'd5: h2_y_5 = h2_r1_1_5;
        6'd6: h2_y_5 = h2_r1_2_5;
        6'd7: h2_y_5 = h2_r1_3_5;
        6'd8: h2_y_5 = h2_r2_0_5;
        6'd9: h2_y_5 = h2_r2_1_5;
        6'd10: h2_y_5 = h2_r2_2_5;
        6'd11: h2_y_5 = h2_r2_3_5;
        6'd12: h2_y_5 = h2_r3_0_5;
        6'd13: h2_y_5 = h2_r3_1_5;
        6'd14: h2_y_5 = h2_r3_2_5;
        6'd15: h2_y_5 = h2_r3_3_5;
        6'd16: h2_y_5 = h2_r4_0_5;
        6'd17: h2_y_5 = h2_r4_1_5;
        6'd18: h2_y_5 = h2_r4_2_5;
        6'd19: h2_y_5 = h2_r4_3_5;
        6'd20: h2_y_5 = h2_r5_0_5;
        6'd21: h2_y_5 = h2_r5_1_5;
        6'd22: h2_y_5 = h2_r5_2_5;
        6'd23: h2_y_5 = h2_r5_3_5;
        6'd24: h2_y_5 = h2_r6_0_5;
        6'd25: h2_y_5 = h2_r6_1_5;
        6'd26: h2_y_5 = h2_r6_2_5;
        6'd27: h2_y_5 = h2_r6_3_5;
        6'd28: h2_y_5 = h2_r7_0_5;
        6'd29: h2_y_5 = h2_r7_1_5;
        6'd30: h2_y_5 = h2_r7_2_5;
        6'd31: h2_y_5 = h2_r7_3_5;
        6'd32: h2_y_5 = h2_r8_0_5;
        6'd33: h2_y_5 = h2_r8_1_5;
        6'd34: h2_y_5 = h2_r8_2_5;
        6'd35: h2_y_5 = h2_r8_3_5;
        6'd36: h2_y_5 = h2_r9_0_5;
        6'd37: h2_y_5 = h2_r9_1_5;
        6'd38: h2_y_5 = h2_r9_2_5;
        6'd39: h2_y_5 = h2_r9_3_5;
        6'd40: h2_y_5 = h2_r10_0_5;
        6'd41: h2_y_5 = h2_r10_1_5;
        6'd42: h2_y_5 = h2_r10_2_5;
        6'd43: h2_y_5 = h2_r10_3_5;
        6'd44: h2_y_5 = h2_r11_0_5;
        6'd45: h2_y_5 = h2_r11_1_5;
        6'd46: h2_y_5 = h2_r11_2_5;
        6'd47: h2_y_5 = h2_r11_3_5;
        6'd48: h2_y_5 = h2_r12_0_5;
        6'd49: h2_y_5 = h2_r12_1_5;
        6'd50: h2_y_5 = h2_r12_2_5;
        6'd51: h2_y_5 = h2_r12_3_5;
        6'd52: h2_y_5 = h2_r13_0_5;
        6'd53: h2_y_5 = h2_r13_1_5;
        6'd54: h2_y_5 = h2_r13_2_5;
        6'd55: h2_y_5 = h2_r13_3_5;
        6'd56: h2_y_5 = h2_r14_0_5;
        6'd57: h2_y_5 = h2_r14_1_5;
        6'd58: h2_y_5 = h2_r14_2_5;
        6'd59: h2_y_5 = h2_r14_3_5;
        6'd60: h2_y_5 = h2_r15_0_5;
        6'd61: h2_y_5 = h2_r15_1_5;
        6'd62: h2_y_5 = h2_r15_2_5;
        6'd63: h2_y_5 = h2_r15_3_5;
        default: h2_y_5 = 8'b0;
    endcase
end
assign h2_out[40 +: 8] = h2_y_5;

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

wire [5:0] h2_ctrl_2 = h2_ctrl[12 +: 6];
wire [127:0] h2_data_2 = h2_data[256 +: 128];
reg [7:0] h2_y_2;

wire [7:0] h2_base0_2 = h2_data_2[7:0];
wire [7:0] h2_base1_2 = h2_data_2[15:8];
wire [7:0] h2_base2_2 = h2_data_2[23:16];
wire [7:0] h2_base3_2 = h2_data_2[31:24];
wire [7:0] h2_base4_2 = h2_data_2[39:32];
wire [7:0] h2_base5_2 = h2_data_2[47:40];
wire [7:0] h2_base6_2 = h2_data_2[55:48];
wire [7:0] h2_base7_2 = h2_data_2[63:56];
wire [7:0] h2_base8_2 = h2_data_2[71:64];
wire [7:0] h2_base9_2 = h2_data_2[79:72];
wire [7:0] h2_base10_2 = h2_data_2[87:80];
wire [7:0] h2_base11_2 = h2_data_2[95:88];
wire [7:0] h2_base12_2 = h2_data_2[103:96];
wire [7:0] h2_base13_2 = h2_data_2[111:104];
wire [7:0] h2_base14_2 = h2_data_2[119:112];
wire [7:0] h2_base15_2 = h2_data_2[127:120];
wire [7:0] h2_r0_0_2 = {h2_base0_2[7:6], h2_base0_2[5:4], h2_base0_2[3:2], h2_base0_2[1:0]};
wire [7:0] h2_r0_1_2 = {h2_base0_2[1:0], h2_base0_2[7:6], h2_base0_2[5:4], h2_base0_2[3:2]};
wire [7:0] h2_r0_2_2 = {h2_base0_2[3:2], h2_base0_2[1:0], h2_base0_2[7:6], h2_base0_2[5:4]};
wire [7:0] h2_r0_3_2 = {h2_base0_2[5:4], h2_base0_2[3:2], h2_base0_2[1:0], h2_base0_2[7:6]};
wire [7:0] h2_r1_0_2 = {h2_base1_2[7:6], h2_base1_2[5:4], h2_base1_2[3:2], h2_base1_2[1:0]};
wire [7:0] h2_r1_1_2 = {h2_base1_2[1:0], h2_base1_2[7:6], h2_base1_2[5:4], h2_base1_2[3:2]};
wire [7:0] h2_r1_2_2 = {h2_base1_2[3:2], h2_base1_2[1:0], h2_base1_2[7:6], h2_base1_2[5:4]};
wire [7:0] h2_r1_3_2 = {h2_base1_2[5:4], h2_base1_2[3:2], h2_base1_2[1:0], h2_base1_2[7:6]};
wire [7:0] h2_r2_0_2 = {h2_base2_2[7:6], h2_base2_2[5:4], h2_base2_2[3:2], h2_base2_2[1:0]};
wire [7:0] h2_r2_1_2 = {h2_base2_2[1:0], h2_base2_2[7:6], h2_base2_2[5:4], h2_base2_2[3:2]};
wire [7:0] h2_r2_2_2 = {h2_base2_2[3:2], h2_base2_2[1:0], h2_base2_2[7:6], h2_base2_2[5:4]};
wire [7:0] h2_r2_3_2 = {h2_base2_2[5:4], h2_base2_2[3:2], h2_base2_2[1:0], h2_base2_2[7:6]};
wire [7:0] h2_r3_0_2 = {h2_base3_2[7:6], h2_base3_2[5:4], h2_base3_2[3:2], h2_base3_2[1:0]};
wire [7:0] h2_r3_1_2 = {h2_base3_2[1:0], h2_base3_2[7:6], h2_base3_2[5:4], h2_base3_2[3:2]};
wire [7:0] h2_r3_2_2 = {h2_base3_2[3:2], h2_base3_2[1:0], h2_base3_2[7:6], h2_base3_2[5:4]};
wire [7:0] h2_r3_3_2 = {h2_base3_2[5:4], h2_base3_2[3:2], h2_base3_2[1:0], h2_base3_2[7:6]};
wire [7:0] h2_r4_0_2 = {h2_base4_2[7:6], h2_base4_2[5:4], h2_base4_2[3:2], h2_base4_2[1:0]};
wire [7:0] h2_r4_1_2 = {h2_base4_2[1:0], h2_base4_2[7:6], h2_base4_2[5:4], h2_base4_2[3:2]};
wire [7:0] h2_r4_2_2 = {h2_base4_2[3:2], h2_base4_2[1:0], h2_base4_2[7:6], h2_base4_2[5:4]};
wire [7:0] h2_r4_3_2 = {h2_base4_2[5:4], h2_base4_2[3:2], h2_base4_2[1:0], h2_base4_2[7:6]};
wire [7:0] h2_r5_0_2 = {h2_base5_2[7:6], h2_base5_2[5:4], h2_base5_2[3:2], h2_base5_2[1:0]};
wire [7:0] h2_r5_1_2 = {h2_base5_2[1:0], h2_base5_2[7:6], h2_base5_2[5:4], h2_base5_2[3:2]};
wire [7:0] h2_r5_2_2 = {h2_base5_2[3:2], h2_base5_2[1:0], h2_base5_2[7:6], h2_base5_2[5:4]};
wire [7:0] h2_r5_3_2 = {h2_base5_2[5:4], h2_base5_2[3:2], h2_base5_2[1:0], h2_base5_2[7:6]};
wire [7:0] h2_r6_0_2 = {h2_base6_2[7:6], h2_base6_2[5:4], h2_base6_2[3:2], h2_base6_2[1:0]};
wire [7:0] h2_r6_1_2 = {h2_base6_2[1:0], h2_base6_2[7:6], h2_base6_2[5:4], h2_base6_2[3:2]};
wire [7:0] h2_r6_2_2 = {h2_base6_2[3:2], h2_base6_2[1:0], h2_base6_2[7:6], h2_base6_2[5:4]};
wire [7:0] h2_r6_3_2 = {h2_base6_2[5:4], h2_base6_2[3:2], h2_base6_2[1:0], h2_base6_2[7:6]};
wire [7:0] h2_r7_0_2 = {h2_base7_2[7:6], h2_base7_2[5:4], h2_base7_2[3:2], h2_base7_2[1:0]};
wire [7:0] h2_r7_1_2 = {h2_base7_2[1:0], h2_base7_2[7:6], h2_base7_2[5:4], h2_base7_2[3:2]};
wire [7:0] h2_r7_2_2 = {h2_base7_2[3:2], h2_base7_2[1:0], h2_base7_2[7:6], h2_base7_2[5:4]};
wire [7:0] h2_r7_3_2 = {h2_base7_2[5:4], h2_base7_2[3:2], h2_base7_2[1:0], h2_base7_2[7:6]};
wire [7:0] h2_r8_0_2 = {h2_base8_2[7:6], h2_base8_2[5:4], h2_base8_2[3:2], h2_base8_2[1:0]};
wire [7:0] h2_r8_1_2 = {h2_base8_2[1:0], h2_base8_2[7:6], h2_base8_2[5:4], h2_base8_2[3:2]};
wire [7:0] h2_r8_2_2 = {h2_base8_2[3:2], h2_base8_2[1:0], h2_base8_2[7:6], h2_base8_2[5:4]};
wire [7:0] h2_r8_3_2 = {h2_base8_2[5:4], h2_base8_2[3:2], h2_base8_2[1:0], h2_base8_2[7:6]};
wire [7:0] h2_r9_0_2 = {h2_base9_2[7:6], h2_base9_2[5:4], h2_base9_2[3:2], h2_base9_2[1:0]};
wire [7:0] h2_r9_1_2 = {h2_base9_2[1:0], h2_base9_2[7:6], h2_base9_2[5:4], h2_base9_2[3:2]};
wire [7:0] h2_r9_2_2 = {h2_base9_2[3:2], h2_base9_2[1:0], h2_base9_2[7:6], h2_base9_2[5:4]};
wire [7:0] h2_r9_3_2 = {h2_base9_2[5:4], h2_base9_2[3:2], h2_base9_2[1:0], h2_base9_2[7:6]};
wire [7:0] h2_r10_0_2 = {h2_base10_2[7:6], h2_base10_2[5:4], h2_base10_2[3:2], h2_base10_2[1:0]};
wire [7:0] h2_r10_1_2 = {h2_base10_2[1:0], h2_base10_2[7:6], h2_base10_2[5:4], h2_base10_2[3:2]};
wire [7:0] h2_r10_2_2 = {h2_base10_2[3:2], h2_base10_2[1:0], h2_base10_2[7:6], h2_base10_2[5:4]};
wire [7:0] h2_r10_3_2 = {h2_base10_2[5:4], h2_base10_2[3:2], h2_base10_2[1:0], h2_base10_2[7:6]};
wire [7:0] h2_r11_0_2 = {h2_base11_2[7:6], h2_base11_2[5:4], h2_base11_2[3:2], h2_base11_2[1:0]};
wire [7:0] h2_r11_1_2 = {h2_base11_2[1:0], h2_base11_2[7:6], h2_base11_2[5:4], h2_base11_2[3:2]};
wire [7:0] h2_r11_2_2 = {h2_base11_2[3:2], h2_base11_2[1:0], h2_base11_2[7:6], h2_base11_2[5:4]};
wire [7:0] h2_r11_3_2 = {h2_base11_2[5:4], h2_base11_2[3:2], h2_base11_2[1:0], h2_base11_2[7:6]};
wire [7:0] h2_r12_0_2 = {h2_base12_2[7:6], h2_base12_2[5:4], h2_base12_2[3:2], h2_base12_2[1:0]};
wire [7:0] h2_r12_1_2 = {h2_base12_2[1:0], h2_base12_2[7:6], h2_base12_2[5:4], h2_base12_2[3:2]};
wire [7:0] h2_r12_2_2 = {h2_base12_2[3:2], h2_base12_2[1:0], h2_base12_2[7:6], h2_base12_2[5:4]};
wire [7:0] h2_r12_3_2 = {h2_base12_2[5:4], h2_base12_2[3:2], h2_base12_2[1:0], h2_base12_2[7:6]};
wire [7:0] h2_r13_0_2 = {h2_base13_2[7:6], h2_base13_2[5:4], h2_base13_2[3:2], h2_base13_2[1:0]};
wire [7:0] h2_r13_1_2 = {h2_base13_2[1:0], h2_base13_2[7:6], h2_base13_2[5:4], h2_base13_2[3:2]};
wire [7:0] h2_r13_2_2 = {h2_base13_2[3:2], h2_base13_2[1:0], h2_base13_2[7:6], h2_base13_2[5:4]};
wire [7:0] h2_r13_3_2 = {h2_base13_2[5:4], h2_base13_2[3:2], h2_base13_2[1:0], h2_base13_2[7:6]};
wire [7:0] h2_r14_0_2 = {h2_base14_2[7:6], h2_base14_2[5:4], h2_base14_2[3:2], h2_base14_2[1:0]};
wire [7:0] h2_r14_1_2 = {h2_base14_2[1:0], h2_base14_2[7:6], h2_base14_2[5:4], h2_base14_2[3:2]};
wire [7:0] h2_r14_2_2 = {h2_base14_2[3:2], h2_base14_2[1:0], h2_base14_2[7:6], h2_base14_2[5:4]};
wire [7:0] h2_r14_3_2 = {h2_base14_2[5:4], h2_base14_2[3:2], h2_base14_2[1:0], h2_base14_2[7:6]};
wire [7:0] h2_r15_0_2 = {h2_base15_2[7:6], h2_base15_2[5:4], h2_base15_2[3:2], h2_base15_2[1:0]};
wire [7:0] h2_r15_1_2 = {h2_base15_2[1:0], h2_base15_2[7:6], h2_base15_2[5:4], h2_base15_2[3:2]};
wire [7:0] h2_r15_2_2 = {h2_base15_2[3:2], h2_base15_2[1:0], h2_base15_2[7:6], h2_base15_2[5:4]};
wire [7:0] h2_r15_3_2 = {h2_base15_2[5:4], h2_base15_2[3:2], h2_base15_2[1:0], h2_base15_2[7:6]};
always @* begin
    case (h2_ctrl_2)
        6'd0: h2_y_2 = h2_r0_0_2;
        6'd1: h2_y_2 = h2_r0_1_2;
        6'd2: h2_y_2 = h2_r0_2_2;
        6'd3: h2_y_2 = h2_r0_3_2;
        6'd4: h2_y_2 = h2_r1_0_2;
        6'd5: h2_y_2 = h2_r1_1_2;
        6'd6: h2_y_2 = h2_r1_2_2;
        6'd7: h2_y_2 = h2_r1_3_2;
        6'd8: h2_y_2 = h2_r2_0_2;
        6'd9: h2_y_2 = h2_r2_1_2;
        6'd10: h2_y_2 = h2_r2_2_2;
        6'd11: h2_y_2 = h2_r2_3_2;
        6'd12: h2_y_2 = h2_r3_0_2;
        6'd13: h2_y_2 = h2_r3_1_2;
        6'd14: h2_y_2 = h2_r3_2_2;
        6'd15: h2_y_2 = h2_r3_3_2;
        6'd16: h2_y_2 = h2_r4_0_2;
        6'd17: h2_y_2 = h2_r4_1_2;
        6'd18: h2_y_2 = h2_r4_2_2;
        6'd19: h2_y_2 = h2_r4_3_2;
        6'd20: h2_y_2 = h2_r5_0_2;
        6'd21: h2_y_2 = h2_r5_1_2;
        6'd22: h2_y_2 = h2_r5_2_2;
        6'd23: h2_y_2 = h2_r5_3_2;
        6'd24: h2_y_2 = h2_r6_0_2;
        6'd25: h2_y_2 = h2_r6_1_2;
        6'd26: h2_y_2 = h2_r6_2_2;
        6'd27: h2_y_2 = h2_r6_3_2;
        6'd28: h2_y_2 = h2_r7_0_2;
        6'd29: h2_y_2 = h2_r7_1_2;
        6'd30: h2_y_2 = h2_r7_2_2;
        6'd31: h2_y_2 = h2_r7_3_2;
        6'd32: h2_y_2 = h2_r8_0_2;
        6'd33: h2_y_2 = h2_r8_1_2;
        6'd34: h2_y_2 = h2_r8_2_2;
        6'd35: h2_y_2 = h2_r8_3_2;
        6'd36: h2_y_2 = h2_r9_0_2;
        6'd37: h2_y_2 = h2_r9_1_2;
        6'd38: h2_y_2 = h2_r9_2_2;
        6'd39: h2_y_2 = h2_r9_3_2;
        6'd40: h2_y_2 = h2_r10_0_2;
        6'd41: h2_y_2 = h2_r10_1_2;
        6'd42: h2_y_2 = h2_r10_2_2;
        6'd43: h2_y_2 = h2_r10_3_2;
        6'd44: h2_y_2 = h2_r11_0_2;
        6'd45: h2_y_2 = h2_r11_1_2;
        6'd46: h2_y_2 = h2_r11_2_2;
        6'd47: h2_y_2 = h2_r11_3_2;
        6'd48: h2_y_2 = h2_r12_0_2;
        6'd49: h2_y_2 = h2_r12_1_2;
        6'd50: h2_y_2 = h2_r12_2_2;
        6'd51: h2_y_2 = h2_r12_3_2;
        6'd52: h2_y_2 = h2_r13_0_2;
        6'd53: h2_y_2 = h2_r13_1_2;
        6'd54: h2_y_2 = h2_r13_2_2;
        6'd55: h2_y_2 = h2_r13_3_2;
        6'd56: h2_y_2 = h2_r14_0_2;
        6'd57: h2_y_2 = h2_r14_1_2;
        6'd58: h2_y_2 = h2_r14_2_2;
        6'd59: h2_y_2 = h2_r14_3_2;
        6'd60: h2_y_2 = h2_r15_0_2;
        6'd61: h2_y_2 = h2_r15_1_2;
        6'd62: h2_y_2 = h2_r15_2_2;
        6'd63: h2_y_2 = h2_r15_3_2;
        default: h2_y_2 = 8'b0;
    endcase
end
assign h2_out[16 +: 8] = h2_y_2;

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

wire [5:0] h2_ctrl_0 = h2_ctrl[0 +: 6];
wire [127:0] h2_data_0 = h2_data[0 +: 128];
reg [7:0] h2_y_0;

wire [7:0] h2_base0_0 = h2_data_0[7:0];
wire [7:0] h2_base1_0 = h2_data_0[15:8];
wire [7:0] h2_base2_0 = h2_data_0[23:16];
wire [7:0] h2_base3_0 = h2_data_0[31:24];
wire [7:0] h2_base4_0 = h2_data_0[39:32];
wire [7:0] h2_base5_0 = h2_data_0[47:40];
wire [7:0] h2_base6_0 = h2_data_0[55:48];
wire [7:0] h2_base7_0 = h2_data_0[63:56];
wire [7:0] h2_base8_0 = h2_data_0[71:64];
wire [7:0] h2_base9_0 = h2_data_0[79:72];
wire [7:0] h2_base10_0 = h2_data_0[87:80];
wire [7:0] h2_base11_0 = h2_data_0[95:88];
wire [7:0] h2_base12_0 = h2_data_0[103:96];
wire [7:0] h2_base13_0 = h2_data_0[111:104];
wire [7:0] h2_base14_0 = h2_data_0[119:112];
wire [7:0] h2_base15_0 = h2_data_0[127:120];
wire [7:0] h2_r0_0_0 = {h2_base0_0[7:6], h2_base0_0[5:4], h2_base0_0[3:2], h2_base0_0[1:0]};
wire [7:0] h2_r0_1_0 = {h2_base0_0[1:0], h2_base0_0[7:6], h2_base0_0[5:4], h2_base0_0[3:2]};
wire [7:0] h2_r0_2_0 = {h2_base0_0[3:2], h2_base0_0[1:0], h2_base0_0[7:6], h2_base0_0[5:4]};
wire [7:0] h2_r0_3_0 = {h2_base0_0[5:4], h2_base0_0[3:2], h2_base0_0[1:0], h2_base0_0[7:6]};
wire [7:0] h2_r1_0_0 = {h2_base1_0[7:6], h2_base1_0[5:4], h2_base1_0[3:2], h2_base1_0[1:0]};
wire [7:0] h2_r1_1_0 = {h2_base1_0[1:0], h2_base1_0[7:6], h2_base1_0[5:4], h2_base1_0[3:2]};
wire [7:0] h2_r1_2_0 = {h2_base1_0[3:2], h2_base1_0[1:0], h2_base1_0[7:6], h2_base1_0[5:4]};
wire [7:0] h2_r1_3_0 = {h2_base1_0[5:4], h2_base1_0[3:2], h2_base1_0[1:0], h2_base1_0[7:6]};
wire [7:0] h2_r2_0_0 = {h2_base2_0[7:6], h2_base2_0[5:4], h2_base2_0[3:2], h2_base2_0[1:0]};
wire [7:0] h2_r2_1_0 = {h2_base2_0[1:0], h2_base2_0[7:6], h2_base2_0[5:4], h2_base2_0[3:2]};
wire [7:0] h2_r2_2_0 = {h2_base2_0[3:2], h2_base2_0[1:0], h2_base2_0[7:6], h2_base2_0[5:4]};
wire [7:0] h2_r2_3_0 = {h2_base2_0[5:4], h2_base2_0[3:2], h2_base2_0[1:0], h2_base2_0[7:6]};
wire [7:0] h2_r3_0_0 = {h2_base3_0[7:6], h2_base3_0[5:4], h2_base3_0[3:2], h2_base3_0[1:0]};
wire [7:0] h2_r3_1_0 = {h2_base3_0[1:0], h2_base3_0[7:6], h2_base3_0[5:4], h2_base3_0[3:2]};
wire [7:0] h2_r3_2_0 = {h2_base3_0[3:2], h2_base3_0[1:0], h2_base3_0[7:6], h2_base3_0[5:4]};
wire [7:0] h2_r3_3_0 = {h2_base3_0[5:4], h2_base3_0[3:2], h2_base3_0[1:0], h2_base3_0[7:6]};
wire [7:0] h2_r4_0_0 = {h2_base4_0[7:6], h2_base4_0[5:4], h2_base4_0[3:2], h2_base4_0[1:0]};
wire [7:0] h2_r4_1_0 = {h2_base4_0[1:0], h2_base4_0[7:6], h2_base4_0[5:4], h2_base4_0[3:2]};
wire [7:0] h2_r4_2_0 = {h2_base4_0[3:2], h2_base4_0[1:0], h2_base4_0[7:6], h2_base4_0[5:4]};
wire [7:0] h2_r4_3_0 = {h2_base4_0[5:4], h2_base4_0[3:2], h2_base4_0[1:0], h2_base4_0[7:6]};
wire [7:0] h2_r5_0_0 = {h2_base5_0[7:6], h2_base5_0[5:4], h2_base5_0[3:2], h2_base5_0[1:0]};
wire [7:0] h2_r5_1_0 = {h2_base5_0[1:0], h2_base5_0[7:6], h2_base5_0[5:4], h2_base5_0[3:2]};
wire [7:0] h2_r5_2_0 = {h2_base5_0[3:2], h2_base5_0[1:0], h2_base5_0[7:6], h2_base5_0[5:4]};
wire [7:0] h2_r5_3_0 = {h2_base5_0[5:4], h2_base5_0[3:2], h2_base5_0[1:0], h2_base5_0[7:6]};
wire [7:0] h2_r6_0_0 = {h2_base6_0[7:6], h2_base6_0[5:4], h2_base6_0[3:2], h2_base6_0[1:0]};
wire [7:0] h2_r6_1_0 = {h2_base6_0[1:0], h2_base6_0[7:6], h2_base6_0[5:4], h2_base6_0[3:2]};
wire [7:0] h2_r6_2_0 = {h2_base6_0[3:2], h2_base6_0[1:0], h2_base6_0[7:6], h2_base6_0[5:4]};
wire [7:0] h2_r6_3_0 = {h2_base6_0[5:4], h2_base6_0[3:2], h2_base6_0[1:0], h2_base6_0[7:6]};
wire [7:0] h2_r7_0_0 = {h2_base7_0[7:6], h2_base7_0[5:4], h2_base7_0[3:2], h2_base7_0[1:0]};
wire [7:0] h2_r7_1_0 = {h2_base7_0[1:0], h2_base7_0[7:6], h2_base7_0[5:4], h2_base7_0[3:2]};
wire [7:0] h2_r7_2_0 = {h2_base7_0[3:2], h2_base7_0[1:0], h2_base7_0[7:6], h2_base7_0[5:4]};
wire [7:0] h2_r7_3_0 = {h2_base7_0[5:4], h2_base7_0[3:2], h2_base7_0[1:0], h2_base7_0[7:6]};
wire [7:0] h2_r8_0_0 = {h2_base8_0[7:6], h2_base8_0[5:4], h2_base8_0[3:2], h2_base8_0[1:0]};
wire [7:0] h2_r8_1_0 = {h2_base8_0[1:0], h2_base8_0[7:6], h2_base8_0[5:4], h2_base8_0[3:2]};
wire [7:0] h2_r8_2_0 = {h2_base8_0[3:2], h2_base8_0[1:0], h2_base8_0[7:6], h2_base8_0[5:4]};
wire [7:0] h2_r8_3_0 = {h2_base8_0[5:4], h2_base8_0[3:2], h2_base8_0[1:0], h2_base8_0[7:6]};
wire [7:0] h2_r9_0_0 = {h2_base9_0[7:6], h2_base9_0[5:4], h2_base9_0[3:2], h2_base9_0[1:0]};
wire [7:0] h2_r9_1_0 = {h2_base9_0[1:0], h2_base9_0[7:6], h2_base9_0[5:4], h2_base9_0[3:2]};
wire [7:0] h2_r9_2_0 = {h2_base9_0[3:2], h2_base9_0[1:0], h2_base9_0[7:6], h2_base9_0[5:4]};
wire [7:0] h2_r9_3_0 = {h2_base9_0[5:4], h2_base9_0[3:2], h2_base9_0[1:0], h2_base9_0[7:6]};
wire [7:0] h2_r10_0_0 = {h2_base10_0[7:6], h2_base10_0[5:4], h2_base10_0[3:2], h2_base10_0[1:0]};
wire [7:0] h2_r10_1_0 = {h2_base10_0[1:0], h2_base10_0[7:6], h2_base10_0[5:4], h2_base10_0[3:2]};
wire [7:0] h2_r10_2_0 = {h2_base10_0[3:2], h2_base10_0[1:0], h2_base10_0[7:6], h2_base10_0[5:4]};
wire [7:0] h2_r10_3_0 = {h2_base10_0[5:4], h2_base10_0[3:2], h2_base10_0[1:0], h2_base10_0[7:6]};
wire [7:0] h2_r11_0_0 = {h2_base11_0[7:6], h2_base11_0[5:4], h2_base11_0[3:2], h2_base11_0[1:0]};
wire [7:0] h2_r11_1_0 = {h2_base11_0[1:0], h2_base11_0[7:6], h2_base11_0[5:4], h2_base11_0[3:2]};
wire [7:0] h2_r11_2_0 = {h2_base11_0[3:2], h2_base11_0[1:0], h2_base11_0[7:6], h2_base11_0[5:4]};
wire [7:0] h2_r11_3_0 = {h2_base11_0[5:4], h2_base11_0[3:2], h2_base11_0[1:0], h2_base11_0[7:6]};
wire [7:0] h2_r12_0_0 = {h2_base12_0[7:6], h2_base12_0[5:4], h2_base12_0[3:2], h2_base12_0[1:0]};
wire [7:0] h2_r12_1_0 = {h2_base12_0[1:0], h2_base12_0[7:6], h2_base12_0[5:4], h2_base12_0[3:2]};
wire [7:0] h2_r12_2_0 = {h2_base12_0[3:2], h2_base12_0[1:0], h2_base12_0[7:6], h2_base12_0[5:4]};
wire [7:0] h2_r12_3_0 = {h2_base12_0[5:4], h2_base12_0[3:2], h2_base12_0[1:0], h2_base12_0[7:6]};
wire [7:0] h2_r13_0_0 = {h2_base13_0[7:6], h2_base13_0[5:4], h2_base13_0[3:2], h2_base13_0[1:0]};
wire [7:0] h2_r13_1_0 = {h2_base13_0[1:0], h2_base13_0[7:6], h2_base13_0[5:4], h2_base13_0[3:2]};
wire [7:0] h2_r13_2_0 = {h2_base13_0[3:2], h2_base13_0[1:0], h2_base13_0[7:6], h2_base13_0[5:4]};
wire [7:0] h2_r13_3_0 = {h2_base13_0[5:4], h2_base13_0[3:2], h2_base13_0[1:0], h2_base13_0[7:6]};
wire [7:0] h2_r14_0_0 = {h2_base14_0[7:6], h2_base14_0[5:4], h2_base14_0[3:2], h2_base14_0[1:0]};
wire [7:0] h2_r14_1_0 = {h2_base14_0[1:0], h2_base14_0[7:6], h2_base14_0[5:4], h2_base14_0[3:2]};
wire [7:0] h2_r14_2_0 = {h2_base14_0[3:2], h2_base14_0[1:0], h2_base14_0[7:6], h2_base14_0[5:4]};
wire [7:0] h2_r14_3_0 = {h2_base14_0[5:4], h2_base14_0[3:2], h2_base14_0[1:0], h2_base14_0[7:6]};
wire [7:0] h2_r15_0_0 = {h2_base15_0[7:6], h2_base15_0[5:4], h2_base15_0[3:2], h2_base15_0[1:0]};
wire [7:0] h2_r15_1_0 = {h2_base15_0[1:0], h2_base15_0[7:6], h2_base15_0[5:4], h2_base15_0[3:2]};
wire [7:0] h2_r15_2_0 = {h2_base15_0[3:2], h2_base15_0[1:0], h2_base15_0[7:6], h2_base15_0[5:4]};
wire [7:0] h2_r15_3_0 = {h2_base15_0[5:4], h2_base15_0[3:2], h2_base15_0[1:0], h2_base15_0[7:6]};
always @* begin
    case (h2_ctrl_0)
        6'd0: h2_y_0 = h2_r0_0_0;
        6'd1: h2_y_0 = h2_r0_1_0;
        6'd2: h2_y_0 = h2_r0_2_0;
        6'd3: h2_y_0 = h2_r0_3_0;
        6'd4: h2_y_0 = h2_r1_0_0;
        6'd5: h2_y_0 = h2_r1_1_0;
        6'd6: h2_y_0 = h2_r1_2_0;
        6'd7: h2_y_0 = h2_r1_3_0;
        6'd8: h2_y_0 = h2_r2_0_0;
        6'd9: h2_y_0 = h2_r2_1_0;
        6'd10: h2_y_0 = h2_r2_2_0;
        6'd11: h2_y_0 = h2_r2_3_0;
        6'd12: h2_y_0 = h2_r3_0_0;
        6'd13: h2_y_0 = h2_r3_1_0;
        6'd14: h2_y_0 = h2_r3_2_0;
        6'd15: h2_y_0 = h2_r3_3_0;
        6'd16: h2_y_0 = h2_r4_0_0;
        6'd17: h2_y_0 = h2_r4_1_0;
        6'd18: h2_y_0 = h2_r4_2_0;
        6'd19: h2_y_0 = h2_r4_3_0;
        6'd20: h2_y_0 = h2_r5_0_0;
        6'd21: h2_y_0 = h2_r5_1_0;
        6'd22: h2_y_0 = h2_r5_2_0;
        6'd23: h2_y_0 = h2_r5_3_0;
        6'd24: h2_y_0 = h2_r6_0_0;
        6'd25: h2_y_0 = h2_r6_1_0;
        6'd26: h2_y_0 = h2_r6_2_0;
        6'd27: h2_y_0 = h2_r6_3_0;
        6'd28: h2_y_0 = h2_r7_0_0;
        6'd29: h2_y_0 = h2_r7_1_0;
        6'd30: h2_y_0 = h2_r7_2_0;
        6'd31: h2_y_0 = h2_r7_3_0;
        6'd32: h2_y_0 = h2_r8_0_0;
        6'd33: h2_y_0 = h2_r8_1_0;
        6'd34: h2_y_0 = h2_r8_2_0;
        6'd35: h2_y_0 = h2_r8_3_0;
        6'd36: h2_y_0 = h2_r9_0_0;
        6'd37: h2_y_0 = h2_r9_1_0;
        6'd38: h2_y_0 = h2_r9_2_0;
        6'd39: h2_y_0 = h2_r9_3_0;
        6'd40: h2_y_0 = h2_r10_0_0;
        6'd41: h2_y_0 = h2_r10_1_0;
        6'd42: h2_y_0 = h2_r10_2_0;
        6'd43: h2_y_0 = h2_r10_3_0;
        6'd44: h2_y_0 = h2_r11_0_0;
        6'd45: h2_y_0 = h2_r11_1_0;
        6'd46: h2_y_0 = h2_r11_2_0;
        6'd47: h2_y_0 = h2_r11_3_0;
        6'd48: h2_y_0 = h2_r12_0_0;
        6'd49: h2_y_0 = h2_r12_1_0;
        6'd50: h2_y_0 = h2_r12_2_0;
        6'd51: h2_y_0 = h2_r12_3_0;
        6'd52: h2_y_0 = h2_r13_0_0;
        6'd53: h2_y_0 = h2_r13_1_0;
        6'd54: h2_y_0 = h2_r13_2_0;
        6'd55: h2_y_0 = h2_r13_3_0;
        6'd56: h2_y_0 = h2_r14_0_0;
        6'd57: h2_y_0 = h2_r14_1_0;
        6'd58: h2_y_0 = h2_r14_2_0;
        6'd59: h2_y_0 = h2_r14_3_0;
        6'd60: h2_y_0 = h2_r15_0_0;
        6'd61: h2_y_0 = h2_r15_1_0;
        6'd62: h2_y_0 = h2_r15_2_0;
        6'd63: h2_y_0 = h2_r15_3_0;
        default: h2_y_0 = 8'b0;
    endcase
end
assign h2_out[0 +: 8] = h2_y_0;

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

wire [5:0] h2_ctrl_3 = h2_ctrl[18 +: 6];
wire [127:0] h2_data_3 = h2_data[384 +: 128];
reg [7:0] h2_y_3;

wire [7:0] h2_base0_3 = h2_data_3[7:0];
wire [7:0] h2_base1_3 = h2_data_3[15:8];
wire [7:0] h2_base2_3 = h2_data_3[23:16];
wire [7:0] h2_base3_3 = h2_data_3[31:24];
wire [7:0] h2_base4_3 = h2_data_3[39:32];
wire [7:0] h2_base5_3 = h2_data_3[47:40];
wire [7:0] h2_base6_3 = h2_data_3[55:48];
wire [7:0] h2_base7_3 = h2_data_3[63:56];
wire [7:0] h2_base8_3 = h2_data_3[71:64];
wire [7:0] h2_base9_3 = h2_data_3[79:72];
wire [7:0] h2_base10_3 = h2_data_3[87:80];
wire [7:0] h2_base11_3 = h2_data_3[95:88];
wire [7:0] h2_base12_3 = h2_data_3[103:96];
wire [7:0] h2_base13_3 = h2_data_3[111:104];
wire [7:0] h2_base14_3 = h2_data_3[119:112];
wire [7:0] h2_base15_3 = h2_data_3[127:120];
wire [7:0] h2_r0_0_3 = {h2_base0_3[7:6], h2_base0_3[5:4], h2_base0_3[3:2], h2_base0_3[1:0]};
wire [7:0] h2_r0_1_3 = {h2_base0_3[1:0], h2_base0_3[7:6], h2_base0_3[5:4], h2_base0_3[3:2]};
wire [7:0] h2_r0_2_3 = {h2_base0_3[3:2], h2_base0_3[1:0], h2_base0_3[7:6], h2_base0_3[5:4]};
wire [7:0] h2_r0_3_3 = {h2_base0_3[5:4], h2_base0_3[3:2], h2_base0_3[1:0], h2_base0_3[7:6]};
wire [7:0] h2_r1_0_3 = {h2_base1_3[7:6], h2_base1_3[5:4], h2_base1_3[3:2], h2_base1_3[1:0]};
wire [7:0] h2_r1_1_3 = {h2_base1_3[1:0], h2_base1_3[7:6], h2_base1_3[5:4], h2_base1_3[3:2]};
wire [7:0] h2_r1_2_3 = {h2_base1_3[3:2], h2_base1_3[1:0], h2_base1_3[7:6], h2_base1_3[5:4]};
wire [7:0] h2_r1_3_3 = {h2_base1_3[5:4], h2_base1_3[3:2], h2_base1_3[1:0], h2_base1_3[7:6]};
wire [7:0] h2_r2_0_3 = {h2_base2_3[7:6], h2_base2_3[5:4], h2_base2_3[3:2], h2_base2_3[1:0]};
wire [7:0] h2_r2_1_3 = {h2_base2_3[1:0], h2_base2_3[7:6], h2_base2_3[5:4], h2_base2_3[3:2]};
wire [7:0] h2_r2_2_3 = {h2_base2_3[3:2], h2_base2_3[1:0], h2_base2_3[7:6], h2_base2_3[5:4]};
wire [7:0] h2_r2_3_3 = {h2_base2_3[5:4], h2_base2_3[3:2], h2_base2_3[1:0], h2_base2_3[7:6]};
wire [7:0] h2_r3_0_3 = {h2_base3_3[7:6], h2_base3_3[5:4], h2_base3_3[3:2], h2_base3_3[1:0]};
wire [7:0] h2_r3_1_3 = {h2_base3_3[1:0], h2_base3_3[7:6], h2_base3_3[5:4], h2_base3_3[3:2]};
wire [7:0] h2_r3_2_3 = {h2_base3_3[3:2], h2_base3_3[1:0], h2_base3_3[7:6], h2_base3_3[5:4]};
wire [7:0] h2_r3_3_3 = {h2_base3_3[5:4], h2_base3_3[3:2], h2_base3_3[1:0], h2_base3_3[7:6]};
wire [7:0] h2_r4_0_3 = {h2_base4_3[7:6], h2_base4_3[5:4], h2_base4_3[3:2], h2_base4_3[1:0]};
wire [7:0] h2_r4_1_3 = {h2_base4_3[1:0], h2_base4_3[7:6], h2_base4_3[5:4], h2_base4_3[3:2]};
wire [7:0] h2_r4_2_3 = {h2_base4_3[3:2], h2_base4_3[1:0], h2_base4_3[7:6], h2_base4_3[5:4]};
wire [7:0] h2_r4_3_3 = {h2_base4_3[5:4], h2_base4_3[3:2], h2_base4_3[1:0], h2_base4_3[7:6]};
wire [7:0] h2_r5_0_3 = {h2_base5_3[7:6], h2_base5_3[5:4], h2_base5_3[3:2], h2_base5_3[1:0]};
wire [7:0] h2_r5_1_3 = {h2_base5_3[1:0], h2_base5_3[7:6], h2_base5_3[5:4], h2_base5_3[3:2]};
wire [7:0] h2_r5_2_3 = {h2_base5_3[3:2], h2_base5_3[1:0], h2_base5_3[7:6], h2_base5_3[5:4]};
wire [7:0] h2_r5_3_3 = {h2_base5_3[5:4], h2_base5_3[3:2], h2_base5_3[1:0], h2_base5_3[7:6]};
wire [7:0] h2_r6_0_3 = {h2_base6_3[7:6], h2_base6_3[5:4], h2_base6_3[3:2], h2_base6_3[1:0]};
wire [7:0] h2_r6_1_3 = {h2_base6_3[1:0], h2_base6_3[7:6], h2_base6_3[5:4], h2_base6_3[3:2]};
wire [7:0] h2_r6_2_3 = {h2_base6_3[3:2], h2_base6_3[1:0], h2_base6_3[7:6], h2_base6_3[5:4]};
wire [7:0] h2_r6_3_3 = {h2_base6_3[5:4], h2_base6_3[3:2], h2_base6_3[1:0], h2_base6_3[7:6]};
wire [7:0] h2_r7_0_3 = {h2_base7_3[7:6], h2_base7_3[5:4], h2_base7_3[3:2], h2_base7_3[1:0]};
wire [7:0] h2_r7_1_3 = {h2_base7_3[1:0], h2_base7_3[7:6], h2_base7_3[5:4], h2_base7_3[3:2]};
wire [7:0] h2_r7_2_3 = {h2_base7_3[3:2], h2_base7_3[1:0], h2_base7_3[7:6], h2_base7_3[5:4]};
wire [7:0] h2_r7_3_3 = {h2_base7_3[5:4], h2_base7_3[3:2], h2_base7_3[1:0], h2_base7_3[7:6]};
wire [7:0] h2_r8_0_3 = {h2_base8_3[7:6], h2_base8_3[5:4], h2_base8_3[3:2], h2_base8_3[1:0]};
wire [7:0] h2_r8_1_3 = {h2_base8_3[1:0], h2_base8_3[7:6], h2_base8_3[5:4], h2_base8_3[3:2]};
wire [7:0] h2_r8_2_3 = {h2_base8_3[3:2], h2_base8_3[1:0], h2_base8_3[7:6], h2_base8_3[5:4]};
wire [7:0] h2_r8_3_3 = {h2_base8_3[5:4], h2_base8_3[3:2], h2_base8_3[1:0], h2_base8_3[7:6]};
wire [7:0] h2_r9_0_3 = {h2_base9_3[7:6], h2_base9_3[5:4], h2_base9_3[3:2], h2_base9_3[1:0]};
wire [7:0] h2_r9_1_3 = {h2_base9_3[1:0], h2_base9_3[7:6], h2_base9_3[5:4], h2_base9_3[3:2]};
wire [7:0] h2_r9_2_3 = {h2_base9_3[3:2], h2_base9_3[1:0], h2_base9_3[7:6], h2_base9_3[5:4]};
wire [7:0] h2_r9_3_3 = {h2_base9_3[5:4], h2_base9_3[3:2], h2_base9_3[1:0], h2_base9_3[7:6]};
wire [7:0] h2_r10_0_3 = {h2_base10_3[7:6], h2_base10_3[5:4], h2_base10_3[3:2], h2_base10_3[1:0]};
wire [7:0] h2_r10_1_3 = {h2_base10_3[1:0], h2_base10_3[7:6], h2_base10_3[5:4], h2_base10_3[3:2]};
wire [7:0] h2_r10_2_3 = {h2_base10_3[3:2], h2_base10_3[1:0], h2_base10_3[7:6], h2_base10_3[5:4]};
wire [7:0] h2_r10_3_3 = {h2_base10_3[5:4], h2_base10_3[3:2], h2_base10_3[1:0], h2_base10_3[7:6]};
wire [7:0] h2_r11_0_3 = {h2_base11_3[7:6], h2_base11_3[5:4], h2_base11_3[3:2], h2_base11_3[1:0]};
wire [7:0] h2_r11_1_3 = {h2_base11_3[1:0], h2_base11_3[7:6], h2_base11_3[5:4], h2_base11_3[3:2]};
wire [7:0] h2_r11_2_3 = {h2_base11_3[3:2], h2_base11_3[1:0], h2_base11_3[7:6], h2_base11_3[5:4]};
wire [7:0] h2_r11_3_3 = {h2_base11_3[5:4], h2_base11_3[3:2], h2_base11_3[1:0], h2_base11_3[7:6]};
wire [7:0] h2_r12_0_3 = {h2_base12_3[7:6], h2_base12_3[5:4], h2_base12_3[3:2], h2_base12_3[1:0]};
wire [7:0] h2_r12_1_3 = {h2_base12_3[1:0], h2_base12_3[7:6], h2_base12_3[5:4], h2_base12_3[3:2]};
wire [7:0] h2_r12_2_3 = {h2_base12_3[3:2], h2_base12_3[1:0], h2_base12_3[7:6], h2_base12_3[5:4]};
wire [7:0] h2_r12_3_3 = {h2_base12_3[5:4], h2_base12_3[3:2], h2_base12_3[1:0], h2_base12_3[7:6]};
wire [7:0] h2_r13_0_3 = {h2_base13_3[7:6], h2_base13_3[5:4], h2_base13_3[3:2], h2_base13_3[1:0]};
wire [7:0] h2_r13_1_3 = {h2_base13_3[1:0], h2_base13_3[7:6], h2_base13_3[5:4], h2_base13_3[3:2]};
wire [7:0] h2_r13_2_3 = {h2_base13_3[3:2], h2_base13_3[1:0], h2_base13_3[7:6], h2_base13_3[5:4]};
wire [7:0] h2_r13_3_3 = {h2_base13_3[5:4], h2_base13_3[3:2], h2_base13_3[1:0], h2_base13_3[7:6]};
wire [7:0] h2_r14_0_3 = {h2_base14_3[7:6], h2_base14_3[5:4], h2_base14_3[3:2], h2_base14_3[1:0]};
wire [7:0] h2_r14_1_3 = {h2_base14_3[1:0], h2_base14_3[7:6], h2_base14_3[5:4], h2_base14_3[3:2]};
wire [7:0] h2_r14_2_3 = {h2_base14_3[3:2], h2_base14_3[1:0], h2_base14_3[7:6], h2_base14_3[5:4]};
wire [7:0] h2_r14_3_3 = {h2_base14_3[5:4], h2_base14_3[3:2], h2_base14_3[1:0], h2_base14_3[7:6]};
wire [7:0] h2_r15_0_3 = {h2_base15_3[7:6], h2_base15_3[5:4], h2_base15_3[3:2], h2_base15_3[1:0]};
wire [7:0] h2_r15_1_3 = {h2_base15_3[1:0], h2_base15_3[7:6], h2_base15_3[5:4], h2_base15_3[3:2]};
wire [7:0] h2_r15_2_3 = {h2_base15_3[3:2], h2_base15_3[1:0], h2_base15_3[7:6], h2_base15_3[5:4]};
wire [7:0] h2_r15_3_3 = {h2_base15_3[5:4], h2_base15_3[3:2], h2_base15_3[1:0], h2_base15_3[7:6]};
always @* begin
    case (h2_ctrl_3)
        6'd0: h2_y_3 = h2_r0_0_3;
        6'd1: h2_y_3 = h2_r0_1_3;
        6'd2: h2_y_3 = h2_r0_2_3;
        6'd3: h2_y_3 = h2_r0_3_3;
        6'd4: h2_y_3 = h2_r1_0_3;
        6'd5: h2_y_3 = h2_r1_1_3;
        6'd6: h2_y_3 = h2_r1_2_3;
        6'd7: h2_y_3 = h2_r1_3_3;
        6'd8: h2_y_3 = h2_r2_0_3;
        6'd9: h2_y_3 = h2_r2_1_3;
        6'd10: h2_y_3 = h2_r2_2_3;
        6'd11: h2_y_3 = h2_r2_3_3;
        6'd12: h2_y_3 = h2_r3_0_3;
        6'd13: h2_y_3 = h2_r3_1_3;
        6'd14: h2_y_3 = h2_r3_2_3;
        6'd15: h2_y_3 = h2_r3_3_3;
        6'd16: h2_y_3 = h2_r4_0_3;
        6'd17: h2_y_3 = h2_r4_1_3;
        6'd18: h2_y_3 = h2_r4_2_3;
        6'd19: h2_y_3 = h2_r4_3_3;
        6'd20: h2_y_3 = h2_r5_0_3;
        6'd21: h2_y_3 = h2_r5_1_3;
        6'd22: h2_y_3 = h2_r5_2_3;
        6'd23: h2_y_3 = h2_r5_3_3;
        6'd24: h2_y_3 = h2_r6_0_3;
        6'd25: h2_y_3 = h2_r6_1_3;
        6'd26: h2_y_3 = h2_r6_2_3;
        6'd27: h2_y_3 = h2_r6_3_3;
        6'd28: h2_y_3 = h2_r7_0_3;
        6'd29: h2_y_3 = h2_r7_1_3;
        6'd30: h2_y_3 = h2_r7_2_3;
        6'd31: h2_y_3 = h2_r7_3_3;
        6'd32: h2_y_3 = h2_r8_0_3;
        6'd33: h2_y_3 = h2_r8_1_3;
        6'd34: h2_y_3 = h2_r8_2_3;
        6'd35: h2_y_3 = h2_r8_3_3;
        6'd36: h2_y_3 = h2_r9_0_3;
        6'd37: h2_y_3 = h2_r9_1_3;
        6'd38: h2_y_3 = h2_r9_2_3;
        6'd39: h2_y_3 = h2_r9_3_3;
        6'd40: h2_y_3 = h2_r10_0_3;
        6'd41: h2_y_3 = h2_r10_1_3;
        6'd42: h2_y_3 = h2_r10_2_3;
        6'd43: h2_y_3 = h2_r10_3_3;
        6'd44: h2_y_3 = h2_r11_0_3;
        6'd45: h2_y_3 = h2_r11_1_3;
        6'd46: h2_y_3 = h2_r11_2_3;
        6'd47: h2_y_3 = h2_r11_3_3;
        6'd48: h2_y_3 = h2_r12_0_3;
        6'd49: h2_y_3 = h2_r12_1_3;
        6'd50: h2_y_3 = h2_r12_2_3;
        6'd51: h2_y_3 = h2_r12_3_3;
        6'd52: h2_y_3 = h2_r13_0_3;
        6'd53: h2_y_3 = h2_r13_1_3;
        6'd54: h2_y_3 = h2_r13_2_3;
        6'd55: h2_y_3 = h2_r13_3_3;
        6'd56: h2_y_3 = h2_r14_0_3;
        6'd57: h2_y_3 = h2_r14_1_3;
        6'd58: h2_y_3 = h2_r14_2_3;
        6'd59: h2_y_3 = h2_r14_3_3;
        6'd60: h2_y_3 = h2_r15_0_3;
        6'd61: h2_y_3 = h2_r15_1_3;
        6'd62: h2_y_3 = h2_r15_2_3;
        6'd63: h2_y_3 = h2_r15_3_3;
        default: h2_y_3 = 8'b0;
    endcase
end
assign h2_out[24 +: 8] = h2_y_3;

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

endmodule
