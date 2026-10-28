"""V9: warmup, side-major initial runs, conditional five-pair time review."""
import json
import os
from pathlib import Path
import time
import uuid
import measure_v8 as native
import heap_policy as H
import official_suite as S
import result_layout as L
import builtin_common as B

SCHEME = 'pmux-perf-warm10-initial-review5-same-run-v9'
METHOD = native.METHOD
POLICY = dict(measurement_revision=H.REVISION, heap_policy=H.POLICY, same_run_metrics=True, warmup_per_case=10, initial_runs_per_side=1,
              initial_order='baseline_all_then_optimized_all', recheck_pairs=5,
              recheck_trigger='initial_time_over_5pct_and_baseline_under_10s',
              recheck_order='case_then_baseline_optimized_pairs',
              recheck_statistic='ratio_of_separate_mean_ticks_excluding_initial',
              memory_source='initial_only', absolute_limits_source='initial_only',
              stage_timeout_s=1800)
ARTIFACTS = native.ARTIFACTS
sha, save, compare = native.sha, native.save, native.compare


def sample_errors(row, require_outputs=False):
    errors = [] if row.get('performance_scheme') == SCHEME else ['V9 measurement identity mismatch']
    translated = dict(row, performance_scheme=native.SCHEME)
    return errors + H.sample_errors(row) + native.sample_errors(translated, require_outputs=require_outputs)


def run_combined_measured(*args, **kwargs):
    return native.run_combined_measured(*args, **kwargs, performance_scheme=SCHEME, measurement_revision=H.REVISION, heap_policy=H.POLICY)


def schedule(context, phase='initial', recheck_cases=()):
    cases = S.case_ids(context)
    if phase == 'warmup':
        pairs = [(c, 'baseline', n) for c in cases for n in range(1, 11)]
    elif phase == 'initial':
        pairs = [(c, s, 1) for s in ('baseline', 'optimized') for c in cases]
    elif phase == 'recheck':
        if len(set(recheck_cases)) != len(recheck_cases) or not set(recheck_cases) <= set(cases):
            raise ValueError('Unknown or duplicate recheck case')
        pairs = [(c, s, n) for c in cases if c in recheck_cases
                 for n in range(1, 6) for s in ('baseline', 'optimized')]
    else:
        raise ValueError('Unknown measurement phase')
    return [dict(phase=phase, case=c, side=s, repetition=n) for c, s, n in pairs]


def recheck_decision(base_ticks, opt_ticks):
    judgment = compare(base_ticks, opt_ticks)
    required = judgment['wall_5pct'] == 'FAIL' and base_ticks < 100_000_000
    scope = ('OFFICIAL_UNDER_1S' if base_ticks < 10_000_000 else 'USER_EXTENSION_1_TO_10S') if required else None
    return dict(required=required, scope=scope)


def evaluate_summary(summary):
    original = summary.get('samples') or []
    translated = dict(summary, performance_scheme=native.SCHEME, same_run_policy=native.POLICY,
                      execution_complete=True,
                      samples=[dict(r, performance_scheme=native.SCHEME) for r in original])
    result = native.evaluate_summary(translated)
    valid = (result['valid'] and summary.get('performance_scheme') == SCHEME
             and summary.get('same_run_policy') == POLICY
             and all(not sample_errors(r) for r in original))
    initial = dict(result)
    initial_valid = valid
    decision = recheck_decision(result['wall_base_ticks'], result['wall_opt_ticks']) if valid else dict(required=False, scope=None)
    reviews = summary.get('recheck_samples') or []
    if decision['required']:
        expected = [(n,s) for n in range(1,6) for s in ('baseline','optimized')]
        valid = (valid and summary.get('recheck_complete') is True and len(reviews) == 10
                 and [(r.get('repetition'),r.get('side')) for r in reviews] == expected
                 and len({r.get('sample_id') for r in original + reviews}) == 12
                 and all(r.get('case') == summary['case'] and r.get('phase') == 'recheck'
                         and r.get('repeat_evidence_ok') is True and not sample_errors(r) for r in reviews))
        if valid:
            bt = sum(r['time_span_ticks'] for r in reviews if r['side'] == 'baseline')
            ot = sum(r['time_span_ticks'] for r in reviews if r['side'] == 'optimized')
            result.update(compare(bt, ot), wall_base_ticks=bt / 5, wall_opt_ticks=ot / 5,
                          wall_base_ms=bt / 5 / 10000, wall_opt_ms=ot / 5 / 10000,
                          recheck_base_ticks_sum=bt, recheck_opt_ticks_sum=ot)
    else:
        valid = valid and not reviews
    case_valid = bool(valid)
    valid = case_valid and summary.get('execution_complete') is True
    result.update(valid=bool(valid), wall_valid=case_valid, memory_valid=bool(initial_valid),
                  initial_valid=bool(initial_valid), round_measurement_complete=summary.get('execution_complete') is True,
                  initial_wall_5pct=initial['wall_5pct'], initial_wall_15pct=initial['wall_15pct'],
                  initial_wall_overhead_pct=initial['wall_overhead_pct'],
                  initial_wall_base_ticks=initial['wall_base_ticks'], initial_wall_opt_ticks=initial['wall_opt_ticks'],
                  recheck_required=decision['required'], recheck_scope=decision['scope'],
                  time_decision_source=('RECHECK_MEAN' if case_valid else 'RECHECK_INCOMPLETE') if decision['required'] else 'INITIAL',
                  recheck_samples=reviews)
    if not case_valid:
        result.update(wall_5pct='INVALID', wall_15pct='INVALID', wall_verdict='INVALID')
        if decision['required']:
            result.update(wall_base_ticks=None,wall_opt_ticks=None,wall_base_ms=None,wall_opt_ms=None)
    result['any_over_15pct'] = bool((case_valid and result['wall_15pct'] == 'FAIL')
                                  or (initial_valid and result['memory_15pct'] == 'FAIL'))
    result['official_midband_score'] = ('NOT_DETERMINED' if not valid else 'ABOVE_15_THRESHOLD'
        if result['any_over_15pct'] else 'NOT_DETERMINED'
        if result['wall_5pct'] != 'PASS' or not result['mem_ok'] else 'UP_TO_5_THRESHOLD')
    result['pass'] = bool(valid and result['wall_5pct'] == 'PASS' and result['mem_ok'] and result['limit_ok'])
    result['reasons'] = ([f'V9测量或复核证据未闭合'] if not valid else
        (['最终相对时间超过5%'] if result['wall_5pct'] != 'PASS' else [])
        + (['首次内存超过5%'] if not result['mem_ok'] else [])
        + (['首次绝对限值未满足'] if not result['limit_ok'] else []))
    return result


def evidence_folder(root, item):
    if item['phase'] == 'initial':
        return root / L.PUBLIC / 'round01' / item['case'] / item['side']
    return root / L.PERFORMANCE / item['phase'] / item['case'] / f"r{item['repetition']:02d}" / item['side']


def resources(folder, top):
    stat = json.loads((folder / 'stat.json').read_text(encoding='utf-8'))
    result = B.parse_resource_counts(stat, (folder / 'mapped.il').read_text(encoding='utf-8'), top)
    result['total_cells'] = int(stat['design']['num_cells'])
    return result


NATIVE_FILES = ('measure_result.raw.json', 'combined_request.json', 'worker_response.json')


def native_errors(folder, row):
    errors=[]
    try:
        bound=row.get('native_evidence') or {}
        if set(bound)!=set(NATIVE_FILES):raise ValueError('Native evidence set missing')
        for name in NATIVE_FILES:
            if bound[name] != sha(folder/name):raise ValueError('Native evidence changed: '+name)
        raw=json.loads((folder/NATIVE_FILES[0]).read_text(encoding='utf-8'))
        ignored={'case','side','sample_id','phase','repetition'}
        if any(row.get(k)!=v for k,v in raw.items() if k not in ignored):raise ValueError('Raw/derived metrics mismatch')
        req=json.loads((folder/NATIVE_FILES[1]).read_text(encoding='utf-8'))
        if req.get('measurement_revision')!=H.REVISION or req.get('heap_policy')!=H.POLICY:raise ValueError('V9 heap request identity mismatch')
        if req.get('performance_scheme')!=SCHEME or req.get('method')!=METHOD or req.get('command')!=row.get('command'):
            raise ValueError('Native request scheme/method/command mismatch')
        for key,name in [('cwd',''),('log_path','run.log'),('result_path',NATIVE_FILES[0])]:
            if Path(req.get(key,'')).resolve()!=(folder/name).resolve():raise ValueError('Native request path mismatch: '+key)
        response=json.loads((folder/NATIVE_FILES[2]).read_text(encoding='utf-8'))
        if response.get('ok') is not True or not response.get('metrics'):raise ValueError('Native worker response invalid')
        if H.sample_errors(raw) or H.sample_errors(response['metrics']):raise ValueError('Native heap evidence missing/invalid')
        if any(raw.get(k)!=v for k,v in response['metrics'].items()):raise ValueError('Worker/raw metrics mismatch')
    except (OSError,ValueError,KeyError,TypeError) as exc:
        errors.append(str(exc))
    return errors


def tool_dependencies(context, side, binary):
    """Hash actual ABC and both direct/common/Intel mapping data outside timing."""
    binary=Path(binary)
    abc=Path(context['builtin']['abc'][side])
    candidates=(binary.parent/'share/yosys',binary.parent/'share',
                binary.parent.parent/'share/yosys',binary.parent.parent/'share')
    share=next((p for p in candidates if (p/'intel/cycloneiv/cells_map.v').is_file()),None)
    if share is None:raise ValueError('Missing actual Yosys share data')
    direct=context['tool_data_fourcase_filter']['direct_share_files']
    paths=[share/n for n in direct]+[p for p in (share/'intel').rglob('*') if p.is_file()]
    data={p.relative_to(share).as_posix():dict(path=str(p),sha256=sha(p)) for p in sorted(set(paths))}
    return dict(abc=dict(path=str(abc),sha256=sha(abc)),data=data)


def repeat_errors(row, first):
    errors = []
    for key in ('executable_sha256','tool_dependencies','input_sha256','input_path','flow_sha256','resource_counts'):
        if row.get(key) != first.get(key) or key not in row:
            errors.append('recheck differs from initial: ' + key)
    for name in ('post_abc.il','mapped.il'):
        if row.get('artifacts',{}).get(name,{}).get('sha256') != first.get('artifacts',{}).get(name,{}).get('sha256'):
            errors.append('recheck netlist differs from initial: ' + name)
    return errors


def run(context, round_dir, binaries, flows, *, execute=None):
    cases = S.case_ids(context)
    if (context.get('mode') != 'builtin' or context.get('performance_scheme') != SCHEME
            or context.get('same_run_policy') != POLICY or set(flows) != set(cases)):
        raise ValueError('V9 context or case set mismatch')
    execute = execute or run_combined_measured
    root = Path(round_dir); out = root / L.PERFORMANCE / 'round01'
    out.mkdir(parents=True, exist_ok=False)
    (root / L.PUBLIC / 'round01').mkdir(parents=True, exist_ok=False)
    specs = {c['id']:c for c in S.context_cases(context)}
    ps = Path(context['wall_time_tool']['path'])
    binary_hashes = {s:sha(p) for s,p in binaries.items()}
    dependencies={s:tool_dependencies(context,s,p) for s,p in binaries.items()}
    (root/L.META).mkdir(parents=True,exist_ok=True)
    save(root/L.META/'measurement_dependencies.json',dict(performance_scheme=SCHEME,by_side=dependencies))
    ledger = dict(schema=2, performance_scheme=SCHEME, expected_runs=2*len(cases),
                  schedule=schedule(context), phases={}, attempts=[], attempted_runs=0,
                  started_runs=0, completed_runs=0, execution_complete=False)
    initial = {}; reviews = {c:[] for c in cases}; failure = None; triggered = []
    def persist():
        first = ledger['phases'].get('initial',{})
        for k in ('attempts','attempted_runs','started_runs','completed_runs'):
            ledger[k] = first.get(k, [] if k == 'attempts' else 0)
        for key in ('attempted_runs','started_runs','completed_runs'):
            ledger['total_public_'+key] = sum(p[key] for p in ledger['phases'].values())
        save(out / 'synthesis_ledger.json', ledger)
    try:
        for phase in ('warmup','initial','recheck'):
            if phase == 'recheck':
                triggered = [c for c in cases if recheck_decision(initial[(c,'baseline')]['time_span_ticks'],
                                                                 initial[(c,'optimized')]['time_span_ticks'])['required']]
                ledger['recheck_cases'] = triggered
            plan = schedule(context,phase,triggered)
            phase_ledger = dict(schedule=plan,expected_runs=len(plan),attempted_runs=0,
                                started_runs=0,completed_runs=0,attempts=[],execution_complete=False)
            ledger['phases'][phase] = phase_ledger
            started = time.monotonic();persist()
            for item in plan:
                folder = L.contained_path(root, *evidence_folder(root,item).relative_to(root).parts)
                folder.mkdir(parents=True,exist_ok=False)
                flow = flows[item['case']]
                (folder/'flow.ys').write_text(flow,encoding='utf-8')
                row = dict(item,sample_id=uuid.uuid4().hex,evidence_dir=str(folder),
                           performance_scheme=SCHEME,wall_time_method=METHOD)
                attempt=dict(row);phase_ledger['attempts'].append(attempt)
                phase_ledger['attempted_runs']+=1;persist()
                try:
                    remaining = POLICY['stage_timeout_s']-(time.monotonic()-started)-45
                    if remaining <= 0:raise TimeoutError(phase+' protection limit')
                    side=item['side'];binary=binaries[side]
                    if sha(binary)!=binary_hashes[side]:raise ValueError('Tool changed during round')
                    if tool_dependencies(context,side,binary)!=dependencies[side]:raise ValueError('ABC/data changed before sample')
                    rtl_line=next(line for line in flow.splitlines() if line.startswith('read_verilog -sv '))
                    rtl=Path(rtl_line[len('read_verilog -sv '):].strip().strip('"'))
                    input_hash=sha(rtl)
                    command=[str(binary),'-s','flow.ys']
                    row.update(execute(command,cwd=folder,log_path=folder/'run.log',timeout_s=remaining,
                                       powershell_path=ps,env=os.environ.copy()))
                    if row.get('performance_scheme') != SCHEME or row.get('wall_time_method') != METHOD:
                        raise ValueError('Raw native measurement returned a different scheme/method')
                    row.update(item,sample_id=attempt['sample_id'],evidence_dir=str(folder),command=command,
                               performance_scheme=SCHEME,wall_time_method=METHOD,
                               tool_dependencies=tool_dependencies(context,side,binary),
                               executable_sha256=sha(binary),input_path=str(rtl),input_sha256=sha(rtl),
                               flow_sha256=sha(folder/'flow.ys'))
                    row['powershell_identity_match']=(Path(row.get('powershell_path','')).resolve()==ps.resolve()
                                                       and row.get('powershell_sha256')==sha(ps))
                    row['artifacts']={n:dict(path=str(folder/n),sha256=sha(folder/n)) for n in ARTIFACTS if (folder/n).is_file()}
                    row['native_evidence']={n:sha(folder/n) for n in NATIVE_FILES}
                    errors=sample_errors(row,require_outputs=True)+native_errors(folder,row)
                    if row['tool_dependencies']!=dependencies[side]:errors.append('ABC/data changed during sample')
                    if row['executable_sha256']!=binary_hashes[side] or row['input_sha256']!=input_hash:
                        errors.append('Tool/input changed inside sample')
                    if errors:raise ValueError('; '.join(errors))
                    row['resource_counts']=resources(folder,specs[item['case']]['top'])
                    if phase=='initial':initial[(item['case'],side)]=row
                    if phase=='recheck':
                        errors=repeat_errors(row,initial[(item['case'],side)])
                        row['repeat_evidence_ok']=not errors
                        if errors:raise ValueError('; '.join(errors))
                    phase_ledger['completed_runs']+=1
                except (Exception,KeyboardInterrupt) as exc:
                    row['measurement_error']=type(exc).__name__+': '+str(exc)
                    row['sample_errors']=[row['measurement_error']]
                    raise
                finally:
                    if type(row.get('main_pid')) is int and row['main_pid']>0:
                        phase_ledger['started_runs']+=1;attempt['yosys_pid']=row['main_pid']
                    if phase=='recheck':reviews[item['case']].append(row)
                    save(folder/'measure_result.json',row);persist()
                print(phase,item['case'],item['side'],item['repetition'],'VALID',flush=True)
            phase_ledger['execution_complete']=True;persist()
        ledger['execution_complete']=True
    except (Exception,KeyboardInterrupt) as exc:
        failure=type(exc).__name__+': '+str(exc)
        print('STOP',failure,flush=True)
    ledger['error']=failure;persist()
    summaries=[dict(case=c,performance_scheme=SCHEME,same_run_policy=POLICY,
                    execution_complete=ledger['execution_complete'],
                    samples=[initial[(c,s)] for s in ('baseline','optimized') if (c,s) in initial],
                    recheck_samples=reviews[c],recheck_complete=(c in triggered and len(reviews[c])==10 and not failure)) for c in cases]
    save(out/'performance_summary.json',summaries)
    return 0 if ledger['execution_complete'] else 1


def verify_run_evidence(root, context):
    """Rebuild phase expectations from raw first runs; summaries are not authority."""
    root=Path(root);errors=[];all_rows=[]
    try:
        ledger=json.loads((root/L.PERFORMANCE/'round01/synthesis_ledger.json').read_text(encoding='utf-8'))
        if ledger.get('performance_scheme')!=SCHEME or ledger.get('execution_complete') is not True:
            raise ValueError('V9 ledger incomplete or wrong version')
        first={}
        specs={c['id']:c for c in S.context_cases(context)}
        summaries=json.loads((root/L.PERFORMANCE/'round01/performance_summary.json').read_text(encoding='utf-8'))
        dep=json.loads((root/L.META/'measurement_dependencies.json').read_text(encoding='utf-8'))
        if dep.get('performance_scheme')!=SCHEME:raise ValueError('Dependency metadata scheme mismatch')
        triggers=[]
        for phase in ('warmup','initial','recheck'):
            if phase=='recheck':
                triggers=[c for c in S.case_ids(context) if recheck_decision(first[(c,'baseline')]['time_span_ticks'],first[(c,'optimized')]['time_span_ticks'])['required']]
            expected=schedule(context,phase,triggers);p=ledger['phases'][phase]
            if (p.get('schedule')!=expected or p.get('expected_runs')!=len(expected)
                    or p.get('execution_complete') is not True or len(p.get('attempts',[]))!=len(expected)
                    or any(p.get(k)!=len(expected) for k in ('attempted_runs','started_runs','completed_runs'))):
                raise ValueError('Phase ledger mismatch: '+phase)
            for item,attempt in zip(expected,p['attempts']):
                folder=evidence_folder(root,item)
                row=json.loads((folder/'measure_result.json').read_text(encoding='utf-8'))
                issues=sample_errors(row,require_outputs=True)+native_errors(folder,row)
                if issues:raise ValueError('; '.join(issues))
                if any(row.get(k)!=v or attempt.get(k)!=v for k,v in item.items()):raise ValueError('Sample order/identity mismatch')
                if row.get('sample_id')!=attempt.get('sample_id') or row.get('main_pid')!=attempt.get('yosys_pid'):raise ValueError('Attempt/sample mismatch')
                for n,spec in row['artifacts'].items():
                    if Path(spec['path']).resolve()!=(folder/n).resolve():raise ValueError('Artifact outside sample')
                if row['flow_sha256']!=sha(folder/'flow.ys') or row['input_sha256']!=sha(row['input_path']):raise ValueError('Input/flow changed')
                binary=context['builtin'][item['side']]
                if row['executable_sha256']!=binary['binary_sha256']:raise ValueError('Tool identity mismatch')
                if row.get('tool_dependencies')!=dep['by_side'][item['side']]:raise ValueError('ABC/data fingerprint mismatch')
                if row['resource_counts']!=resources(folder,specs[item['case']]['top']):raise ValueError('Resource record mismatch')
                if phase=='initial':first[(item['case'],item['side'])]=row
                if phase=='recheck' and (repeat_errors(row,first[(item['case'],item['side'])]) or row.get('repeat_evidence_ok') is not True):raise ValueError('Recheck differs')
                all_rows.append(row)
        if len({r['sample_id'] for r in all_rows})!=len(all_rows):raise ValueError('Duplicate sample ID')
        for row in all_rows:
            first_row=first[(row['case'],row['side'])]
            for key in ('input_path','input_sha256','flow_sha256','executable_sha256'):
                if row.get(key)!=first_row.get(key):raise ValueError('Phase input/flow/tool identity changed: '+key)
        if ledger.get('recheck_cases')!=triggers:raise ValueError('Wrong trigger set')
        p=ledger['phases']['initial']
        for key in ('attempts','attempted_runs','started_runs','completed_runs','schedule','expected_runs'):
            if ledger.get(key)!=p[key]:raise ValueError('Initial ledger alias mismatch')
        for key in ('attempted_runs','started_runs','completed_runs'):
            if ledger.get('total_public_'+key)!=sum(p[key] for p in ledger['phases'].values()):raise ValueError('Total ledger mismatch')
        if len(summaries)!=len(specs) or [s['case'] for s in summaries]!=list(S.case_ids(context)):raise ValueError('Summary cases mismatch')
        for summ in summaries:
            c=summ['case']; expected_first=[first[(c,s)] for s in ('baseline','optimized')]
            expected_reviews=[r for r in all_rows if r['phase']=='recheck' and r['case']==c]
            if summ.get('samples')!=expected_first or summ.get('recheck_samples')!=expected_reviews or not evaluate_summary(summ)['valid']:
                raise ValueError('Summary differs from original samples')
    except (OSError,ValueError,KeyError,TypeError) as exc:
        errors.append(str(exc))
    return dict(ok=not errors,errors=errors,verified_public_samples=len(all_rows))


def main():
    import p3_common as C
    flows={c['id']:B.gen_builtin_formal_ys(L.validate_output_root(S.case_path(C.TREE,c)),c['top']) for c in S.context_cases(C.CONTEXT)}
    return run(C.CONTEXT,C.ROUND_DIR,B.select_binaries(C.CONTEXT['builtin']),flows)


if __name__=='__main__':raise SystemExit(main())
