"""Registered built-in integration profiles; no arbitrary patch execution."""
import hashlib
import json
from pathlib import Path
import result_layout as L
import re

P3_ID = 'pmux-opt-inline-p3-v1'
LOCAL_ID = 'pmux-opt-inline-p3-local-lut-v1'
TWO_CALL_ID = 'pmux-opt-inline-p3-arith-v1'
TWO_CALL_PATCH_SHA256 = '7bc4901a6c57f3739dfb592c6c9ac7193bb71a10bad110baafa11e2502735bb2'
ARITH_ID = 'pmux-opt-inline-p3-arith-local-lut-v1'
ARITH_PATCH_PATH = 'integration/yosys_0_69_stable_pmux.patch'
ARITH_PATCH_SHA256 = '11c25e8030fa31221679f56759fde4bac63a04fe92de1be63fbf79d2d0286725'
def has_lut(integration_id): return integration_id in (LOCAL_ID, ARITH_ID)
def has_arith(integration_id): return integration_id in (ARITH_ID, TWO_CALL_ID)

def requires_evidence(integration_id): return has_lut(integration_id) or has_arith(integration_id)

def patch_identity(integration_id):
    if integration_id == TWO_CALL_ID: return ARITH_PATCH_PATH, TWO_CALL_PATCH_SHA256
    return (ARITH_PATCH_PATH, ARITH_PATCH_SHA256) if has_arith(integration_id) else (PATCH_PATH, PATCH_SHA256)

SAME_RUN_SCHEME = 'pmux-perf-single-powershell-same-run-exitpeak-v8'
PATCH_PATH = 'integration/yosys_0_69_local_lut.patch'
PATCH_SHA256 = 'd21c3cbc519586df587ccdf5334b6275ef7022b443cd34b4435b96d55f24157b'
LUT_ANCHOR = ('\t\t\trun("opt -fast");\n\t\t\trun("autoname");\n'
              '\t\t\trun("clean");\n\t\t}\n\n\t\tif (check_label("map_cells")) {')
LUT_BLOCK = LUT_ANCHOR.replace('\t\t}\n', '\t\t\trun("pmux_opt -lut");\n\t\t}\n', 1)
import official_suite as S
CHAINS = ('c4a_rtl_opt_mapped', 'c4b_rtl_base_mapped')


def identity(cfg):
    value = cfg.get('builtin', {}).get('integration_id', P3_ID)
    if value not in (P3_ID, LOCAL_ID, ARITH_ID, TWO_CALL_ID):
        raise ValueError('Unsupported integration identity: ' + str(value))
    return value


def configure(cfg, profile, patch, stable_patch=None):
    if stable_patch is not None and profile not in ('p3-arith', 'p3-arith-local-lut'):
        raise ValueError('Target requires --integration-profile p3-arith or p3-arith-local-lut')
    if profile in ('p3-arith', 'p3-arith-local-lut'):
        if cfg.get('performance_scheme') != 'pmux-perf-warm10-initial-review5-same-run-v9':
            raise ValueError('Arithmetic integration requires Windows V9')
        integration_id = TWO_CALL_ID if profile == 'p3-arith' else ARITH_ID
        patch_path, patch_sha = patch_identity(integration_id)
        if stable_patch is None or hashlib.sha256(stable_patch).hexdigest() != patch_sha:
            raise ValueError('Missing or unrecognized arithmetic integration patch')
        cfg['integration_profile'] = profile
        cfg['builtin']['integration_id'] = integration_id
        cfg['integration_patch'] = dict(path=patch_path, sha256=patch_sha, text=stable_patch.decode('utf-8'))
        cfg['expected_pmux_calls'] = ['pmux_opt -arith', 'pmux_opt'] + (['pmux_opt -lut'] if has_lut(integration_id) else [])
        return
    if cfg.get('performance_scheme') not in (SAME_RUN_SCHEME, 'pmux-perf-warm10-initial-review5-same-run-v9'):
        raise ValueError('Integration profiles require a registered Windows builtin flow')
    if profile not in ('p3', 'p3-local-lut'):
        raise ValueError('Unknown integration profile: ' + str(profile))
    if profile == 'p3':
        if patch is not None:
            raise ValueError('Target contains a local LUT integration patch; use --integration-profile p3-local-lut')
        cfg['integration_profile'] = 'p3'
        cfg['builtin']['integration_id'] = P3_ID
        return
    if patch is None or hashlib.sha256(patch).hexdigest() != PATCH_SHA256:
        raise ValueError('Missing or unrecognized target local LUT integration patch')
    cfg['integration_profile'] = profile
    cfg['builtin']['integration_id'] = LOCAL_ID
    cfg['integration_patch'] = {'path': PATCH_PATH, 'sha256': PATCH_SHA256,
                                'text': patch.decode('utf-8')}


def check_calls(log, integration_id=P3_ID, require_export=False):
    import builtin_common as B
    entries = B.extract_executing_entries(log)
    normalized = [(n, 'PMUX_OPT_LUT' if d == 'PMUX_OPT local LUT optimization (7.1).'
                   else 'PMUX_OPT_ARITH' if d == 'PMUX_OPT arithmetic sharing.'
                   else 'PMUX_OPT' if d == 'PMUX_OPT pair-swap optimization.'
                   else 'PMUX_OPT_UNKNOWN' if d.startswith('PMUX_OPT')
                   else B.executing_name(d).split()[0]) for n, d in entries]
    arith = [(n, name) for n, name in normalized if name == 'PMUX_OPT_ARITH']
    arith_ok = False
    if has_arith(integration_id) and len(arith) == 1:
        n = arith[0][0]
        if n and n.split('.')[-1].isdigit():
            parts = n.split('.'); index = int(parts[-1])
            lookup = dict(normalized)
            sibling = lambda offset: lookup.get('.'.join(parts[:-1] + [str(index+offset)]))
            arith_ok = (sibling(-1), sibling(1), sibling(2)) == ('OPT', 'PMUX_OPT', 'WREDUCE')
            if integration_id == TWO_CALL_ID:
                arith_ok = arith_ok and sibling(-2) == 'FSM'
            nums = ['.'.join(parts[:-1] + [str(index+offset)]) for offset in ((-2,-1,0,1,2) if integration_id == TWO_CALL_ID else (-1,0,1,2))]
            positions = [[i for i,(num,_) in enumerate(normalized) if num == want] for want in nums]
            arith_ok = arith_ok and all(len(v)==1 for v in positions) and [v[0] for v in positions] == sorted(v[0] for v in positions)
    checked = normalized
    if has_arith(integration_id):
        checked = [(n, name) for n, name in normalized if name != 'PMUX_OPT_ARITH']
        # Ordinary PMUX follows ARITH; validate its predecessor through arith_ok.
        checked = [(n, name) for n, name in checked]

    early = B.check_pmux_position(checked)
    if has_arith(integration_id):
        early['after_arith'] = arith_ok
        early['after_opt'] = arith_ok
    late = [i for i, (_, name) in enumerate(normalized) if name == 'PMUX_OPT_LUT']
    result = {'integration_id': integration_id, 'early_position': early,
              'early_count': early['count'], 'lut_count': len(late), 'arith_count': len(arith),
              'unknown_pmux_calls': [n for n, name in normalized if name == 'PMUX_OPT_UNKNOWN'],
              'after_abc9': False, 'before_map_cells': False, 'export_after_lut': False}
    early_ok = (early['count'] == 1 and early['after_opt'] and early['before_wreduce']
                and not result['unknown_pmux_calls'] and (arith_ok if has_arith(integration_id) else not arith))
    if integration_id == P3_ID:
        result['ok'] = bool(early_ok and not late)
        return result
    if integration_id == TWO_CALL_ID:
        abc = [i for i, (_, d) in enumerate(entries) if d.startswith('ABC9 pass')]
        maps = [i for i,(n,name) in enumerate(normalized) if abc and i > abc[0] and name == 'TECHMAP' and n and entries[abc[0]][0] and len(n.split('.')) == len(entries[abc[0]][0].split('.'))]
        # The formal script writes post_abc.il, then mapped.il later in the
        # same process. Bind the checkpoint to the RTLIL backend's own filename
        # line; an arbitrary RTLIL invocation or detached filename is insufficient.
        exports = []
        for match in re.finditer(
                r'^[ \t]*(?:[\d.]+[ \t]+)?Executing[ \t]+RTLIL backend\.[ \t]*\r?\n'
                r'[ \t]*Output filename: ([^\r\n]+)', log, re.M):
            if match.group(1).strip() == 'post_abc.il':
                exports.append(len(B.extract_executing_entries(log[:match.start()])))
        declarations = re.findall(r'^[ \t]*Output filename:[ \t]*post_abc\.il[ \t\r]*$', log, re.M)
        boundary_ok = False
        if len(abc) == 1 and maps and len(exports) == len(declarations) == 1:
            ai, mi, ei = abc[0], maps[0], exports[0]
            an = entries[ai][0]
            descendants = [i for i,(n,_) in enumerate(entries) if an and n and n.startswith(an+'.')]
            cleanup = [name for n,name in normalized[max([ai]+descendants)+1:ei] if n and n.split('.')[:-1] == an.split('.')[:-1]]
            boundary_ok = ai < ei < mi and [name.upper() for name in cleanup if name.upper() != 'CLEAN'][-2:] == ['OPT','AUTONAME']
        result['export_after_abc'] = boundary_ok
        result['ok'] = bool(early_ok and not late and (not require_export or boundary_ok))
        return result
    if not has_lut(integration_id):
        result['ok'] = False
        return result
    # ABC9 also prints a nested "Executing ABC9." at its executable boundary.
    # Only the enclosing ABC9 pass establishes the map_luts completion boundary.
    abc = [i for i, (_, desc) in enumerate(entries) if desc.startswith('ABC9 pass')]
    if len(late) == len(abc) == 1:
        li, ai = late[0], abc[0]
        an, ln = entries[ai][0], entries[li][0]
        descendants = [i for i, (n, _) in enumerate(entries) if an and n and n.startswith(an + '.')]
        result['after_abc9'] = bool(an and ln and li > max([ai] + descendants)
                                    and ln.split('.')[:-1] == an.split('.')[:-1])
        # Nested ABC9 techmaps are not the vendor map_cells boundary.
        maps = [i for i, (n, name) in enumerate(normalized)
                if i > ai and n and an and name == 'TECHMAP'
                and len(n.split('.')) == len(an.split('.'))]
        result['before_map_cells'] = bool(maps and li < maps[0])
        exports = [i for i, (_, name) in enumerate(normalized) if name == 'RTLIL']
        result['export_after_lut'] = bool(exports and maps and li < exports[0] < maps[0])
    result['ok'] = bool(early_ok and len(late) == 1 and result['after_abc9']
                        and result['before_map_cells']
                        and (not require_export or result['export_after_lut']))
    return result


def formal_chains_ok(rows, context):
    from report import row_functional_ok
    expected = {(c, chain) for c in S.case_ids(context) for chain in CHAINS}
    return (len(rows) == len(expected)
            and {(r.get('case'), r.get('chain')) for r in rows} == expected
            and all(row_functional_ok(r) for r in rows))


def evidence_errors(root, ctx):
    """The same integration/proof gate is used before timing and in the report."""
    if not requires_evidence(identity(ctx)):
        return []
    root = Path(root)
    def load(rel, default):
        try:
            return json.loads((root / rel).read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return default
    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()
    expected_cases = S.case_ids(ctx)
    errors = []
    if has_arith(identity(ctx)):
        from arith_probe import verify_probe
        errors.extend(verify_probe(ctx.get('builtin', {}).get('arith_probe'),ctx.get('builtin',{}).get('optimized',{}).get('binary_sha256')))
    patch_path, patch_sha = patch_identity(identity(ctx))
    patch = root / (L.ASSETS + '/tree') / patch_path
    if not patch.is_file() or sha(patch) != (ctx.get('integration_patch') or {}).get('sha256') \
            or (ctx.get('integration_patch') or {}).get('sha256') != patch_sha:
        errors.append('frozen integration patch identity mismatch')
    fc = load((L.FLOWCHECK + '/builtin_run01/builtin_flowcheck.json'), {})
    cases = fc.get('cases') or []
    if fc.get('all_ok') is not True or len(cases) != len(expected_cases) or {r.get('case') for r in cases} != set(expected_cases):
        errors.append('suite invocation evidence missing or failed')
    for row in cases:
        call = row.get('sides', {}).get('optimized', {}).get('integration_calls') or {}
        if call.get('integration_id') != identity(ctx) or call.get('ok') is not True:
            errors.append('new integration invocation not verified: ' + str(row.get('case')))
    public = load((L.PUBLIC + '/round01/summary.json'), {}).get('cases') or []
    chains = load((L.SELFCHECK + '/chains/run01/chains_summary.json'), [])
    if not formal_chains_ok(chains, ctx):
        errors.append('original RTL functional proofs are incomplete or failed')
    if len(public) != len(expected_cases) or {r.get('case') for r in public} != set(expected_cases):
        errors.append('suite exported netlist evidence missing')
    for row in public:
        case = row.get('case')
        call = row.get('optimized_integration_calls') or {}
        if call.get('integration_id') != identity(ctx) or call.get('ok') is not True or call.get('export_after_lut' if has_lut(identity(ctx)) else 'export_after_abc') is not True:
            errors.append('functional netlist export boundary was not verified: ' + str(case))
        for side, chain in zip(('optimized', 'baseline'), CHAINS):
            net = root / (L.PUBLIC + '/round01') / str(case) / side / 'post_abc.il'
            matched = [r for r in chains if r.get('case') == case and r.get('chain') == chain]
            if not net.is_file() or len(matched) != 1 or row.get(side + '_post_abc_sha256') != sha(net) \
                    or matched[0].get('formal_netlist_sha256') != sha(net):
                errors.append('EQY/exported netlist hash mismatch: ' + str(case) + '/' + side)
    return errors
