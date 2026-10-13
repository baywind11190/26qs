"""Attested technical ETW selfcheck, not a +/-1pp accuracy certificate."""
import json
import ast
import csv,collections,re
import hashlib
from pathlib import Path
import sys
from cpu_qualification import sha_file,fingerprint as legacy_fingerprint
from cpu_statistics import analyse_cpu_runs as analyse_job_runs
from cpu_statistics_v5 import SCHEME,METHOD,POLICY,sample_errors

SCOPE='etw-integrity-software-selfcheck-v5-not-absolute-accuracy'

def parser_digest(path):
    text=Path(path).read_text(encoding='utf-8');lines=text.splitlines(keepends=True)
    functions=[n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name in ('_pid','_records','read_reference')]
    if not {'_pid','read_reference'}<={n.name for n in functions}:raise ValueError('ETW parser functions missing')
    return hashlib.sha256(''.join(''.join(lines[n.lineno-1:n.end_lineno]) for n in functions).encode('utf-8')).hexdigest()

def fingerprint(cfg,runner_dir=None):
    runner=Path(runner_dir or Path(__file__).parent)
    fp=legacy_fingerprint(cfg,runner)
    fp.update(schema=5,scheme=SCHEME,policy=POLICY,cpu_primary_method=METHOD,scope=SCOPE)
    fp['code'].update({name:__import__('hashlib').sha256((runner/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest()
                       for name in ('cpu_statistics_v5.py','cpu_selfcheck_v5.py','measure_v5.py')})
    fp['source_evidence']=cfg.get('cpu_etw_selfcheck_evidence')
    return fp

def cache_path(cfg):
    return Path(cfg['repo'])/'results/官方口径评测/_共享CPU方法自检_etw_v5/selfcheck.json'

def certificate_valid(cert,expected):
    try:
        if cert.get('ok') is not True or cert.get('scope')!=SCOPE or cert.get('fingerprint')!=expected:
            return False,'v5 selfcheck scope/fingerprint mismatch'
        root=Path(cert['evidence_root']).resolve();inventory=cert.get('evidence_sha256') or {}
        if 'result.json' not in inventory:return False,'v5 selfcheck result not attested'
        for rel,want in inventory.items():
            p=(root/rel).resolve();p.relative_to(root)
            if not p.is_file() or sha_file(p)!=want:return False,'v5 evidence missing/changed: '+rel
        result=json.loads((root/'result.json').read_text(encoding='utf-8'))
        if result.get('ok') is not True or result.get('scope')!=SCOPE or result.get('fingerprint')!=expected:
            return False,'v5 result disagrees with selfcheck'
        for name,want in cert.get('external_evidence_sha256',{}).items():
            p=Path(name)
            if not p.is_file() or sha_file(p)!=want:return False,'v5 source evidence missing/changed: '+name
        return True,None
    except (ValueError,TypeError,KeyError,OSError) as exc:return False,'v5 selfcheck error: '+str(exc)

def status(cfg,runner_dir=None):
    try:
        fp=fingerprint(cfg,runner_dir);path=cache_path(cfg)
        cert=json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {}
        valid,reason=certificate_valid(cert,fp)
        return dict(required=not valid,qualified=valid,reason=reason,certificate=cert if valid else None,
                    fingerprint=fp,cache_path=str(path),scope=SCOPE)
    except Exception as exc:
        return dict(required=True,qualified=False,reason=str(exc),certificate=None,fingerprint=None,
                    cache_path=str(cache_path(cfg)),scope=SCOPE)

def _attest_from_index(path):
    path=Path(path).resolve()
    parent=next((p for p in path.parents if (p/'ALL_SHA256.txt').is_file() or (p/'11_汇总与证据_summary/ALL_SHA256.txt').is_file()),None)
    if parent is None:raise ValueError('source evidence index missing: '+str(path))
    index=parent/'ALL_SHA256.txt'
    if not index.is_file():index=parent/'11_汇总与证据_summary/ALL_SHA256.txt'
    inventory={rel.replace('\\','/'):h for h,rel in (line.split('  ',1) for line in index.read_text(encoding='utf-8').splitlines())}
    digest=sha_file(path)
    if inventory.get(path.relative_to(parent).as_posix())!=digest:raise ValueError('source evidence index mismatch: '+str(path))
    return digest

def run(cfg,round_dir):
    from measure_v4 import save
    root=Path(round_dir);runner=root/'03_脚本与插件_runner'
    out=root/'10_验证工具自检_selfcheck/cpu_etw_v5';out.mkdir(parents=True,exist_ok=False)
    previous=status(cfg,runner);fp=previous['fingerprint'];error=None;external={};checks={}
    if previous['qualified']:
        save(out/'reused_selfcheck.json',previous)
        save(root/'01_来源与环境_meta/cpu_etw_selfcheck.json',previous)
        print('v5 ETW technical selfcheck REUSED',flush=True);return 0
    try:
        if fp is None:raise ValueError(previous['reason'])
        spec=cfg.get('cpu_etw_selfcheck_evidence') or {}
        audit=Path(spec['audit_root']);impact=Path(spec['interference_root'])
        names=[audit/'result.json',audit/'metrics_corrected.json',audit/'parser_xperf_comparisons.json',
               impact/'result.json',impact/'all_raw.json',impact/'identity_before.json']
        external={str(p):_attest_from_index(p) for p in names}
        a=json.loads((audit/'result.json').read_text(encoding='utf-8'))
        frozen_parser=audit.parent/'03_执行脚本与测试/runner/etw_reference.py'
        external[str(frozen_parser)]=_attest_from_index(frozen_parser)
        if a.get('ok') is not True or a.get('parser_sha256')!=sha_file(frozen_parser):
            raise ValueError('ETW software analysis identity missing/changed')
        for path,want in a['source_hashes'].items():
            if sha_file(path)!=want:raise ValueError('raw reference evidence hash changed: '+path)
            external[path]=want
        audited=json.loads((audit/'metrics_corrected.json').read_text(encoding='utf-8'))
        if len(audited)!=1400:raise ValueError('audited reference count mismatch')
        replayed=False
        if parser_digest(frozen_parser)!=parser_digest(runner/'etw_reference.py'):
            from etw_reference import read_reference
            events=next(path for path in a['source_hashes'] if Path(path).name=='events.csv')
            print('v5 selfcheck: parser changed, replaying existing 1400 event records; no new Yosys runs',flush=True)
            current=read_reference(events,audited)
            if len(current)!=len(audited):raise ValueError('replayed reference sample count mismatch')
            counts=collections.Counter(p['pid'] for r in current for p in r['reference_processes'])
            if any(n!=1 for n in counts.values()):raise ValueError('PID reuse makes process-only software cross-check ambiguous')
            cpu_csv=next(path for path in a['source_hashes'] if Path(path).name=='cpu.csv')
            actual=collections.Counter();process_section=False
            with Path(cpu_csv).open(encoding='utf-8-sig',newline='') as stream:
                for fields in csv.reader(stream,skipinitialspace=True):
                    if fields and fields[0].strip()=='Time (us)':process_section=len(fields)==2;continue
                    if process_section and len(fields)==2:
                        match=re.search(r'\(\s*(\d+)\s*\)',fields[1])
                        if match:
                            try:actual[int(match[1])]+=int(fields[0])
                            except ValueError:pass
            differences=[]
            for r in current:
                reference=sum(actual[p['pid']] for p in r['reference_processes'])*10
                if reference<=0:raise ValueError('xperf process CPU missing')
                differences.append(abs(r['cpu_reference_ticks']/reference-1)*100)
            if max(differences)>a['software_tolerance_pct']:
                raise ValueError('current event parser / xperf software cross-check exceeds existing tolerance')
            save(out/'parser_replay_crosscheck.json',dict(samples=len(current),max_sample_difference_pct=max(differences),
                tolerance_pct=a['software_tolerance_pct'],comparison='current parser vs xperf, not equality to a formerly buggy reader'))
            audited=current;replayed=True
        for r in audited:
            candidate=dict(r,performance_scheme=SCHEME,cpu_primary_method=METHOD,
                           cpu_etw_total_ticks=r.get('cpu_reference_ticks'),etw_capture_complete=True)
            if sample_errors(candidate):raise ValueError('audited event sample incomplete')
        groups={r['group'] for r in audited}
        if not {'test1','test2','test3','test4','fixture_zero','fixture_small','fixture_large'}<=groups:
            raise ValueError('four-case reference coverage missing')
        software=json.loads((audit/'parser_xperf_comparisons.json').read_text(encoding='utf-8'))
        if set(software)!=groups or not all(s.get('valid') is True for s in software.values()):
            raise ValueError('software cross-check incomplete')
        # Bind the reference to the actual baseline, ABC source and frozen inputs.
        source_round=Path(next(iter(a['source_hashes'])))
        source_round=next(p for p in source_round.parents if (p/'validation_context.json').is_file())
        old=json.loads((source_round/'validation_context.json').read_text(encoding='utf-8'))
        original_fingerprint=source_round/'10_验证工具自检_selfcheck/cpu_method_qualification/fingerprint.json'
        external[str(original_fingerprint)]=_attest_from_index(original_fingerprint)
        old_fp=json.loads(original_fingerprint.read_text(encoding='utf-8'))
        for key in ('environment','tools','tool_data','build_identity','suite_manifest_sha256','abc_source_commit'):
            if old_fp.get(key)!=fp.get(key):raise ValueError('reference environment/tool identity mismatch: '+key)
        for name in ('cpu_precise.wprp','cpu_etw_collector.ps1'):
            if old_fp['code'][name]!=fp['code'][name]:raise ValueError('reference recorder/profile identity changed')
        if old['suite_manifest_sha256']!=cfg['suite_manifest_sha256']:
            raise ValueError('reference input suite identity mismatch')
        if old['builtin']['baseline']['binary_sha256']!=sha_file(cfg['builtin']['baseline']['path']):
            raise ValueError('baseline reference identity mismatch')
        old_evidence=json.loads((source_round/'01_来源与环境_meta/builtin_evidence.json').read_text(encoding='utf-8'))['evidence']
        if old_evidence['abc_baseline']['sha256']!=sha_file(cfg['builtin']['abc']['baseline']):
            raise ValueError('ABC reference identity mismatch')
        context_hash=sha_file(source_round/'validation_context.json')
        external[str(source_round/'validation_context.json')]=context_hash
        external[str(source_round/'01_来源与环境_meta/builtin_evidence.json')]=sha_file(source_round/'01_来源与环境_meta/builtin_evidence.json')
        impact_rows=json.loads((impact/'all_raw.json').read_text(encoding='utf-8'))
        if len(impact_rows)!=1200:raise ValueError('interference evidence count mismatch')
        impact_stats={v:analyse_job_runs([r for r in impact_rows if r['variant']==v]) for v in ('baseline','optimized')}
        if not all(s['valid'] for s in impact_stats.values()):raise ValueError('interference sample integrity invalid')
        identities=json.loads((impact/'identity_before.json').read_text(encoding='utf-8'))
        applies={v:identities.get(str(Path(cfg['builtin'][v]['path'])))==sha_file(cfg['builtin'][v]['path']) for v in ('baseline','optimized')}
        checks=dict(reference_samples=1400,groups=sorted(groups),software_crosscheck=a,parser_replayed_existing_events=replayed,
                    interference_scope='test2, recorded original/optimized identities only; not all circuits',
                    interference_current_identity_matches=applies,interference_statistics=impact_stats,
                    absolute_accuracy_guarantee=False,job_event_agreement_gate=False,wall_clock_gate=False)
    except Exception as exc:error=str(exc)
    result=dict(ok=error is None,error=error,scope=SCOPE,fingerprint=fp,checks=checks,new_yosys_samples=0)
    save(out/'result.json',result);save(out/'source_evidence.json',external)
    if result['ok']:
        inventory={p.relative_to(out).as_posix():sha_file(p) for p in out.rglob('*') if p.is_file()}
        cert=dict(ok=True,scope=SCOPE,fingerprint=fp,evidence_root=str(out),evidence_sha256=inventory,
                  external_evidence_sha256=external)
        path=cache_path(cfg);path.parent.mkdir(parents=True,exist_ok=True);save(path,cert)
        state=dict(required=False,qualified=True,reason=None,certificate=cert,fingerprint=fp,scope=SCOPE)
    else:state=dict(required=True,qualified=False,reason=error,certificate=None,fingerprint=fp,scope=SCOPE)
    save(root/'01_来源与环境_meta/cpu_etw_selfcheck.json',state)
    print('v5 ETW technical selfcheck '+('PASS' if result['ok'] else 'FAIL: '+str(error)),flush=True)
    return 0 if result['ok'] else 1

if __name__=='__main__':
    import p3_common as C
    sys.exit(run(C.CONTEXT,C.ROUND_DIR))
