"""Pure formatting helpers for measured-run progress lines."""
import math
EXIT_PEAK_SCHEME = 'pmux-perf-15p-windows-separate-cpu-exitpeak-v3'


def merge_cpu_memory_runs(cpu, memory):
    """Keep plain CPU and event memory from separate, fully recorded executions."""
    result = dict(memory)
    for key in ('cpu_user_s', 'cpu_system_s', 'cpu_total_s', 'wall_s'):
        result[key] = cpu.get(key)
    result['rc'] = cpu.get('rc') if cpu.get('rc') != 0 else memory.get('rc')
    result['timed_out'] = bool(cpu.get('timed_out') or memory.get('timed_out'))
    result['cpu_run'] = cpu
    result['memory_run'] = memory
    result['memory_wall_s'] = memory.get('wall_s')
    result['cpu_measurement_uninstrumented'] = cpu.get('root_debugged') is False
    result['metrics_valid'] = cpu.get('metrics_valid') is True and memory.get('metrics_valid') is True
    result['measurement_error'] = '; '.join(label + ': ' + str(run['measurement_error'])
                                            for label, run in (('cpu', cpu), ('memory', memory))
                                            if run.get('measurement_error')) or None
    result['performance_scheme'] = EXIT_PEAK_SCHEME
    return result


def finite_positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def sample_errors(result, windows=None):
    """Validate raw evidence, with strict Windows fields and legacy compatibility."""
    if windows is None:
        windows = result.get('memory_metric') == 'yosys_peak_working_set_bytes'
    errors = []
    if result.get('rc') != 0:
        errors.append('rc missing/nonzero')
    timeout_invalid = result.get('timed_out') is not False if windows else bool(result.get('timed_out'))
    if timeout_invalid:
        errors.append('timed_out missing/true')
    if result.get('stat_exists') is not True:
        errors.append('stat_exists missing/false')
    if windows:
        if result.get('metrics_valid') is not True:
            errors.append('metrics_valid missing/false')
        if 'measurement_error' not in result or result['measurement_error'] not in (None, ''):
            errors.append('measurement_error missing/error: {}'.format(result.get('measurement_error')))
        if result.get('performance_scheme') == EXIT_PEAK_SCHEME:
            for name in ('memory_capture_complete', 'memory_exit_event_observed',
                         'cpu_measurement_uninstrumented', 'subruns_stat_match'):
                if result.get(name) is not True:
                    errors.append(name + ' missing/false')
            if result.get('memory_method_version') != 'windows-root-exit-event-v1':
                errors.append('memory_method_version missing/mismatch')
            if (type(result.get('main_pid')) is not int or result['main_pid'] <= 0
                    or result.get('memory_exit_event_pid') != result.get('main_pid')):
                errors.append('root exit-event PID identity mismatch')
            cpu, memory = result.get('cpu_run') or {}, result.get('memory_run') or {}
            if (cpu.get('root_debugged') is not False or cpu.get('metrics_valid') is not True
                    or cpu.get('rc') != 0 or cpu.get('stat_exists') is not True):
                errors.append('ordinary CPU subrun invalid')
            if (memory.get('root_debugged') is not True or memory.get('metrics_valid') is not True
                    or memory.get('rc') != 0 or memory.get('stat_exists') is not True
                    or memory.get('memory_capture_complete') is not True):
                errors.append('exit-event memory subrun invalid')
    mem_key = ('yosys_peak_working_set_bytes' if windows else
               'yosys_main_rss_peak_kb' if result.get('memory_metric') == 'yosys_main_rss_peak_kb'
               else 'tree_rss_peak_kb')
    for key in ('cpu_total_s', mem_key):
        if not finite_positive(result.get(key)):
            errors.append(key + ' missing/nonfinite/nonpositive')
    return errors


def format_run_progress(case, pair_index, order_tag, side, result):
    """Format one sample without assuming Linux-only measurement fields."""
    if result.get("memory_metric") == "yosys_peak_working_set_bytes":
        peak_bytes = result.get("yosys_peak_working_set_bytes")
        memory_text = "{} B ({:.2f} MiB)".format(
            peak_bytes,
            (peak_bytes or 0) / (1024 * 1024),
        )
    else:
        memory_text = "{} kB".format(result.get("yosys_main_rss_peak_kb"))

    gn_rss = result.get("gn_time_maxrss_kb")
    extra_metrics = " gn_rss={}kB".format(gn_rss) if gn_rss is not None else ""
    return (
        f"  [{case}] pair{pair_index} {order_tag} {side}: "
        f"rc={result['rc']} cpu={result['cpu_total_s']}s wall={result['wall_s']}s "
        f"yosys_main_peak={memory_text}{extra_metrics}"
    )


def collect_metric_values(runs, side, key):
    """Collect available successful sample values, skipping platform-only fields."""
    if any(r.get('memory_metric') == 'yosys_peak_working_set_bytes' and sample_errors(r)
           for r in runs):
        return []  # A partial median must not masquerade as the required full scheme.
    return [
        result.get(key)
        for result in runs
        if result.get("side") == side
        and (not sample_errors(result)
             if result.get('memory_metric') == 'yosys_peak_working_set_bytes'
             else result.get('rc') == 0 and not result.get('timed_out'))
        and type(result.get(key)) in (int, float) and math.isfinite(result[key])
    ]
