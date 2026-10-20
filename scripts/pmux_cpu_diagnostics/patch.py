"""Exact diagnostic changes applied only to isolated source copies."""
import hashlib
from pathlib import Path

HERE=Path(__file__).parent
DECLARATIONS='''
// CPU stage diagnostics, enabled only by the isolated diagnostic launcher.
void diag_cpu_init();
void diag_cpu_mark(const char *label);
void diag_cpu_abc_begin(const std::string &command, const std::string &tempdir);
void diag_cpu_abc_end(int code);
bool diag_cpu_keep_abc();
bool diag_cpu_write();
'''

def replace(text,old,new):
    if text.count(old)!=1:raise ValueError('diagnostic source anchor mismatch: '+old)
    return text.replace(old,new,1)

def contents(original,optimized=False):
    out=dict(original)
    out['kernel/yosys.h']=replace(out['kernel/yosys.h'],'void yosys_setup();','void yosys_setup();\n'+DECLARATIONS)
    out['kernel/yosys.cc']=replace(out['kernel/yosys.cc'],'YOSYS_NAMESPACE_BEGIN\n','YOSYS_NAMESPACE_BEGIN\n\n#include "kernel/diag_cpu_impl.inc"\n')
    out['kernel/driver.cc']=replace(out['kernel/driver.cc'],'int wmain(int argc, wchar_t **wargv)\n{','int wmain(int argc, wchar_t **wargv)\n{\n\tdiag_cpu_init();')
    out['kernel/driver.cc']=replace(out['kernel/driver.cc'],'\t_Exit(0);','\tif (!diag_cpu_write()) _Exit(1);\n\t_Exit(0);')
    text=out['techlibs/intel/synth_intel.cc']
    text=replace(text,'\t\tlog_header(design, "Executing SYNTH_INTEL pass.\\n");','\t\tdiag_cpu_mark("design_read_end");\n\t\tlog_header(design, "Executing SYNTH_INTEL pass.\\n");')
    old='\t\t\trun("fsm");\n\t\t\trun("opt");\n\t\t\trun("wreduce");'
    new='\t\t\trun("fsm");\n\t\t\trun("opt");\n\t\t\tdiag_cpu_mark("fsm_opt_end");\n\t\t\tdiag_cpu_mark("pmux_begin");\n'
    if optimized:new+='\t\t\trun("pmux_opt");\n'
    new+='\t\t\tdiag_cpu_mark("pmux_end");\n\t\t\trun("wreduce");'
    text=replace(text,old,new)
    old='\t\t\trun("abc9 -lut 4 -W 300" + string(dff ? " -dff" : ""));'
    new='\t\t\tdiag_cpu_mark("abc9_begin");\n'+old+'\n\t\t\tdiag_cpu_mark("abc9_end");'
    out['techlibs/intel/synth_intel.cc']=replace(text,old,new)
    out['passes/techmap/abc9.cc']=replace(out['passes/techmap/abc9.cc'],'\t\t\t\t\tif (cleanup) {','\t\t\t\t\tif (cleanup && !diag_cpu_keep_abc()) {')
    old='\tint ret = run_command(buffer, std::bind(&abc9_output_filter::next_line, filt, std::placeholders::_1));'
    out['passes/techmap/abc9_exe.cc']=replace(out['passes/techmap/abc9_exe.cc'],old,'\tdiag_cpu_abc_begin(buffer, tempdir_name);\n'+old+'\n\tdiag_cpu_abc_end(ret);')
    out['abc/src/base/main/main.c']=replace(out['abc/src/base/main/main.c'],'#include <misc/util/abc_global.h>','#include <misc/util/abc_global.h>\n#include "diag_cpu_shared.h"')
    out['abc/src/base/main/main.c']=replace(out['abc/src/base/main/main.c'],'   return ABC_NAMESPACE_PREFIX Abc_RealMain(argc, argv);','   diag_abc_entry();\n   int result = ABC_NAMESPACE_PREFIX Abc_RealMain(argc, argv);\n   diag_abc_exit(result);\n   return result;')
    if optimized:
        import prepare_builtin
        out['passes/opt/CMakeLists.txt']=replace(out['passes/opt/CMakeLists.txt'],prepare_builtin.CMAKE_ANCHOR,prepare_builtin.CMAKE_ANCHOR+prepare_builtin.CMAKE_BLOCK)
    return out

FILES=('kernel/yosys.h','kernel/yosys.cc','kernel/driver.cc','techlibs/intel/synth_intel.cc','passes/techmap/abc9.cc','passes/techmap/abc9_exe.cc','abc/src/base/main/main.c','passes/opt/CMakeLists.txt')

def apply(tree,optimized=False):
    tree=Path(tree);original={p:(tree/p).read_text(encoding='utf-8') for p in FILES}
    for name,text in contents(original,optimized).items():(tree/name).write_bytes(text.encode('utf-8'))
    for source,target in [('diag_cpu_impl.inc','kernel/diag_cpu_impl.inc'),('diag_cpu_shared.h','kernel/diag_cpu_shared.h'),('diag_cpu_shared.h','abc/src/base/main/diag_cpu_shared.h')]:
        (tree/target).write_bytes((HERE/source).read_bytes())

def identity():
    return {n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ('patch.py','diag_cpu_impl.inc','diag_cpu_shared.h')}
