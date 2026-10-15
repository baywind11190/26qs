#!/usr/bin/env python3
"""Check 5.1 entry work, mapped resources, and old/new netlist equivalence."""
import argparse
import importlib.util
import json
import re
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = 'b87e3ab3ad475ef581a1fc09ebd365c0e2d0e59a'
spec = importlib.util.spec_from_file_location('feedback', ROOT / 'scripts/run_enable_feedback_regression.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--baseline-source', type=Path)
    ap.add_argument('--check-index', action='store_true')
    ns = ap.parse_args()
    out = ns.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    plugins = {}
    for label in ['baseline', 'candidate']:
        source = ((ns.baseline_source.read_text() if ns.baseline_source else subprocess.check_output(['git','show',BASE+':src/pmux_opt.cc'], cwd=ROOT).decode())
                  if label == 'baseline' else (ROOT/'src/pmux_opt.cc').read_text())
        # Test-only hook observes construction of 5.1's full signal map.
        assert source.count('SigMap h3_sigmap(module);') == 1
        source = source.replace('SigMap h3_sigmap(module);',
            '''log("TEST PRIORITY ANALYSIS ENTRY\\n");
            int test_map_calls = 0;
            auto test_report = std::shared_ptr<void>(nullptr, [&](void*) { log("TEST MAP CALLS %d\\n", test_map_calls); });
            SigMap test_map(module);
            auto h3_sigmap = [&](const RTLIL::SigSpec &s) { ++test_map_calls; return test_map(s); };''')
        cc = out/(label+'.cc')
        cc.write_text(source)
        plugins[label] = out/(label+'.so')
        helper.run(['yosys-config','--build',str(plugins[label]),str(cc)], out/(label+'_build.log'))
    results = {}
    for depth in [0,1,2,3]:
        rtl = out/f'chain{depth}.v'
        expression = "4'b0000"
        for i in range(depth): expression = f's[{i}] ? d[{4*i}+:4] : ({expression})'
        rtl.write_text(f'module top(input [2:0] s,input [11:0] d,output [3:0] y); assign y={expression}; endmodule\n')
        ys = out/f'chain{depth}.ys'
        ys.write_text(f'read_verilog {rtl}\nprep -top top\npmux_opt\nwrite_rtlil {out}/chain{depth}.il\n')
        log = out/f'chain{depth}.log'
        helper.run(['yosys','-m',str(plugins['candidate']),'-s',str(ys)],log)
        entered = 'TEST PRIORITY ANALYSIS ENTRY' in log.read_text()
        assert entered == (depth >= 3), (depth,entered)
        helper.prove(rtl,'top',out/f'chain{depth}.il',out/f'chain{depth}_formal')
        results[f'chain{depth}'] = {'analysis_entered':entered,'formal':'PASS'}
        print(f'chain{depth}',results[f'chain{depth}'],flush=True)
    expressions = []
    for offset in [0,12]:
        expr = "4'b0000"
        for i in range(3): expr = f's[{i}] ? d[{offset+4*i}+:4] : ({expr})'
        expressions.append(expr)
    private = '''module top(input [2:0] s,input [11:0] d,output [3:0] y,output tap);
wire [3:0] low = s[0] ? d[3:0] : 4'b0;
assign y = s[2] ? d[11:8] : (s[1] ? d[7:4] : low);
assign tap = EXPR;
endmodule
'''
    fixtures = [('partial_output',private.replace('EXPR','low[0]'),0),
                ('extra_user',private.replace('EXPR','~low[1]'),0),
                ('two_chains','module top(input [2:0] s,input [23:0] d,output [7:0] y);\n'
                 +f'assign y[3:0]={expressions[0]};\nassign y[7:4]={expressions[1]};\nendmodule\n',2)]
    for name,text,expected in fixtures:
        rtl = out/(name+'.v')
        rtl.write_text(text)
        for label,plugin in plugins.items():
            prefix = out/(name+'_'+label)
            ys = prefix.with_suffix('.ys')
            ys.write_text(f'read_verilog {rtl}\nprep -top top\npmux_opt\nwrite_rtlil {prefix}.il\n')
            helper.run(['yosys','-m',str(plugin),'-s',str(ys)],prefix.with_suffix('.log'))
            hits = int(re.search(r'Total H3 rebuilt: (\d+)',prefix.with_suffix('.log').read_text())[1])
            assert hits == expected, (name,label,hits)
            helper.prove(rtl,'top',prefix.with_suffix('.il'),out/(name+'_'+label+'_formal'))
        results[name] = {'rebuilt_each_side':expected,'formal':'PASS'}
        print(name,results[name],flush=True)
    # Invalid duplicate drivers: only compare rejection, not functionality.
    ys = out/'ambiguous_prepare.ys'
    ys.write_text(f'read_verilog {out}/chain3.v\nprep -top top\nwrite_json {out}/ambiguous.json\n')
    helper.run(['yosys','-s',str(ys)],out/'ambiguous_prepare.log')
    design = json.loads((out/'ambiguous.json').read_text())
    module = design['modules']['top']
    bottom = next(c for c in module['cells'].values() if c['type'] == '$mux' and all(b == '0' for b in c['connections']['A']))
    duplicate = json.loads(json.dumps(bottom))
    duplicate['connections']['B'] = module['ports']['d']['bits'][4:8]
    module['cells']['duplicate_driver'] = duplicate
    (out/'ambiguous.json').write_text(json.dumps(design))
    for label,plugin in plugins.items():
        ys = out/('ambiguous_'+label+'.ys')
        ys.write_text(f'read_json {out}/ambiguous.json\npmux_opt\n')
        log = out/('ambiguous_'+label+'.log')
        helper.run(['yosys','-m',str(plugin),'-s',str(ys)],log)
        assert 'Total H3 rebuilt: 0' in log.read_text()
    results['ambiguous_driver'] = {'rebuilt_each_side':0}
    for i in range(1,5):
        name = f'test{i}'
        rtl = ROOT/f'pmux_case/competition_case/{name}/{name}.v'
        row = {}
        for label,plugin in plugins.items():
            dest = out/name/label
            dest.mkdir(parents=True)
            ys = dest/'run.ys'
            ys.write_text(helper.flow(rtl,name,dest))
            helper.run(['yosys','-m',str(plugin),'-s',str(ys)],dest/'run.log')
            row[label] = json.loads((dest/'stat.json').read_text())['modules']['\\'+name]['num_cells_by_type']
        assert row['baseline'] == row['candidate'], (name,row)
        if i == 2: assert 'Total H3 rebuilt: 1' in (out/name/'candidate/run.log').read_text()
        if i == 2 and ns.check_index:
            calls = [int(re.search(r'TEST MAP CALLS (\d+)', (out/name/label/'run.log').read_text())[1]) for label in plugins]
            assert calls[1] < calls[0], calls
            row['signal_map_calls'] = calls
        if i == 4: assert 'TEST PRIORITY ANALYSIS ENTRY' not in (out/name/'candidate/run.log').read_text()
        ys = out/name/'equiv.ys'
        ys.write_text(f'''read_rtlil {out}/{name}/baseline/rebuilt.il
rename {name} gold
read_rtlil {out}/{name}/candidate/rebuilt.il
rename {name} gate
memory_map
async2sync
equiv_make gold gate equiv
hierarchy -top equiv
opt_clean
equiv_simple
equiv_induct -seq 6
equiv_status -assert
''')
        helper.run(['yosys','-s',str(ys)],out/name/'equiv.log')
        row['baseline_candidate_formal'] = 'PASS'
        results[name] = row
        print(name,row,flush=True)
    (out/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
    print('All priority entry checks passed:',out)

if __name__ == '__main__': main()
