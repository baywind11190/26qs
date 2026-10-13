"""Independent CPU method identity and attested certificate cache (no algorithm key)."""
import ctypes
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import subprocess

from cpu_statistics import SCHEME, POLICY


def sha_file(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()


def environment():
    import winreg
    info=dict(platform=platform.platform(),windows_version=list(platform.win32_ver()))
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as key:
        info['cpu']=winreg.QueryValueEx(key,'ProcessorNameString')[0].strip()
        info['cpu_identifier']=winreg.QueryValueEx(key,'Identifier')[0]
    info['logical_cpus']=os.cpu_count()
    power=subprocess.check_output(['powercfg.exe','/getactivescheme'],text=True,errors='replace')
    match=re.search(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}',power)
    if not match: raise ValueError('active power plan GUID unavailable')
    info['power_plan_guid']=match[0].lower()
    class Power(ctypes.Structure):
        _fields_=[('ac',ctypes.c_ubyte),('flags',ctypes.c_ubyte),('percent',ctypes.c_ubyte),
                  ('reserved',ctypes.c_ubyte),('life',ctypes.c_uint32),('full',ctypes.c_uint32)]
    status=Power()
    if not ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status)):
        raise OSError('GetSystemPowerStatus failed')
    info['ac_line_status']=int(status.ac)
    return info


def fingerprint(cfg,runner_dir=None):
    runner=Path(runner_dir or Path(__file__).parent)
    files=('cpu_statistics.py','win_measure.py','measure_v4.py','cpu_qualification.py',
           'etw_reference.py','qualify_cpu_method.py','cpu_qualification_probe.c','cpu_etw_collector.ps1','cpu_precise.wprp',
           'builtin_common.py','p3_common.py')
    tools={}
    builtin=cfg.get('builtin') or {}
    baseline=builtin.get('baseline') or builtin.get('baseline_reuse') or {}
    actual_yosys=baseline.get('path') or baseline.get('binary') or cfg['tools']['yosys']['path']
    actual_abc=(builtin.get('abc') or {}).get('baseline') or baseline.get('abc') or cfg['tools']['abc']['path']
    for name in ('yosys','abc','compiler'):
        path=actual_yosys if name=='yosys' else actual_abc if name=='abc' else cfg['tools'][name]['path']
        tools[name]=sha_file(path)
    tools['fixture_gcc']=sha_file(Path(cfg['tools']['compiler']['path']).parent/'gcc.exe')
    for name,path in cfg.get('cpu_reference_tools',{}).items():
        p=Path(path)
        if not p.is_file(): raise FileNotFoundError('CPU reference tool missing: '+str(p))
        tools[name]=sha_file(p)
    for name,tool in cfg.get('runtime_tools',{}).items():tools['runtime_'+name]=sha_file(tool['path'])
    git=(cfg.get('runtime_tools',{}).get('git') or {}).get('path','git')
    abc_source=Path(cfg['builtin'].get('source_repo',cfg['yosys_source']))/'abc'
    commit=subprocess.check_output([git,'-C',str(abc_source),'rev-parse','HEAD'],text=True).strip()
    declared=cfg
    if cfg.get('config_path') and Path(cfg['config_path']).is_file():
        declared=json.loads(Path(cfg['config_path']).read_text(encoding='utf-8'))
    declared_builtin=declared.get('builtin') or {}
    dependency=declared_builtin.get('toolchain_identity_manifest')
    build_identity=dict(profile=declared_builtin.get('build_profile'),source_commit=cfg.get('yosys_src_commit'),
                        dependency_manifest_sha256=sha_file(dependency) if dependency else None,
                        dependency_identity=declared_builtin.get('toolchain_dependency_identity'))
    tool_data={}
    if cfg.get('tool_data'):
        binary=Path(actual_yosys)
        candidates=(binary.parent/'share/yosys',binary.parent/'share',binary.parent.parent/'share/yosys',binary.parent.parent/'share')
        share=next((p for p in candidates if (p/'intel/cycloneiv/cells_map.v').is_file()),None)
        if share is None:raise ValueError('actual baseline Yosys data root not found')
        rules=cfg['tool_data_fourcase_filter']
        for item in cfg['tool_data']:
            path=Path(item['path']);normalized=str(path).replace('\\','/')
            selected=any(sub.replace('\\','/') in normalized for sub in rules['include_subpaths']) or (path.parent.name.lower() in ('share','yosys') and path.name in rules['direct_share_files'])
            if not selected:continue
            anchor='/share/yosys/' if '/share/yosys/' in normalized else '/share/'
            if anchor not in normalized:raise ValueError('unrecognized tool data path: '+normalized)
            rel=normalized.split(anchor,1)[1]
            tool_data[rel]=sha_file(share/rel)
    return dict(schema=1,scheme=SCHEME,policy=POLICY,environment=environment(),tools=tools,
                tool_data=tool_data,
                build_identity=build_identity,suite_manifest_sha256=cfg.get('suite_manifest_sha256'),
                abc_source_commit=commit,code={f:hashlib.sha256((runner/f).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for f in files})


def cache_path(cfg):
    return Path(cfg['repo'])/'results/官方口径评测/_共享CPU方法资格_cpu/certificate.json'


def certificate_valid(cert,expected):
    try:
        if cert.get('ok') is not True or cert.get('fingerprint')!=expected:
            return False,'qualification missing/failed/fingerprint mismatch'
        guard=cert.get('guard_pct')
        if type(guard) not in (int,float) or not math.isfinite(guard) or not 0<=guard<=1+1e-9:
            return False,'qualification guard invalid'
        inventory=cert.get('evidence_sha256') or {}
        if not inventory:return False,'qualification evidence inventory missing'
        root=Path(cert['evidence_root']).resolve()
        for rel,want in inventory.items():
            path=(root/rel).resolve();path.relative_to(root)
            if not path.is_file() or sha_file(path)!=want:return False,'qualification evidence missing/changed: '+rel
        result_path=root/'qualification_result.json'
        if 'qualification_result.json' not in inventory:return False,'qualification result not attested'
        result=json.loads(result_path.read_text(encoding='utf-8'))
        if result.get('ok') is not True or result.get('fingerprint')!=expected or result.get('guard_pct')!=guard:
            return False,'certificate disagrees with attested qualification result'
        return True,None
    except (KeyError,ValueError,OSError,TypeError) as exc:
        return False,'qualification verification error: '+str(exc)


def qualification_status(cfg,runner_dir=None):
    try:
        fp=fingerprint(cfg,runner_dir)
        path=cache_path(cfg)
        cert=json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {}
        valid,reason=certificate_valid(cert,fp)
        return dict(required=not valid,qualified=valid,reason=reason,certificate=cert if valid else None,
                    fingerprint=fp,cache_path=str(path))
    except Exception as exc:
        return dict(required=True,qualified=False,reason=str(exc),certificate=None,fingerprint=None,
                    cache_path=str(cache_path(cfg)))
