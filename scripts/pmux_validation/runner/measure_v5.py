"""20 ETW batches, 2600 ordinary CPU runs, then 120 root-debug memory runs."""
import csv
import json
from pathlib import Path
import statistics
import time
from cpu_statistics_v5 import SCHEME,METHOD,POLICY,analyse_cpu_runs,judge_cpu,sample_errors
from cpu_statistics import cpu_sample_errors,aa_is_healthy
from cpu_selfcheck_v5 import status as selfcheck_status,sha_file
from cpu_qualification import environment
from measure_v4 import schedule,resource_signature,memory_errors,save,CASES
from etw_reference import Recorder,export_trace,read_reference

def analyse_trace(etl,rows,context,out,remaining):
    exported=export_trace(etl,context['cpu_reference_tools']['xperf'],out,timeout_s=remaining)
    result=read_reference(exported/'events.csv',rows,deadline_check=remaining)
    if remaining()<=0:raise TimeoutError('30 minute performance protection limit')
    if len(result)!=len(rows) or {r['sample_id'] for r in result}!={r['sample_id'] for r in rows}:
        raise ValueError('ETW sample identity/count mismatch')
    for r in result:
        r.update(cpu_etw_total_ticks=r['cpu_reference_ticks'],etw_capture_complete=True,
                 cpu_primary_method=METHOD,etw_trace_path=str(etl),etw_events_path=str(exported/'events.csv'))
        if sample_errors(r):raise ValueError('ETW sample invalid: '+str(sample_errors(r)))
    return result

def run(context,round_dir,binaries,flows,*,cpu_execute=None,memory_execute=None,
        recorder_factory=None,trace_analyser=None,selfcheck_provider=None,elapsed_budget_used_s=0):
    from win_measure import run_cpu_measured,run_measured
    cpu_execute=cpu_execute or run_cpu_measured;memory_execute=memory_execute or run_measured
    recorder_factory=recorder_factory or Recorder;trace_analyser=trace_analyser or analyse_trace
    selfcheck_provider=selfcheck_provider or selfcheck_status
    if context.get('cpu_policy')!=POLICY or context.get('performance_scheme')!=SCHEME:
        raise ValueError('v5 fixed policy/scheme mismatch')
    root=Path(round_dir);out=root/'09_时间内存开销_performance/round01';out.mkdir(parents=True,exist_ok=False)
    selfcheck=selfcheck_provider(context,root/'03_脚本与插件_runner')
    save(out/'selfcheck.json',selfcheck);save(out/'environment.json',environment())
    if not selfcheck['qualified']:
        save(out/'execution_status.json',dict(complete=False,error='v5 ETW technical selfcheck invalid',completed=0,planned=2720))
        return 3
    expected={(c,s):resource_signature(root/f'05_公开四例_public/round01/{c}/{s}/stat.json') for c in CASES for s in binaries}
    summaries={c:dict(case=c,performance_scheme=SCHEME,cpu_policy=POLICY,cpu_primary_method=METHOD,
        memory_metric='yosys_peak_working_set_bytes',cpu_runs=[],memory_runs=[],
        method_selfcheck=selfcheck['certificate'],selfcheck_fingerprint=selfcheck['fingerprint']) for c in CASES}
    aa=[];raw=[];traces=[];collector=None;error=None;completed=0;cpu_complete=False
    started=time.monotonic();deadline=started+POLICY['stage_timeout_s']-elapsed_budget_used_s
    def remaining():
        left=deadline-time.monotonic()
        if left<=0:raise TimeoutError('30 minute performance protection limit')
        return left
    def perform(item,memory=False):
        nonlocal completed
        purpose,case,side=item['purpose'],item['case'],item['side']
        actual_side='baseline' if purpose=='aa' else side
        folder=(out/'aa' if purpose=='aa' else out/case/purpose)/f"block{item['block']:02d}"/f"{side}_{item['pair']:02d}"
        folder.mkdir(parents=True,exist_ok=False);flow=flows[case];(folder/'flow.ys').write_text(flow,encoding='utf-8')
        execute=memory_execute if memory else cpu_execute
        r=execute([str(binaries[actual_side]),'-s','flow.ys'],cwd=folder,log_path=folder/'run.log',timeout_s=remaining())
        r.update(item,actual_side=actual_side,execution_kind='synthesis',performance_scheme=SCHEME,
                 stat_exists=(folder/'stat.json').is_file(),flow_match=(folder/'flow.ys').read_text(encoding='utf-8')==flow,
                 sample_id=f"{purpose}:{case}:{side}:{item['block']}:{item['pair']}",evidence_dir=str(folder))
        try:r['resource_match']=resource_signature(folder/'stat.json')==expected[case,actual_side]
        except (ValueError,OSError,KeyError):r['resource_match']=False
        if memory:
            r['cpu_role']='not_scored_debug_run';issues=memory_errors(r)
            summaries[case]['memory_runs'].append(r)
        else:
            r.update(cpu_primary_method=METHOD,cpu_etw_total_ticks=None,etw_capture_complete=False)
            issues=cpu_sample_errors(r);raw.append(r)
            (aa if purpose=='aa' else summaries[case]['cpu_runs']).append(r)
        r['validation_errors']=issues;save(folder/'metrics.json',r);completed+=1
        remaining()
        if issues:raise RuntimeError('invalid sample: '+str(issues))
        return r
    try:
        collector=recorder_factory(out/'etw_collector')
        collector.deadline=deadline
        all_items=list(schedule());cpu_items=[r for r in all_items if r['purpose']!='memory']
        for block in range(1,21):
            remaining();collector.start();block_rows=[]
            for item in cpu_items:
                if item['block']==block:block_rows.append(perform(item))
            etl=collector.stop(f'block{block:02d}')
            traces.append((etl,block_rows))
            save(out/'cpu_raw_partial.json',raw)
            remaining()
            print('v5 CPU batch {}/20; {}/2600 native runs; {:.1f}s'.format(block,len(raw),time.monotonic()-started),flush=True)
        collector.deadline=None;collector.close();collector=None
        for index,(etl,block_rows) in enumerate(traces,1):
            remaining()
            enriched=trace_analyser(etl,block_rows,context,out/'etw_exports'/f'block{index:02d}',remaining)
            by_id={r['sample_id']:r for r in enriched}
            if len(by_id)!=len(block_rows) or set(by_id)!={r['sample_id'] for r in block_rows}:
                raise ValueError('ETW block sample identity mismatch')
            for r in block_rows:
                e=by_id[r['sample_id']]
                for key in ('main_pid','process_create_filetime','process_exit_filetime','job_total_processes',
                            'cpu_user_ticks','cpu_kernel_ticks','cpu_total_ticks','case','side','pair','block'):
                    if e.get(key)!=r.get(key):raise ValueError('ETW changed native identity/accounting: '+key)
                if sample_errors(e):raise ValueError('ETW enriched sample invalid: '+str(sample_errors(e)))
                r.update(e);save(Path(r['evidence_dir'])/'metrics_with_etw.json',r)
            remaining()
            print('v5 ETW analysed batch {}/20; {:.1f}s'.format(index,time.monotonic()-started),flush=True)
        cpu_complete=True
        # No recorder is active during root-debug memory observations.
        for item in all_items:
            if item['purpose']=='memory':perform(item,memory=True)
        remaining()
    except Exception as exc:error=str(exc)
    finally:
        if collector:
            try:collector.deadline=None;collector.close()
            except Exception as exc:error=(error+'; ' if error else '')+'collector cleanup: '+str(exc)
        if time.monotonic()>=deadline:error=(error+'; ' if error else '')+'30 minute performance protection limit'
        save(out/'cpu_raw_all.json',raw);save(out/'aa_raw.json',aa)
        aa_stats=analyse_cpu_runs(aa,pairs_per_block=5)
        save(out/'aa_summary.json',aa_stats)
        rows=[]
        for c,s in summaries.items():
            stats=analyse_cpu_runs(s['cpu_runs']);warnings=[]
            if aa_stats['valid'] and not aa_is_healthy(aa_stats):warnings.append('A/A interval excludes zero; diagnostic only')
            if stats['valid'] and stats['ci95_pct'][0]<=5<stats['ci95_pct'][1]:warnings.append('CPU interval crosses 5%; point grading retained')
            decision=judge_cpu(stats)
            if error is not None or completed!=2720 or not aa_stats['valid']:
                decision.update(cpu_verdict='INVALID',cpu_point_requirement_met=False)
            s.update(cpu_statistics=stats,cpu_decision=decision,aa_runs=aa,aa_statistics=aa_stats,
                     execution_complete=error is None and completed==2720,cpu_collection_complete=cpu_complete,
                     quality_warnings=warnings,execution_error=error)
            mem=s['memory_runs'];valid=len(mem)==30 and {(r['side'],r['pair']) for r in mem}=={(v,p) for v in binaries for p in range(1,16)} and all(not memory_errors(r) for r in mem)
            s['memory_samples_valid']=valid
            if valid:
                for side in binaries:s[side+'_yosys_peak_working_set_bytes_median']=statistics.median(r['yosys_peak_working_set_bytes'] for r in mem if r['side']==side)
            (out/c).mkdir(exist_ok=True);rows.append(s)
        def invalidate_late():
            nonlocal error
            if time.monotonic()>=deadline and error is None:
                error='30 minute performance protection limit during final statistics/output'
                for row in rows:
                    row.update(execution_complete=False,execution_error=error)
                    row['cpu_decision'].update(cpu_verdict='INVALID',cpu_point_requirement_met=False)
                return True
            return False
        def persist():
            for row in rows:save(out/row['case']/'summary.json',row)
            save(out/'performance_summary.json',rows)
            with (out/'performance_summary.csv').open('w',newline='',encoding='utf-8-sig') as f:
                writer=csv.writer(f);writer.writerow(['case','cpu_primary_method','base_etw_mean_s','opt_etw_mean_s','overhead_pct','cpu_verdict','ci95_diagnostic',
                    'base_job_mean_s','opt_job_mean_s','base_wall_mean_s','opt_wall_mean_s','memory_base_median_bytes','memory_opt_median_bytes','warnings'])
                for s in rows:
                    st=s['cpu_statistics'];writer.writerow([s['case'],METHOD,st['baseline_mean_s'],st['optimized_mean_s'],st['overhead_pct'],s['cpu_decision']['cpu_verdict'],st['ci95_pct'],
                        st.get('baseline_job_mean_s'),st.get('optimized_job_mean_s'),st.get('baseline_wall_mean_s'),st.get('optimized_wall_mean_s'),
                        s.get('baseline_yosys_peak_working_set_bytes_median'),s.get('optimized_yosys_peak_working_set_bytes_median'),s['quality_warnings']])
        invalidate_late();persist()
        if invalidate_late():persist()
        save(out/'execution_status.json',dict(complete=error is None and completed==2720,completed=completed,planned=2720,error=error,elapsed_s=elapsed_budget_used_s+time.monotonic()-started,elapsed_budget_used_s=elapsed_budget_used_s,new_processing_s=time.monotonic()-started,reused_cpu_runs=sum(r.get('measurement_reused') is True for r in raw),new_memory_runs=sum(len(s['memory_runs']) for s in rows)))
    return 0 if error is None and completed==2720 else 1
