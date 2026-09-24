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


# 支持配置（official4-p2；未列出的参数/端口/取值一律阻断，不静默建模）：
DFFEAS_PORTS = ("d", "q", "clk", "clrn", "prn", "ena", "asdata", "aload", "sclr", "sload")
DFFEAS_CONST_PORTS = {"prn": "1'1", "asdata": "1'0", "aload": "1'0", "sclr": "1'0", "sload": "1'0"}
DFFEAS_PARAMS = ("power_up", "is_wysiwyg")
LCELL_PORTS = ("dataa", "datab", "datac", "datad", "cin", "combout", "cout")
LCELL_PARAMS = ("lut_mask", "sum_lutc_input", "dont_touch", "lpm_type")


def _cells_of(text, top):
    module = re.search(r'^module \\' + re.escape(top) + r'\n(.*?)^end$', text, re.M | re.S)
    if not module:
        raise ValueError(f'Mapped top absent: {top}')
    for cell in re.finditer(r'^  cell (\S+) [^\n]+\n(.*?)^  end$', module[1], re.M | re.S):
        yield cell[1].lstrip('\\'), cell[2]


def check_mapped_model(il_path, top):
    """映射网表支持配置检查（official4-p2）。

    允许：$ 前缀内建单元（Yosys 自带形式语义）；dffeas / cycloneiv_lcell_comb /
    VCC / GND（自有模型）。
    dffeas：power_up ∈ {low,high}；prn=1、asdata/aload/sclr/sload=0；
    控制端口（clrn/ena）与数据端口必须存在——缺失即阻断；
    未知参数、未知端口取值一律阻断。
    cycloneiv_lcell_comb：必需端口与参数存在；sum_lutc_input ∈ {datac,cin}。
    纯组合设计（无 dffeas）合法。
    """
    text = Path(il_path).read_text()
    for kind, body in _cells_of(text, top):
        if kind.startswith('$'):
            continue
        if kind == 'dffeas':
            params = dict(re.findall(r'^    parameter \\(\S+) (.*)$', body, re.M))
            conns = dict(re.findall(r'^    connect \\(\S+) (.*)$', body, re.M))
            for p in params:
                if p not in DFFEAS_PARAMS:
                    raise ValueError(f'dffeas 未知参数: {p}（不支持配置）')
            if 'power_up' not in params:
                raise ValueError('dffeas 缺少 power_up 参数（不支持配置）')
            pu = params['power_up'].strip().strip('"')
            if pu not in ('low', 'high'):
                raise ValueError(f'dffeas power_up 取值不受支持: {params["power_up"]!r}')
            for port in DFFEAS_PORTS:
                if port not in conns:
                    raise ValueError(f'dffeas 缺少端口连接: {port}（缺失控制端口必须阻断）')
            for port, want in DFFEAS_CONST_PORTS.items():
                if conns[port] != want:
                    raise ValueError(f'dffeas {port} 必须为常量 {want}，实际 {conns[port]!r}')
            for port in ('d', 'clk', 'clrn', 'ena', 'q'):
                if not conns[port].strip():
                    raise ValueError(f'dffeas {port} 连接为空')
        elif kind == 'cycloneiv_lcell_comb':
            params = dict(re.findall(r'^    parameter \\(\S+) (.*)$', body, re.M))
            conns = dict(re.findall(r'^    connect \\(\S+) (.*)$', body, re.M))
            for p in params:
                if p not in LCELL_PARAMS:
                    raise ValueError(f'lcell 未知参数: {p}（不支持配置）')
            if 'lut_mask' not in params:
                raise ValueError('lcell 缺少 lut_mask 参数')
            sli = params.get('sum_lutc_input', '"datac"').strip().strip('"')
            if sli not in ('datac', 'cin'):
                raise ValueError(f'lcell sum_lutc_input 取值不受支持: {params["sum_lutc_input"]!r}')
            # 实测本套网表全部 lcell 均连接 dataa/datab/datac/datad/combout（cin/cout 完全未使用）。
            for port in ('dataa', 'datab', 'datac', 'datad', 'combout'):
                if port not in conns:
                    raise ValueError(f'lcell 缺少必需端口连接: {port}')
            for port in conns:
                if port not in LCELL_PORTS:
                    raise ValueError(f'lcell 未知端口: {port}（不支持配置）')
            if sli == 'cin' and 'cin' not in conns:
                raise ValueError('lcell sum_lutc_input="cin" 但 cin 未连接')
            if 'cout' in conns and 'cin' not in conns:
                raise ValueError('lcell cout 已连接但 cin 未连接（不支持配置）')
        elif kind in ('VCC', 'GND'):
            continue
        else:
            raise ValueError(f'Unmodeled cell type: {kind}')
