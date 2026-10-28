"""Two fixed built-in integration profiles; no arbitrary patch execution."""
import hashlib
import json
from pathlib import Path
import result_layout as L
import re

P3_ID = 'pmux-opt-inline-p3-v1'
LOCAL_ID = 'pmux-opt-inline-p3-local-lut-v1'
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
    if value not in (P3_ID, LOCAL_ID):
        raise ValueError('Unsupported integration identity: ' + str(value))
    return value


def configure(cfg, profile, patch):
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
    normalized = [(n, 'PMUX_OPT_LUT' if d.startswith('PMUX_OPT local LUT')
                   else B.executing_name(d).split()[0]) for n, d in entries]
    early = B.check_pmux_position(normalized)
    late = [i for i, (_, name) in enumerate(normalized) if name == 'PMUX_OPT_LUT']
    result = {'integration_id': integration_id, 'early_position': early,
              'early_count': early['count'], 'lut_count': len(late),
              'after_abc9': False, 'before_map_cells': False, 'export_after_lut': False}
    early_ok = early['count'] == 1 and early['after_opt'] and early['before_wreduce']
    if integration_id == P3_ID:
        result['ok'] = bool(early_ok and not late)
        return result
    if integration_id != LOCAL_ID:
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
    if identity(ctx) != LOCAL_ID:
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
    patch = root / (L.ASSETS + '/tree') / PATCH_PATH
    if not patch.is_file() or sha(patch) != (ctx.get('integration_patch') or {}).get('sha256') \
            or (ctx.get('integration_patch') or {}).get('sha256') != PATCH_SHA256:
        errors.append('frozen integration patch identity mismatch')
    fc = load((L.FLOWCHECK + '/builtin_run01/builtin_flowcheck.json'), {})
    cases = fc.get('cases') or []
    if fc.get('all_ok') is not True or len(cases) != len(expected_cases) or {r.get('case') for r in cases} != set(expected_cases):
        errors.append('suite invocation evidence missing or failed')
    for row in cases:
        call = row.get('sides', {}).get('optimized', {}).get('integration_calls') or {}
        if call.get('integration_id') != LOCAL_ID or call.get('ok') is not True:
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
        if call.get('integration_id') != LOCAL_ID or call.get('ok') is not True or call.get('export_after_lut') is not True:
            errors.append('functional netlist was not exported after local LUT: ' + str(case))
        for side, chain in zip(('optimized', 'baseline'), CHAINS):
            net = root / (L.PUBLIC + '/round01') / str(case) / side / 'post_abc.il'
            matched = [r for r in chains if r.get('case') == case and r.get('chain') == chain]
            if not net.is_file() or len(matched) != 1 or row.get(side + '_post_abc_sha256') != sha(net) \
                    or matched[0].get('formal_netlist_sha256') != sha(net):
                errors.append('EQY/exported netlist hash mismatch: ' + str(case) + '/' + side)
    return errors
