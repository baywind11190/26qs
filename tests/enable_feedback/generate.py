"""Fixtures for the bounded three-condition EN/D rewrite."""
from pathlib import Path
import re


def generate(root: Path, out: Path):
    original = (root / 'pmux_case/competition_case/test3/test3.v').read_text()
    fixtures = []
    def save(name, text, hit, top='test3'):
        path = out / (name + '.v')
        path.write_text(text)
        fixtures.append((name, path, top, hit))
    renamed = original
    for name in ['test3', 'clk', 'cs', 'sr_in', 'sr_out', 'gpioout', 'sr', 'rw']:
        renamed = re.sub(r'\b' + name + r'\b', 'renamed_' + name, renamed)
    save('renamed', renamed, 1, 'renamed_test3')
    for name, permutation in [('permuted', [4, 0, 6, 2, 7, 1, 5, 3]),
                              ('reversed', list(reversed(range(8))))]:
        text = original.replace('assign rw = sr[7];',
            'wire [7:0] command = {' + ','.join(f'sr[{i}]' for i in reversed(permutation)) + '};\nassign rw = command[7];')
        start = text.index('case (sr)')
        text = text[:start] + text[start:].replace('case (sr)', 'case (command)').replace('sr[', 'command[')
        save(name, text, 1)
    wide = original.replace('8\'b10101010', "9'b110101010").replace("8'b11111111", "9'b111111111").replace("8'b11111110", "9'b111111110")
    wide = wide.replace('reg [7:0] sr;', 'reg [8:0] sr;').replace('assign rw = sr[7];', 'assign rw = sr[8] & sr[7];')
    wide = wide.replace('sr_out <= sr[7];', 'sr_out <= sr[8];').replace('sr[7:1] <= sr[6:0];', 'sr[8:1] <= sr[7:0];')
    save('control_width9', wide, 1)
    save('initialized', original.replace('assign rw = sr[7];', "initial gpioout = 8'h00;\nassign rw = sr[7];"), 0)
    reset = original.replace('(clk, cs, sr_in, gpioout, sr_out)', '(clk, cs, sr_in, gpioout, sr_out, reset)').replace('input clk, cs;', 'input clk, cs, reset;').replace('always@(posedge clk )', 'always@(posedge clk or posedge reset)')
    reset = reset.replace("if (cs == 1'b0)", "if(reset) begin sr<=0; sr_out<=0; gpioout<=0; end else begin\nif (cs == 1'b0)", 1)
    reset = reset.replace('endmodule', 'end\nendmodule')
    save('async_reset', reset, 0)
    save('changed_default', original.replace('gpioout[0] <= sr[0];', 'gpioout[0] <= ~sr[0];'), 0)
    save('extra_command', original.replace('default   :', "8'hAB : gpioout <= 8'h00;\ndefault   :"), 0)
    save('external_data', original.replace('(clk, cs, sr_in, gpioout, sr_out)', '(clk, cs, sr_in, gpioout, sr_out, payload)').replace('input sr_in;', 'input sr_in; input [3:0] payload;').replace(
        '{sr[0], sr[1], sr[2], sr[3]}', 'payload'), 0)
    case_equal = original.replace('(clk, cs, sr_in, gpioout, sr_out)', '(clk, cs, sr_in, gpioout, sr_out, p, q)').replace('input sr_in;', 'input sr_in; input p, q;')
    case_equal = case_equal.replace('{sr[0], sr[1], sr[2], sr[3]}', "{sr[0], (sr[0] & (p === q)), sr[2], (sr[0] & (p === q))}")
    save('external_case_equality', case_equal, 0)
    return fixtures
