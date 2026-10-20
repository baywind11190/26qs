#include "private_job.h"
#include <cpuid.h>
#include <x86intrin.h>
#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include <vector>
#include <string>

struct Calibration { unsigned cpu; uint64_t tsc_delta,qpc_delta; bool affinity_restored; };
static uint64_t read_tsc() { _mm_lfence(); auto v=__rdtsc(); _mm_lfence(); return v; }
static uint64_t qpc() { LARGE_INTEGER n={}; if(!QueryPerformanceCounter(&n)) std::abort(); return n.QuadPart; }
static uint64_t file_ticks(FILETIME f) { return (uint64_t(f.dwHighDateTime)<<32)|f.dwLowDateTime; }
static bool process_times(HANDLE h,uint64_t &created,uint64_t &cpu) {
    FILETIME c={},e={},k={},u={};
    if(!GetProcessTimes(h,&c,&e,&k,&u))return false;
    created=file_ticks(c);cpu=file_ticks(k)+file_ticks(u);return true;
}
static Calibration calibrate(unsigned cpu,uint64_t qpc_hz) {
    Calibration row={cpu,0,0,false};
    DWORD_PTR old=SetThreadAffinityMask(GetCurrentThread(),DWORD_PTR(1)<<cpu);
    if(!old)return row;
    uint64_t qb=qpc(),tb=read_tsc(),qe;
    do { qe=qpc(); } while(qe-qb<qpc_hz/5);
    uint64_t te=read_tsc();
    row.tsc_delta=te-tb;row.qpc_delta=qe-qb;
    row.affinity_restored=SetThreadAffinityMask(GetCurrentThread(),old)!=0;
    return row;
}
struct Increment {unsigned iterations;uint64_t process_cycles,thread_cycles,process_ticks,thread_ticks;bool valid;};
static volatile uint64_t work_value=1;
static void fixed_work(unsigned iterations) {
    for(unsigned i=0;i<iterations;i++)work_value=work_value*1664525+1013904223;
}
static Increment measure_block(unsigned iterations,bool wait=false) {
    ULONG64 pb=0,pe=0,tb=0,te=0;uint64_t created=0,pb_ticks=0,pe_ticks=0;
    FILETIME c={},e={},k={},u={};
    bool ok=process_times(GetCurrentProcess(),created,pb_ticks)&&GetThreadTimes(GetCurrentThread(),&c,&e,&k,&u);
    uint64_t tb_ticks=file_ticks(k)+file_ticks(u);
    ok=QueryProcessCycleTime(GetCurrentProcess(),&pb)&&QueryThreadCycleTime(GetCurrentThread(),&tb)&&ok;
    if(wait)Sleep(200);else fixed_work(iterations);
    ok=QueryThreadCycleTime(GetCurrentThread(),&te)&&QueryProcessCycleTime(GetCurrentProcess(),&pe)&&ok;
    ok=process_times(GetCurrentProcess(),created,pe_ticks)&&GetThreadTimes(GetCurrentThread(),&c,&e,&k,&u)&&ok;
    uint64_t te_ticks=file_ticks(k)+file_ticks(u);
    ok=ok&&pe>=pb&&te>=tb&&pe_ticks>=pb_ticks&&te_ticks>=tb_ticks;
    return {iterations,pe-pb,te-tb,pe_ticks-pb_ticks,te_ticks-tb_ticks,ok};
}
static int increments_mode(const char*output) {
    std::vector<Increment> blocks;
    for(unsigned iterations:{0u,100u,1000u,10000u,100000u})for(int n=0;n<3;n++)blocks.push_back(measure_block(iterations));
    auto waited=measure_block(0,true);
    LARGE_INTEGER freq={};QueryPerformanceFrequency(&freq);
    DWORD_PTR pa=0,sa=0;GetProcessAffinityMask(GetCurrentProcess(),&pa,&sa);
    unsigned cpu=0;while(cpu<63 && !(pa&(DWORD_PTR(1)<<cpu)))cpu++;
    auto end=calibrate(cpu,freq.QuadPart);
    FILE*f=fopen(output,"wb");if(!f)return 3;
    fprintf(f,"{\"method\":\"windows-internal-cycle-cpu-pilot-v1\",\"mode\":\"increments\",\"pid\":%lu,\"blocks\":[",GetCurrentProcessId());
    for(size_t i=0;i<blocks.size();i++) {
        auto&r=blocks[i];fprintf(f,"%s{\"iterations\":%u,\"process_cycles\":%llu,\"thread_cycles\":%llu,\"process_ticks\":%llu,\"thread_ticks\":%llu,\"valid\":%s}",i?",":"",r.iterations,(unsigned long long)r.process_cycles,(unsigned long long)r.thread_cycles,(unsigned long long)r.process_ticks,(unsigned long long)r.thread_ticks,r.valid?"true":"false");
    }
    fprintf(f,"],\"wait\":{\"requested_ms\":200,\"process_cycles\":%llu,\"thread_cycles\":%llu,\"process_ticks\":%llu,\"thread_ticks\":%llu,\"valid\":%s},\"end_calibration\":{\"cpu\":%u,\"tsc_delta\":%llu,\"qpc_delta\":%llu,\"affinity_restored\":%s}}\n",(unsigned long long)waited.process_cycles,(unsigned long long)waited.thread_cycles,(unsigned long long)waited.process_ticks,(unsigned long long)waited.thread_ticks,waited.valid?"true":"false",end.cpu,(unsigned long long)end.tsc_delta,(unsigned long long)end.qpc_delta,end.affinity_restored?"true":"false");
    bool ok=!ferror(f);if(fclose(f))ok=false;return ok?0:4;
}
struct TreeShared {volatile LONG state,error;DWORD root_pid,child_pid,grandchild_pid;uint64_t grandchild_handle;};
static bool spawn(const std::string&args,PROCESS_INFORMATION &pi) {
    char exe[MAX_PATH]={};if(!GetModuleFileNameA(nullptr,exe,sizeof(exe)))return false;
    std::string cmd=std::string("\"")+exe+"\" "+args;
    STARTUPINFOA si={};si.cb=sizeof(si);
    // No console host in this controlled tree. Real Yosys launching is unchanged.
    return CreateProcessA(nullptr,&cmd[0],nullptr,nullptr,FALSE,DETACHED_PROCESS,nullptr,nullptr,&si,&pi);
}
static int tree_worker(const char*name,bool grandchild) {
    HANDLE mapping=OpenFileMappingA(FILE_MAP_ALL_ACCESS,FALSE,name);
    if(!mapping)return 10;
    auto*s=static_cast<TreeShared*>(MapViewOfFile(mapping,FILE_MAP_ALL_ACCESS,0,0,sizeof(TreeShared)));
    if(!s)return 11;
    if(grandchild) {
        while(s->state<2)Sleep(1);
        fixed_work(100000000);return 0;
    }
    s->child_pid=GetCurrentProcessId();PROCESS_INFORMATION pi={};
    if(!spawn(std::string("tree-grandchild ")+name,pi)) {InterlockedExchange(&s->error,12);return 12;}
    s->grandchild_pid=pi.dwProcessId;
    HANDLE root=OpenProcess(PROCESS_DUP_HANDLE,FALSE,s->root_pid),remote=nullptr;
    if(!root||!DuplicateHandle(GetCurrentProcess(),pi.hProcess,root,&remote,0,FALSE,DUPLICATE_SAME_ACCESS)) {InterlockedExchange(&s->error,13);return 13;}
    s->grandchild_handle=(uint64_t)(uintptr_t)remote;InterlockedExchange(&s->state,1);
    while(s->state<2)Sleep(1);
    fixed_work(100000000);
    if(WaitForSingleObject(pi.hProcess,10000)!=WAIT_OBJECT_0)return 14;
    CloseHandle(root);CloseHandle(pi.hProcess);CloseHandle(pi.hThread);return 0;
}
struct Bracket {uint64_t low,job,high;ULONG processes,active,returned;LONG status;bool valid;};
static Bracket bracket(HANDLE job,const std::vector<HANDLE>&handles,uint64_t closed_cycles=0) {
    Bracket r={};r.low=r.high=closed_cycles;r.valid=true;
    for(HANDLE h:handles) {ULONG64 v=0;if(!QueryProcessCycleTime(h,&v))r.valid=false;r.low+=v;}
    PilotJobExtendedAccounting j={};r.status=pilot_query_job(job,j,r.returned);r.job=j.TotalCycleTime.QuadPart;
    r.processes=j.BasicInfo.TotalProcesses;r.active=j.BasicInfo.ActiveProcesses;
    for(HANDLE h:handles) {ULONG64 v=0;if(!QueryProcessCycleTime(h,&v))r.valid=false;r.high+=v;}
    r.valid=r.valid&&r.status==0&&r.returned==sizeof(j)&&r.high>=r.low;
    return r;
}
static void print_bracket(FILE*f,const char*name,const Bracket&r,bool comma) {
    fprintf(f,"%s\"%s\":{\"sum_low\":%llu,\"job_cycles\":%llu,\"sum_high\":%llu,\"processes\":%lu,\"active\":%lu,\"ntstatus\":%u,\"returned_bytes\":%lu,\"valid\":%s}",comma?",":"",name,(unsigned long long)r.low,(unsigned long long)r.job,(unsigned long long)r.high,r.processes,r.active,(unsigned)r.status,r.returned,r.valid?"true":"false");
}
static int tree_mode(const char*output) {
    HANDLE job=CreateJobObjectW(nullptr,nullptr);if(!job||!AssignProcessToJobObject(job,GetCurrentProcess()))return 20;
    uint64_t root_created=0,coarse=0;if(!process_times(GetCurrentProcess(),root_created,coarse))return 21;
    auto initial=bracket(job,{GetCurrentProcess()});
    std::string name="Local\\pmux_internal_cycle_"+std::to_string(GetCurrentProcessId())+"_"+std::to_string(root_created);
    HANDLE mapping=CreateFileMappingA(INVALID_HANDLE_VALUE,nullptr,PAGE_READWRITE,0,sizeof(TreeShared),name.c_str());
    if(!mapping||GetLastError()==ERROR_ALREADY_EXISTS)return 22;
    auto*s=static_cast<TreeShared*>(MapViewOfFile(mapping,FILE_MAP_ALL_ACCESS,0,0,sizeof(TreeShared)));
    if(!s)return 23;
    std::memset(s,0,sizeof(*s));s->root_pid=GetCurrentProcessId();
    PROCESS_INFORMATION child={};if(!spawn("tree-child "+name,child))return 24;
    unsigned retry=0;while(!s->state&&!s->error&&retry++<5000)Sleep(1);
    if(s->state!=1||s->error)return 25;
    HANDLE grandchild=(HANDLE)(uintptr_t)s->grandchild_handle;
    auto live=bracket(job,{GetCurrentProcess(),child.hProcess,grandchild});
    struct {DWORD assigned,count;ULONG_PTR pids[16];} list={};
    bool list_ok=QueryInformationJobObject(job,JobObjectBasicProcessIdList,&list,sizeof(list),nullptr)&&list.count<=16;
    InterlockedExchange(&s->state,2);
    if(WaitForSingleObject(child.hProcess,10000)!=WAIT_OBJECT_0 || WaitForSingleObject(grandchild,10000)!=WAIT_OBJECT_0)return 26;
    DWORD child_exit=0,grandchild_exit=0;
    bool codes=GetExitCodeProcess(child.hProcess,&child_exit)&&GetExitCodeProcess(grandchild,&grandchild_exit);
    ULONG64 child_cycles=0,grandchild_cycles=0;
    uint64_t child_created=0,grandchild_created=0,child_coarse=0,grandchild_coarse=0;
    bool identities=QueryProcessCycleTime(child.hProcess,&child_cycles)&&QueryProcessCycleTime(grandchild,&grandchild_cycles)&&process_times(child.hProcess,child_created,child_coarse)&&process_times(grandchild,grandchild_created,grandchild_coarse);
    auto exited=bracket(job,{GetCurrentProcess(),child.hProcess,grandchild});
    CloseHandle(child.hThread);CloseHandle(child.hProcess);CloseHandle(grandchild);
    auto closed=bracket(job,{GetCurrentProcess()},child_cycles+grandchild_cycles);
    LARGE_INTEGER freq={};QueryPerformanceFrequency(&freq);auto end=calibrate(0,freq.QuadPart);
    FILE*f=fopen(output,"wb");if(!f)return 27;
    fprintf(f,"{\"method\":\"windows-internal-cycle-cpu-pilot-v1\",\"mode\":\"tree\",\"root_pid\":%lu,\"root_created\":%llu,\"list_valid\":%s,\"live_pids\":[",GetCurrentProcessId(),(unsigned long long)root_created,list_ok?"true":"false");
    if(list_ok)for(DWORD i=0;i<list.count;i++)fprintf(f,"%s%llu",i?",":"",(unsigned long long)list.pids[i]);
    fprintf(f,"],\"identities_valid\":%s,\"codes_valid\":%s,\"child\":{\"pid\":%lu,\"created\":%llu,\"cycles\":%llu,\"coarse_ticks\":%llu,\"exit\":%lu},\"grandchild\":{\"pid\":%lu,\"created\":%llu,\"cycles\":%llu,\"coarse_ticks\":%llu,\"exit\":%lu}",identities?"true":"false",codes?"true":"false",s->child_pid,(unsigned long long)child_created,(unsigned long long)child_cycles,(unsigned long long)child_coarse,child_exit,s->grandchild_pid,(unsigned long long)grandchild_created,(unsigned long long)grandchild_cycles,(unsigned long long)grandchild_coarse,grandchild_exit);
    print_bracket(f,"initial",initial,true);print_bracket(f,"live",live,true);print_bracket(f,"exited",exited,true);print_bracket(f,"handles_closed",closed,true);
    fprintf(f,",\"end_calibration\":{\"cpu\":%u,\"tsc_delta\":%llu,\"qpc_delta\":%llu,\"affinity_restored\":%s}}\n",end.cpu,(unsigned long long)end.tsc_delta,(unsigned long long)end.qpc_delta,end.affinity_restored?"true":"false");
    bool ok=!ferror(f);if(fclose(f))ok=false;return ok?0:28;
}
int main(int argc,char**argv) {
    if(argc==3&&std::string(argv[1])=="increments")return increments_mode(argv[2]);
    if(argc==3&&std::string(argv[1])=="tree")return tree_mode(argv[2]);
    if(argc==3&&std::string(argv[1])=="tree-child")return tree_worker(argv[2],false);
    if(argc==3&&std::string(argv[1])=="tree-grandchild")return tree_worker(argv[2],true);
    if(argc!=2)return 2;
    const char *output=argv[1];
    unsigned a=0,b=0,c=0,d=0,maxext=__get_cpuid_max(0x80000000,nullptr);
    bool invariant=maxext>=0x80000007 && __get_cpuid(0x80000007,&a,&b,&c,&d) && (d&(1u<<8));
    unsigned invariant_edx=d;
    LARGE_INTEGER frequency={};bool qok=QueryPerformanceFrequency(&frequency)!=0;
    DWORD adjust=0,increment=0;BOOL disabled=FALSE;
    bool timer_ok=GetSystemTimeAdjustment(&adjust,&increment,&disabled)!=0;
    DWORD_PTR process_affinity=0,system_affinity=0;
    bool affinity_ok=GetProcessAffinityMask(GetCurrentProcess(),&process_affinity,&system_affinity)!=0;
    std::vector<unsigned> processors;
    for(unsigned i=0;i<sizeof(DWORD_PTR)*8;i++)if(process_affinity&(DWORD_PTR(1)<<i))processors.push_back(i);
    std::vector<Calibration> rows;
    if(invariant&&qok&&affinity_ok&&processors.size()>=2)
        for(unsigned cpu: {processors[0],processors[1]})for(int n=0;n<3;n++)rows.push_back(calibrate(cpu,frequency.QuadPart));
    HANDLE job=CreateJobObjectW(nullptr,nullptr);
    DWORD job_error=job?0:GetLastError();
    PilotJobExtendedAccounting empty={},live={};ULONG returned_empty=0,returned_live=0;
    LONG status_empty=job?pilot_query_job(job,empty,returned_empty):LONG(0xc0000008);
    bool assigned=job&&AssignProcessToJobObject(job,GetCurrentProcess());
    if(!assigned)job_error=GetLastError();
    LONG status_live=assigned?pilot_query_job(job,live,returned_live):LONG(0xc0000008);
    JOBOBJECT_BASIC_ACCOUNTING_INFORMATION documented={};
    bool basic_ok=assigned&&QueryInformationJobObject(job,JobObjectBasicAccountingInformation,&documented,sizeof(documented),nullptr);
    ULONG64 cycles=0,thread_cycles=0;uint64_t created=0,cpu=0;
    bool process_ok=QueryProcessCycleTime(GetCurrentProcess(),&cycles)&&process_times(GetCurrentProcess(),created,cpu);
    bool thread_ok=QueryThreadCycleTime(GetCurrentThread(),&thread_cycles)!=0;
    FILE*f=fopen(output,"wb");if(!f)return 3;
    fprintf(f,"{\"method\":\"windows-internal-cycle-cpu-pilot-v1\",\"mode\":\"gate1\",\"pid\":%lu,\"created\":%llu,\"hardware\":{\"max_extended_cpuid_leaf\":%u,\"invariant_tsc_edx\":%u,\"invariant_tsc\":%s,\"qpc_valid\":%s,\"qpc_hz\":%llu,\"system_time_increment_100ns\":%lu,\"timer_query_valid\":%s,\"process_affinity_mask\":%llu},\"layout\":{\"size\":%llu,\"cycle_offset\":%llu,\"empty_ntstatus\":%u,\"empty_returned_bytes\":%lu,\"live_ntstatus\":%u,\"live_returned_bytes\":%lu,\"assigned\":%s,\"win32_error\":%lu,\"empty_cycles\":%lld,\"live_cycles\":%lld,\"extended_processes\":%lu,\"extended_active\":%lu,\"basic_valid\":%s,\"documented_processes\":%lu,\"documented_active\":%lu},\"process_interface_valid\":%s,\"thread_interface_valid\":%s,\"root_cycles\":%llu,\"thread_cycles\":%llu,\"coarse_cpu_ticks\":%llu,\"calibrations\":[",
      GetCurrentProcessId(),(unsigned long long)created,maxext,invariant_edx,invariant?"true":"false",qok?"true":"false",(unsigned long long)frequency.QuadPart,increment,timer_ok?"true":"false",(unsigned long long)process_affinity,
      (unsigned long long)sizeof(live),(unsigned long long)offsetof(PilotJobExtendedAccounting,TotalCycleTime),(unsigned)status_empty,returned_empty,(unsigned)status_live,returned_live,assigned?"true":"false",job_error,(long long)empty.TotalCycleTime.QuadPart,(long long)live.TotalCycleTime.QuadPart,live.BasicInfo.TotalProcesses,live.BasicInfo.ActiveProcesses,basic_ok?"true":"false",documented.TotalProcesses,documented.ActiveProcesses,
      process_ok?"true":"false",thread_ok?"true":"false",(unsigned long long)cycles,(unsigned long long)thread_cycles,(unsigned long long)cpu);
    for(size_t i=0;i<rows.size();i++)fprintf(f,"%s{\"cpu\":%u,\"tsc_delta\":%llu,\"qpc_delta\":%llu,\"affinity_restored\":%s}",i?",":"",rows[i].cpu,(unsigned long long)rows[i].tsc_delta,(unsigned long long)rows[i].qpc_delta,rows[i].affinity_restored?"true":"false");
    fprintf(f,"]}\n");bool written=!ferror(f);if(fclose(f)!=0)written=false;
    if(job)CloseHandle(job);
    return written?0:4;
}
