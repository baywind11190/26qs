"""eqy-zero-init-r1: native EQY completion plus non-vacuity and init-only audits.

JSON rewriting is deliberately limited to Q-wire init attributes. It is the
attribute-only equivalent of selecting Q wires for setundef -zero -init, without
setundef's rewriting of selected combinational connections.
"""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import function_common as F
from process_utils import process_group_kwargs, terminate_process_tree

VERSION = 'eqy-zero-init-r1'
FF_TYPES = {'$dff','$dffe','$dffsr','$dffsre','$adff','$adffe','$aldff','$aldffe','$sdff','$sdffe','$sdffce','$ff'}


def enabled(context):
    return context.get('strategy_version', context.get('functional_strategy')) == VERSION


def remaining_seconds(deadline, now=None):
    return max(0, deadline - (time.monotonic() if now is None else now))


def merged_coverage(expected, actual):
    return bool(expected) and set(expected) <= set(actual)


def audit_workspace(work, result):
    """Always check path safety; partial failed work need not be complete."""
    import eqy_workspace as W
    work = W.safe_root(work)
    paths = W.check_paths([work, *work.rglob('*')])
    if result.get('state') == 'TIMEOUT':
        return {'complete':False, 'state':'TIMEOUT', 'paths':paths}
    try:
        audit = W.check_work(work, expected=None)
        if set(audit['partitions']) != set(result.get('partition_states', {})):
            raise ValueError('Native partition coverage differs from path audit')
        return dict(audit, complete=True)
    except (ValueError, FileNotFoundError) as exc:
        result['state'] = 'TOOL_OR_CONFIG_ERROR'
        result.setdefault('native_errors', []).append('Workspace completeness audit: '+str(exc))
        return {'complete':False, 'state':result['state'], 'error':str(exc), 'paths':paths}


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2); f.write('\n')


def zero_init_json(original):
    out = copy.deepcopy(original)
    count = 0
    for mod in out['modules'].values():
        qbits = {b for c in mod.get('cells',{}).values()
                 if c['type'] in FF_TYPES or c['type'].startswith(('$_DFF','$_SDFF','$_DFFE'))
                 for b in c['connections']['Q'] if isinstance(b,int)}
        known = {}
        nets = mod.get('netnames',{})
        for net in nets.values():
            init = net.get('attributes',{}).get('init','')
            for bit,val in zip(net['bits'],init[::-1]):
                if bit in qbits and val in '01':
                    if bit in known and known[bit] != val:
                        raise ValueError('Conflicting explicit init aliases')
                    known[bit] = val
        missing = qbits-set(known)
        count += len(missing)
        # Use existing wire aliases; never add/change ports, cells or connections.
        assigned=set()
        for net in nets.values():
            bits=net['bits']; attrs=net.setdefault('attributes',{})
            old=attrs.get('init','x'*len(bits)); vals=list(old[::-1].ljust(len(bits),'x'))
            changed=False
            for i,bit in enumerate(bits):
                if bit in qbits and vals[i] not in '01':
                    if bit in known:
                        vals[i]=known[bit];changed=True
                    elif bit not in assigned:
                        vals[i]='0';assigned.add(bit);changed=True
            if changed: attrs['init']=''.join(vals[::-1])
        if assigned != missing:
            raise ValueError('Some FF Q bits have no wire alias')
    def strip_init(d):
        d=copy.deepcopy(d)
        for m in d['modules'].values():
            for n in m.get('netnames',{}).values(): n.get('attributes',{}).pop('init',None)
        return d
    if strip_init(out) != strip_init(original):
        raise ValueError('Zero initialization changed non-init data')
    return out, {'only_init_attributes_changed':True,'initialized_bits':count,
                 'method':'Q-wire-init-attributes-only','explicit_01_preserved':True}


def make_cfg(gold,gate,top):
    partition='\n[partition test3]\nmerge *\n' if top=='test3' else ''
    return (f'[gold]\nread_json {Path(gold).as_posix()}\n\n[gate]\nread_json {Path(gate).as_posix()}\n'
            +partition+f'\n[strategy simple]\nuse sat\ndepth {16 if top=="test3" else 5}\n')


def make_probe(script):
    lines=script.splitlines(); idx=F._find_sat_line(lines); sat=lines[idx]
    if sat.count('-set-def-formal')!=1 or '-set-assumes' not in sat:
        raise ValueError('Native SAT assumptions changed')
    depth=re.search(r'-maxsteps (\d+)',sat)
    if not depth: raise ValueError('Missing native SAT depth')
    # Keep the generated preparation and all SAT assumptions, remove goals only.
    sat=sat.replace('-tempinduct',f'-seq {depth[1]}').replace('-prove-asserts','')
    sat=re.sub(r'-maxsteps \d+','',sat)
    sat=re.sub(r'-dump_vcd \S+','',sat)
    return '\n'.join(lines[:idx]+['chformal -assert -remove',sat]+lines[idx+1:])+'\n'


def aggregate(rc,status,errors,parts):
    states=[v['proof']['state'] for v in parts.values()]
    premises=bool(parts) and all(v['probe'].get('state')=='VALID' and v['probe']['verdict']=='PREMISES_SAT' for v in parts.values())
    cover=bool(parts) and all(v['coverage_ok'] for v in parts.values())
    if rc==124: state='TIMEOUT'
    elif errors or status=='ERROR' or (rc not in (0,2,4,8)):
        state='TOOL_OR_CONFIG_ERROR'
    elif any(v['probe'].get('verdict')=='PREMISES_UNSAT' for v in parts.values()): state='PREMISES_NOT_SAT'
    elif 'FAIL' in states: state='FAIL'
    elif 'TIMEOUT' in states: state='TIMEOUT'
    elif any(v['probe'].get('state')=='TIMEOUT' or v['probe'].get('rc')==124 for v in parts.values()): state='TIMEOUT'
    elif any(v['probe'].get('state')=='TOOL_OR_CONFIG_ERROR' for v in parts.values()): state='TOOL_OR_CONFIG_ERROR'
    elif any(s in ('TOOL_OR_CONFIG_ERROR','INCOMPLETE') for s in states): state='TOOL_OR_CONFIG_ERROR'
    elif rc==0 and status=='PASS' and cover and premises and all(s=='PASS' for s in states): state='PASS'
    elif status in ('FAIL','UNKNOWN') or 'UNKNOWN' in states: state='UNPROVEN'
    else: state='INCONCLUSIVE'
    return {'state':state,'native_rc':rc,'native_status':status,'native_errors':errors,
            'premises_all_sat':premises,'coverage_ok':cover,'partitions':parts,
            'partitions_total':len(parts),'partitions_pass':sum(s=='PASS' for s in states),
            'partition_states':{k:v['proof']['state'] for k,v in parts.items()}}


def frozen_env(yosys):
    env=dict(os.environ)
    # EQY strategy run.sh calls bare yosys, including under make's Bash shell.
    env['PATH']=str(Path(yosys).resolve().parent)+os.pathsep+env.get('PATH','')
    actual=shutil.which('yosys',path=env['PATH'])
    if not actual or Path(actual).resolve()!=Path(yosys).resolve():
        raise ValueError('Native EQY bare yosys PATH resolution differs')
    bash=shutil.which('bash',path=env['PATH'])
    if not bash: raise ValueError('Native EQY bash unavailable')
    check=subprocess.run([bash,'-c','command -v yosys'],env=env,text=True,capture_output=True)
    resolved=check.stdout.strip()
    # Bash/MSYS returns /d/... even when invoked by Windows Python.
    cyg=shutil.which('cygpath',path=env['PATH'])
    if cyg:
        converted=subprocess.run([cyg,'-w',resolved],env=env,text=True,capture_output=True,check=True).stdout.strip()
    else: converted=resolved
    if check.returncode or Path(converted).resolve()!=Path(yosys).resolve():
        raise ValueError('Bash bare yosys resolves to a different executable: '+resolved)
    return env, {'path':env['PATH'],'bare_yosys':actual,'bash_yosys':resolved,'bash':bash}


def run_chain(gold_lines,gate_lines,top,job,*,yosys,abc,eqy,timeout_s=600):
    job=Path(job);job.mkdir(parents=True,exist_ok=True)
    deadline=time.monotonic()+timeout_s
    def remaining(): return remaining_seconds(deadline)
    init_audits={}
    def finish(result, markers=None):
        result.update(strategy_version=VERSION, method='native_eqy', init_audits=init_audits,
                      init_audit_ok=set(init_audits)=={'gold','gate'} and all(a['only_init_attributes_changed'] for a in init_audits.values()),
                      native_status_files=markers or [], timeout_s=timeout_s,
                      chain_deadline_exhausted=remaining() <= 0)
        save(job/'native_summary.json', result)
        return result
    for side,lines in [('gold',gold_lines),('gate',gate_lines)]:
        before=job/(side+'.before.json');after=job/(side+'.zero.json')
        ys=job/(side+'.ys')
        ys.write_text('\n'.join(lines+['flatten','proc','write_json '+before.as_posix()])+'\n',encoding='utf-8')
        rc=(F.run_yosys_script(ys,job/(side+'.log'),job,yosys=yosys,timeout_s=remaining())
            if remaining() > 0 else 124)
        if rc: return finish({'state':'TIMEOUT' if rc==124 else 'TOOL_OR_CONFIG_ERROR','error':side+' preparation failed','partitions':{},'native_rc':rc})
        normalized,audit=zero_init_json(json.loads(before.read_text(encoding='utf-8')))
        save(after,normalized);audit.update(before_sha256=F.sha256_file(before),after_sha256=F.sha256_file(after))
        save(job/(side+'.init_audit.json'),audit);init_audits[side]=audit
    cfg=job/'config.eqy';cfg.write_text(make_cfg(job/'gold.zero.json',job/'gate.zero.json',top),encoding='utf-8')
    work=job/'work'
    if work.exists(): raise FileExistsError('Refusing reused native EQY work')
    env,path_audit=frozen_env(yosys); save(job/'tool_path_audit.json',path_audit)
    cmd=[str(eqy),'-j','1','-d',str(work),'--yosys',str(yosys),'--abc',str(abc),str(cfg)]
    if remaining() <= 0:
        return finish({'state':'TIMEOUT','error':'chain deadline before native EQY','partitions':{},'native_rc':124})
    with (job/'native_eqy.log').open('x',encoding='utf-8') as log:
        proc=subprocess.Popen(cmd,cwd=job,env=env,stdout=log,stderr=subprocess.STDOUT,**process_group_kwargs())
        try: rc=proc.wait(timeout=remaining())
        except subprocess.TimeoutExpired:
            terminate_process_tree(proc);proc.wait();rc=124
    markers=[s for s in ['PASS','FAIL','UNKNOWN','ERROR','TIMEOUT'] if (work/s).is_file()]
    status=markers[0] if len(markers)==1 else 'MISSING_OR_AMBIGUOUS'
    logs=[p for p in work.rglob('*.log') if p.is_file()]+[job/'native_eqy.log']
    errors=[f'{p.relative_to(job)}: {line}' for p in logs for line in p.read_text(errors='replace').splitlines() if re.search(r'(^|\s)ERROR:',line)]
    parts={}
    svs={p.stem:p for p in (work/'partitions').glob('*.sv')}
    generated={p.parent.name:p for p in (work/'strategies').glob('*/simple')}
    # EQY may be killed while creating strategy directories, before run.ys exists.
    # Keep its partial work and global markers; never let a missing file hide timeout.
    if rc == 124 or remaining() <= 0:
        result=aggregate(rc,status,errors,{})
        result.update(state='TIMEOUT', partial_partitions=sorted(generated))
        return finish(result, markers)
    absent=[str(p/'run.ys') for p in generated.values() if not (p/'run.ys').is_file()]
    if absent:
        errors.append('Missing native generated strategy scripts: '+', '.join(absent))
        return finish(aggregate(rc,status,errors,{}), markers)
    for name,sdir in sorted(generated.items()):
        script=(sdir/'run.ys').read_text(encoding='utf-8')
        if '-set-def-formal' not in script: raise ValueError('Native strategy was altered')
        proof=F.classify_proof_text((sdir/'run.log').read_text(errors='replace') if (sdir/'run.log').is_file() else '')
        native_partition=(sdir/'status').read_text().strip() if (sdir/'status').is_file() else 'MISSING'
        if native_partition!='PASS' and proof['state']=='PASS': proof['state']='INCOMPLETE'
        sv=svs[name].read_text(encoding='utf-8') if name in svs else ''
        suffixes=re.findall(r'\s(\\?\S+__assert)\s*\(',sv)
        suffixes=[s.lstrip('\\')+'.okay' for s in suffixes]
        coverage,missing=F.verify_expected_asserts(suffixes,proof['asserts'])
        coverage=coverage and bool(suffixes)
        probe_ys=sdir/'probe_native.ys';probe_ys.write_text(make_probe(script),encoding='utf-8')
        prc=(F.run_yosys_script(probe_ys,sdir/'probe_native.log',sdir,yosys=yosys,timeout_s=remaining())
             if remaining() > 0 else 124)
        probe=F.classify_probe_result((sdir/'probe_native.log').read_text(errors='replace') if (sdir/'probe_native.log').is_file() else '',prc)
        parts[name]={'proof':proof,'probe':probe,'native_status':native_partition,'coverage_ok':coverage,'expected_asserts':suffixes,'missing_asserts':missing,'run_ys_sha256':F.sha256_file(sdir/'run.ys')}
    if set(svs)!=set(generated): errors.append('Partition/strategy set coverage differs')
    merged_audit = None
    if top == 'test3' and (work/'matched.ids').is_file():
        inputs={line.split()[1] for line in (work/'gold.ids').read_text().splitlines()
                if len(line.split()) > 1 and 'P=I' in line}
        expected={line.split()[1] for line in (work/'matched.ids').read_text().splitlines()
                  if line.startswith('test3 ') and len(line.split()) == 3} - inputs
        actual=set()
        for p in (work/'partitions').glob('*.json'):
            actual.update(json.loads(p.read_text())['partition']['outbits'])
        ok=len(parts)==1 and merged_coverage(expected, actual)
        merged_audit={'expected_matchpoints_and_outputs':sorted(expected),'actual_proved_outputs':sorted(actual),'ok':ok}
        if not ok: errors.append('Native test3 merge does not cover all matchpoints and outputs')
    result=aggregate(rc,status,errors,parts)
    result['chain_deadline_exhausted'] = remaining() <= 0
    if result['chain_deadline_exhausted']:
        result['state'] = 'TIMEOUT'
    result.update(strategy_version=VERSION,method='native_eqy',init_audits=init_audits,
                  init_audit_ok=all(a['only_init_attributes_changed'] for a in init_audits.values()),
                  native_status_files=markers,timeout_s=timeout_s,merged_coverage_audit=merged_audit)
    if result['state']=='PASS' and not result['init_audit_ok']:result['state']='TOOL_OR_CONFIG_ERROR'
    save(job/'native_summary.json',result)
    return result
