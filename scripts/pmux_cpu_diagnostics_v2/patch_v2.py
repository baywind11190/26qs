"""Only isolated copies are transformed. Formal runtime formula is retained."""
import hashlib
from pathlib import Path
import runtime_patch
import prepare_builtin as P

HERE=Path(__file__).parent
FILES=('kernel/yosys.h','kernel/yosys.cc','kernel/driver.cc','techlibs/intel/synth_intel.cc','passes/techmap/abc9.cc','passes/techmap/abc9_exe.cc','abc/src/base/main/main.c','passes/opt/CMakeLists.txt')
DECL='''
#ifdef _WIN32
void diag_v2_bind(void *);
void diag_v2_mark(const char *);
void diag_v2_abc_begin(const std::string &,const std::string &);
void diag_v2_abc_end(int);
void diag_v2_final(const void *,const void *,const void *);
bool diag_v2_keep();
bool diag_v2_skip();
bool diag_v2_write();
#endif
'''

def replace(text,old,new):
    if text.count(old)!=1:raise ValueError('diagnostic anchor mismatch: '+old)
    return text.replace(old,new,1)

def contents(original,optimized):
    out=dict(original)
    # Windows declarations need windows.h first, as in the original diag v1.
    out['kernel/yosys.h']=replace(out['kernel/yosys.h'],'void yosys_setup();','void yosys_setup();\n'+DECL)
    out['kernel/yosys.cc']=replace(out['kernel/yosys.cc'],'YOSYS_NAMESPACE_BEGIN\n','YOSYS_NAMESPACE_BEGIN\n#include "kernel/diag_v2_impl.inc"\n')
    driver=runtime_patch.transform(out['kernel/driver.cc'])
    driver=replace(driver,'\tWindowsRuntimeCpu runtime_cpu;','\tWindowsRuntimeCpu runtime_cpu;\n\tdiag_v2_bind(runtime_cpu.job);')
    driver=replace(driver,'        FILE *f = fopen(path.c_str(), "wb");','        diag_v2_final(&info, &user, &kernel);\n        FILE *f = fopen(path.c_str(), "wb");')
    driver=replace(driver,'\t_Exit(0);','\tif (!diag_v2_write()) _Exit(1);\n\t_Exit(0);')
    out['kernel/driver.cc']=driver
    synth=out['techlibs/intel/synth_intel.cc']
    synth=replace(synth,'\t\tlog_header(design, "Executing SYNTH_INTEL pass.\\n");','\t\tdiag_v2_mark("design_read_end");\n\t\tlog_header(design, "Executing SYNTH_INTEL pass.\\n");')
    old='\t\t\trun("fsm");\n\t\t\trun("opt");\n\t\t\trun("wreduce");'
    call='\t\t\tif (!diag_v2_skip()) run("pmux_opt");\n' if optimized else ''
    synth=replace(synth,old,'\t\t\trun("fsm");\n\t\t\trun("opt");\n\t\t\tdiag_v2_mark("fsm_opt_end");\n\t\t\tdiag_v2_mark("pmux_begin");\n'+call+'\t\t\tdiag_v2_mark("pmux_end");\n\t\t\trun("wreduce");')
    old='\t\t\trun("abc9 -lut 4 -W 300" + string(dff ? " -dff" : ""));'
    synth=replace(synth,old,'\t\t\tdiag_v2_mark("abc9_begin");\n'+old+'\n\t\t\tdiag_v2_mark("abc9_end");')
    out['techlibs/intel/synth_intel.cc']=synth
    out['passes/techmap/abc9.cc']=replace(out['passes/techmap/abc9.cc'],'\t\t\t\t\tif (cleanup) {','\t\t\t\t\tif (cleanup && !diag_v2_keep()) {')
    old='\tint ret = run_command(buffer, std::bind(&abc9_output_filter::next_line, filt, std::placeholders::_1));'
    out['passes/techmap/abc9_exe.cc']=replace(out['passes/techmap/abc9_exe.cc'],old,'\tdiag_v2_abc_begin(buffer, tempdir_name);\n'+old+'\n\tdiag_v2_abc_end(ret);')
    main=out['abc/src/base/main/main.c']
    main=replace(main,'#include <misc/util/abc_global.h>','#include <misc/util/abc_global.h>\n#include "diag_v2_shared.h"')
    main=replace(main,'   return ABC_NAMESPACE_PREFIX Abc_RealMain(argc, argv);','   v2abc_entry();\n   int result = ABC_NAMESPACE_PREFIX Abc_RealMain(argc, argv);\n   v2abc_exit(result);\n   return result;')
    out['abc/src/base/main/main.c']=main
    if optimized:out['passes/opt/CMakeLists.txt']=replace(out['passes/opt/CMakeLists.txt'],P.CMAKE_ANCHOR,P.CMAKE_ANCHOR+P.CMAKE_BLOCK)
    return out

def identity():
    return {n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ('patch_v2.py','diag_v2_shared.h','diag_v2_impl.inc')}

def apply(tree,optimized):
    tree=Path(tree);original={p:(tree/p).read_text(encoding='utf-8') for p in FILES}
    for name,text in contents(original,optimized).items():(tree/name).write_bytes(text.encode())
    for s,d in [('diag_v2_impl.inc','kernel/diag_v2_impl.inc'),('diag_v2_shared.h','kernel/diag_v2_shared.h'),('diag_v2_shared.h','abc/src/base/main/diag_v2_shared.h')]:
        (tree/d).write_bytes((HERE/s).read_bytes())
