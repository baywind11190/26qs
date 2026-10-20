#include <windows.h>
#include <cstdio>
#include <string>
#include "diag_cpu_shared.h"
int main(int argc,char **argv) {
    if(argc>1) {
        diag_abc_entry();
        uint64_t c,u,k;volatile unsigned long long value=0;
        do {
            for(int i=0;i<10000;i++)value=value*1664525+1013904223;
            if(!diag_process_times(GetCurrentProcess(),&c,&u,&k))return 2;
        }while(u+k<2500000);
        diag_abc_exit(0);return 0;
    }
    uint64_t created,root_u,root_k;
    if(!diag_process_times(GetCurrentProcess(),&created,&root_u,&root_k))return 3;
    // A controlled pre-association CPU interval distinguishes Job scope from
    // lifetime process CPU; it is not an algorithm performance sample.
    uint64_t entry_cpu=root_u+root_k;
    volatile unsigned long long warm=0;
    do {
        for(int i=0;i<10000;i++)warm=warm*1664525+1013904223;
        if(!diag_process_times(GetCurrentProcess(),&created,&root_u,&root_k))return 3;
    }while(root_u+root_k-entry_cpu<1250000);
    uint64_t before_u=root_u,before_k=root_k;
    HANDLE job=CreateJobObjectW(NULL,NULL);
    JOBOBJECT_BASIC_ACCOUNTING_INFORMATION before={},assigned={},finished={};
    if(!job || !QueryInformationJobObject(job,JobObjectBasicAccountingInformation,&before,sizeof(before),NULL) ||
       !AssignProcessToJobObject(job,GetCurrentProcess()) ||
       !QueryInformationJobObject(job,JobObjectBasicAccountingInformation,&assigned,sizeof(assigned),NULL))return 4;
    std::string name="Local\\pmux_diag_probe_"+std::to_string(GetCurrentProcessId())+"_"+std::to_string(created);
    HANDLE mapping=CreateFileMappingA(INVALID_HANDLE_VALUE,NULL,PAGE_READWRITE,0,sizeof(DiagShared),name.c_str());
    if(!mapping || GetLastError()==ERROR_ALREADY_EXISTS)return 5;
    DiagShared *shared=(DiagShared*)MapViewOfFile(mapping,FILE_MAP_ALL_ACCESS,0,0,sizeof(DiagShared));
    if(!shared)return 6;
    memset(shared,0,sizeof(*shared));shared->magic=DIAG_MAGIC;shared->root_pid=GetCurrentProcessId();shared->root_created=created;
    if(!SetEnvironmentVariableA("PMUX_CPU_DIAG_MAPPING",name.c_str()))return 7;
    DWORD pids[2];uint64_t child_c[2],child_u[2],child_k[2];
    struct ProcessList {DWORD assigned,count;ULONG_PTR pid[32];} lists[2]={};
    char images[2][32][MAX_PATH]={};
    for(int i=0;i<2;i++) {
        InterlockedExchange(&shared->current_call,i+1);
        char exe[MAX_PATH];if(!GetModuleFileNameA(NULL,exe,MAX_PATH))return 8;
        std::string command=std::string("\"")+exe+"\" child";
        STARTUPINFOA startup={};startup.cb=sizeof(startup);PROCESS_INFORMATION pi={};
        if(!CreateProcessA(NULL,&command[0],NULL,NULL,FALSE,CREATE_NO_WINDOW,NULL,NULL,&startup,&pi))return 9;
        pids[i]=pi.dwProcessId;
        // Observe once the child has actually executed, so startup helpers are
        // visible rather than querying immediately after CreateProcess.
        uint64_t observed_c,observed_u,observed_k;
        for(int retry=0;retry<500;retry++) {
            if(!diag_process_times(pi.hProcess,&observed_c,&observed_u,&observed_k))return 9;
            if(observed_u+observed_k>=1250000 || WaitForSingleObject(pi.hProcess,10)==WAIT_OBJECT_0)break;
        }
        if(!QueryInformationJobObject(job,JobObjectBasicProcessIdList,&lists[i],sizeof(lists[i]),NULL) || lists[i].count>32)return 9;
        for(DWORD n=0;n<lists[i].count;n++) {
            HANDLE observed=OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION,FALSE,(DWORD)lists[i].pid[n]);
            if(observed) {DWORD length=MAX_PATH;QueryFullProcessImageNameA(observed,0,images[i][n],&length);CloseHandle(observed);}
        }
        if(WaitForSingleObject(pi.hProcess,10000)!=WAIT_OBJECT_0)return 10;
        DWORD code;if(!GetExitCodeProcess(pi.hProcess,&code) || code)return 11;
        if(!diag_process_times(pi.hProcess,&child_c[i],&child_u[i],&child_k[i]))return 12;
        CloseHandle(pi.hThread);CloseHandle(pi.hProcess);
    }
    if(!QueryInformationJobObject(job,JobObjectBasicAccountingInformation,&finished,sizeof(finished),NULL))return 13;
    if(!diag_process_times(GetCurrentProcess(),&created,&root_u,&root_k))return 14;
    bool ok=!shared->errors && before.TotalProcesses==0 && assigned.TotalProcesses==1;
    FILE *f=fopen("probe.json","wb");if(!f)return 15;
    fprintf(f,"{\"pid\":%lu,\"created\":%llu,\"valid\":%s,\"before_assignment_processes\":%lu,\"after_assignment_processes\":%lu,\"final_inner_processes\":%lu,\"root_before_assignment_user\":%llu,\"root_before_assignment_kernel\":%llu,\"job_at_assignment_user\":%llu,\"job_at_assignment_kernel\":%llu,\"root_user\":%llu,\"root_kernel\":%llu,\"inner_user\":%llu,\"inner_kernel\":%llu,\"children\":[",
            GetCurrentProcessId(),(unsigned long long)created,ok?"true":"false",before.TotalProcesses,assigned.TotalProcesses,finished.TotalProcesses,
            (unsigned long long)before_u,(unsigned long long)before_k,(unsigned long long)assigned.TotalUserTime.QuadPart,(unsigned long long)assigned.TotalKernelTime.QuadPart,
            (unsigned long long)root_u,(unsigned long long)root_k,(unsigned long long)finished.TotalUserTime.QuadPart,(unsigned long long)finished.TotalKernelTime.QuadPart);
    for(int i=0;i<2;i++) {
        DiagAbcRecord &r=shared->records[i];
        if(r.ready!=2 || r.call_id!=(DWORD)(i+1) || r.pid!=pids[i] || r.created!=child_c[i] || r.end_user+r.end_kernel>child_u[i]+child_k[i])ok=false;
        fprintf(f,"%s{\"call_id\":%lu,\"pid\":%lu,\"created\":%llu,\"ready\":%ld,\"shared_total_ticks\":%llu,\"after_exit_total_ticks\":%llu}",
            i?",":"",r.call_id,r.pid,(unsigned long long)r.created,r.ready,(unsigned long long)(r.end_user+r.end_kernel),(unsigned long long)(child_u[i]+child_k[i]));
    }
    fprintf(f,"],\"live_snapshots\":[");
    for(int i=0;i<2;i++) {
        fprintf(f,"%s[",i?",":"");
        for(DWORD n=0;n<lists[i].count;n++) {
            std::string escaped;
            for(char c:std::string(images[i][n])) {if(c=='\\' || c=='\"')escaped+='\\';escaped+=c;}
            fprintf(f,"%s{\"pid\":%llu,\"image\":\"%s\"}",n?",":"",(unsigned long long)lists[i].pid[n],escaped.c_str());
        }
        fprintf(f,"]");
    }
    fprintf(f,"],\"shared_errors\":%ld,\"final_active_processes\":%lu,\"expected_children\":[{\"pid\":%lu,\"created\":%llu},{\"pid\":%lu,\"created\":%llu}]}\n",
            shared->errors,finished.ActiveProcesses,pids[0],(unsigned long long)child_c[0],pids[1],(unsigned long long)child_c[1]);
    bool written=!ferror(f);if(fclose(f)!=0)written=false;
    return ok && written ? 0:16;
}
