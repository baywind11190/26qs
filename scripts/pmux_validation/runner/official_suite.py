"""Validated, ordered official inputs shared by every validation stage."""
import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import re


def contained(root, relative):
    if not isinstance(relative, str) or '\\' in relative or ':' in relative:
        raise ValueError('invalid suite relative path: ' + str(relative))
    rel = PurePosixPath(relative)
    if rel.is_absolute() or '..' in rel.parts or not rel.parts:
        raise ValueError('suite path escapes root: ' + relative)
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError('suite path escapes root: ' + relative)
    return path


def validate_cases(records):
    if not isinstance(records, list) or not records:
        raise ValueError('official_cases missing or empty')
    ids, paths, originals = set(), set(), set()
    for item in records:
        if not isinstance(item, dict):
            raise ValueError('invalid official case record')
        for key in ('id', 'top'):
            if not isinstance(item.get(key), str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', item[key]):
                raise ValueError('invalid case ' + key)
        for key in ('file', 'canonical_file'):
            contained(Path.cwd(), item.get(key))
        for key, seen in (('id', ids), ('file', paths), ('canonical_file', originals)):
            value = item[key] if key == 'id' else str(contained(Path.cwd(), item[key])).casefold()
            if value in seen:
                raise ValueError('duplicate official case ' + key)
            seen.add(value)
        if not item['file'].startswith('tree/'):
            raise ValueError('case file must be under tree/')
        for key in ('sha256', 'canonical_sha256'):
            if not re.fullmatch(r'[0-9a-f]{64}', str(item.get(key, ''))):
                raise ValueError('invalid case ' + key)
        if not isinstance(item.get('default_parameters'), dict):
            raise ValueError('default_parameters provenance missing')
    return copy.deepcopy(records)


def context_cases(context):
    records = validate_cases(context.get('official_cases'))
    expected = context.get('official_cases_sha256')
    if expected is not None and expected != cases_sha256(records):
        raise ValueError('frozen official_cases hash mismatch')
    return records


def case_ids(context):
    return tuple(c['id'] for c in context_cases(context))


def cases_sha256(records):
    validated = validate_cases(records)
    return hashlib.sha256(json.dumps(validated, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')).hexdigest()


def normalized_sha(path):
    return hashlib.sha256(Path(path).read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def load_suite(manifest_path, repo):
    path = Path(manifest_path)
    data = json.loads(path.read_text(encoding='utf-8-sig'))
    records = validate_cases(data.get('cases'))
    files = data.get('files')
    if not isinstance(files, list):
        raise ValueError('suite files missing')
    registered = {}
    resolved_files = set()
    for item in files:
        relative = item.get('file')
        target = contained(path.parent, relative)
        resolved = str(target).casefold()
        if resolved in resolved_files or relative in registered or not target.is_file() or normalized_sha(target) != item.get('sha256'):
            raise ValueError('invalid frozen suite file: ' + str(relative))
        registered[relative] = item
        resolved_files.add(resolved)
    for item in records:
        execution = contained(path.parent, item['file'])
        original = contained(repo, item['canonical_file'])
        if item['file'] not in registered or registered[item['file']]['sha256'] != item['sha256']:
            raise ValueError('case not bound to files manifest: ' + item['id'])
        if not original.is_file() or hashlib.sha256(original.read_bytes()).hexdigest() != item['canonical_sha256']:
            raise ValueError('canonical raw hash mismatch: ' + item['id'])
        if not execution.is_file() or normalized_sha(execution) != item['sha256'] or normalized_sha(original) != item['sha256']:
            raise ValueError('case execution hash mismatch: ' + item['id'])
        text = execution.read_text(encoding='utf-8-sig')
        text = re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)
        if not re.search(r'\bmodule\s+' + re.escape(item['top']) + r'\b', text):
            raise ValueError('case top missing: ' + item['top'])
    return records


def case_path(tree, case):
    return contained(tree, case['file'][len('tree/'):])
