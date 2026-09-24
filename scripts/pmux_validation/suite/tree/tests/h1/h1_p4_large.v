module h1_p4_large(
    input [4:0] control,
    input [767:0] din,
    output reg [11:0] out_a,
    output reg [11:0] out_b
);

always @*
begin
    case (control)
        5'd16: out_a = din[23:12];
        5'd3: out_a = din[155:144];
        5'd14: out_a = din[683:672];
        5'd26: out_a = din[503:492];
        5'd19: out_a = din[179:168];
        5'd28: out_a = din[599:588];
        5'd22: out_a = din[311:300];
        5'd7: out_a = din[347:336];
        5'd21: out_a = din[263:252];
        5'd29: out_a = din[647:636];
        5'd31: out_a = din[743:732];
        5'd15: out_a = din[731:720];
        5'd27: out_a = din[563:552];
        5'd9: out_a = din[443:432];
        5'd5: out_a = din[251:240];
        5'd0: out_a = din[11:0];
        5'd18: out_a = din[119:108];
        5'd13: out_a = din[635:624];
        5'd2: out_a = din[107:96];
        5'd1: out_a = din[59:48];
        5'd8: out_a = din[395:384];
        5'd17: out_a = din[71:60];
        5'd12: out_a = din[587:576];
        5'd10: out_a = din[491:480];
        5'd24: out_a = din[407:396];
        5'd23: out_a = din[359:348];
        5'd20: out_a = din[215:204];
        5'd30: out_a = din[695:684];
        5'd4: out_a = din[203:192];
        5'd11: out_a = din[539:528];
        5'd25: out_a = din[455:444];
        5'd6: out_a = din[299:288];
        default: out_a = 12'bx;
    endcase
end

always @*
begin
    case (control)
        5'd16: out_b = din[11:0];
        5'd3: out_b = din[167:156];
        5'd14: out_b = din[695:684];
        5'd26: out_b = din[491:480];
        5'd19: out_b = din[191:180];
        5'd28: out_b = din[587:576];
        5'd22: out_b = din[299:288];
        5'd7: out_b = din[359:348];
        5'd21: out_b = din[251:240];
        5'd29: out_b = din[635:624];
        5'd31: out_b = din[731:720];
        5'd15: out_b = din[743:732];
        5'd27: out_b = din[575:564];
        5'd9: out_b = din[455:444];
        5'd5: out_b = din[263:252];
        5'd0: out_b = din[23:12];
        5'd18: out_b = din[107:96];
        5'd13: out_b = din[647:636];
        5'd2: out_b = din[119:108];
        5'd1: out_b = din[71:60];
        5'd8: out_b = din[407:396];
        5'd17: out_b = din[59:48];
        5'd12: out_b = din[599:588];
        5'd10: out_b = din[503:492];
        5'd24: out_b = din[395:384];
        5'd23: out_b = din[347:336];
        5'd20: out_b = din[203:192];
        5'd30: out_b = din[683:672];
        5'd4: out_b = din[215:204];
        5'd11: out_b = din[551:540];
        5'd25: out_b = din[443:432];
        5'd6: out_b = din[311:300];
        default: out_b = 12'bx;
    endcase
end

endmodule
