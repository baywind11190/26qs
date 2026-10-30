module top(input [6:0] s,input [27:0] d,output [3:0] y);assign y=s[6]?d[27:24]:(s[5]?d[23:20]:(s[4]?d[19:16]:(s[3]?d[15:12]:(s[2]?d[11:8]:(s[1]?d[7:4]:(s[0]?d[3:0]:(4'd0)))))));endmodule
