"""Eight official syntheses; each process supplies time, root peak and netlists."""
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

from measure_v7 import compare
from process_utils import process_group_kwargs, terminate_process_tree

SCHEME = 'pmux-perf-single-powershell-same-run-exitpeak-v8'
METHOD = 'powershell-measure-command-same-run-wall-v2'
POLICY = {'synthesis_runs_per_side': 1, 'same_run_metrics': True, 'stage_timeout_s': 1800}
CASES = ('test1', 'test2', 'test3', 'test4')
ARTIFACTS = ('flow.ys', 'run.log', 'post_abc.il', 'post_abc_stat.json', 'mapped.il', 'stat.json')


def save(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def schedule():
    for case in CASES:
        for side in ('baseline', 'optimized'):
            yield {'case': case, 'side': side}


def sample_errors(row, require_outputs=False):
    errors = []
    if row.get('performance_scheme') != SCHEME or row.get('wall_time_method') != METHOD:
        errors.append('joint measurement identity mismatch')
    for key in ('metrics_valid', 'root_debugged', 'memory_capture_complete',
                'memory_exit_event_observed', 'memory_root_process_only',
                'process_exit_observed', 'output_capture_complete'):
        if row.get(key) is not True:
            errors.append(key + ' missing/false')
    pid = row.get('main_pid')
    if type(pid) is not int or pid <= 0 or any(row.get(k) != pid for k in
            ('yosys_pid', 'time_pid', 'memory_exit_event_pid')):
        errors.append('time/memory root PID mismatch')
    if row.get('rc') != 0 or row.get('timed_out') is not False:
        errors.append('native synthesis failed or timed out')
    if 'measurement_error' not in row or row.get('measurement_error') not in (None, ''):
        errors.append('measurement error missing/nonempty')
    if row.get('memory_method_version') != 'windows-root-exit-event-v1' or row.get('memory_sample_count') != 1:
        errors.append('root exit-event method mismatch')
    peak = row.get('yosys_peak_working_set_bytes')
    if type(peak) is not int or peak <= 0:
        errors.append('peak working set missing/invalid')
    ticks, ms = row.get('time_span_ticks'), row.get('total_milliseconds')
    if type(ticks) is not int or ticks <= 0 or not isinstance(ms, (int, float)) \
            or not math.isfinite(ms) or not math.isclose(ms, ticks / 10000, rel_tol=0, abs_tol=1e-8):
        errors.append('Measure-Command elapsed value missing/inconsistent')
    if row.get('powershell_major') != 5 or row.get('powershell_minor') != 1:
        errors.append('Windows PowerShell 5.1 required')
    if require_outputs:
        evidence = row.get('artifacts') or {}
        if set(evidence) != set(ARTIFACTS):
            errors.append('required synthesis artifacts missing')
        for name, spec in evidence.items():
            path = Path(spec.get('path', ''))
            if not path.is_file() or sha(path) != spec.get('sha256'):
                errors.append('artifact hash mismatch: ' + name)
        if row.get('powershell_identity_match') is not True:
            errors.append('PowerShell executable identity mismatch')
    return errors


def evaluate_summary(summary):
    rows = summary.get('samples') or []
    valid = (summary.get('performance_scheme') == SCHEME
             and summary.get('same_run_policy') == POLICY
             and summary.get('execution_complete') is True and len(rows) == 2
             and {r.get('side') for r in rows} == {'baseline', 'optimized'}
             and len({r.get('sample_id') for r in rows}) == 2
             and all(r.get('case') == summary.get('case') and not sample_errors(r) for r in rows))
    by = {r.get('side'): r for r in rows}
    b, o = by.get('baseline', {}), by.get('optimized', {})
    bt, ot = (b.get('time_span_ticks'), o.get('time_span_ticks')) if valid else (None, None)
    bm, om = (b.get('yosys_peak_working_set_bytes'), o.get('yosys_peak_working_set_bytes')) if valid else (None, None)
    judgment = compare(bt, ot)
    mem_ok = bool(valid and om * 100 <= bm * 105)
    mem15 = bool(valid and om * 100 <= bm * 115)
    over15 = bool(valid and (judgment['wall_15pct'] == 'FAIL' or not mem15))
    wall_abs = bool(valid and (ot <= 60 * 10_000_000 or bt > 60 * 10_000_000))
    mem_abs = bool(valid and (om <= 2 * 1024**3 or bm > 2 * 1024**3))
    if over15:
        judgment['official_midband_score'] = 'ABOVE_15_THRESHOLD'
    elif valid and (not mem_ok or judgment['wall_5pct'] != 'PASS'):
        judgment['official_midband_score'] = 'NOT_DETERMINED'
    reasons = []
    if not valid: reasons.append('同次样本缺失、无效或八次正式综合未完成')
    if valid and judgment['wall_5pct'] != 'PASS': reasons.append('墙钟时间相对开销超过本地5%目标')
    if valid and not mem_ok: reasons.append('内存相对开销超过5%')
    if valid and not (wall_abs and mem_abs): reasons.append('超过60秒/2GiB且原版未超限')
    return dict(case=summary.get('case'), valid=valid, wall_valid=valid, memory_valid=valid,
                wall_base_ticks=bt, wall_opt_ticks=ot,
                wall_base_ms=bt / 10000 if valid else None, wall_opt_ms=ot / 10000 if valid else None,
                **judgment, base_memory_bytes=bm, opt_memory_bytes=om,
                base_memory_mib=bm / 1024**2 if valid else None,
                opt_memory_mib=om / 1024**2 if valid else None,
                mem_overhead_pct=(om / bm - 1) * 100 if valid else None,
                mem_ok=mem_ok, memory_15pct='PASS' if mem15 else 'FAIL' if valid else 'INVALID',
                any_over_15pct=over15, wall_absolute_ok=wall_abs, memory_absolute_ok=mem_abs,
                limit_ok=wall_abs and mem_abs,
                limit_bits={'wall_exempt_upstream_over_60s': bool(valid and bt > 60 * 10_000_000),
                            'memory_exempt_upstream_over_2gib': bool(valid and bm > 2 * 1024**3)},
                **{'pass': bool(valid and judgment['wall_5pct'] == 'PASS' and mem_ok and wall_abs and mem_abs)},
                reasons=reasons)


def run_combined_measured(command, *, cwd, log_path, timeout_s, powershell_path, env=None):
    folder = Path(cwd)
    request_path = folder / 'combined_request.json'
    raw_path = folder / 'measure_result.raw.json'
    save(request_path, {'schema': 1, 'command': list(map(str, command)),
                       'cwd': str(folder), 'log_path': str(log_path), 'timeout_s': timeout_s,
                       'python': sys.executable, 'runner': str(Path(__file__).parent),
                       'result_path': str(raw_path), 'performance_scheme': SCHEME, 'method': METHOD})
    host_log = folder / 'measurement_host.log'
    with host_log.open('xb') as stream:
        process = subprocess.Popen([str(powershell_path), '-NoLogo', '-NoProfile', '-NonInteractive',
                    '-ExecutionPolicy', 'Bypass', '-File', str(Path(__file__).with_name('measure_command_v8.ps1')),
                    '-RequestPath', str(request_path)], stdout=stream, stderr=subprocess.STDOUT,
                    cwd=folder, env=env, **process_group_kwargs())
        try:
            rc = process.wait(timeout=timeout_s + 45)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            terminate_process_tree(process); process.wait()
            raise TimeoutError('combined measurement host timed out; no replacement run')
    if not raw_path.is_file():
        raise RuntimeError('measurement host did not save its raw result; rc=' + str(rc))
    row = json.loads(raw_path.read_text(encoding='utf-8-sig'))
    if rc and not row.get('measurement_error'):
        row['measurement_error'] = 'measurement host rc=' + str(rc)
    return row


def run(context, round_dir, binaries, flows, *, execute=None):
    if context.get('mode') != 'builtin' or context.get('performance_scheme') != SCHEME \
            or context.get('same_run_policy') != POLICY or set(flows) != set(CASES):
        raise ValueError('V8 fixed four-case joint policy mismatch')
    execute = execute or run_combined_measured
    root = Path(round_dir)
    pub = root / '05_公开四例_public/round01'
    out = root / '09_时间内存开销_performance/round01'
    pub.mkdir(parents=True, exist_ok=False); out.mkdir(parents=True, exist_ok=False)
    samples = []; failure = None; started = time.monotonic()
    ledger = {'schema': 1, 'performance_scheme': SCHEME, 'expected_runs': 8,
              'attempted_runs': 0, 'started_runs': 0, 'completed_runs': 0, 'execution_complete': False,
              'schedule': list(schedule()), 'attempts': []}
    ps = Path(context['wall_time_tool']['path'])
    for item in schedule():
        case, side = item['case'], item['side']
        folder = pub / case / side; folder.mkdir(parents=True)
        flow = flows[case]; (folder / 'flow.ys').write_text(flow, encoding='utf-8')
        sample_id = uuid.uuid4().hex
        ledger['attempted_runs'] += 1
        ledger['attempts'].append(dict(item, sample_id=sample_id, evidence_dir=str(folder)))
        save(out / 'synthesis_ledger.json', ledger)
        row = dict(item, sample_id=sample_id, performance_scheme=SCHEME, wall_time_method=METHOD)
        try:
            remaining = POLICY['stage_timeout_s'] - (time.monotonic() - started) - 45
            if remaining <= 0: raise TimeoutError('30 minute performance protection limit')
            command = [str(binaries[side]), '-s', 'flow.ys']
            result = execute(command, cwd=folder, log_path=folder / 'run.log', timeout_s=remaining,
                             powershell_path=ps, env=os.environ.copy())
            row.update(result)
            row.update(item, sample_id=sample_id, performance_scheme=SCHEME, wall_time_method=METHOD,
                       evidence_dir=str(folder), command=command, executable_sha256=sha(binaries[side]),
                       flow_sha256=sha(folder / 'flow.ys'))
            row['powershell_identity_match'] = (
                Path(row.get('powershell_path', '')).resolve() == ps.resolve()
                and row.get('powershell_sha256') == sha(ps))
            rtl_line = next(line for line in flow.splitlines() if line.startswith('read_verilog -sv '))
            rtl = Path(rtl_line[len('read_verilog -sv '):].strip().strip('"'))
            row.update(input_path=str(rtl), input_sha256=sha(rtl))
            row['artifacts'] = {name: {'path': str(folder / name), 'sha256': sha(folder / name)}
                                for name in ARTIFACTS if (folder / name).is_file()}
            row['sample_errors'] = sample_errors(row, require_outputs=True)
            if row['sample_errors']: failure = '; '.join(row['sample_errors'])
            else: ledger['completed_runs'] += 1
        except Exception as exc:
            failure = str(exc); row['sample_errors'] = [failure]
            row['measurement_error'] = row.get('measurement_error') or failure
        if type(row.get('main_pid')) is int and row['main_pid'] > 0:
            ledger['started_runs'] += 1
            ledger['attempts'][-1]['yosys_pid'] = row['main_pid']
        samples.append(row); save(folder / 'measure_result.json', row)
        save(out / 'synthesis_ledger.json', ledger)
        print(case, side, 'VALID' if not failure else 'INVALID', flush=True)
        if failure: break
    complete = failure is None and ledger['attempted_runs'] == ledger['started_runs'] == ledger['completed_runs'] == 8
    ledger.update(execution_complete=complete, error=failure)
    save(out / 'synthesis_ledger.json', ledger)
    summaries = [dict(case=case, performance_scheme=SCHEME, same_run_policy=POLICY,
                      memory_metric='yosys_peak_working_set_bytes', execution_complete=complete,
                      samples=[r for r in samples if r['case'] == case]) for case in CASES]
    save(out / 'performance_summary.json', summaries)
    return 0 if complete else 1


def main():
    import p3_common as C
    import builtin_common as B
    flows = {}
    for case in CASES:
        rtl = C.stage_to_ascii_bridge(C.TREE / f'pmux_case/competition_case/{case}/{case}.v',
                                     f'builtin_inputs/{case}.v')
        flows[case] = B.gen_builtin_formal_ys(rtl, case)
    return run(C.CONTEXT, C.ROUND_DIR, B.select_binaries(C.CONTEXT['builtin']), flows)


if __name__ == '__main__':
    raise SystemExit(main())
