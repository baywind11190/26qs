"""ETW arithmetic means and exact point grading; v4 remains unchanged."""
import statistics
from cpu_statistics import POLICY,percentile,_draws,_validated_blocks,cpu_sample_errors

SCHEME='pmux-perf-300p-windows-etw-mean-exitpeak-v5'
METHOD='windows-etw-cswitch-root-and-descendants-v1'

def sample_errors(row):
    errors=cpu_sample_errors(row)
    if row.get('performance_scheme')!=SCHEME:errors.append('v5 sample scheme missing/mismatch')
    if row.get('cpu_primary_method')!=METHOD:errors.append('ETW primary method missing/mismatch')
    if row.get('etw_capture_complete') is not True:errors.append('ETW capture incomplete')
    for key in ('reference_events_lost','reference_buffers_lost'):
        if type(row.get(key)) is not int or row[key]!=0:errors.append(key+' missing/nonzero')
    ticks=row.get('cpu_etw_total_ticks');tree=row.get('reference_processes')
    if type(ticks) is not int or ticks<=0:errors.append('ETW integer CPU ticks missing/invalid')
    if not isinstance(tree,list) or not tree or len(tree)!=row.get('job_total_processes'):
        errors.append('ETW/Job process tree count mismatch')
    elif any(type(p.get('cpu_us')) is not int or p['cpu_us']<=0 for p in tree):
        errors.append('ETW process CPU invalid')
    elif sum(p['cpu_us'] for p in tree)*10!=ticks:errors.append('ETW process CPU sum mismatch')
    return errors

def analyse_cpu_runs(rows,*,blocks=20,pairs_per_block=15,resamples=20000,seed=20261011):
    if any(type(v) is not int or v<=0 for v in (blocks,pairs_per_block,resamples)):
        raise ValueError('positive integer statistical policy required')
    grouped,errors=_validated_blocks(rows,blocks,pairs_per_block)
    for i,row in enumerate(rows):
        issues=sample_errors(row)
        if issues:errors.append('sample {}: {}'.format(i+1,'; '.join(issues)))
    result=dict(valid=not errors,errors=errors,blocks=blocks,pairs_per_block=pairs_per_block,
        resamples=resamples,seed=seed,baseline_mean_s=None,optimized_mean_s=None,overhead_pct=None,
        ci95_pct=None,statistic='arithmetic_mean',cpu_primary_method=METHOD,
        interval_method='paired-whole-block-bootstrap-percentile-95-diagnostic-v1')
    if errors:return result
    sums={s:[sum(r['cpu_etw_total_ticks'] for r in grouped[b][s]) for b in grouped] for s in ('baseline','optimized')}
    tb,to=sum(sums['baseline']),sum(sums['optimized'])
    result['overhead_pct']=(to-tb)/tb*100
    result['block_totals_ticks']=[dict(block=b,baseline=sums['baseline'][b-1],optimized=sums['optimized'][b-1]) for b in grouped]
    for side in sums:
        selected=[r for r in rows if r['side']==side];values=[r['cpu_etw_total_ticks']/10_000_000 for r in selected]
        result.update({side+'_mean_s':sum(sums[side])/len(values)/10_000_000,
            side+'_samples':len(values),side+'_total_ticks':sum(sums[side]),
            side+'_median_s':statistics.median(values),side+'_min_s':min(values),side+'_max_s':max(values),
            side+'_stddev_s':statistics.stdev(values) if len(values)>1 else 0,
            side+'_job_mean_s':sum(r['cpu_total_ticks'] for r in selected)/len(selected)/10_000_000,
            side+'_wall_mean_s':sum(r['wall_s'] for r in selected)/len(selected)})
    values=[(sum(sums['optimized'][i] for i in draw)/sum(sums['baseline'][i] for i in draw)-1)*100
            for draw in _draws(blocks,resamples,seed)]
    result['ci95_pct']=[percentile(values,.025),percentile(values,.975)]
    return result

def judge_cpu(stats):
    b,o=stats.get('baseline_total_ticks'),stats.get('optimized_total_ticks')
    valid=stats.get('valid') is True and type(b) is int and b>0 and type(o) is int and o>0
    met=valid and (o-b)*100<=b*5
    return dict(cpu_verdict=('PASS' if met else 'FAIL') if valid else 'INVALID',
                cpu_point_requirement_met=met,cpu_overhead_pct=stats.get('overhead_pct'),
                cpu_ci95_pct=stats.get('ci95_pct'),cpu_primary_method=METHOD,
                cpu_decision_method='exact-integer-mean-overhead-5pct',
                cpu_interval_role='diagnostic_only')
