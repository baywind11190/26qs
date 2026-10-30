module top(input [4:0] s,input [19:0] d,output [3:0] y);assign y=s[4]?d[19:16]:(s[3]?d[15:12]:(s[2]?d[11:8]:(s[1]?d[7:4]:(s[0]?d[3:0]:(4'd9)))));endmodule
