"""Fixed independent qualification; failed references never issue certificates."""
import json
from pathlib import Path
import subprocess
import sys

from cpu_statistics import cpu_sample_errors, analyse_reference_difference, analyse_cpu_runs
from cpu_qualification import fingerprint, qualification_status, cache_path, sha_file
from etw_reference import Recorder,export_trace,read_reference
from measure_v4 import resource_signature,save
from win_measure import run_cpu_measured


def qualify(context,round_dir,binaries,flows):
    root=Path(round_dir);runner=root/'03_脚本与插件_runner'
    output=root/'10_验证工具自检_selfcheck/cpu_method_qualification'
    output.mkdir(parents=True,exist_ok=False)
    fp=fingerprint(context,runner);save(output/'fingerprint.json',fp)
    previous=qualification_status(context,runner)
    if previous['qualified']:
        save(output/'reused_certificate.json',previous);return 0
    results=[];groups={};collector=None;guard=None;ok=False;error=None
    try:
        gcc=Path(context['tools']['compiler']['path']).parent/'gcc.exe'
        probe=Path(context['ascii_bridge'])/'cpu_qualification_probe.exe'
        cmd=[str(gcc),'-O2','-municode',str(runner/'cpu_qualification_probe.c'),'-o',str(probe)]
        built=subprocess.run(cmd,capture_output=True,text=True,errors='replace',timeout=120)
        (output/'fixture_build.log').write_text(built.stdout+built.stderr,encoding='utf-8')
        if built.returncode:raise RuntimeError('qualification fixture build failed')
        save(output/'fixture_identity.json',dict(command=cmd,sha256=sha_file(probe)))
        collector=Recorder(output/'collector')
        collector.start()

        def one(group,block,pair,side,*,case=None,mode=None,traced=True):
            d=output/group/f'block{block:02d}'/f'{side}_{pair:02d}'
            d.mkdir(parents=True,exist_ok=False)
            if case:
                flow=flows[case];(d/'flow.ys').write_text(flow,encoding='utf-8')
                command=[str(binaries['baseline']),'-s','flow.ys']
            else:command=[str(probe),mode]
            r=run_cpu_measured(command,cwd=d,log_path=d/'run.log',timeout_s=60)
            r.update(side=side,block=block,pair=pair,group=group,traced=traced,command=command,
                     execution_kind='synthesis' if case else 'fixture',evidence_dir=str(d))
            if case:
                reference=root/f'04_流程一致性_flowcheck/builtin_run01/{case}/baseline/stat.json'
                r.update(stat_exists=(d/'stat.json').is_file(),flow_match=(d/'flow.ys').read_text(encoding='utf-8')==flows[case])
                try:r['resource_match']=resource_signature(d/'stat.json')==resource_signature(reference)
                except (ValueError,OSError,KeyError):r['resource_match']=False
            errors=cpu_sample_errors(r);r['validation_errors']=errors
            save(d/'metrics.json',r);results.append(r)
            if errors:raise RuntimeError('qualification sample invalid: '+str(errors))
            return r

        names=[('fixture_zero',None,'--base'),('fixture_small',None,'--small'),('fixture_large',None,'--large')]
        names +=[(case,case,None) for case in flows]
        for group,case,mode in names:
            groups[group]=[]
            for block in range(1,11):
                for pair in range(1,11):
                    for side in (('baseline','optimized') if (block+pair)%2==0 else ('optimized','baseline')):
                        groups[group].append(one(group,block,pair,side,case=case,mode='--base' if side=='baseline' else mode))
                print('CPU qualification {} block {}/10'.format(group,block),flush=True)
            save(output/(group+'_raw.json'),groups[group])
        trace=collector.stop('reference')
        save(output/'diagnostic_means.json',{g:analyse_cpu_runs(rows,blocks=10,pairs_per_block=10) for g,rows in groups.items()})
        exported=export_trace(trace,context['cpu_reference_tools']['xperf'],output/'reference_export')
        enriched=read_reference(exported/'events.csv',results)
        for r in enriched:save(Path(r['evidence_dir'])/'metrics_with_reference.json',r)
        groups={g:[r for r in enriched if r['group']==g] for g in groups}
        comparisons={g:analyse_reference_difference(rows) for g,rows in groups.items()}
        save(output/'reference_comparisons.json',comparisons)
        if not all(r['valid'] for r in comparisons.values()):raise RuntimeError('independent reference incomplete')
        guard=max(r['guard_pct'] for r in comparisons.values())
        if guard>1+1e-9:raise RuntimeError('Job/ETW agreement guard {:.6f} percentage points exceeds 1'.format(guard))

        impact=[]
        for block in range(1,11):
            order=('baseline','optimized') if block%2 else ('optimized','baseline')
            for side in order:
                if side=='optimized':collector.start()
                for pair in range(1,11):
                    impact.append(one('tracking_impact',block,pair,side,case='test2',traced=side=='optimized'))
                if side=='optimized':collector.stop('impact_'+str(block))
        collector.close();collector=None
        impact_stats=analyse_cpu_runs(impact,blocks=10,pairs_per_block=10)
        save(output/'tracking_impact_summary.json',impact_stats)
        if not impact_stats['valid'] or impact_stats['ci95_pct'][1]>5+1e-9:
            raise RuntimeError('tracing influence cannot exclude overhead above 5%')
        ok=True
    except Exception as exc:error=str(exc)
    finally:
        if collector:
            try:collector.close()
            except Exception as exc:error=(error+'; ' if error else '')+'collector cleanup: '+str(exc);ok=False
    result=dict(ok=ok,error=error,guard_pct=guard,fingerprint=fp,
                actual_samples=len(results),all_raw_samples_preserved=True,
                reference_scope='same-run root and descendants, process/thread lifecycle, excluded DPC/ISR')
    save(output/'qualification_result.json',result)
    if ok:
        inventory={p.relative_to(output).as_posix():sha_file(p) for p in sorted(output.rglob('*')) if p.is_file()}
        cert=dict(ok=True,guard_pct=guard,fingerprint=fp,evidence_root=str(output),evidence_sha256=inventory)
        path=cache_path(context);path.parent.mkdir(parents=True,exist_ok=True);save(path,cert)
    print('CPU qualification {}'.format('PASS' if ok else 'FAIL: '+str(error)),flush=True)
    return 0 if ok else 1


def main():
    import p3_common as C
    import builtin_common as B
    status=qualification_status(C.CONTEXT,Path(__file__).parent)
    if status['qualified']:
        save(C.ROUND_DIR/'01_来源与环境_meta/cpu_qualification.json',status)
        print('CPU qualification REUSED',flush=True);return 0
    flows={}
    for case in ('test1','test2','test3','test4'):
        rtl=C.stage_to_ascii_bridge(C.TREE/f'pmux_case/competition_case/{case}/{case}.v',f'builtin_inputs/{case}.v')
        flows[case]=C.gen_builtin_synth_ys(rtl,case)
    rc=qualify(C.CONTEXT,C.ROUND_DIR,B.select_binaries(C.CONTEXT['builtin']),flows)
    save(C.ROUND_DIR/'01_来源与环境_meta/cpu_qualification.json',qualification_status(C.CONTEXT,Path(__file__).parent))
    return rc

if __name__=='__main__':sys.exit(main())
