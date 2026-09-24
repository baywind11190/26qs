"""Strict EQY status and isolated subprocess handling. No inferred success."""
import json
import os
from pathlib import Path
import re
import subprocess


def run_eqy(cfg, workdir, log, timeout_s=900):
    import p3_common as C
    if workdir.exists() or log.exists():
        raise FileExistsError(f"Refusing proof overwrite: {workdir}")
    workdir.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, YOSYS=str(C.EQY_YOSYS), ABC=str(C.EQY_ABC), LC_ALL="C.UTF-8",
               PATH=str(C.EQY_YOSYS.parent) + os.pathsep + os.environ.get('PATH', '/usr/bin:/bin'))
    cmd = [str(C.TOOL_EQY), '-j', '4', '-d', str(workdir), '--yosys',
           str(C.EQY_YOSYS), '--abc', str(C.EQY_ABC), str(cfg)]
    with log.open('x') as f:
        p = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT,
                             cwd=cfg.parent, env=env, start_new_session=True)
        try:
            rc = p.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, 9)
            p.wait()
            rc = 124
    log.with_suffix('.execution.json').write_text(json.dumps({
        'command': cmd, 'rc': rc, 'timeout_s': timeout_s,
    }, indent=2) + '\n')
    return rc


def summarize_eqy(log, workdir):
    log, workdir = Path(log), Path(workdir)
    text = log.read_text(errors='replace') if log.exists() else ''
    receipt = log.with_suffix('.execution.json')
    rc = json.loads(receipt.read_text())['rc'] if receipt.exists() else None
    names = list(dict.fromkeys(re.findall(r'Failed to prove equivalence of partition (\S+)', text)))
    failures = []
    for name in names:
        statuses = [p.read_text().strip() for p in (workdir / 'strategies' / name).glob('*/status')]
        failures.append({'name': name, 'status': ','.join(statuses) or 'UNKNOWN'})
    proved = len(re.findall('Successfully proved equivalence of partition', text))
    if rc == 124:
        state = 'TIMEOUT'
    elif rc == 0 and 'DONE (PASS, rc=0)' in text and not names and 'ERROR:' not in text:
        state = 'PASS'
    elif rc == 2 and 'DONE (FAIL, rc=2)' in text and names:
        state = 'COUNTEREXAMPLE_REQUIRES_REVIEW' if 'partitions not equivalent' in text else 'UNPROVEN'
    elif 'ERROR:' in text or (rc is not None and rc not in (0, 2)):
        state = 'TOOL_OR_CONFIG_ERROR'
    else:
        state = 'INCOMPLETE'
    errors = re.findall(r'ERROR: (.*)', text)
    return {'rc': rc, 'state': state, 'proved': proved, 'total': proved + len(names),
            'failed': len(names), 'failed_partitions': failures,
            'error': '\n'.join(errors)[:800] or None}


def check_mapped_model(il_path, top):
    """Only the locally modeled cell types and constant-zero aload are supported."""
    text = Path(il_path).read_text()
    module = re.search(r'^module \\' + re.escape(top) + r'\n(.*?)^end$', text, re.M | re.S)
    if not module:
        raise ValueError(f'Mapped top absent: {top}')
    for cell in re.finditer(r'^  cell (\S+) [^\n]+\n(.*?)^  end$', module[1], re.M | re.S):
        kind, body = cell[1].lstrip('\\'), cell[2]
        # $-prefixed cells use Yosys's built-in formal semantics, not our custom model.
        if not kind.startswith('$') and kind not in ('dffeas', 'cycloneiv_lcell_comb', 'VCC', 'GND'):
            raise ValueError(f'Unmodeled cell type: {kind}')
        if kind == 'dffeas' and not re.search(r"^    connect \\aload 1'0$", body, re.M):
            raise ValueError('Model requires every dffeas aload to be literal constant zero')
