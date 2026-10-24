"""One dedicated allocation/release probe; no public circuit warmup."""
import json
import os
from pathlib import Path
import sys
from measure_v8 import METHOD, SCHEME, run_combined_measured, sample_errors, save, sha


def run(context, output_dir):
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=False)
    probe = out / 'probe.py'
    probe.write_text('''import ctypes, gc, time
from ctypes import wintypes
class Counters(ctypes.Structure):
    _fields_ = [('cb',wintypes.DWORD),('faults',wintypes.DWORD)] + [(n,ctypes.c_size_t) for n in ('peak','current','pqp','qp','pqnp','qnp','page','ppage','private')]
k=ctypes.WinDLL('kernel32',use_last_error=True)
p=ctypes.WinDLL('psapi',use_last_error=True)
k.GetCurrentProcess.restype=wintypes.HANDLE
p.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
data=bytearray(192*1024*1024)
for i in range(0,len(data),4096): data[i]=1
del data; gc.collect(); time.sleep(0.05)
c=Counters(); c.cb=ctypes.sizeof(c)
assert p.GetProcessMemoryInfo(k.GetCurrentProcess(),ctypes.byref(c),c.cb)
assert c.peak >= 192*1024*1024 and c.current < c.peak
print('peak-vs-current',c.peak,c.current,flush=True)
print('probe-late-output-complete',flush=True)
''', encoding='utf-8')
    record = run_combined_measured([sys.executable, str(probe)], cwd=out,
                                  log_path=out / 'probe.log', timeout_s=30,
                                  powershell_path=context['wall_time_tool']['path'], env=os.environ.copy())
    errors = sample_errors(record)
    checks = {'joint_record_valid': not errors,
              'pinned_powershell_identity': record.get('powershell_sha256') == sha(context['wall_time_tool']['path'])
                  and Path(record.get('powershell_path', '')).resolve() == Path(context['wall_time_tool']['path']).resolve(),
              'allocation_peak_retained': record.get('yosys_peak_working_set_bytes', 0) >= 192 * 1024**2,
              'late_output_complete': 'probe-late-output-complete' in (out / 'probe.log').read_text(encoding='utf-8', errors='replace'),
              'released_before_exit': 'peak-vs-current' in (out / 'probe.log').read_text(encoding='utf-8', errors='replace')}
    result = dict(schema=1, performance_scheme=SCHEME, method=METHOD,
                  selftest_ok=all(checks.values()), checks=checks, errors=errors,
                  record=record, public_case_syntheses=0)
    save(out / 'selftest_results.json', result)
    print(json.dumps({'selftest_ok': result['selftest_ok'], 'checks': checks}), flush=True)
    return 0 if result['selftest_ok'] else 1


if __name__ == '__main__':
    raise SystemExit(run(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')), sys.argv[2]))
