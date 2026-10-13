"""Strict arithmetic CPU statistics, independently paired whole-block resampling."""
import math
import random
import statistics

SCHEME='pmux-perf-300p-windows-mean-block-ci-exitpeak-v4'
POLICY=dict(blocks=20,pairs_per_block=15,aa_pairs_per_block=5,memory_pairs=15,
            resamples=20000,seed=20261011,stage_timeout_s=1800)
TICKS_PER_SECOND=10_000_000
EPS=1e-9


def cpu_sample_errors(row):
    errors=[]
    keys=('metrics_valid','cpu_descendants_included')
    if row.get('execution_kind')!='fixture':keys+=('stat_exists','resource_match','flow_match')
    for key in keys:
        if row.get(key) is not True: errors.append(key+' missing/false')
    if row.get('rc')!=0: errors.append('rc missing/nonzero')
    if row.get('timed_out') is not False: errors.append('timed_out missing/true')
    if row.get('root_debugged') is not False: errors.append('CPU run must not be debugged')
    if 'measurement_error' not in row or row['measurement_error'] not in (None,''):
        errors.append('measurement error missing/nonempty')
    ticks=[row.get(k) for k in ('cpu_user_ticks','cpu_kernel_ticks','cpu_total_ticks')]
    if any(type(x) is not int or x<0 for x in ticks) or not ticks[-1]:
        errors.append('raw CPU ticks missing/invalid')
    elif ticks[0]+ticks[1]!=ticks[2]: errors.append('CPU tick sum mismatch')
    return errors


def percentile(values,p):
    values=sorted(values)
    pos=(len(values)-1)*p
    lo=math.floor(pos); hi=math.ceil(pos)
    return values[lo]+(values[hi]-values[lo])*(pos-lo)


def _draws(blocks,resamples,seed):
    rng=random.Random(seed)
    for _ in range(resamples): yield [rng.randrange(blocks) for _ in range(blocks)]


def _validated_blocks(rows,blocks,pairs_per_block):
    errors=[]; seen=set(); grouped={b:{s:[] for s in ('baseline','optimized')} for b in range(1,blocks+1)}
    if len(rows)!=blocks*pairs_per_block*2: errors.append('sample count mismatch')
    for index,row in enumerate(rows):
        issues=cpu_sample_errors(row)
        if issues: errors.append('sample {}: {}'.format(index+1,'; '.join(issues)))
        b,p,s=row.get('block'),row.get('pair'),row.get('side')
        if type(b) is not int or type(p) is not int or b not in grouped or not 1<=p<=pairs_per_block or s not in ('baseline','optimized'):
            errors.append('sample {}: invalid block/pair/side'.format(index+1));continue
        key=(b,p,s)
        if key in seen: errors.append('duplicate block/pair/side: '+str(key))
        seen.add(key);grouped[b][s].append(row)
    expected={(b,p,s) for b in grouped for p in range(1,pairs_per_block+1) for s in ('baseline','optimized')}
    if seen!=expected: errors.append('missing or unexpected paired identities')
    return grouped,errors


def analyse_cpu_runs(rows,*,blocks=20,pairs_per_block=15,resamples=20000,seed=20261011):
    if any(type(v) is not int or v<=0 for v in (blocks,pairs_per_block,resamples)):
        raise ValueError('positive integer statistical policy required')
    grouped,errors=_validated_blocks(rows,blocks,pairs_per_block)
    result=dict(valid=not errors,errors=errors,blocks=blocks,pairs_per_block=pairs_per_block,
        resamples=resamples,seed=seed,baseline_mean_s=None,optimized_mean_s=None,
        overhead_pct=None,ci95_pct=None,statistic='arithmetic_mean',interval_method='paired-whole-block-bootstrap-percentile-95-v1')
    if errors:return result
    sums={s:[sum(r['cpu_total_ticks'] for r in grouped[b][s]) for b in grouped] for s in ('baseline','optimized')}
    total_b=sum(sums['baseline']);total_o=sum(sums['optimized'])
    result['overhead_pct']=(total_o/total_b-1)*100
    result['block_totals_ticks']=[dict(block=b,baseline=sums['baseline'][b-1],optimized=sums['optimized'][b-1]) for b in grouped]
    for s in ('baseline','optimized'):
        values=[r['cpu_total_ticks']/TICKS_PER_SECOND for r in rows if r['side']==s]
        result.update({s+'_mean_s':sum(sums[s])/len(values)/TICKS_PER_SECOND,
            s+'_median_s':statistics.median(values),s+'_min_s':min(values),s+'_max_s':max(values),
            s+'_stddev_s':statistics.stdev(values) if len(values)>1 else 0,
            s+'_samples':len(values),s+'_total_ticks':sum(sums[s])})
    values=[(sum(sums['optimized'][i] for i in draw)/sum(sums['baseline'][i] for i in draw)-1)*100
            for draw in _draws(blocks,resamples,seed)]
    result['ci95_pct']=[percentile(values,.025),percentile(values,.975)]
    return result


def aa_is_healthy(stats):
    return bool(stats.get('valid') and stats.get('ci95_pct') and
                stats['ci95_pct'][0]<=EPS and stats['ci95_pct'][1]>=-EPS)


def judge_cpu(stats,*,qualified,guard_pct,aa_ok,limit=5):
    valid=stats.get('valid') is True
    point=stats.get('overhead_pct')
    result=dict(cpu_verdict='INVALID' if not valid else 'INCONCLUSIVE',
        cpu_point_requirement_met=valid and point is not None and point<=limit+EPS,
        cpu_overhead_pct=point,cpu_ci95_pct=stats.get('ci95_pct'),cpu_expanded_interval_pct=None,
        cpu_method_qualified=qualified is True,aa_ok=aa_ok is True,guard_pct=guard_pct)
    guard_ok=type(guard_pct) in (int,float) and math.isfinite(guard_pct) and 0<=guard_pct<=1+EPS
    if not valid or qualified is not True or aa_ok is not True or not guard_ok:return result
    lo,hi=stats['ci95_pct'];lo-=guard_pct;hi+=guard_pct
    result['cpu_expanded_interval_pct']=[lo,hi]
    result['cpu_verdict']='PASS' if hi<=limit+EPS else 'FAIL' if lo>limit+EPS else 'INCONCLUSIVE'
    return result


def analyse_reference_difference(rows,*,blocks=10,pairs_per_block=10,resamples=20000,seed=20261011):
    grouped,errors=_validated_blocks(rows,blocks,pairs_per_block)
    if any(type(r.get('cpu_reference_ticks')) is not int or r['cpu_reference_ticks']<=0 for r in rows):
        errors.append('independent reference ticks missing/invalid')
    if errors:return dict(valid=False,errors=errors,guard_pct=None,ci95_difference_pct=None)
    sums={k:{s:[sum(r[k] for r in grouped[b][s]) for b in grouped] for s in ('baseline','optimized')}
          for k in ('cpu_total_ticks','cpu_reference_ticks')}
    differences=[]
    for draw in _draws(blocks,resamples,seed):
        estimates=[]
        for data in sums.values():
            estimates.append((sum(data['optimized'][i] for i in draw)/sum(data['baseline'][i] for i in draw)-1)*100)
        differences.append(estimates[0]-estimates[1])
    ci=[percentile(differences,.025),percentile(differences,.975)]
    return dict(valid=True,errors=[],ci95_difference_pct=ci,guard_pct=max(abs(x) for x in ci))
