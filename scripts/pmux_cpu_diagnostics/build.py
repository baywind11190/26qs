"""Independent diagnostic cache. Never publishes to the official v6 registry."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import patch
import prepare_builtin as P

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def save(path,data):Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def key(cfg,source):
    return dict(schema=1,commit=cfg['target_commit'],source_sha256=hashlib.sha256(source).hexdigest(),
                patch=patch.identity(),base_commit=cfg['builtin']['source_commit'],
                abc_commit=P._current_abc_commit(cfg),compiler=cfg['tools']['compiler'],
                build_profile=P.build_profile(cfg),platform=cfg['platform'],
                dependency_sha256=cfg['builtin']['toolchain_dependency_sha256'])

def directory(cfg,source):
    k=key(cfg,source);tag=hashlib.sha256(json.dumps(k,sort_keys=True).encode()).hexdigest()[:16]
    return Path(cfg['repo'])/'.tools/cache-cpu-stage-diag-v1'/tag

def check_source_identity(tree,optimized,base_commit,abc_commit):
    tree=Path(tree)
    for repo,want in ((tree,base_commit),(tree/'abc',abc_commit)):
        if P._git(repo,'rev-parse','HEAD')!=want:raise ValueError('diagnostic source HEAD differs from pinned identity')
        if P._git(repo,'diff','--cached','--name-only'):raise ValueError('diagnostic source index contains changes')
    expected={'kernel/diag_cpu_impl.inc','kernel/diag_cpu_shared.h'}
    if optimized:expected.add('passes/opt/pmux_opt.cc')
    if set(P._git(tree,'ls-files','--others','--exclude-standard').splitlines())!=expected:
        raise ValueError('unapproved untracked diagnostic source')
    if set(P._git(tree/'abc','ls-files','--others','--exclude-standard').splitlines())!={'src/base/main/diag_cpu_shared.h'}:
        raise ValueError('unapproved untracked ABC source')

def verify_sources(tree,optimized,source,base_commit=None,abc_commit=None):
    tree=Path(tree)
    if base_commit is not None:check_source_identity(tree,optimized,base_commit,abc_commit)
    original={}
    for p in patch.FILES:
        repo=tree/'abc' if p.startswith('abc/') else tree
        rel=p[4:] if p.startswith('abc/') else p
        original[p]=subprocess.check_output(['git','-C',str(repo),'show','HEAD:'+rel]).decode('utf-8')
    expected=patch.contents(original,optimized)
    for p,text in expected.items():
        if (tree/p).read_text(encoding='utf-8')!=text:raise ValueError('source differs from exact diagnostic patch: '+p)
    changed=set(P._git(tree,'diff','--name-only').splitlines())
    allowed={'kernel/yosys.h','kernel/yosys.cc','kernel/driver.cc','techlibs/intel/synth_intel.cc','passes/techmap/abc9.cc','passes/techmap/abc9_exe.cc','abc'}
    if optimized:allowed.add('passes/opt/CMakeLists.txt')
    if changed!=allowed:raise ValueError('unexpected diagnostic source diff: '+str(changed))
    if set(P._git(tree/'abc','diff','--name-only').splitlines())!={'src/base/main/main.c'}:raise ValueError('unexpected ABC diff')
    for src,dst in [('diag_cpu_impl.inc','kernel/diag_cpu_impl.inc'),('diag_cpu_shared.h','kernel/diag_cpu_shared.h'),('diag_cpu_shared.h','abc/src/base/main/diag_cpu_shared.h')]:
        if (tree/dst).read_bytes()!=(patch.HERE/src).read_bytes():raise ValueError('diagnostic include mismatch')
    if optimized and (tree/'passes/opt/pmux_opt.cc').read_bytes()!=source:raise ValueError('algorithm bytes mismatch')

def load(cfg,source):
    root=directory(cfg,source);p=root/'manifest.json'
    # A repaired owned build may retain its original directory and failure logs.
    if not p.is_file():
        candidates=sorted(root.parent.glob('*/manifest.json'))
        p=next((v for v in candidates if read_key(v)==key(cfg,source)),None)
        if p is None:return None
    m=json.loads(p.read_text(encoding='utf-8'))
    if m.get('state')!='READY' or m.get('key')!=key(cfg,source):return None
    for side in ('baseline','optimized'):
        s=m[side]
        verify_sources(s['source'],side=='optimized',source,m['key']['base_commit'],m['key']['abc_commit'])
        for name in ('yosys','abc'):
            if sha(s[name])!=s[name+'_sha256']:raise ValueError('cached diagnostic binary changed')
    if m['baseline']['abc_sha256']!=m['optimized']['abc_sha256']:raise ValueError('diagnostic ABC binaries differ')
    return m

def read_key(path):
    m=json.loads(Path(path).read_text(encoding='utf-8'))
    return m.get('key') if m.get('state')=='READY' else None

def prepare(cfg,source):
    hit=load(cfg,source)
    if hit:return hit
    root=directory(cfg,source);root.mkdir(parents=True,exist_ok=False);logs=root/'logs';logs.mkdir()
    m=dict(state='BUILDING',key=key(cfg,source),cache=str(root))
    save(root/'manifest.json',m)
    try:
        for side in ('baseline','optimized'):
            tree=root/(side+'-src')
            print('DIAG_BUILD '+side,flush=True)
            shutil.copytree(cfg['builtin']['source_repo'],tree,ignore=P._ignore_root_build(cfg['builtin']['source_repo']))
            if P._git(tree,'rev-parse','HEAD')!=cfg['builtin']['source_commit'] or P._git(tree,'status','--porcelain','--untracked-files=no'):raise ValueError('base source not clean/pinned')
            patch.apply(tree,side=='optimized')
            if side=='optimized':(tree/'passes/opt/pmux_opt.cc').write_bytes(source)
            verify_sources(tree,side=='optimized',source,m['key']['base_commit'],m['key']['abc_commit'])
            # Reuse the established compiler/environment/build profile, in the independent cache.
            P._cmake_build(tree,logs,side,cfg)
            exe=tree/'build/yosys.exe';abc=tree/'build/yosys-abc.exe'
            m[side]=dict(source=str(tree),yosys=str(exe),abc=str(abc))
        # Exactly one diagnostic ABC image is used on both sides.
        shutil.copy2(m['baseline']['abc'],m['optimized']['abc'])
        for side in ('baseline','optimized'):
            s=m[side]
            for name in ('yosys','abc'):s[name+'_sha256']=sha(s[name])
            P._verify_binary(Path(s['yosys']),side=='optimized','0.69',env=P._build_env(cfg))
        m['state']='READY';save(root/'manifest.json',m);return m
    except Exception as exc:
        m.update(state='FAILED',error=str(exc));save(root/'manifest.json',m);raise
