"""Fixed complete-process CPU blocks, independent AA control, then root memory."""
import csv
import hashlib
import json
from pathlib import Path
import statistics
import time

from cpu_statistics import POLICY, SCHEME, analyse_cpu_runs, aa_is_healthy, cpu_sample_errors, judge_cpu
from cpu_qualification import qualification_status, environment

CASES=('test1','test2','test3','test4')


def schedule():
    for block in range(1,21):
        def aa():
            for pair in range(1,6):
                for side in (('baseline','optimized') if (block+pair)%2==0 else ('optimized','baseline')):
                    yield dict(purpose='aa',case='test2',side=side,block=block,pair=pair)
        if block%2:yield from aa()
        offset=(block-1)%4
        for case in CASES[offset:]+CASES[:offset]:
            for pair in range(1,16):
                for side in (('baseline','optimized') if (block+pair)%2==0 else ('optimized','baseline')):
                    yield dict(purpose='cpu',case=case,side=side,block=block,pair=pair)
        if not block%2:yield from aa()
    for case in CASES:
        for pair in range(1,16):
            for side in (('baseline','optimized') if pair%2 else ('optimized','baseline')):
                yield dict(purpose='memory',case=case,side=side,block=1,pair=pair)


def save(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def resource_signature(path):
    d=json.loads(Path(path).read_text(encoding='utf-8'))['design']
    return {key:d.get(key) for key in ('num_cells_by_type','num_ports','num_port_bits')}


def memory_errors(row):
    errors=[]
    for key in ('metrics_valid','memory_capture_complete','memory_exit_event_observed','root_debugged',
                'stat_exists','resource_match','flow_match'):
        if row.get(key) is not True:errors.append(key+' missing/false')
    if row.get('rc')!=0 or row.get('timed_out') is not False:errors.append('memory execution failed')
    if 'measurement_error' not in row or row.get('measurement_error') not in (None,''):errors.append('memory measurement error missing/nonempty')
    if row.get('memory_method_version')!='windows-root-exit-event-v1':errors.append('memory method mismatch')
    if type(row.get('main_pid')) is not int or row['main_pid']<=0 or row.get('memory_exit_event_pid')!=row['main_pid']:
        errors.append('memory exit-event PID mismatch')
    if type(row.get('yosys_peak_working_set_bytes')) is not int or row['yosys_peak_working_set_bytes']<=0:
        errors.append('memory peak missing/invalid')
    return errors


def run(context,round_dir,binaries,flows,*,cpu_execute=None,memory_execute=None):
    from win_measure import run_cpu_measured,run_measured
    cpu_execute=cpu_execute or run_cpu_measured;memory_execute=memory_execute or run_measured
    if context.get('cpu_policy')!=POLICY:raise ValueError('v4 fixed policy mismatch')
    root=Path(round_dir);out=root/'09_时间内存开销_performance/round01'
    out.mkdir(parents=True,exist_ok=False)
    qualifier=qualification_status(context,root/'03_脚本与插件_runner')
    save(out/'qualification.json',qualifier)
    save(out/'environment.json',environment())
    if not qualifier['qualified']:
        save(out/'execution_status.json',dict(complete=False,error='CPU method not qualified',detail=qualifier['reason']))
        return 3
    expected={(c,s):resource_signature(root/f'05_公开四例_public/round01/{c}/{s}/stat.json') for c in CASES for s in binaries}
    summaries={c:dict(case=c,performance_scheme=SCHEME,cpu_policy=POLICY,
        memory_metric='yosys_peak_working_set_bytes',cpu_runs=[],memory_runs=[],
        method_certificate=qualifier['certificate'],qualification_fingerprint=qualifier['fingerprint']) for c in CASES}
    aa=[];started=time.monotonic();deadline=started+1800;error=None;completed=0
    try:
        for item in schedule():
            remaining=deadline-time.monotonic()
            if remaining<=0:raise TimeoutError('30 minute performance protection limit')
            purpose,case,side=item['purpose'],item['case'],item['side']
            actual_side='baseline' if purpose=='aa' else side
            folder=(out/'aa' if purpose=='aa' else out/case/purpose)/f"block{item['block']:02d}"/f"{side}_{item['pair']:02d}"
            folder.mkdir(parents=True,exist_ok=False)
            flow=flows[case];(folder/'flow.ys').write_text(flow,encoding='utf-8')
            execute=memory_execute if purpose=='memory' else cpu_execute
            result=execute([str(binaries[actual_side]),'-s','flow.ys'],cwd=folder,log_path=folder/'run.log',timeout_s=remaining)
            result.update(item,execution_kind='synthesis',evidence_dir=str(folder),actual_side=actual_side,
                          performance_scheme=SCHEME,stat_exists=(folder/'stat.json').is_file(),
                          flow_match=(folder/'flow.ys').read_text(encoding='utf-8')==flow,
                          flow_sha256=hashlib.sha256((folder/'flow.ys').read_bytes()).hexdigest())
            try:result['resource_match']=resource_signature(folder/'stat.json')==expected[case,actual_side]
            except (OSError,ValueError,KeyError):result['resource_match']=False
            errors=memory_errors(result) if purpose=='memory' else cpu_sample_errors(result)
            result['validation_errors']=errors;save(folder/'metrics.json',result)
            (aa if purpose=='aa' else summaries[case][purpose+'_runs']).append(result)
            completed+=1
            if errors:raise RuntimeError('{} {} {}: {}'.format(purpose,case,side,'; '.join(errors)))
            if completed%50==0:print('v4 progress {}/2720 elapsed {:.1f}s'.format(completed,time.monotonic()-started),flush=True)
    except Exception as exc:error=str(exc)
    aa_stats=analyse_cpu_runs(aa,pairs_per_block=5)
    save(out/'aa_raw.json',aa);save(out/'aa_summary.json',aa_stats)
    rows=[]
    for c,summ in summaries.items():
        summ.update(cpu_statistics=analyse_cpu_runs(summ['cpu_runs']),aa_statistics=aa_stats,
                    aa_runs=aa,
                    aa_ok=aa_is_healthy(aa_stats),execution_complete=error is None,memory_samples_valid=False)
        summ['cpu_decision']=judge_cpu(summ['cpu_statistics'],qualified=qualifier['qualified'],
                                     guard_pct=(qualifier['certificate'] or {}).get('guard_pct'),aa_ok=summ['aa_ok'])
        mem=summ['memory_runs'];keys={(r['side'],r['pair']) for r in mem}
        expected_keys={(s,p) for s in binaries for p in range(1,16)}
        good=len(mem)==30 and keys==expected_keys and all(not memory_errors(r) for r in mem)
        summ['memory_samples_valid']=good
        if good:
            for side in binaries:
                vals=[r['yosys_peak_working_set_bytes'] for r in mem if r['side']==side]
                summ[side+'_yosys_peak_working_set_bytes_median']=statistics.median(vals)
        save(out/c/'summary.json',summ) if (out/c).is_dir() else None
        rows.append(summ)
    save(out/'performance_summary.json',rows)
    with (out/'performance_summary.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['case','cpu_base_mean_s','cpu_opt_mean_s','cpu_overhead_pct','ci_low_pct','ci_high_pct',
            'guard_percentage_points','expanded_low_pct','expanded_high_pct','cpu_point_requirement_met','cpu_verdict','aa_ok',
            'memory_base_median_bytes','memory_opt_median_bytes'])
        for s in rows:
            stats=s['cpu_statistics'];ci=stats['ci95_pct'] or [None,None]
            decision=s['cpu_decision'];expanded=decision['cpu_expanded_interval_pct'] or [None,None]
            w.writerow([s['case'],stats['baseline_mean_s'],stats['optimized_mean_s'],stats['overhead_pct'],*ci,
                        decision['guard_pct'],*expanded,decision['cpu_point_requirement_met'],decision['cpu_verdict'],decision['aa_ok'],
                        s.get('baseline_yosys_peak_working_set_bytes_median'),s.get('optimized_yosys_peak_working_set_bytes_median')])
    save(out/'execution_status.json',dict(complete=error is None,completed=completed,planned=2720,error=error,elapsed_s=time.monotonic()-started))
    return 0 if error is None else 1
