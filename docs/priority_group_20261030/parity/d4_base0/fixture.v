module top(input [3:0] s,input [15:0] d,output [3:0] y);assign y=s[3]?d[15:12]:(s[2]?d[11:8]:(s[1]?d[7:4]:(s[0]?d[3:0]:(4'd0))));endmodule
