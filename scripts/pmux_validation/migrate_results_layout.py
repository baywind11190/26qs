"""One-time, content-preserving ASCII results migration and historical locator.

plan records every original file/directory; apply resumes by verified location;
verify/resolve never write. Historical file contents and ZIP payloads are immutable.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import ntpath
import os
from pathlib import Path
import re
import subprocess

MIGRATION_ID = '20261025_ascii_layout'
MANAGEMENT = 'results/_migrations/' + MIGRATION_ID
DEFAULT_MANIFEST = MANAGEMENT + '/manifest.json'

ROUND_NAMES = {
    '2026-10-22_2136_同次综合墙钟与峰值内存_17f9361_第01轮': '2026-10-22_2136_same_run_pre_v8_17f9361_r01',
    '2026-10-23_0117_Windows同次墙钟与峰值内存_v8_17f9361_第01轮': '2026-10-23_0117_v8_same_run_17f9361_r01',
    '2026-10-23_0121_V8同次八次_计量兼容修复后_17f9361_第01轮': '2026-10-23_0121_v8_measurement_fix_17f9361_r01',
    '2026-10-23_1038_Windows同次墙钟与峰值内存_v8_17f9361_第01轮': '2026-10-23_1038_v8_same_run_17f9361_r01',
    '2026-10-23_1232_Windows同次墙钟与峰值内存_v8_17f9361_第01轮': '2026-10-23_1232_v8_same_run_17f9361_r01',
    '2026-10-23_无调试墙钟与JobCPU诊断_17f9361_test2-test3_第01轮': '2026-10-23_diag_wall_jobcpu_test2-test3_17f9361_r01',
    '2026-10-23_无调试墙钟与JobCPU诊断_17f9361_test2-test3_第02轮': '2026-10-23_diag_wall_jobcpu_test2-test3_17f9361_r02',
    '2026-10-23_正常启动无调试墙钟诊断_17f9361_test2-test3_第03轮': '2026-10-23_diag_normal_wall_test2-test3_17f9361_r03',
    '2026-10-23_test2正常启动阶段墙钟诊断_17f9361_第04轮': '2026-10-23_diag_test2_phase_wall_17f9361_r04',
    '2026-10-23_test2正常启动阶段墙钟诊断_17f9361_第05轮': '2026-10-23_diag_test2_phase_wall_17f9361_r05',
}
SEGMENTS = {
    '官方口径评测': 'official_eval',
    '01_来源与环境_meta': '01_meta',
    '02_冻结源码与输入_assets': '02_assets',
    '03_脚本与插件_runner': '03_runner',
    '04_流程一致性_flowcheck': '04_flowcheck',
    '04_计量自检': '04_measurement_selfcheck',
    '05_公开四例_public': '05_public',
    '08_test2阶段时间诊断_phase-timing': '08_phase_timing',
    '08_无调试时间诊断_time-only': '08_time_only',
    '08_正常启动时间诊断_normal-launch': '08_normal_launch',
    '08_正式单次_official-single': '08_official_single',
    '09_时间内存开销_performance': '09_performance',
    '09_稳定性诊断_stability-diagnostics': '09_stability_diagnostics',
    '10_功能等价性_formal': '10_formal',
    '10_测量方法自检_selfcheck': '10_measurement_selfcheck',
    '10_验证工具自检_selfcheck': '10_selfcheck',
    '11_汇总与证据_summary': '11_summary',
    '工具链与构建证据': 'toolchain_evidence',
    'V8快照补档与最终核对.json': 'v8_snapshot_audit.json',
    '_共享自检缓存_v8-same-run': '_history',
    '00_本轮完整验收报告.md': '00_report.md',
    '00_本轮验证结论.md': '00_report.md',
    '00_正常启动墙钟诊断报告.md': '00_report.md',
    '00_test2阶段墙钟诊断报告.md': '00_report.md',
    '00_诊断报告.md': '00_report.md',
}
BRIDGES = {
    '_eval_ascii_4a697140d2c34ed1850133fe0cf3f409': 'official_eval/2026-10-23_0117_v8_same_run_17f9361_r01/legacy_workspace',
    '_eval_ascii_21b5e6673cde4bc0953bc058cc2b8436': 'official_eval/2026-10-23_0121_v8_measurement_fix_17f9361_r01/legacy_workspace',
    '_eval_ascii_73d7a4a350ac49ecaf5b5bf207332b60': 'official_eval/2026-10-23_1038_v8_same_run_17f9361_r01/legacy_workspace',
    '_eval_ascii_094ada9a41454b0ba3f987f84e615345': 'official_eval/2026-10-23_1232_v8_same_run_17f9361_r01/legacy_workspace',
    '_eval_ascii_ad2d9c12a5fb4d76b6f29d3f682309e4': 'official_eval/_shared_evidence/2026-10-22_1823_v7_17f9361',
    '_eval_formal_17f9361_20261022': 'official_eval/2026-10-22_2136_same_run_pre_v8_17f9361_r01/legacy_formal_workspace',
}
EMPTY_ROOTS = {
    '_eval_ascii_0200a46df60a407caa4ca8f9cbe5f629',
    '_eval_ascii_9f8aac09f39e4fcda8b1524a6aa157e8',
}


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def _lexical(repo, relative):
    """Construct a contained path without repeated filesystem calls."""
    relative = str(relative).replace('\\', '/')
    if (not relative.casefold().startswith('results/') or '..' in relative.split('/')
            or ':' in relative or ntpath.isabs(relative)):
        raise ValueError('Path outside results: ' + relative)
    return Path(repo) / relative


def _safe(repo, relative):
    """Recheck resolved boundaries immediately before accessing/moving a path."""
    p = _lexical(repo, relative)
    p.resolve().relative_to(Path(repo) / 'results')
    return p


def _check_links(repo, paths):
    """Check each unique ancestor once per operation, never cache across calls."""
    checked = set()
    for p in paths:
        for ancestor in [p, *p.parents]:
            if ancestor == Path(repo):
                break
            key = str(ancestor).casefold()
            if key in checked:
                break
            checked.add(key)
            if ancestor.is_symlink() or ancestor.is_junction():
                raise ValueError('Directory links are not migration targets: ' + str(ancestor))


def map_relative(old):
    parts = old.replace('\\', '/').split('/')
    if parts[0] != 'results' or len(parts) < 2:
        raise ValueError('Expected results-relative path')
    if parts[1] in EMPTY_ROOTS:
        if len(parts) != 2:
            raise ValueError('Expected empty legacy root contains data: ' + old)
        return None
    if old == 'results/00_目录导航.md':
        return MANAGEMENT + '/navigation_before.md'
    if parts[1] in BRIDGES:
        parts = ['results', *BRIDGES[parts[1]].split('/'), *parts[2:]]
    mapped = []
    for part in parts:
        if part in ROUND_NAMES:
            part = ROUND_NAMES[part]
        elif part.endswith('.zip') and part[:-4] in ROUND_NAMES:
            part = ROUND_NAMES[part[:-4]] + '.zip'
        else:
            part = SEGMENTS.get(part, part)
        if not part.isascii():
            raise ValueError('Unmapped non-ASCII name: ' + part)
        mapped.append(part)
    new = '/'.join(mapped)
    if new == 'results/official_eval/_history/selfcheck_cache.json':
        new = 'results/official_eval/_history/selfcheck_cache_v8.json'
    return new


def build_manifest(repo, *, tracked=None):
    repo = Path(repo).resolve()
    results = repo / 'results'
    if tracked is None:
        raw = subprocess.check_output(['git', '-C', str(repo), 'ls-files', '-z', '--', 'results'])
        tracked = {p.decode('utf-8') for p in raw.split(b'\0') if p}
    files, directories = [], []
    for parent, dirs, names in os.walk(results, followlinks=False):
        dirs.sort()
        for name in dirs:
            p = Path(parent) / name
            old = p.relative_to(repo).as_posix()
            _lexical(repo, old)
            if p.is_symlink() or p.is_junction():
                raise ValueError('Directory links are not migration targets: ' + old)
            new = map_relative(old)
            if new is None and any(p.iterdir()):
                raise ValueError('Legacy empty root is no longer empty: ' + old)
            directories.append({'old_path': old, 'new_path': new})
        for name in sorted(names):
            p = Path(parent) / name
            old = p.relative_to(repo).as_posix()
            _lexical(repo, old)
            if p.is_symlink() or p.is_junction():
                raise ValueError('Links are not migration targets: ' + old)
            files.append({'old_path': old, 'new_path': map_relative(old),
                          'size': p.stat().st_size, 'sha256': digest(p),
                          'git_tracked': old in tracked})
    manifest = {'schema_version': 1, 'migration_id': MIGRATION_ID,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'repo_root': str(repo), 'files': files, 'directories': directories}
    _validate(manifest)
    for row in files:
        if row['old_path'] != row['new_path'] and _safe(repo, row['new_path']).exists():
            raise FileExistsError('Migration destination already exists: ' + row['new_path'])
    return manifest


def _validate(manifest):
    if manifest.get('schema_version') != 1 or manifest.get('migration_id') != MIGRATION_ID:
        raise ValueError('Unsupported migration manifest')
    repo = Path(manifest['repo_root']).resolve()
    file_targets, directory_targets, paths = set(), set(), []
    for kind in ('files', 'directories'):
        old_keys = set()
        for row in manifest[kind]:
            old, new = row['old_path'], row['new_path']
            paths.append(_lexical(repo, old))
            if old.casefold() in old_keys:
                raise ValueError('Duplicate source path: ' + old)
            old_keys.add(old.casefold())
            if new is None:
                if kind != 'directories' or old.split('/')[-1] not in EMPTY_ROOTS:
                    raise ValueError('Only approved empty roots may disappear')
                continue
            paths.append(_lexical(repo, new))
            if not new.isascii():
                raise ValueError('Destination must be ASCII: ' + new)
            targets = file_targets if kind == 'files' else directory_targets
            if new.casefold() in targets:
                raise ValueError('Colliding destination: ' + new)
            targets.add(new.casefold())
    if file_targets & directory_targets:
        raise ValueError('File/directory target collision')
    for target in file_targets | directory_targets:
        if any(parent in file_targets for parent in _parent_keys(target)):
            raise ValueError('File used as destination parent: ' + target)
    _check_links(repo, paths)


def _parent_keys(relative):
    parts = relative.split('/')
    return ['/'.join(parts[:i]) for i in range(2, len(parts))]


def _check_file(path, row):
    if not path.is_file() or path.stat().st_size != row['size'] or digest(path) != row['sha256']:
        raise ValueError('Evidence missing or changed: ' + str(path))


def apply_manifest(manifest, *, on_progress=None, journal=None):
    """No-overwrite same-volume file renames; a verified interrupted apply resumes."""
    _validate(manifest)
    repo = Path(manifest['repo_root'])
    # Check EVERY source/destination before the first move. A conflict cannot yield
    # a half-migration merely because the conflicting record sorted late.
    for row in manifest['files']:
        src, dst = _safe(repo, row['old_path']), _safe(repo, row['new_path'])
        if src == dst:
            _check_file(src, row)
        elif src.exists() and dst.exists():
            raise FileExistsError('Both source and destination exist: ' + row['old_path'])
        else:
            _check_file(src if src.exists() else dst, row)
    for row in manifest['directories']:
        if row['new_path'] is None:
            src = _safe(repo, row['old_path'])
            if src.exists() and any(src.iterdir()):
                raise ValueError('Expected empty root contains data: ' + row['old_path'])
        else:
            dst = _safe(repo, row['new_path'])
            if dst.exists() and not dst.is_dir():
                raise FileExistsError(str(dst))
    for row in manifest['directories']:
        if row['new_path'] is not None:
            _safe(repo, row['new_path']).mkdir(parents=True, exist_ok=True)
    for index, row in enumerate(manifest['files']):
        src, dst = _safe(repo, row['old_path']), _safe(repo, row['new_path'])
        if src != dst and src.exists():
            _check_file(src, row)
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists():
                raise FileExistsError(str(dst))
            src.rename(dst)
            if journal:
                journal.write(json.dumps({'state': 'MOVED', 'index': index}) + '\n')
                journal.flush()
            if on_progress:
                on_progress(index, row)
    # rmdir only removes empty directories. Never recursively remove evidence.
    wanted = {row['new_path'].casefold() for row in manifest['directories'] if row['new_path']}
    for row in sorted(manifest['directories'], key=lambda r: r['old_path'].count('/'), reverse=True):
        if row['old_path'].casefold() not in wanted:
            src = _safe(repo, row['old_path'])
            if src.exists():
                src.rmdir()


def verify_manifest(manifest):
    _validate(manifest)
    repo = Path(manifest['repo_root'])
    errors, missing = [], 0
    for row in manifest['files']:
        dst = _safe(repo, row['new_path'])
        if not dst.is_file():
            missing += 1
            errors.append({'path': row['new_path'], 'reason': 'missing'})
        elif dst.stat().st_size != row['size'] or digest(dst) != row['sha256']:
            errors.append({'path': row['new_path'], 'reason': 'content'})
        elif row['old_path'] != row['new_path'] and _safe(repo, row['old_path']).exists():
            errors.append({'path': row['old_path'], 'reason': 'source_still_present'})
    for row in manifest['directories']:
        if row['new_path'] and not _safe(repo, row['new_path']).is_dir():
            errors.append({'path': row['new_path'], 'reason': 'directory_missing'})
        if row['new_path'] is None and _safe(repo, row['old_path']).exists():
            errors.append({'path': row['old_path'], 'reason': 'empty_root_still_present'})
    return {'ok': not errors, 'files': len(manifest['files']),
            'bytes': sum(r['size'] for r in manifest['files']),
            'directories': len(manifest['directories']), 'missing_files': missing,
            'errors': errors}


def resolve_path(manifest, value, *, base=None):
    """Locate historical Windows absolute or repo/round-relative references."""
    repo = Path(manifest['repo_root'])
    repo_key = ntpath.normpath(str(repo)).replace('\\', '/')
    value = str(value).replace('\\', '/')
    if ntpath.isabs(value):
        absolute = ntpath.normpath(value).replace('\\', '/')
    else:
        origin = repo_key
        if base is not None and not value.casefold().startswith('results/'):
            base_value = str(base).replace('\\', '/')
            origin = base_value if ntpath.isabs(base_value) else repo_key + '/' + base_value
        absolute = ntpath.normpath(origin + '/' + value).replace('\\', '/')
    prefix = repo_key.rstrip('/') + '/'
    if not absolute.casefold().startswith(prefix.casefold()):
        raise ValueError('Historical reference escapes repository')
    old = absolute[len(prefix):]
    _safe(repo, old)
    rows = manifest['files'] + manifest['directories']
    for row in rows:
        if old.casefold() == row['old_path'].casefold():
            if row['new_path'] is None:
                raise ValueError('Historical empty root was removed')
            return _safe(repo, row['new_path'])
    # Prefix resolution also works for old bridge roots and nested references.
    for row in sorted(manifest['directories'], key=lambda r: len(r['old_path']), reverse=True):
        if row['new_path'] and old.casefold().startswith(row['old_path'].casefold() + '/'):
            return _safe(repo, row['new_path'] + old[len(row['old_path']):])
    raise KeyError('Path is not in the historical migration inventory: ' + value)


def rollback_manifest(manifest):
    """Reverse evidence moves without deleting any newly generated files."""
    _validate(manifest)
    repo = Path(manifest['repo_root'])
    for row in manifest['files']:
        src, dst = _safe(repo, row['new_path']), _safe(repo, row['old_path'])
        if src != dst and src.exists() and dst.exists():
            raise FileExistsError(str(dst))
        _check_file(src if src.exists() else dst, row)
    for row in manifest['directories']:
        _safe(repo, row['old_path']).mkdir(parents=True, exist_ok=True)
    for row in reversed(manifest['files']):
        src, dst = _safe(repo, row['new_path']), _safe(repo, row['old_path'])
        if src != dst and src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            src.rename(dst)
    old_dirs = {r['old_path'].casefold() for r in manifest['directories']}
    for row in sorted(manifest['directories'], key=lambda r: (r['new_path'] or '').count('/'), reverse=True):
        if row['new_path'] and row['new_path'].casefold() not in old_dirs:
            p = _safe(repo, row['new_path'])
            if p.is_dir() and not any(p.iterdir()):
                p.rmdir()


def verify_legacy_hashes(manifest):
    """Read old ALL_SHA256 lists through the map; expose pre-existing anomalies.

    The same report is produced before/after migration. A mismatch is reported,
    never repaired by overwriting an original list or historical evidence.
    """
    repo = Path(manifest['repo_root'])
    repo_key = ntpath.normpath(str(repo)).replace('\\', '/').rstrip('/')
    lookup = {r['old_path'].casefold(): r for r in manifest['files']}
    cache, issues = {}, []
    matched, checked, lists = 0, 0, 0

    def current_file(row):
        new, old = _safe(repo, row['new_path']), _safe(repo, row['old_path'])
        return new if new.is_file() else old

    for index in manifest['files']:
        if index['old_path'].split('/')[-1] != 'ALL_SHA256.txt':
            continue
        lists += 1
        parts = index['old_path'].split('/')
        position = next((i for i, p in enumerate(parts) if p in ROUND_NAMES), None)
        base = '/'.join(parts[:position + 1]) if position is not None else '/'.join(parts[:-1])
        for line_no, line in enumerate(current_file(index).read_text(encoding='utf-8-sig').splitlines(), 1):
            if not line.strip():
                continue
            found = re.fullmatch(r'([0-9a-fA-F]{64})\s+\*?(.+)', line)
            if not found:
                issues.append({'index': index['old_path'], 'line': line_no, 'reason': 'unparsed'})
                continue
            expected, reference = found.groups()
            reference = reference.replace('\\', '/')
            if ntpath.isabs(reference):
                absolute = ntpath.normpath(reference).replace('\\', '/')
            else:
                absolute = ntpath.normpath(repo_key + '/' + base + '/' + reference).replace('\\', '/')
            prefix = repo_key + '/'
            key = absolute[len(prefix):].casefold() if absolute.casefold().startswith(prefix.casefold()) else None
            record = lookup.get(key)
            checked += 1
            if record is None:
                issues.append({'index': index['old_path'], 'line': line_no,
                               'reference': reference, 'reason': 'not_in_inventory'})
                continue
            if key not in cache:
                file = current_file(record)
                cache[key] = digest(file) if file.is_file() else None
            actual = cache[key]
            if actual == expected.lower():
                matched += 1
            else:
                issues.append({'index': index['old_path'], 'line': line_no, 'reference': reference,
                               'reason': 'hash_mismatch', 'expected': expected.lower(), 'actual': actual})
    return {'lists': lists, 'checked': checked, 'matched': matched, 'issues': issues}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action', choices=['plan', 'apply', 'verify', 'verify-legacy', 'resolve', 'rollback'])
    ap.add_argument('--repo', default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument('--manifest')
    ap.add_argument('--path')
    ap.add_argument('--base', help='Old directory used as base for a relative reference')
    args = ap.parse_args(argv)
    file = Path(args.manifest) if args.manifest else Path(args.repo) / DEFAULT_MANIFEST
    if args.action == 'plan':
        manifest = build_manifest(args.repo)
        file.parent.mkdir(parents=True, exist_ok=True)
        with file.open('x', encoding='utf-8') as out:
            json.dump(manifest, out, ensure_ascii=False, indent=2)
            out.write('\n')
        print(json.dumps({'manifest': str(file), 'files': len(manifest['files']),
                          'directories': len(manifest['directories'])}, ensure_ascii=False))
        return 0
    manifest = json.loads(file.read_text(encoding='utf-8'))
    if Path(args.repo).resolve() != Path(manifest['repo_root']).resolve():
        raise ValueError('Manifest repository does not match --repo')
    if args.action == 'apply':
        with file.with_name('operations.jsonl').open('a', encoding='utf-8') as journal:
            apply_manifest(manifest, journal=journal)
    elif args.action == 'rollback':
        rollback_manifest(manifest)
        print('Evidence paths restored; active code/docs are not reverted.')
        return 0
    elif args.action == 'resolve':
        if not args.path:
            ap.error('--path is required')
        print(resolve_path(manifest, args.path, base=args.base))
        return 0
    elif args.action == 'verify-legacy':
        result = verify_legacy_hashes(manifest)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if not result['issues'] else 2
    result = verify_manifest(manifest)
    print(json.dumps({**result, 'errors': result['errors'][:20]}, ensure_ascii=False))
    return 0 if result['ok'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
