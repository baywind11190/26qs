module stress_top(
    input [13:0] a_ctrl,
    input [111:0] a_data,
    output [55:0] a_out,
    input [15:0] c_ctrl,
    output [15:0] c_out,
    input [7:0] n_ctrl,
    input [63:0] n_data,
    output [15:0] n_out
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

endmodule
