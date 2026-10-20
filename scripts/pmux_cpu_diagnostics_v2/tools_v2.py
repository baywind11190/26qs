"""Independent cache, exact source transforms, no official registry mutations."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import patch_v2
import prepare_builtin as P

HERE=Path(__file__).parent

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def save(p,x):
    Path(p).parent.mkdir(parents=True,exist_ok=True)
    Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))

def seal(root,preserve_previous=False):
    root=Path(root);manifest=root/'SHA256.json'
    previous=root/'SHA256_before_trace.json'
    if preserve_previous and manifest.exists() and not previous.exists():shutil.copy2(manifest,previous)
    save(manifest,{p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p!=manifest})

def source_bytes(cfg):
    return subprocess.check_output(['git','-C',str(cfg['repo']),'show',cfg['target_commit']+':src/pmux_opt.cc'])

def protected(project):
    root=Path(project)
    files=[root/'src/pmux_opt.cc']+list((root/'scripts/pmux_validation').rglob('*'))
    files+=[p for d in ('pmux_cpu_diagnostics','pmux_cpu_internal_pilot') for p in (root/'scripts'/d).rglob('*')]
    return {p.relative_to(root).as_posix():sha(p) for p in files if p.is_file() and '__pycache__' not in p.parts}

def key(cfg,source):
    return dict(schema=2,commit=cfg['target_commit'],source_sha256=hashlib.sha256(source).hexdigest(),
        patch=patch_v2.identity(),runtime_patch=P.runtime_patch.identity(),base_commit=cfg['builtin']['source_commit'],
        abc_commit=P._current_abc_commit(cfg),compiler=cfg['tools']['compiler'],build_profile=P.build_profile(cfg),
        dependencies=cfg['builtin']['toolchain_dependency_sha256'])

def verify_source(tree,optimized,source,k):
    tree=Path(tree)
    for repo,want in ((tree,k['base_commit']),(tree/'abc',k['abc_commit'])):
        if P._git(repo,'rev-parse','HEAD')!=want or P._git(repo,'diff','--cached','--name-only'):
            raise ValueError('source commit/index changed')
    original={}
    for name in patch_v2.FILES:
        repo=tree/'abc' if name.startswith('abc/') else tree;rel=name[4:] if name.startswith('abc/') else name
        original[name]=subprocess.check_output(['git','-C',str(repo),'show','HEAD:'+rel]).decode()
    expected=patch_v2.contents(original,optimized)
    for name,text in expected.items():
        if (tree/name).read_text(encoding='utf-8')!=text:raise ValueError('unexpected diagnostic source: '+name)
    allowed={'kernel/yosys.h','kernel/yosys.cc','kernel/driver.cc','techlibs/intel/synth_intel.cc','passes/techmap/abc9.cc','passes/techmap/abc9_exe.cc','abc'}
    if optimized:allowed.add('passes/opt/CMakeLists.txt')
    if set(P._git(tree,'diff','--name-only').splitlines())!=allowed:raise ValueError('unexpected tracked source files')
    new={'kernel/diag_v2_impl.inc','kernel/diag_v2_shared.h'}
    if optimized:new.add('passes/opt/pmux_opt.cc')
    if set(P._git(tree,'ls-files','--others','--exclude-standard').splitlines())!=new:raise ValueError('unexpected source files')
    if set(P._git(tree/'abc','diff','--name-only').splitlines())!={'src/base/main/main.c'}:raise ValueError('unexpected ABC changes')
    if set(P._git(tree/'abc','ls-files','--others','--exclude-standard').splitlines())!={'src/base/main/diag_v2_shared.h'}:raise ValueError('unexpected ABC files')
    for s,d in [('diag_v2_impl.inc','kernel/diag_v2_impl.inc'),('diag_v2_shared.h','kernel/diag_v2_shared.h'),('diag_v2_shared.h','abc/src/base/main/diag_v2_shared.h')]:
        if (tree/d).read_bytes()!=(HERE/s).read_bytes():raise ValueError('diagnostic include changed')
    if optimized and (tree/'passes/opt/pmux_opt.cc').read_bytes()!=source:raise ValueError('algorithm bytes changed')

def prepare(cfg,source,round_dir):
    k=key(cfg,source);tag=hashlib.sha256(json.dumps(k,sort_keys=True).encode()).hexdigest()[:16]
    root=Path(cfg['repo'])/'.tools/cache-cpu-diag-v2'/tag
    manifest=root/'manifest.json'
    if manifest.exists():
        m=read(manifest)
        if m.get('state')!='READY' or m['key']!=k:raise ValueError('cache incomplete; preserved, no automatic repair/rebuild')
        for side in ('baseline','optimized'):
            s=m[side];verify_source(s['source'],side=='optimized',source,k)
            for name in ('yosys','abc'):
                if sha(s[name])!=s[name+'_sha256']:raise ValueError('diagnostic binary changed')
        return m
    root.mkdir(parents=True,exist_ok=False);logs=root/'logs';logs.mkdir();m=dict(state='BUILDING',key=k,cache=str(root),started=time.time())
    save(manifest,m)
    try:
        for side in ('baseline','optimized'):
            tree=root/(side+'-src');print('DIAG_BUILD '+side,flush=True)
            shutil.copytree(cfg['builtin']['source_repo'],tree,ignore=P._ignore_root_build(cfg['builtin']['source_repo']))
            if P._git(tree,'rev-parse','HEAD')!=k['base_commit'] or P._git(tree,'status','--porcelain','--untracked-files=no'):raise ValueError('base tree not clean/pinned')
            patch_v2.apply(tree,side=='optimized')
            if side=='optimized':(tree/'passes/opt/pmux_opt.cc').write_bytes(source)
            verify_source(tree,side=='optimized',source,k)
            P._cmake_build(tree,logs,side,cfg)
            m[side]=dict(source=str(tree),yosys=str(tree/'build/yosys.exe'),abc=str(tree/'build/yosys-abc.exe'))
        shutil.copy2(m['baseline']['abc'],m['optimized']['abc'])
        for side in ('baseline','optimized'):
            s=m[side]
            for name in ('yosys','abc'):s[name+'_sha256']=sha(s[name])
            P._verify_binary(Path(s['yosys']),side=='optimized','0.69',env=P._build_env(cfg))
        m.update(state='READY',finished=time.time());save(manifest,m);return m
    except Exception as exc:
        m.update(state='FAILED',error=str(exc));save(manifest,m);raise
