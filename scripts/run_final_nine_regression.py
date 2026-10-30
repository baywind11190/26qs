#!/usr/bin/env python3
"""Check a built-in PMUX candidate against stock on all supplied cases."""

import argparse
import importlib.util
import json
import statistics
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / 'tests/local_lut/dffeas_model.v'


def cases():
    public = [(f'test{i}', ROOT / f'pmux_case/competition_case/test{i}/test{i}.v')
              for i in range(1, 5)]
    added = [(p.stem, p) for p in sorted((ROOT / 'tests/official_new5').glob('*.v'))]
    assert len(added) == 5, 'Expected all five supplied new cases'
    return public + added


def run_yosys(executable, script, log):
    with log.open('w') as stream:
        subprocess.run([str(executable), '-Q', '-s', str(script)], cwd=ROOT,
                       stdout=stream, stderr=subprocess.STDOUT, check=True, timeout=300)


def check_gate_model(path, top):
    cells = json.loads(path.read_text())['modules'][top]['cells'].values()
    for cell in cells:
        if cell['type'] == '$lut':
            continue
        assert cell['type'] == 'dffeas', (top, cell['type'])
        for port, value in [('prn', '1'), ('asdata', '0'), ('aload', '0'),
                            ('sclr', '0'), ('sload', '0')]:
            assert cell['connections'][port] == [value], (top, port)
        assert cell['parameters']['power_up'] in ('low', 'high', 'dontcare')


def negative_control(helper, candidate, out):
    import copy

    top = 'pmux_case01_balanced'
    source = out / top / 'candidate/post_abc.json'
    design = json.loads(source.read_text())
    module = copy.deepcopy(design['modules'][top])
    cells = module['cells']
    ff = next(cell for cell in cells.values() if cell['type'] == 'dffeas')
    old_d = ff['connections']['d']
    fresh = 1 + max(bit for cell in cells.values()
                    for signal in cell['connections'].values()
                    for bit in signal if isinstance(bit, int))
    ff['connections']['d'] = [fresh]
    cells['deliberate_negative_inversion'] = {
        'hide_name': 0, 'type': '$lut',
        'parameters': {'WIDTH': format(1, '032b'), 'LUT': '01'},
        'attributes': {}, 'port_directions': {'A': 'input', 'Y': 'output'},
        'connections': {'A': old_d, 'Y': [fresh]},
    }
    design['modules'] = {top: module}
    folder = out / 'negative'
    folder.mkdir()
    bad_json = folder / 'negative.json'
    bad_json.write_text(json.dumps(design))
    script = folder / 'convert.ys'
    script.write_text(f'read_json {bad_json}\nwrite_rtlil {folder}/negative.il\n')
    run_yosys(candidate, script, folder / 'convert.log')
    rtl = ROOT / f'tests/official_new5/{top}.v'
    helper.prove(rtl, top, folder / 'negative.il', folder / 'formal',
                 negative=True, model=MODEL)
    (folder / 'result.json').write_text(json.dumps({'base_case_counterexample': True}, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', required=True, type=Path)
    parser.add_argument('--candidate', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--resource-only', action='store_true')
    args = parser.parse_args()
    baseline, candidate = args.baseline.resolve(), args.candidate.resolve()
    assert baseline.is_file() and candidate.is_file()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    rows = {}
    for top, rtl in cases():
        rows[top] = {}
        for label, executable in [('baseline', baseline), ('candidate', candidate)]:
            folder = out / top / label
            folder.mkdir(parents=True)
            script = folder / 'flow.ys'
            script.write_text(
                f'read_verilog -sv {rtl}\n'
                f'synth_intel -family cycloneiv -top {top} -run begin:map_cells\n'
                f'select {top}\n'
                f'write_rtlil -selected {folder}/post_abc.il\n'
                f'write_json {folder}/post_abc.json\n'
                f'select -clear\n'
                f'synth_intel -family cycloneiv -top {top} -run map_cells:\n'
                f'tee -o {folder}/stat.json stat -json\n'
            )
            run_yosys(executable, script, folder / 'run.log')
            types = json.loads((folder / 'stat.json').read_text())['modules']['\\' + top]['num_cells_by_type']
            rows[top][label] = {
                'logic': types.get('cycloneiv_lcell_comb', 0) + types.get('$not', 0),
                'dff': types.get('dffeas', 0),
                'cells': types,
            }
        base, result = rows[top]['baseline'], rows[top]['candidate']
        assert result['logic'] <= base['logic'], (top, base, result)
        rows[top]['area_reduction_percent'] = 100 * (1 - result['logic'] / base['logic'])
        print(top, base['logic'], result['logic'], rows[top]['area_reduction_percent'], flush=True)
    average = statistics.mean(row['area_reduction_percent'] for row in rows.values())
    summary = {'average_area_reduction_percent': average,
               'all_cases_no_logic_increase': True,
               'case_count': len(rows)}
    (out / 'resources.json').write_text(json.dumps(rows, indent=2))
    (out / 'summary.json').write_text(json.dumps(summary, indent=2))
    print('AVERAGE', average, flush=True)
    assert average > 20, f'Average area reduction must exceed 20%, got {average:.8f}%'
    if args.resource_only:
        return

    spec = importlib.util.spec_from_file_location('formal_helper', ROOT / 'scripts/run_enable_feedback_regression.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    formal = {}
    for top, rtl in cases():
        folder = out / top / 'candidate'
        check_gate_model(folder / 'post_abc.json', top)
        helper.prove(rtl, top, folder / 'post_abc.il', folder / 'formal', model=MODEL)
        formal[top] = 'PASS actual induction'
        (out / 'formal.json').write_text(json.dumps(formal, indent=2))
        print('FORMAL', top, formal[top], flush=True)
    negative_control(helper, candidate, out)
    print('NEGATIVE actual base-case counterexample detected', flush=True)


if __name__ == '__main__':
    main()
