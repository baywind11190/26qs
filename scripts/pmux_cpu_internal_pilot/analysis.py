"""Integer-cycle evidence and explicit experimental gates; no scoring fallback."""


def calibration_hz(row, qpc_hz):
    if row['tsc_delta'] <= 0 or row['qpc_delta'] <= 0 or qpc_hz <= 0:
        return 0
    return row['tsc_delta'] * qpc_hz / row['qpc_delta']


def frequency_gate(values):
    if not values or min(values) <= 0:
        return False, None
    reference = values[-1]  # approved last sample, never average/median
    spread = (max(values) - min(values)) / reference
    return spread <= 0.001, spread


def increment_gate(work_us, wait_us):
    positive = [v for v in work_us if v > 0]
    minimum = min(positive) if positive else None
    return {'valid': minimum is not None and minimum <= 100 and 0 <= wait_us < 5000,
            'minimum_work_us': minimum, 'wait_us': wait_us}


def verdict(hardware_and_conversion, increments, tree_coverage):
    if not hardware_and_conversion:
        return '本机方案不可用'
    if not increments or not tree_coverage:
        return '仅部分计量可行'
    return '本机试验可行'


def tree_gate(row):
    failures = []
    result = {}
    for phase in ('initial', 'live', 'exited', 'handles_closed'):
        b = row[phase]
        counters_ok=all(type(b[k]) is int and b[k]>=0 for k in ('sum_low','job_cycles','sum_high'))
        inside = counters_ok and b['sum_low'] <= b['job_cycles'] <= b['sum_high']
        readable = b['valid'] is True and b['ntstatus'] == 0 and b['returned_bytes'] == 432
        result[phase] = dict(inside_bracket=inside, readable=readable,
                             residual_from_lower_cycles=b['job_cycles']-b['sum_low'],
                             residual_from_upper_cycles=b['job_cycles']-b['sum_high'])
        if not readable:
            failures.append(phase+'_query_invalid')
        if not inside:
            failures.append(phase+'_outside_bracket')
    expected = {row['root_pid'], row['child']['pid'], row['grandchild']['pid']}
    if row['list_valid'] is not True or set(row['live_pids']) != expected or len(row['live_pids'])!=len(expected):
        failures.append('actual_process_inventory_not_closed')
    if row['identities_valid'] is not True or row['codes_valid'] is not True or row['child']['exit'] or row['grandchild']['exit']:
        failures.append('process_identity_or_exit_invalid')
    if row['initial']['processes'] != 1 or row['initial']['active'] != 1:
        failures.append('root_scope_unclear')
    if row['live']['processes'] != len(expected) or row['live']['active'] != len(expected):
        failures.append('live_scope_unclear')
    for phase in ('exited','handles_closed'):
        if row[phase]['processes'] != len(expected) or row[phase]['active'] != 1:
            failures.append(phase+'_scope_unclear')
    result.update(valid=not failures, failures=failures,
                  root_addition='NONE: active root already present in the live Job stream')
    return result


def summarize_increments(row, hz):
    if hz<=0:
        return dict(valid=False,failures=['calibration_frequency_invalid'])
    expected=[n for n in (0,100,1000,10000,100000) for _ in range(3)]
    if [v.get('iterations') for v in row['blocks']]!=expected:
        return dict(valid=False,failures=['fixed_15_block_protocol_incomplete'])
    fields=('process_cycles','thread_cycles','process_ticks','thread_ticks')
    if any(v.get('valid') is not True or any(type(v.get(k)) is not int or v[k]<0 for k in fields) for v in row['blocks']):
        return dict(valid=False,failures=['block_counter_or_validity_invalid'])
    wait=row['wait']
    if wait.get('requested_ms')!=200 or wait.get('valid') is not True or any(type(wait.get(k)) is not int or wait[k]<0 for k in ('process_cycles','thread_cycles')):
        return dict(valid=False,failures=['fixed_wait_or_counter_invalid'])
    rows = [dict(v, process_us=v['process_cycles']/hz*1e6,
                 thread_us=v['thread_cycles']/hz*1e6) for v in row['blocks']]
    empty = [v for v in rows if v['iterations']==0]
    summaries = []
    for iterations in sorted({v['iterations'] for v in rows}):
        group = [v for v in rows if v['iterations']==iterations]
        summaries.append(dict(iterations=iterations,
                              process_us=[v['process_us'] for v in group],
                              thread_us=[v['thread_us'] for v in group],
                              coarse_ticks=[v['process_ticks'] for v in group],
                              thread_above_all_empty=min(v['thread_us'] for v in group)>max(v['thread_us'] for v in empty),
                              process_above_all_empty=min(v['process_us'] for v in group)>max(v['process_us'] for v in empty)))
    wait_process_us = row['wait']['process_cycles']/hz*1e6
    wait_thread_us = row['wait']['thread_cycles']/hz*1e6
    distinguishable = [v for v in summaries if v['iterations'] and v['thread_above_all_empty'] and max(v['thread_us'])<=100]
    valid = bool(distinguishable) and all(v['valid'] for v in rows) and row['wait']['valid'] and wait_process_us<5000 and wait_thread_us<5000
    return dict(valid=valid, blocks=rows, groups=summaries,
                minimum_nonzero_thread_us=min(v['thread_us'] for v in rows if v['thread_us']>0),
                minimum_nonzero_process_us=min(v['process_us'] for v in rows if v['process_us']>0),
                minimum_distinguished_work_thread_us=min((min(v['thread_us']) for v in distinguishable),default=None),
                wait_process_us=wait_process_us,wait_thread_us=wait_thread_us,
                process_sub100us_discrimination_confirmed=any(v['iterations'] and v['process_above_all_empty'] and max(v['process_us'])<=100 for v in summaries),
                caution='Empty-read cost is included; no subtraction. Thread increments do not certify whole-process accuracy.')
