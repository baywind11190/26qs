#ifdef _WIN32
#include "diag_cpu_shared.h"
namespace {
struct DiagMark { const char *label; uint64_t root_user,root_kernel,job_user,job_kernel; DWORD processes; int call_id; };
struct DiagCall { std::string command,tempdir; int exit_code; };
static HANDLE diag_job=NULL,diag_mapping=NULL;
static DiagShared *diag_shared=NULL;
static DiagMark diag_marks[256];
static DiagCall diag_calls[DIAG_MAX_ABC];
static int diag_count=0,diag_call_count=0;
static DWORD diag_error=0;
static uint64_t diag_created=0;
static std::string diag_output;
static bool diag_keep=false;
static std::string diag_json_string(const std::string &s) {
    std::string result="\"";
    for (unsigned char c:s) {
        if (c=='\\' || c=='\"') { result+='\\';result+=c; }
        else if (c<32) { char text[7];snprintf(text,sizeof(text),"\\u%04x",c);result+=text; }
        else result+=c;
    }
    return result+"\"";
}
}
void diag_cpu_mark(const char *label) {
    if (diag_output.empty()) return;
    if (diag_count>=256) { diag_error=ERROR_INSUFFICIENT_BUFFER; return; }
    DiagMark &m=diag_marks[diag_count++];m.label=label;m.call_id=diag_call_count;
    uint64_t created=0;
    if (!diag_process_times(GetCurrentProcess(),&created,&m.root_user,&m.root_kernel)) diag_error=GetLastError();
    if (created!=diag_created) diag_error=ERROR_INVALID_DATA;
    JOBOBJECT_BASIC_ACCOUNTING_INFORMATION info={};
    if (diag_job && !QueryInformationJobObject(diag_job,JobObjectBasicAccountingInformation,&info,sizeof(info),NULL)) diag_error=GetLastError();
    m.job_user=info.TotalUserTime.QuadPart;m.job_kernel=info.TotalKernelTime.QuadPart;m.processes=info.TotalProcesses;
}
void diag_cpu_init() {
    const char *output=getenv("PMUX_CPU_DIAG_JSON");
    if (!output || !*output) return;
    uint64_t user=0,kernel=0;
    bool entry_ok=diag_process_times(GetCurrentProcess(),&diag_created,&user,&kernel)!=0;
    diag_output=output;
    diag_marks[diag_count++]={"main_entry",user,kernel,0,0,0,0};
    if (!entry_ok) diag_error=GetLastError();
    diag_job=CreateJobObjectW(NULL,NULL);
    if (!diag_job || !AssignProcessToJobObject(diag_job,GetCurrentProcess())) diag_error=GetLastError();
    std::string name="Local\\pmux_cpu_diag_"+std::to_string(GetCurrentProcessId())+"_"+std::to_string(diag_created);
    diag_mapping=CreateFileMappingA(INVALID_HANDLE_VALUE,NULL,PAGE_READWRITE,0,sizeof(DiagShared),name.c_str());
    if (!diag_mapping || GetLastError()==ERROR_ALREADY_EXISTS) {diag_error=ERROR_INVALID_DATA;return;}
    diag_shared=(DiagShared*)MapViewOfFile(diag_mapping,FILE_MAP_ALL_ACCESS,0,0,sizeof(DiagShared));
    if (!diag_shared) {diag_error=GetLastError();return;}
    memset(diag_shared,0,sizeof(DiagShared));diag_shared->magic=DIAG_MAGIC;
    diag_shared->root_pid=GetCurrentProcessId();diag_shared->root_created=diag_created;
    if (!SetEnvironmentVariableA("PMUX_CPU_DIAG_MAPPING",name.c_str())) diag_error=GetLastError();
    const char *keep=getenv("PMUX_CPU_DIAG_KEEP_ABC");diag_keep=keep && strcmp(keep,"1")==0;
    diag_cpu_mark("job_assigned");
}
void diag_cpu_abc_begin(const std::string &command,const std::string &tempdir) {
    if (diag_output.empty()) return;
    if (diag_call_count>=DIAG_MAX_ABC) {diag_error=ERROR_INSUFFICIENT_BUFFER;return;}
    DiagCall &call=diag_calls[diag_call_count++];call.command=command;call.tempdir=tempdir;call.exit_code=-1;
    if (diag_shared) InterlockedExchange(&diag_shared->current_call,diag_call_count);
    diag_cpu_mark("abc_call_begin");
}
void diag_cpu_abc_end(int code) {
    if (diag_output.empty()) return;
    diag_cpu_mark("abc_call_end");
    if (diag_call_count>0 && diag_call_count<=DIAG_MAX_ABC) diag_calls[diag_call_count-1].exit_code=code;
    if (diag_shared) InterlockedExchange(&diag_shared->current_call,0);
}
bool diag_cpu_keep_abc() { return !diag_output.empty() && diag_keep; }
bool diag_cpu_write() {
    if (diag_output.empty()) return true;
    diag_cpu_mark("final");
    JOBOBJECT_BASIC_ACCOUNTING_INFORMATION info={};
    if (!diag_job || !QueryInformationJobObject(diag_job,JobObjectBasicAccountingInformation,&info,sizeof(info),NULL)) diag_error=GetLastError();
    if (!diag_shared) return false;
    bool valid=!diag_error && !diag_shared->errors && info.ActiveProcesses==1;
    for (int i=0;i<diag_call_count;i++) {
        const DiagAbcRecord &r=diag_shared->records[i];
        if (r.ready!=2 || r.call_id!=(DWORD)(i+1) || !r.pid || !r.created || r.exit_code || diag_calls[i].exit_code) valid=false;
    }
    FILE *f=fopen(diag_output.c_str(),"wb");if (!f) return false;
    fprintf(f,"{\"schema\":1,\"method\":\"windows-cpu-stage-diagnostic-v1\",\"pid\":%lu,\"created\":%llu,\"valid\":%s,\"error\":%lu,\"keep_abc\":%s,\"marks\":[",
        GetCurrentProcessId(),(unsigned long long)diag_created,valid?"true":"false",diag_error,diag_keep?"true":"false");
    for(int i=0;i<diag_count;i++) { const DiagMark &m=diag_marks[i];
        fprintf(f,"%s{\"label\":%s,\"root_user\":%llu,\"root_kernel\":%llu,\"job_user\":%llu,\"job_kernel\":%llu,\"processes\":%lu,\"call_id\":%d}",
            i?",":"",diag_json_string(m.label).c_str(),(unsigned long long)m.root_user,(unsigned long long)m.root_kernel,
            (unsigned long long)m.job_user,(unsigned long long)m.job_kernel,m.processes,m.call_id);
    }
    fprintf(f,"],\"abc\":[");
    for(int i=0;i<diag_call_count;i++) { const DiagAbcRecord &r=diag_shared->records[i];const DiagCall &c=diag_calls[i];
        fprintf(f,"%s{\"call_id\":%lu,\"ready\":%ld,\"pid\":%lu,\"created\":%llu,\"start_user\":%llu,\"start_kernel\":%llu,\"end_user\":%llu,\"end_kernel\":%llu,\"exit_code\":%d,\"launcher_exit\":%d,\"command\":%s,\"tempdir\":%s}",
            i?",":"",r.call_id,r.ready,r.pid,(unsigned long long)r.created,(unsigned long long)r.start_user,(unsigned long long)r.start_kernel,
            (unsigned long long)r.end_user,(unsigned long long)r.end_kernel,r.exit_code,c.exit_code,diag_json_string(c.command).c_str(),diag_json_string(c.tempdir).c_str());
    }
    fprintf(f,"]}\n");bool written=!ferror(f);if(fclose(f)!=0)written=false;return valid && written;
}
#endif
