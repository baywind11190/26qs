#!/usr/bin/env python3
"""Build exact baseline/current pass; prove fixtures and check mapped resources."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = '9f89a809c29382421a162eeafdb815c9c0cfe49f'

def run(args, log, cwd=ROOT):
    with log.open('w') as stream:
        subprocess.run(args, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT, check=True, timeout=120)

def flow(rtl, top, dest):
    return '\n'.join([
        f'read_verilog -sv {rtl}', f'synth_intel -family cycloneiv -top {top} -run begin:coarse',
        'proc', 'check', 'flatten', 'tribuf -logic', 'deminout', 'opt_expr', 'opt_clean', 'check',
        'opt -nodffe -nosdff', 'fsm', 'opt', 'pmux_opt', f'select {top}',
        f'write_rtlil -selected {dest}/rebuilt.il', 'select -clear',
        'wreduce', 'peepopt', 'opt_clean', 'techmap -map +/cmp2lut.v -D LUT_WIDTH=4',
        'opt_expr', 'opt_clean', 'alumacc', 'opt', 'memory -nomap', 'opt_clean',
        f'synth_intel -family cycloneiv -top {top} -run map_bram:map_cells',
        f'write_rtlil {dest}/post_abc.il',
        f'synth_intel -family cycloneiv -top {top} -run map_cells:',
        f'write_rtlil {dest}/mapped.il', f'tee -o {dest}/stat.json stat -json']) + '\n'

def prove(rtl, top, gate, dest, negative=False, model=None):
    cfg = dest.with_suffix('.eqy')
    gate_read = (f'read_verilog {model}\n' if model else '') + f'read_rtlil {gate}\nhierarchy -check -top {top}\nflatten\n'
    cfg.write_text(f'''[gold]
read_verilog -sv {rtl}
hierarchy -top {top}
proc
memory_map
opt
async2sync
formalff -clk2ff
prep -top {top}
[gate]
{gate_read}proc
memory_map
opt
async2sync
formalff -clk2ff
prep -top {top}
[collect {top}]
group *
bind *
[partition {top}]
merge *
[strategy sat]
use sat
depth 20
''')
    # EQY provides partition preparation; checked replay avoids the known
    # contradictory initial-undef -set-def-formal setting and uses -verify.
    with dest.with_suffix('.log').open('w') as log:
        subprocess.run(['eqy', '-j', '2', '-f', '-d', str(dest), str(cfg)], cwd=ROOT,
                       stdout=log, stderr=subprocess.STDOUT, timeout=120)
    scripts = list((dest / 'strategies').glob('*/sat/run.ys'))
    assert len(scripts) == 1, (dest, scripts)
    script = scripts[0]
    checked = script.with_name('checked.ys')
    checked.write_text(script.read_text().replace(' -set-def-formal', '').replace('sat -tempinduct', 'sat -verify -tempinduct'))
    with script.with_name('checked.log').open('w') as log:
        result = subprocess.run(['yosys', '-Q', '-T', '-s', checked.name], cwd=script.parent,
                                stdout=log, stderr=subprocess.STDOUT, timeout=120)
    text = script.with_name('checked.log').read_text()
    partition = json.loads(next((dest / 'partitions').glob('*.json')).read_text())['partition']
    assert not partition['crossbits'], (dest, partition)
    if negative:
        assert result.returncode != 0 and 'model found for base case: FAIL' in text
    else:
        assert result.returncode == 0 and 'Induction step proven: SUCCESS!' in text, dest

def boundary_checks(out, plugin):
    """Exercise safety guards before old optimizations can remove the fixture."""
    folder = out / 'boundaries'
    folder.mkdir()
    rtl = ROOT / 'pmux_case/competition_case/test3/test3.v'
    ys = folder / 'prepare.ys'
    ys.write_text(flow(rtl, 'test3', folder).split('pmux_opt')[0] + f'write_json {folder}/original.json\n')
    run(['yosys', '-s', str(ys)], folder / 'prepare.log')
    original = json.loads((folder / 'original.json').read_text())
    for name in ['positive', 'multiple_data_drivers', 'different_clock', 'kept_register', 'negative_enable', 'partial_selection']:
        design = copy.deepcopy(original)
        module = design['modules']['test3']
        cells = module['cells']
        xname, x = next((n,c) for n,c in cells.items() if c['type'] == '$dffe' and len(c['connections']['Q']) == 3)
        if name == 'multiple_data_drivers':
            fresh = 1 + max(b for net in module['netnames'].values() for b in net['bits'] if isinstance(b,int))
            module['netnames']['boundary_bit'] = {'hide_name': 0, 'bits': [fresh], 'attributes': {}}
            for index, constant in enumerate(['1','0']):
                cells[f'boundary_driver{index}'] = {'hide_name':0, 'type':'$and', 'parameters':
                    {k:format(v,'032b') for k,v in [('A_SIGNED',0), ('B_SIGNED',0), ('A_WIDTH',1), ('B_WIDTH',1), ('Y_WIDTH',1)]},
                    'attributes':{}, 'port_directions':{'A':'input','B':'input','Y':'output'},
                    'connections':{'A':[module['netnames']['sr']['bits'][0]],'B':[constant],'Y':[fresh]}}
            pmux = next(c for c in cells.values() if c['type'] == '$pmux' and c['connections']['Y'] == x['connections']['D'])
            pmux['connections']['B'][0] = fresh
            pmux['connections']['B'][2] = fresh
        if name == 'different_clock': x['connections']['CLK'] = module['ports']['sr_in']['bits']
        if name == 'kept_register': x['attributes']['keep'] = '1'
        if name == 'negative_enable': x['parameters']['EN_POLARITY'] = '0'
        source = folder / (name + '.json')
        source.write_text(json.dumps(design))
        script = folder / (name + '.ys')
        selection = f'select -clear\nselect test3/{xname}\n' if name == 'partial_selection' else ''
        script.write_text(f'read_json {source}\n{selection}enable_feedback_test\nselect -clear\nwrite_json {folder}/{name}_after.json\n')
        run(['yosys','-m',str(plugin),'-s',str(script)], folder / (name + '.log'))
        log = (folder / (name + '.log')).read_text()
        count = int(re.search(r'Total enable-feedback rebuilt: (\d+)', log)[1])
        assert count == int(name == 'positive'), (name, count)
        after = json.loads((folder / (name + '_after.json')).read_text())['modules']['test3']['cells']
        if name != 'positive':
            for n,c in cells.items():
                if c['type'] == '$dffe': assert after[n]['connections'] == c['connections'], name
    print('Isolated boundary checks passed', flush=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--resource-only', action='store_true')
    ns = ap.parse_args()
    out = ns.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    plugins = {}
    for label in ['baseline', 'candidate']:
        source = out / (label + '.cc')
        source.write_bytes(subprocess.check_output(['git', 'show', BASE + ':src/pmux_opt.cc'], cwd=ROOT)
                           if label == 'baseline' else (ROOT / 'src/pmux_opt.cc').read_bytes())
        plugin = out / (label + '.so')
        run(['yosys-config', '--build', str(plugin), str(source)], out / (label + '_build.log'))
        plugins[label] = plugin
    fixtures = out / 'fixtures'
    fixtures.mkdir()
    isolated = out / 'isolated.so'
    run(['yosys-config', '--build', str(isolated), '-I' + str(out),
         str(ROOT / 'tests/enable_feedback/isolated.cc')], out / 'isolated_build.log')
    boundary_checks(out, isolated)
    spec = importlib.util.spec_from_file_location('fixtures', ROOT / 'tests/enable_feedback/generate.py')
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    cases = [(f'test{i}', ROOT / f'pmux_case/competition_case/test{i}/test{i}.v', f'test{i}', int(i == 3)) for i in range(1, 5)]
    cases += generator.generate(ROOT, fixtures)
    rows = {}
    for name, rtl, top, expected in cases:
        rows[name] = {}
        for label, plugin in plugins.items():
            dest = out / name / label
            dest.mkdir(parents=True)
            ys = dest / 'run.ys'
            script = flow(rtl, top, dest)
            if name == 'external_case_equality':
                # Older expression folding treats outside inputs as X. This
                # fixture tests 6.1 alone, not that pre-existing rule.
                script = script.replace('pmux_opt', 'enable_feedback_test' if label == 'candidate' else 'opt_clean')
                plugin = isolated if label == 'candidate' else plugin
            ys.write_text(script)
            run(['yosys', '-Q', '-T', '-m', str(plugin), '-s', str(ys)], dest / 'run.log')
            cells = json.loads((dest / 'stat.json').read_text())['modules']['\\' + top]['num_cells_by_type']
            count = re.search(r'Total enable-feedback rebuilt: (\d+)', (dest / 'run.log').read_text())
            rows[name][label] = {'cells': cells, 'logic': cells.get('cycloneiv_lcell_comb', 0) + cells.get('$not', 0),
                                 'rebuilt': int(count[1]) if count else 0}
        b, c = rows[name]['baseline'], rows[name]['candidate']
        assert c['logic'] <= b['logic'], (name, rows[name])
        if name == 'test3':
            assert b['logic'] == 10 and c['logic'] == 9, (name, rows[name])
            assert b['cells'].get('dffeas') == c['cells'].get('dffeas') == 12
        elif name in ('test1', 'test2', 'test4'):
            assert c['cells'] == b['cells'], (name, rows[name])
        assert c['rebuilt'] == expected, (name, rows[name])
        for kind in set(b['cells']) | set(c['cells']):
            if kind not in ('$not', 'cycloneiv_lcell_comb'):
                assert c['cells'].get(kind, 0) <= b['cells'].get(kind, 0), (name, kind)
        if not ns.resource_only and (expected or name not in ('test1', 'test2', 'test4')):
            prove(rtl, top, out / name / 'candidate/rebuilt.il', out / name / 'formal')
            rows[name]['formal'] = 'PASS'
        if not ns.resource_only and name == 'test3':
            dest = out / name / 'candidate'
            extract = dest / 'extract.ys'
            extract.write_text(f'read_rtlil {dest}/post_abc.il\nselect {top}\nwrite_rtlil -selected {dest}/abc_top.il\nwrite_json {dest}/abc.json\n')
            run(['yosys', '-s', str(extract)], dest / 'extract.log')
            module = json.loads((dest / 'abc.json').read_text())['modules'][top]
            for cell in module['cells'].values():
                assert cell['type'] in ('$lut', 'dffeas'), cell['type']
                if cell['type'] == 'dffeas':
                    for port, value in [('clrn','1'), ('prn','1'), ('asdata','0'), ('aload','0'), ('sclr','0'), ('sload','0')]:
                        assert cell['connections'][port] == [value], (port, cell)
                    assert cell['connections']['clk'] == module['ports']['clk']['bits']
                    assert cell['parameters']['power_up'] == 'low'
            model = dest / 'dffeas.v'
            model.write_text('''module dffeas(output reg q, input d, clk, clrn, prn, ena, asdata, aload, sclr, sload);
parameter power_up="low", is_wysiwyg="false";
always @(posedge clk or negedge clrn)
    if (!clrn) q <= 0;
    else if (ena) q <= d;
endmodule
''')
            prove(rtl, top, dest / 'abc_top.il', out / name / 'formal_abc', model=model)
            rows[name]['formal_abc'] = 'PASS'
            badmodel = dest / 'negative_dffeas.v'
            badmodel.write_text(model.read_text().replace('q <= d;', 'q <= ~d;'))
            prove(rtl, top, dest / 'abc_top.il', out / name / 'negative_abc', negative=True, model=badmodel)
        print(name, rows[name], flush=True)
        (out / 'summary.json').write_text(json.dumps(rows, indent=2) + '\n')
    if not ns.resource_only:
        bad = fixtures / 'negative.v'
        original = (ROOT / 'pmux_case/competition_case/test3/test3.v').read_text()
        text = original.replace('gpioout[0] <= sr[0];', 'gpioout[0] <= ~sr[0];')
        assert text != original
        bad.write_text(text)
        ys = out / 'negative.ys'
        ys.write_text(f'read_verilog {bad}\nprep -top test3\nwrite_rtlil {out}/negative.il\n')
        run(['yosys', '-s', str(ys)], out / 'negative_build.log')
        prove(ROOT / 'pmux_case/competition_case/test3/test3.v', 'test3', out / 'negative.il', out / 'negative_formal', True)
    (out / 'source_manifest.json').write_text(json.dumps({label: hashlib.sha256((out/(label+'.cc')).read_bytes()).hexdigest() for label in plugins}, indent=2))
    print('All checks passed:', out)

if __name__ == '__main__':
    main()
