"""Reuse the ordinary v6 launcher in memory, exposing already-read root CPU."""
from pathlib import Path
import types

def load(project):
    path=Path(project)/'scripts/pmux_validation/runner/win_measure.py'
    source=path.read_text(encoding='utf-8')
    changes=[('    cpu_user_ticks = cpu_kernel_ticks = None',
              '    cpu_user_ticks = cpu_kernel_ticks = None\n    root_cpu_user_ticks = root_cpu_kernel_ticks = None'),
             ('            process_create_filetime = (int(creation.dwHighDateTime) << 32) | int(creation.dwLowDateTime)',
              '            root_cpu_user_ticks = (int(user_time.dwHighDateTime) << 32) | int(user_time.dwLowDateTime)\n            root_cpu_kernel_ticks = (int(kernel_time.dwHighDateTime) << 32) | int(kernel_time.dwLowDateTime)\n            process_create_filetime = (int(creation.dwHighDateTime) << 32) | int(creation.dwLowDateTime)'),
             ('        "cpu_user_ticks": cpu_user_ticks,',
              '        "root_cpu_user_ticks": root_cpu_user_ticks,\n        "root_cpu_kernel_ticks": root_cpu_kernel_ticks,\n        "cpu_user_ticks": cpu_user_ticks,')]
    for old,new in changes:
        if source.count(old)!=1:raise ValueError('ordinary launcher anchor mismatch')
        source=source.replace(old,new,1)
    module=types.ModuleType('diagnostic_ordinary_launcher');module.__file__=str(path)
    exec(compile(source,str(path),'exec'),module.__dict__)
    def execute(cmd,**kwargs):
        row=module.run_cpu_measured(cmd,**kwargs)
        fields=('rc','timed_out','main_pid','process_create_filetime','process_exit_filetime',
                'cpu_user_ticks','cpu_kernel_ticks','cpu_total_ticks','job_total_processes',
                'root_cpu_user_ticks','root_cpu_kernel_ticks','metrics_valid','measurement_error','root_debugged')
        return {k:row[k] for k in fields}
    return execute
