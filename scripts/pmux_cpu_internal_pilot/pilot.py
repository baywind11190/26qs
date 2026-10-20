"""Read-only status and offline analysis for the stopped internal cycle pilot.

The native probe has already run. This entry never builds Yosys or reruns the
failed coverage experiment. A future continuation needs a separate approved
scope; formal v6 is neither imported for execution nor changed here.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import analysis

HERE=Path(__file__).resolve().parent


def evaluate(result):
    result=Path(result)
    first=json.loads((result/'01_probe/gate1.json').read_text(encoding='utf-8'))
    outer=json.loads((result/'01_probe/gate1_outer.json').read_text(encoding='utf-8'))
    frequencies=[analysis.calibration_hz(v,first['hardware']['qpc_hz']) for v in first['calibrations']]
    frequency_ok,spread=analysis.frequency_gate(frequencies)
    layout=first['layout']
    sample_counts=Counter(v['cpu'] for v in first['calibrations'])
    calibration_schema_ok=(len(sample_counts)==2 and set(sample_counts.values())=={3} and
                           all(v['affinity_restored'] is True and
                               type(v['tsc_delta']) is int and v['tsc_delta']>0 and
                               type(v['qpc_delta']) is int and v['qpc_delta']>=first['hardware']['qpc_hz']/5
                               for v in first['calibrations']))
    gate1=(frequency_ok and len(frequencies)==6 and calibration_schema_ok and first['hardware']['invariant_tsc'] is True and
           first['process_interface_valid'] is True and first['thread_interface_valid'] is True and
           layout['size']==432 and layout['cycle_offset']==144 and
           layout['empty_ntstatus']==0 and layout['live_ntstatus']==0 and
           layout['empty_returned_bytes']==432 and layout['live_returned_bytes']==432 and
           layout['assigned'] is True and layout['basic_valid'] is True and
           layout['extended_processes']==layout['documented_processes'] and
           layout['extended_active']==layout['documented_active'] and
           outer['rc']==0 and outer['timed_out'] is False and outer['metrics_valid'] is True and
           first['pid']==outer['main_pid'] and first['created']==outer['process_create_filetime'])
    summary=dict(method='windows-internal-cycle-cpu-pilot-v1',gate1=gate1,
                 frequencies_hz=frequencies,relative_frequency_range=spread,
                 selected_hz=frequencies[-1] if frequency_ok else None,
                 gate2=False,gate2_scope='THREAD_SMALL_INCREMENT_ONLY',
                 time_conversion_status='CONDITIONAL_EXPERIMENTAL_NOT_ACCURACY_CERTIFIED',
                 gate3=False,synthesis_runs=0,stop_reasons=[])
    if not gate1:
        summary['stop_reasons'].append('hardware_layout_or_calibration_gate_failed')
        summary['verdict']=analysis.verdict(False,False,False)
        return summary
    hz=frequencies[-1]
    for name in ('increments','tree'):
        native=json.loads((result/'01_probe'/f'{name}.json').read_text(encoding='utf-8'))
        ext=json.loads((result/'01_probe'/f'{name}_outer.json').read_text(encoding='utf-8'))
        end=analysis.calibration_hz(native['end_calibration'],first['hardware']['qpc_hz'])
        valid=(ext['rc']==0 and ext['timed_out'] is False and ext['metrics_valid'] is True and
               native['end_calibration']['affinity_restored'] is True and
               type(native['end_calibration']['tsc_delta']) is int and native['end_calibration']['tsc_delta']>0 and
               type(native['end_calibration']['qpc_delta']) is int and native['end_calibration']['qpc_delta']>=first['hardware']['qpc_hz']/5 and
               abs(end/hz-1)<=.001)
        pid_key='pid' if name=='increments' else 'root_pid'
        valid=valid and native[pid_key]==ext['main_pid']
        if name=='tree':valid=valid and native['root_created']==ext['process_create_filetime']
        summary[name+'_end_hz']=end
        summary[name+'_end_relative_drift']=end/hz-1
        if name=='increments':
            inc=analysis.summarize_increments(native,hz)
            summary['increments']=inc
            summary['gate2']=valid and inc['valid']
            if not summary['gate2']:
                summary['stop_reasons'].append('increment_wait_or_postcalibration_gate_failed')
                break
        else:
            tree=analysis.tree_gate(native)
            for phase in ('initial','live','exited','handles_closed'):
                for bound in ('lower','upper'):
                    tree[phase][f'residual_from_{bound}_us']=tree[phase][f'residual_from_{bound}_cycles']/hz*1e6
            summary['tree']=tree
            summary['gate3']=valid and tree['valid']
            summary['stop_reasons'].extend(tree['failures'])
            if not valid:summary['stop_reasons'].append('tree_launcher_identity_or_postcalibration_invalid')
    summary['verdict']=analysis.verdict(summary['gate1'],summary['gate2'],summary['gate3'])
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['plan','analyze'])
    parser.add_argument('--result',type=Path)
    args=parser.parse_args()
    state=json.loads((HERE/'execution_state.json').read_text(encoding='utf-8'))
    if args.mode=='plan':
        print(json.dumps(dict(state,read_only=True,native_runs_completed=3,
                              permitted_automatic_synthesis_runs=0),ensure_ascii=False,indent=2))
    else:
        print(json.dumps(evaluate(args.result or state['result']),ensure_ascii=False,indent=2))


if __name__=='__main__':main()
