"""Exact common driver patch; never accepts arbitrary baseline differences."""
import hashlib
from pathlib import Path
import subprocess

METHOD='windows-yosys-main-job-cpu-v1'
SCHEME='pmux-perf-single-windows-internalcpu-exitpeak-v6'

def transform(text):
    body=Path(__file__).with_name('runtime_cpu_windows.inc').read_text(encoding='utf-8')
    edits=[('int wmain(int argc, wchar_t **wargv)\n{',
            'int wmain(int argc, wchar_t **wargv)\n{\n\tWindowsRuntimeCpu runtime_cpu;\n\tstd::string runtime_json;'),
           ('\toptions.add_options("operation")',
            '\toptions.add_options("operation")\n#ifdef _WIN32\n\t\t("runtime-json", "write full process-tree CPU accounting at exit", cxxopts::value<std::string>(), "<path>")\n#endif'),
           ('\t\tauto result = options.parse(argc, argv);',
            '\t\tauto result = options.parse(argc, argv);\n#ifdef _WIN32\n\t\tif (result.count("runtime-json")) {\n\t\t\truntime_json = result["runtime-json"].as<std::string>();\n\t\t\tif (runtime_json.empty() || runtime_cpu.error) { fprintf(stderr, "Cannot initialize runtime CPU accounting\\n"); return 1; }\n\t\t}\n#endif'),
           ('\t_Exit(0);', '\tif (!runtime_json.empty() && !runtime_cpu.write(runtime_json)) _Exit(1);\n\t_Exit(0);')]
    # Insert immediately before the Windows entry-point block; headers are already included.
    anchor='#ifdef _WIN32\nint wmain'
    if text.count(anchor)!=1: raise ValueError('Windows entry anchor mismatch')
    text=text.replace(anchor,body+'\n'+anchor)
    for old,new in edits:
        if text.count(old)!=1: raise ValueError('runtime patch anchor mismatch: '+old)
        text=text.replace(old,new)
    return text

def identity():
    h=hashlib.sha256()
    for name in ('runtime_patch.py','runtime_cpu_windows.inc'):
        h.update(Path(__file__).with_name(name).read_bytes())
    return dict(method=METHOD,sha256=h.hexdigest())

def enabled(cfg): return cfg.get('performance_scheme')==SCHEME

def apply(tree):
    path=Path(tree)/'kernel/driver.cc'
    path.write_bytes(transform(path.read_text(encoding='utf-8')).encode('utf-8'))

def verify(tree):
    original=subprocess.check_output(['git','-C',str(tree),'show','HEAD:kernel/driver.cc']).decode('utf-8')
    if (Path(tree)/'kernel/driver.cc').read_text(encoding='utf-8')!=transform(original):
        raise ValueError('common runtime patch differs from exact template')
    return identity()
