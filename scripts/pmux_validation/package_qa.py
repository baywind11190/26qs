"""Portable QA, executed by the ZIP's own Python in a new extraction."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    root = Path(__file__).resolve().parents[1]
    work = root / 'qa/smoke-work'
    work.mkdir(exist_ok=False)
    env = dict(os.environ)
    env['PATH'] = os.pathsep.join(map(str, [root / 'runtime/mingw64/bin',
                                         root / 'runtime/msys/usr/bin', root / 'tools/baseline/bin',
                                         Path(os.environ['SystemRoot']) / 'System32', Path(os.environ['SystemRoot'])]))
    env.update(PYTHONHOME=str(root / 'runtime/mingw64'), PYTHONUTF8='1',
               PYTHONIOENCODING='utf-8', PYTHONNOUSERSITE='1',
               PYTHONPATH=str(root / 'runtime/mingw64/lib/python3.14/site-packages'),
               MSYSTEM='MINGW64', MSYS2_PATH_TYPE='inherit', LC_ALL='C.UTF-8')
    for k in ('BASH_ENV', 'ENV', 'PYTHONUSERBASE'):
        env.pop(k, None)
    result = {'state': 'RUNNING', 'checks': {}, 'tools': {}, 'path': env['PATH'],
              'four_case_reproduction': 'NOT_RUN', 'scope': 'small positive/negative and actual tool-error QA'}

    def run(name, args, expected=0, extra_env=None):
        with (work / (name + '.log')).open('wb') as f:
            p = subprocess.run(list(map(str, args)), cwd=work, env=extra_env or env,
                               stdout=f, stderr=subprocess.STDOUT, timeout=120)
        result['checks'][name] = dict(rc=p.returncode, expected_rc=expected,
                                     pass_check=(p.returncode == expected))
        if p.returncode != expected:
            raise RuntimeError(name + ' unexpected rc=' + str(p.returncode))

    try:
        manifest = json.loads((root / 'package_manifest.json').read_text(encoding='utf-8'))
        for item in manifest['files']:
            p = root / item['path']
            if sha(p) != item['sha256']:
                raise RuntimeError('Package hash mismatch: ' + item['path'])
        result['checks']['manifest'] = {'pass_check': True, 'files': len(manifest['files'])}
        for name in ('python3', 'bash', 'make', 'grep', 'sh'):
            p = shutil.which(name, path=env['PATH'])
            if not p or not Path(p).resolve().is_relative_to(root):
                raise RuntimeError('External tool lookup: ' + name)
            version = subprocess.check_output([p, '--version'], env=env, encoding='utf-8', errors='replace').splitlines()[0]
            result['tools'][name] = dict(path=p, sha256=sha(p), version=version)
        (work / 'gold.v').write_text('module top(input [3:0] a,b,input sel,output [3:0] y); assign y=sel?b:a; endmodule\n')
        (work / 'gate.v').write_text('module top(input [3:0] a,b,input sel,output [3:0] y); assign y=(a&{4{~sel}})|(b&{4{sel}}); endmodule\n')
        (work / 'bad.v').write_text('module top(input [3:0] a,b,input sel,output [3:0] y); assign y=~(sel?b:a); endmodule\n')
        flow = 'read_verilog -sv gold.v\nsynth_intel -family cycloneiv -top top\ncheck -assert\nwrite_rtlil mapped.il\ntee -o stat.json stat -json\n'
        binaries = {}
        for side in ('baseline', 'optimized'):
            binary = root / 'tools' / side / 'bin/yosys.exe'
            binaries[side] = binary
            version = subprocess.check_output([str(binary), '-V'], env=env, encoding='utf-8').strip()
            if not version.startswith('Yosys 0.69'):
                raise RuntimeError('Yosys version mismatch')
            result['tools'][side] = dict(path=str(binary), sha256=sha(binary), version=version)
            side_dir = work / side
            side_dir.mkdir()
            shutil.copy2(work / 'gold.v', side_dir / 'gold.v')
            (side_dir / 'flow.ys').write_text(flow)
            side_env = dict(env, YOSYS_DATDIR=str(root / 'tools' / side / 'share/yosys'))
            with (side_dir / 'run.log').open('wb') as f:
                p = subprocess.run([str(binary), '-s', 'flow.ys'], cwd=side_dir, env=side_env,
                                   stdout=f, stderr=subprocess.STDOUT, timeout=120)
            result['checks'][side + '_synthesis'] = {'pass_check': p.returncode == 0, 'rc': p.returncode,
                                                    'flow_sha256': sha(side_dir / 'flow.ys'),
                                                    'input_sha256': sha(side_dir / 'gold.v')}
            if p.returncode != 0:
                raise RuntimeError('Synthesis failed: ' + side)
        for mode, gate in [('positive', 'gate.v'), ('negative', 'bad.v')]:
            cfg = '[gold]\nread_verilog -sv gold.v\nprep -top top\n[gate]\nread_verilog -sv ' + gate + '\nprep -top top\n[strategy simple]\nuse sat\ndepth 5\n'
            (work / (mode + '.eqy')).write_text(cfg)
            run(mode, [root / 'eqy-portable.cmd', '-f', '-d', mode + '-work',
                       '--yosys', binaries['baseline'], '--abc', root / 'tools/baseline/bin/yosys-abc.exe', mode + '.eqy'],
                expected=0 if mode == 'positive' else 2)
            marker = work / (mode + '-work') / ('PASS' if mode == 'positive' else 'FAIL')
            log = (work / (mode + '.log')).read_text(encoding='utf-8', errors='replace')
            if not marker.is_file() or (mode == 'negative' and 'partitions not equivalent' not in log):
                raise RuntimeError('EQY result missing or failure is not an actual counterexample')
        # Exercise real native subprocess bytes through the exact packaged decoder.
        job = root / 'tools/eqy/share/yosys/python3/eqy_job.py'
        sys.path.insert(0, str(job.parent))
        spec = importlib.util.spec_from_file_location('package_eqy_job', job)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        error = subprocess.run([sys.executable, '-c',
            "import sys;sys.stdout.buffer.write('工具错误：故意失败'.encode('cp936'));sys.exit(3)"],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        decoded = module.decode_process_output(error.stdout)
        (work / 'encoding_error.raw').write_bytes(error.stdout)
        (work / 'encoding_error.log').write_text(decoded, encoding='utf-8')
        if error.returncode != 3 or '工具错误' not in decoded:
            raise RuntimeError('Native error decoding or exit preservation failed')
        result['checks']['encoding_error'] = {'pass_check': True, 'rc': 3,
                                               'raw_sha256': sha(work / 'encoding_error.raw')}
        result['state'] = 'PASS'
    except Exception as exc:
        result['state'] = 'FAIL'
        result['error'] = str(exc)
        raise
    finally:
        (work / 'smoke_result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('PACKAGE_SMOKE=PASS\nRESULT=' + str(work / 'smoke_result.json'))


if __name__ == '__main__':
    main()
