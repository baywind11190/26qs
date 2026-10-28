"""ASCII-only paths shared by the V8 entrypoint, runners, and reports."""
from pathlib import Path
import re

LAYOUT_VERSION = 'ascii-v1'
ROUND_PARENT_REL = 'results/official_eval'
SELFCHECK_CACHE_REL = 'results/official_eval/_cache/selfcheck_v8.json'
ROUND_LABEL_DEFAULT = 'v9'
META = '01_meta'
ASSETS = '02_assets'
RUNNER = '03_runner'
FLOWCHECK = '04_flowcheck'
PUBLIC = '05_public'
PERFORMANCE = '09_performance'
SELFCHECK = '10_selfcheck'
SUMMARY = '11_summary'
REPORT = '00_report.md'
TOOLCHAIN_EVIDENCE = 'toolchain_evidence'


def result_parent(cfg):
    if str(cfg.get('performance_scheme','')).endswith('-v9'):
        if not cfg.get('results_root'): raise ValueError('V9 results_root is required')
        return contained_path(cfg['results_root'], 'r')
    return validate_output_root(Path(cfg['repo']) / ROUND_PARENT_REL)


def selfcheck_cache(cfg):
    if str(cfg.get('performance_scheme','')).endswith('-v9'):
        if not cfg.get('results_root'): raise ValueError('V9 results_root is required')
        return contained_path(cfg['results_root'], 'c', 'selfcheck_v9.json')
    return Path(cfg['repo']) / cfg.get('selfcheck_cache_rel', SELFCHECK_CACHE_REL)


def validate_label(label):
    if not isinstance(label, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', label):
        raise ValueError('Label may contain only ASCII letters, digits, underscore and hyphen')
    return label


def validate_output_root(root):
    """Resolve and check without creating paths or using a fallback workspace."""
    original = Path(root).absolute()
    for part in (original, *original.parents):
        if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
            raise ValueError('Linked validation output path: ' + str(part))
    root = Path(root).resolve()
    if not str(root).isascii() or any(
            not re.fullmatch(r'[A-Za-z0-9._-]+', part)
            for part in root.parts if part != root.anchor):
        raise ValueError('Validation output path must be ASCII without spaces or shell characters: '
                         + str(root))
    if root.drive and not re.fullmatch(r'[A-Za-z]:', root.drive):
        raise ValueError('Validation output requires a local drive path: ' + str(root))
    return root


def contained_path(root, *parts):
    """Return an ASCII final evidence path strictly contained by its root."""
    root = validate_output_root(root)
    path = (root.joinpath(*parts)).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError('Evidence path escapes its result directory') from exc
    return validate_output_root(path)
