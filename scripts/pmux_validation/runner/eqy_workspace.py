"""Byte-preserving managed EQY workspaces; no synthesis or proof execution."""
from pathlib import Path
import hashlib
import json
import ntpath
import os
import re
import shutil
import result_layout as L

VERSION = 'managed-short-v1'
LIMIT = 200


def path_identity(path):
    """Windows native and MINGW slash spellings identify the same local path."""
    return ntpath.normcase(ntpath.normpath(str(path).replace('/', '\\')))


def _links(path):
    for p in (Path(path), *Path(path).parents):
        if p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction()):
            raise ValueError('Linked evidence path: ' + str(p))


def safe_root(path):
    _links(Path(path).absolute())
    return L.validate_output_root(path)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def _save(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def _read(path):
    _links(path)
    return json.loads(Path(path).read_text(encoding='utf-8'))


def _token(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', value):
        raise ValueError('Unsafe workspace name: ' + str(value))
    return value


def plan_workspace(cfg, round_name, checks):
    plan = {'root': str(cfg.get('eqy_work_root', '')), 'workspace': '', 'version': VERSION,
            'path_limit': cfg.get('eqy_path_limit', LIMIT), 'case_map': {}, 'selfcheck_map': {},
            'blocked': [], 'partition_paths_status': 'PENDING_SETUP'}
    try:
        if not cfg.get('eqy_work_root'): raise ValueError('Missing eqy_work_root')
        root = safe_root(cfg['eqy_work_root'])
        if root == Path(root.anchor): raise ValueError('Workspace root cannot be a drive root')
        token = _token(round_name)
        if cfg.get('eqy_workspace_naming') == 'round-sha256-16-v1':
            token = 'q' + hashlib.sha256(token.encode('ascii')).hexdigest()[:16]
        elif cfg.get('eqy_workspace_naming') not in (None, 'full-round-v1'):
            raise ValueError('Unknown EQY workspace naming')
        workspace = root / token / 'a01'
        safe_root(workspace)
        plan.update(root=str(root), workspace=str(workspace))
        if cfg.get('eqy_workspace_version', VERSION) != VERSION: raise ValueError('Unsupported workspace version')
        if plan['path_limit'] != LIMIT: raise ValueError('EQY path limit must be 200')
        for key, items, field, prefix in [('case_map', cfg['official_cases'], 'id', 'c'), ('selfcheck_map', checks, 'name', 's')]:
            for n, item in enumerate(items, 1):
                name = item[field]
                if not isinstance(name, str) or not name or name in plan[key]: raise ValueError('Duplicate or invalid workspace key')
                plan[key][name] = prefix + format(n, '02d')
        if workspace.exists(): raise FileExistsError('Workspace already exists: ' + str(workspace))
        # Only deterministic input/job paths are known before EQY setup.
        budgets = [workspace/'workspace_manifest.json', workspace/'chains/inputs/inputs_manifest.json']
        budgets += [workspace/'chains'/code/side/'merged/partition_noDF.log' for code in plan['case_map'].values() for side in ('b','o')]
        budgets += [workspace/'sc'/code/'merged/partition_noDF.log' for code in plan['selfcheck_map'].values()]
        check_paths(budgets, limit=plan['path_limit'])
    except (ValueError, OSError, KeyError, TypeError) as exc:
        plan['blocked'].append(str(exc))
    return plan


def create_workspace(cfg, round_root, checks):
    round_root = safe_root(round_root)
    plan = plan_workspace(cfg, round_root.name, checks)
    if plan['blocked']:
        if Path(plan['workspace']).exists() and plan['workspace']: raise FileExistsError(plan['workspace'])
        raise ValueError('; '.join(plan['blocked']))
    identity = {k:v for k,v in plan.items() if k != 'blocked'}
    identity.update(round=str(round_root), target_commit=cfg.get('target_commit'), source_sha256=cfg.get('source_sha256'), tools=cfg.get('tools', {}))
    workspace = Path(identity['workspace']);workspace.mkdir(parents=True, exist_ok=False)
    _save(workspace/'workspace_manifest.json', identity)
    return identity


def _identity(ctx):
    identity = ctx['eqy_workspace']
    workspace = safe_root(identity['workspace'])
    frozen = _read(workspace/'workspace_manifest.json')
    for key in ('workspace','root','round'):
        if path_identity(identity[key]) != path_identity(frozen[key]): raise ValueError('Workspace path identity differs: '+key)
    for key in ('version','path_limit','case_map','selfcheck_map','target_commit','source_sha256','tools'):
        if identity.get(key) != frozen.get(key): raise ValueError('Workspace identity differs: '+key)
    for key in ('target_commit','source_sha256','tools'):
        if key in ctx and ctx[key] != frozen.get(key): raise ValueError('Frozen context differs: '+key)
    return workspace, frozen


def job_dir(ctx, stage, case=None, side=None, check=None):
    workspace, identity = _identity(ctx)
    try:
        if stage == 'chains' and side in ('baseline','optimized'):
            result = workspace/'chains'/identity['case_map'][case]/('b' if side=='baseline' else 'o')
        elif stage == 'sc': result = workspace/'sc'/identity['selfcheck_map'][check]
        else: raise ValueError('Unknown workspace stage or side')
    except KeyError as exc: raise ValueError('Unknown workspace case/check') from exc
    _links(result);check_paths([result],limit=identity['path_limit'])
    return result


def stage_input(ctx, stage, source, name=None):
    workspace, identity = _identity(ctx)
    if stage not in ('sc','chains'): raise ValueError('Unknown input stage')
    source = Path(source).absolute();_links(source)
    if not source.is_file(): raise ValueError('Missing source input')
    name = name or source.name
    if Path(name).name != name or not re.fullmatch(r'[A-Za-z0-9._-]+',name) or name in ('.','..'): raise ValueError('Unsafe input name')
    folder = workspace/stage/'inputs'; destination = folder/name
    _links(destination);check_paths([destination],limit=identity['path_limit'])
    manifest = workspace/stage/'inputs_manifest.json'
    rows = _read(manifest) if manifest.exists() else {}
    row = {'source':str(source), 'execution':str(destination), 'sha256':sha(source), 'size':source.stat().st_size}
    if name in rows:
        prior = rows[name]
        if path_identity(prior['source']) != path_identity(source) or any(prior[k] != row[k] for k in ('sha256','size')):
            raise ValueError('Input source/hash binding conflict')
        if not destination.is_file() or sha(destination)!=row['sha256'] or destination.stat().st_size!=row['size']: raise ValueError('Staged input changed')
        return destination
    if destination.exists(): raise ValueError('Unregistered staged input exists')
    folder.mkdir(parents=True,exist_ok=True)
    with source.open('rb') as src, destination.open('xb') as dst: shutil.copyfileobj(src,dst)
    if sha(destination)!=row['sha256'] or sha(source)!=row['sha256'] or destination.stat().st_size!=row['size']: raise ValueError('Input copy changed')
    rows[name]=row;_save(manifest,rows)
    return destination


def check_paths(paths, cwd=None, limit=LIMIT):
    rows=[]
    for path in paths:
        original=str(path);p=Path(path)
        if cwd is not None and not p.is_absolute(): p=Path(cwd)/p
        _links(p.absolute()); absolute=p.resolve()
        raw=str(cwd)+'/'+original if cwd is not None and not Path(path).is_absolute() else original
        if max(len(raw),len(str(absolute)))>limit: raise ValueError('EQY path budget exceeded: '+raw)
        rows.append({'cwd':str(cwd) if cwd is not None else None,'relative':original,'raw_length':len(raw),'absolute':str(absolute),'absolute_length':len(str(absolute))})
    return rows


def check_work(work, expected=None, limit=LIMIT):
    work=safe_root(work)
    dirs=sorted(p for p in (work/'strategies').glob('*/*') if p.is_dir())
    partitions=sorted(set(p.parent.name for p in dirs))
    if not partitions or (expected is not None and (len(expected)!=len(set(expected)) or set(partitions)!=set(expected))): raise ValueError('Generated partition set differs from frozen source')
    for p in work.rglob('*'): _links(p);check_paths([p],limit=limit)
    actual_sv={p.stem for p in (work/'partitions').glob('*.sv')}
    actual_il={p.stem for p in (work/'partitions').glob('*.il')}
    if actual_sv!=set(partitions) or actual_il!=set(partitions): raise ValueError('Partition strategy/files coverage differs')
    refs=[]
    for d in dirs:
        script=d/'run.ys'
        if not script.is_file(): raise ValueError('Missing strategy run.ys')
        local=[]
        for rel in re.findall(r'(?:^|\s|[\"\'])([^\s\"\']+\.(?:sv|il))(?=$|\s|[\"\'])',script.read_text(encoding='utf-8'), re.M):
            target=(d/rel).resolve()
            try: target.relative_to(work)
            except ValueError as exc: raise ValueError('Partition reference escapes work') from exc
            if not target.is_file(): raise ValueError('Missing partition input: '+rel)
            row=check_paths([rel],cwd=d,limit=limit)[0];row['sha256']=sha(target);local.append(row)
        if not local: raise ValueError('No partition input references')
        refs.extend(local)
    return {'partitions':partitions,'references':refs,'max_raw_length':max(r['raw_length'] for r in refs)}


def inventory(root):
    root=Path(root);_links(root)
    out={}
    for p in sorted(root.rglob('*')):
        _links(p)
        if p.is_file(): out[p.relative_to(root).as_posix()]={'sha256':sha(p),'size':p.stat().st_size}
    return out


def archive_tree(source,destination):
    source,destination=Path(source),Path(destination);_links(source);_links(destination)
    before=inventory(source)
    shutil.copytree(source,destination)
    if before!=inventory(destination) or before!=inventory(source): raise ValueError('Archive byte verification failed')
    return [{'execution_path':str(source/rel),'archive_path':str(destination/rel),**item} for rel,item in before.items()]


def archive(ctx,round_root):
    round_root=Path(round_root);destination=round_root/'10_selfcheck/eqy_archive'
    status={'ok':False,'status':'ARCHIVE_ERROR','workspace':str(ctx['eqy_workspace']['workspace']),
            'archive_root':'10_selfcheck/eqy_archive','manifest_path':'10_selfcheck/eqy_archive_manifest.json','files':[]}
    try:
        workspace,identity=_identity(ctx)
        if path_identity(identity['round'])!=path_identity(round_root.resolve()): raise ValueError('Archive round identity differs')
        _links(round_root)
        manifest=round_root/status['manifest_path']
        if manifest.exists() or (round_root/'01_meta/eqy_archive.json').exists(): raise FileExistsError('Archive metadata exists')
        destination.parent.mkdir(parents=True,exist_ok=True)
        rows=archive_tree(workspace,destination)
        for row in rows: row['archive_path']=Path(row['archive_path']).relative_to(round_root).as_posix()
        directories=sorted(p.relative_to(destination).as_posix() for p in destination.rglob('*') if p.is_dir())
        _save(manifest,{'workspace':str(workspace),'archive_root':status['archive_root'],'files':rows,'directories':directories})
        status.update(ok=True,status='ARCHIVED',files=rows)
    except Exception as exc: status['error']=str(exc)
    meta=round_root/'01_meta/eqy_archive.json'
    try:
        meta.parent.mkdir(parents=True,exist_ok=True)
        if not meta.exists():
            with meta.open('x',encoding='utf-8') as f: json.dump(status,f,ensure_ascii=False,indent=2);f.write('\n')
    except Exception as exc: status.update(ok=False,status='ARCHIVE_ERROR',error=str(exc))
    return status


def _archive_manifest(round_root):
    root=Path(round_root).resolve(); _links(root)
    data=_read(root/'10_selfcheck/eqy_archive_manifest.json')
    base=root/data['archive_root'];base.resolve().relative_to(root);_links(base)
    if not base.is_dir(): raise ValueError('Archive directory missing')
    if base.resolve()!=root/'10_selfcheck/eqy_archive': raise ValueError('Unexpected archive root')
    return root,base,data


def verify_archive(round_root):
    try:
        root,base,data=_archive_manifest(round_root)
        expected={}
        for row in data['files']:
            path=root/row['archive_path'];path.resolve().relative_to(base)
            rel=path.relative_to(base).as_posix()
            if rel in expected: raise ValueError('Duplicate archive file')
            if path_identity(row['execution_path'])!=path_identity(Path(data['workspace'])/rel): raise ValueError('Invalid execution mapping')
            expected[rel]={k:row[k] for k in ('sha256','size')}
        if inventory(base)!=expected: raise ValueError('Archive file set or bytes differ')
        directories=sorted(p.relative_to(base).as_posix() for p in base.rglob('*') if p.is_dir())
        if directories!=data['directories']: raise ValueError('Archive directory set differs')
        return {'ok':True,'status':'VERIFIED','files':len(expected)}
    except Exception as exc: return {'ok':False,'status':'ARCHIVE_ERROR','error':str(exc)}


def resolve_evidence(round_root,execution_path):
    result=verify_archive(round_root)
    if not result['ok']: raise ValueError(result['error'])
    root,base,data=_archive_manifest(round_root)
    matches=[r for r in data['files'] if path_identity(r['execution_path'])==path_identity(execution_path)]
    if len(matches)!=1: raise ValueError('Unregistered execution evidence')
    return root/matches[0]['archive_path']
