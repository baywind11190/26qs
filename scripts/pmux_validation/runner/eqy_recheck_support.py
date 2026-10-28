"""Managed, proof-only short workspaces; never synthesizes or mutates a source round."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import result_layout as L
import eqy_workspace as W

TARGET_CASES = ('pmux_case01_balanced', 'pmux_case02_pipeline', 'pmux_case04_feedback')
CHAINS = ('c4a_rtl_opt_mapped', 'c4b_rtl_base_mapped')
CASE_CODES = dict(zip(TARGET_CASES, ('c01', 'c02', 'c04')))
LIMIT = 200


def sha(path):
    return W.sha(path)


def save(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def safe_root(path):
    return W.safe_root(path)


def job_dir(root, case, side):
    if case not in CASE_CODES or side not in ('baseline', 'optimized'):
        raise ValueError('Unknown recheck case or side')
    return Path(root) / CASE_CODES[case] / ('b' if side == 'baseline' else 'o')


def select_cases(cases, requested):
    if not requested or len(set(requested)) != len(requested):
        raise ValueError('Cases must be explicit and unique')
    known = {c['id'] for c in cases}
    if not set(requested) <= known or not set(requested) <= set(TARGET_CASES):
        raise ValueError('Unsupported or missing recheck case')
    return [c for c in cases if c['id'] in requested]


def create_workspace(path, identity):
    path = safe_root(path)
    path.mkdir(parents=True, exist_ok=False)
    save(path / 'workspace_manifest.json', identity)
    return path


def check_work(work, expected, limit=LIMIT):
    return W.check_work(work, expected, limit)


def complete(rows, cases):
    expected = {(c, chain) for c in cases for chain in CHAINS}
    actual = [(r['case'], r['chain']) for r in rows]
    return (len(actual) == len(expected) and set(actual) == expected and all(
        r.get('state') == 'PASS' and r.get('verified') and r.get('probes_noDF_all_sat')
        and r.get('partitions_total', 0) > 0 and r['partitions_total'] == r['partitions_pass'] for r in rows))


def inventory(root):
    return W.inventory(root)


def archive_tree(source, destination):
    return W.archive_tree(source, destination)


def audit_source(source):
    """Audit original checksums without normalizing bytes or writing to the source."""
    source = safe_root(source)
    actual = inventory(source)
    index = {}
    for line in (source / '11_summary/ALL_SHA256.txt').read_text(encoding='utf-8').splitlines():
        h, rel = line.split('  ', 1)
        if rel in index or not re.fullmatch('[a-fA-F0-9]{64}', h):
            raise ValueError('Invalid original checksum manifest')
        p = Path(rel)
        if p.is_absolute() or '..' in p.parts:
            raise ValueError('Unsafe original checksum entry')
        index[rel] = h
    bad = [rel for rel, h in index.items() if actual.get(rel, {}).get('sha256') != h]
    if bad:
        raise ValueError('Original round checksums differ: ' + repr(bad[:8]))
    return {'manifest_entries': len(index), 'files': actual}


def proof_gate(parts):
    """Keep solver premises separate from process/tool failure."""
    if not parts:
        return 'INCOMPLETE'
    proof_states = [r['proof']['state'] for r in parts.values()]
    probes = [r['probes']['noDF'] for r in parts.values()]
    states = proof_states + [p.get('state', 'VALID') for p in probes]
    for failure in ('TOOL_OR_CONFIG_ERROR', 'TIMEOUT'):
        if failure in states:
            return failure
    if any(p.get('rc', 0) != 0 for p in probes):
        return 'TOOL_OR_CONFIG_ERROR'
    if any(p['verdict'] == 'OTHER' for p in probes):
        return 'INCOMPLETE'
    if any(p['verdict'] == 'PREMISES_UNSAT' for p in probes):
        return 'PREMISES_NOT_SAT'
    return None
