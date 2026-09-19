#!/usr/bin/env python3
"""Frozen P/R1 evaluation. Uses exact commit sources and unique output directories."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(args, log, timeout=120):
    with log.open('w') as stream:
        p = subprocess.Popen(args, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                             start_new_session=True)
        try:
            return p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            p.wait()
            return 124

def capture(args):
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()

def quote(path):
    return '"' + str(path).replace('\\', '\\\\').replace('"', '\\"') + '"'

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--suite', choices=['h1', 'public', 'all'], default='all')
    ap.add_argument('--flows', nargs='+', choices=['P', 'R1'], default=['P', 'R1'])
    ap.add_argument('--stable', default='244baaf19c8abf62443aabfb5ff449ff535a447d')
    ap.add_argument('--candidate', default='0c0ee40aabfaf62fad3ab7c04dd42d092d6ca483')
    ap.add_argument('--out', type=Path)
    ns = ap.parse_args()
    out = (ns.out or ROOT / 'results' / ('frozen_' + time.strftime('%Y%m%d_%H%M%S'))).resolve()
    out.mkdir(parents=True, exist_ok=False)
    manifest = {'flows': ns.flows, 'suite': ns.suite, 'sources': {}, 'inputs': {},
                'tool_paths': {name: shutil.which(name) for name in ['yosys', 'yosys-config', 'eqy', 'z3']},
                'runner_sha256': sha(Path(__file__)),
                'template_sha256': sha(ROOT / 'formal/templates/pairwise.eqy.in'),
                'worktree_status': capture(['git', 'status', '--short']),
                'tools': {name: capture([name, flag]) for name, flag in
                          [('yosys', '-V'), ('eqy', '--version'), ('z3', '--version')]}}
    plugins = {}
    for label, ref in [('stable', ns.stable), ('candidate', ns.candidate)]:
        commit = capture(['git', 'rev-parse', ref + '^{commit}'])
        source = out / (label + '.cc')
        source.write_bytes(subprocess.check_output(['git', 'show', commit + ':src/pmux_opt.cc'], cwd=ROOT))
        plugin = out / (label + '.so')
        rc = run(['yosys-config', '--build', str(plugin), str(source)], out / (label + '_build.log'), 180)
        if rc:
            raise RuntimeError(f'{label} build failed: {rc}; see {out}')
        plugins[label] = plugin
        manifest['sources'][label] = {'commit': commit, 'source_sha256': sha(source), 'plugin_sha256': sha(plugin)}
    cases = []
    if ns.suite in ('h1', 'all'):
        cases += [(p.stem, p, 'h1') for p in sorted((ROOT / 'tests/h1').glob('*.v'))]
    if ns.suite in ('public', 'all'):
        cases += [(f'test{i}', ROOT / f'pmux_case/competition_case/test{i}/test{i}.v', 'public') for i in range(1, 5)]
    expected_count = {'all': 16, 'h1': 12, 'public': 4}[ns.suite]
    if len(cases) != expected_count:
        raise RuntimeError(f'Expected {expected_count} cases, found {len(cases)}')
    template = (ROOT / 'formal/templates/pairwise.eqy.in').read_text(encoding='utf-8-sig')
    rows = []
    failed = False
    def equivalent(gold, gate, top, dest):
        cfg = dest.with_suffix('.eqy')
        cfg.write_text(template.format(gold=quote(gold), gate=quote(gate), top=top))
        log = dest.with_suffix('.log')
        rc = run(['eqy', '-j', '2', '-f', '-d', str(dest), str(cfg)], log)
        text = log.read_text(errors='replace')
        if rc == 124:
            return 'TIMEOUT'
        if rc == 0 and 'DONE (PASS' in text:
            return 'PASS'
        return 'FAIL_OR_UNKNOWN' if rc == 2 else 'ERROR'
    # Deliberately unequal outputs must be rejected by this exact EQY path.
    control = out / 'negative_control'
    control.mkdir()
    for label, expr in [('gold', 'a'), ('gate', '~a')]:
        rtl = control / (label + '.v')
        rtl.write_text(f'module top(input a, output y); assign y = {expr}; endmodule\n')
        ys = control / (label + '.ys')
        ys.write_text(f'read_verilog {quote(rtl)}\nprep -top top\nwrite_rtlil {quote(control / (label + ".il"))}\n')
        if run(['yosys', '-s', str(ys)], control / (label + '.log')):
            raise RuntimeError('Negative control synthesis failed')
    verdict = equivalent(control / 'gold.il', control / 'gate.il', 'top', control / 'eqy')
    manifest['negative_control'] = verdict
    if verdict != 'FAIL_OR_UNKNOWN':
        raise RuntimeError('Deliberately unequal control was not rejected: ' + verdict)
    for flow in ns.flows:
        for top, rtl, suite in cases:
            manifest['inputs'][str(rtl.relative_to(ROOT))] = sha(rtl)
            dest = out / flow / top
            dest.mkdir(parents=True)
            metrics = {}
            statuses = []
            for label in ['baseline', 'stable', 'candidate']:
                prefix = dest / label
                generic = prefix.with_suffix('.il')
                stat = prefix.with_suffix('.json')
                commands = [f'read_verilog -sv {quote(rtl)}', f'hierarchy -check -top {top}', 'proc']
                if flow == 'P':
                    commands.append('opt')
                if label != 'baseline':
                    commands.append('pmux_opt')
                commands += ['opt' if flow == 'P' else 'opt_clean']
                # Memory lowering is common to both endpoints, needed by test4 EQY.
                commands += ['check -assert', 'design -push-copy', 'memory_map', 'opt_clean', 'check -assert', f'write_rtlil {quote(generic)}', 'design -pop',
                             f'synth_intel -family cycloneiv -top {top}', 'check -assert',
                             f'tee -o {quote(stat)} stat -json']
                ys = prefix.with_suffix('.ys')
                ys.write_text('\n'.join(commands) + '\n')
                args = ['yosys']
                if label != 'baseline':
                    args += ['-m', str(plugins[label])]
                args += ['-s', str(ys)]
                timing = prefix.with_suffix('.time')
                rc = run(['/usr/bin/time', '-f', '%e %M', '-o', str(timing)] + args, prefix.with_suffix('.log'), 60)
                if rc:
                    statuses.append(label + (':TIMEOUT' if rc == 124 else ':ERROR'))
                    continue
                module = json.loads(stat.read_text())['modules']['\\' + top]
                cells = module['num_cells_by_type']
                elapsed, rss = timing.read_text().strip().split()
                logtext = prefix.with_suffix('.log').read_text()
                rebuild = re.search(r'Total pair-swap rebuilt: (\d+)', logtext)
                metrics[label] = {'total': module['num_cells'], 'comb': cells.get('cycloneiv_lcell_comb', 0),
                                  'dff': cells.get('dffeas', 0), 'seconds': float(elapsed), 'rss_kb': int(rss),
                                  'rebuilt': int(rebuild.group(1)) if rebuild else 0}
            row = {'flow': flow, 'case': top, 'suite': suite}
            for label, values in metrics.items():
                row.update({label + '_' + key: value for key, value in values.items()})
            if len(metrics) == 3:
                for gold, gate in [('baseline', 'candidate'), ('stable', 'candidate')]:
                    key = gold + '_vs_' + gate
                    row[key] = equivalent(dest / (gold + '.il'), dest / (gate + '.il'), top, dest / key)
                    if row[key] != 'PASS':
                        statuses.append(key + ':' + row[key])
                if flow == 'R1':
                    raw = dest / 'rtl_reference.il'
                    ys = dest / 'rtl_reference.ys'
                    ys.write_text(f'read_verilog -sv {quote(rtl)}\nhierarchy -check -top {top}\nproc\nmemory_map\nopt_clean\nwrite_rtlil {quote(raw)}\n')
                    rc = run(['yosys', '-s', str(ys)], dest / 'rtl_reference.log')
                    row['rtl_vs_candidate'] = equivalent(raw, dest / 'candidate.il', top, dest / 'rtl_vs_candidate') if rc == 0 else 'ERROR'
                    if row['rtl_vs_candidate'] != 'PASS':
                        statuses.append('rtl_vs_candidate:' + row['rtl_vs_candidate'])
                if metrics['candidate']['total'] > metrics['stable']['total'] or metrics['candidate']['total'] > metrics['baseline']['total']:
                    statuses.append('TOTAL_REGRESSION')
                if metrics['candidate']['rss_kb'] > 2_000_000:
                    statuses.append('RSS_LIMIT')
                if suite == 'h1' and flow == 'P':
                    expected = (1, 1) if top.startswith(('h1_p5', 'h1_p6')) else ((0, 1) if top.startswith('h1_p') else (0, 0))
                    if (metrics['stable']['rebuilt'], metrics['candidate']['rebuilt']) != expected:
                        statuses.append('TRIGGER_MISMATCH')
                    if expected == (0, 1) and metrics['candidate']['total'] >= metrics['stable']['total']:
                        statuses.append('H1_NO_GAIN')
            row['status'] = ';'.join(statuses) or 'PASS'
            failed |= bool(statuses)
            rows.append(row)
            print(flow, top, row['status'], flush=True)
            (out / 'summary.json').write_text(json.dumps(rows, indent=2))
            (out / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with (out / 'summary.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print('Output:', out, flush=True)
    return int(failed)

if __name__ == '__main__':
    raise SystemExit(main())
