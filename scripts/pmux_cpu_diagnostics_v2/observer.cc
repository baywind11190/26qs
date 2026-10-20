// Ordinary (non-debugged) launches. All observation work stays outside the Job.
#define _WIN32_WINNT 0x0602
#include <windows.h>
#include <tlhelp32.h>
#include <algorithm>
#include <cstdio>
#include <cstdint>
#include <string>
#include <vector>
#include <map>
#include <set>
#include <thread>
#include <mutex>

using U=unsigned long long;
U ft(FILETIME f){return (U(f.dwHighDateTime)<<32)|f.dwLowDateTime;}
U qpc(){LARGE_INTEGER v;QueryPerformanceCounter(&v);return v.QuadPart;}
std::string utf8(const std::wstring &s){if(s.empty())return "";int n=WideCharToMultiByte(CP_UTF8,0,s.c_str(),int(s.size()),NULL,0,NULL,NULL);std::string r(n,' ');WideCharToMultiByte(CP_UTF8,0,s.c_str(),int(s.size()),&r[0],n,NULL,NULL);return r;}
std::string js(const std::string &s){std::string o="\"";for(unsigned char c:s){if(c=='\\'||c=='\"'){o+='\\';o+=c;}else if(c<32){char b[7];snprintf(b,sizeof(b),"\\u%04x",c);o+=b;}else o+=c;}return o+'"';}
std::wstring quote(const std::wstring &v){std::wstring r=L"\"";int n=0;for(wchar_t c:v){if(c==L'\\')n++;else{if(c==L'"')r.append(n*2+1,L'\\');else r.append(n,L'\\');n=0;r+=c;}}r.append(n*2,L'\\');return r+L'"';}
struct Proc {DWORD pid=0,ppid=0,error=0,module_error=0,exit_code=STILL_ACTIVE;HANDLE h=NULL;U created=0,user=0,kernel=0,ended=0,seen=0;bool read=false;std::string image;std::set<std::string> modules;};
std::vector<Proc> procs;std::vector<std::pair<DWORD,DWORD>> open_errors;std::mutex mx;
DWORD parent(DWORD pid){DWORD p=0;HANDLE s=CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS,0);if(s!=INVALID_HANDLE_VALUE){PROCESSENTRY32W e={};e.dwSize=sizeof(e);if(Process32FirstW(s,&e))do{if(e.th32ProcessID==pid){p=e.th32ParentProcessID;break;}}while(Process32NextW(s,&e));CloseHandle(s);}return p;}
void modules(Proc &p){HANDLE s=CreateToolhelp32Snapshot(TH32CS_SNAPMODULE|TH32CS_SNAPMODULE32,p.pid);if(s==INVALID_HANDLE_VALUE){p.module_error=GetLastError();return;}MODULEENTRY32W e={};e.dwSize=sizeof(e);if(Module32FirstW(s,&e)){do{p.modules.insert(utf8(e.szExePath));}while(Module32NextW(s,&e));p.module_error=0;}else p.module_error=GetLastError();CloseHandle(s);}
void add(DWORD pid,HANDLE owned=NULL){std::lock_guard<std::mutex> lock(mx);HANDLE h=owned?owned:OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION|SYNCHRONIZE,FALSE,pid);if(!h){open_errors.push_back({pid,GetLastError()});return;}FILETIME c,e,k,u;if(!GetProcessTimes(h,&c,&e,&k,&u)){DWORD er=GetLastError();if(!owned)CloseHandle(h);open_errors.push_back({pid,er});return;}U created=ft(c);for(auto &p:procs)if(p.pid==pid&&p.created==created){if(!owned)CloseHandle(h);return;}Proc p;p.pid=pid;p.created=created;p.h=h;p.seen=qpc();p.ppid=parent(pid);wchar_t b[32768];DWORD n=32768;if(QueryFullProcessImageNameW(h,0,b,&n))p.image=utf8(std::wstring(b,n));else p.error=GetLastError();modules(p);procs.push_back(p);}
void snapshot(HANDLE job){DWORD size=4096;std::vector<char> buf(size);auto p=(JOBOBJECT_BASIC_PROCESS_ID_LIST*)buf.data();if(!QueryInformationJobObject(job,JobObjectBasicProcessIdList,p,size,NULL)){DWORD er=GetLastError();if(er!=ERROR_MORE_DATA)return;size=sizeof(*p)+sizeof(ULONG_PTR)*p->NumberOfAssignedProcesses;buf.resize(size);p=(JOBOBJECT_BASIC_PROCESS_ID_LIST*)buf.data();if(!QueryInformationJobObject(job,JobObjectBasicProcessIdList,p,size,NULL))return;}for(DWORD i=0;i<p->NumberOfProcessIdsInList;i++)add(DWORD(p->ProcessIdList[i]));}
std::string environment(){FILETIME idle,kernel,user;MEMORYSTATUSEX m={};m.dwLength=sizeof(m);bool s=GetSystemTimes(&idle,&kernel,&user)!=0;bool mem=GlobalMemoryStatusEx(&m)!=0;char b[400];snprintf(b,sizeof(b),"{\"system_times_valid\":%s,\"idle\":%llu,\"kernel\":%llu,\"user\":%llu,\"available_memory_bytes\":%llu,\"memory_valid\":%s}",s?"true":"false",s?ft(idle):0,s?ft(kernel):0,s?ft(user):0,mem?U(m.ullAvailPhys):0,mem?"true":"false");return b;}
int wmain(int argc,wchar_t **argv){
    if(argc<6){fwprintf(stderr,L"observer out.json run.log cwd timeout_ms exe arguments...\n");return 2;}
    U begin=qpc();std::string before=environment();DWORD error=0;bool timed_out=false;
    LARGE_INTEGER freq;QueryPerformanceFrequency(&freq);
    HANDLE job=CreateJobObjectW(NULL,NULL);HANDLE port=CreateIoCompletionPort(INVALID_HANDLE_VALUE,NULL,0,1);
    if(!job||!port)return 3;
    JOBOBJECT_ASSOCIATE_COMPLETION_PORT assoc={};assoc.CompletionKey=job;assoc.CompletionPort=port;
    if(!SetInformationJobObject(job,JobObjectAssociateCompletionPortInformation,&assoc,sizeof(assoc)))return 4;
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION limits={};limits.BasicLimitInformation.LimitFlags=JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
    if(!SetInformationJobObject(job,JobObjectExtendedLimitInformation,&limits,sizeof(limits)))return 5;
    JOBOBJECT_BASIC_ACCOUNTING_INFORMATION initial={},final={};
    if(!QueryInformationJobObject(job,JobObjectBasicAccountingInformation,&initial,sizeof(initial),NULL))return 6;
    SECURITY_ATTRIBUTES sa={sizeof(sa),NULL,TRUE};
    HANDLE log=CreateFileW(argv[2],GENERIC_WRITE,FILE_SHARE_READ,&sa,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,NULL);
    HANDLE nul=CreateFileW(L"NUL",GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_WRITE,&sa,OPEN_EXISTING,0,NULL);
    if(log==INVALID_HANDLE_VALUE||nul==INVALID_HANDLE_VALUE)return 7;
    STARTUPINFOW si={};si.cb=sizeof(si);si.dwFlags=STARTF_USESTDHANDLES;si.hStdInput=nul;si.hStdOutput=si.hStdError=log;
    std::wstring cmd;for(int i=5;i<argc;i++){if(i>5)cmd+=L' ';cmd+=quote(argv[i]);}
    PROCESS_INFORMATION pi={};U create_begin=qpc();
    if(!CreateProcessW(argv[5],&cmd[0],NULL,NULL,TRUE,CREATE_SUSPENDED|CREATE_NO_WINDOW,NULL,argv[3],&si,&pi))return 8;
    if(!AssignProcessToJobObject(job,pi.hProcess)){TerminateProcess(pi.hProcess,9);return 9;}
    add(pi.dwProcessId,pi.hProcess);
    std::thread watcher([&](){while(true){DWORD msg=0;ULONG_PTR key=0;LPOVERLAPPED ov=NULL;BOOL ok=GetQueuedCompletionStatus(port,&msg,&key,&ov,20);if(key==1)break;if(ok&&msg==JOB_OBJECT_MSG_NEW_PROCESS)add(DWORD(ULONG_PTR(ov)));snapshot(job);std::lock_guard<std::mutex> l(mx);for(auto &p:procs)if(WaitForSingleObject(p.h,0)==WAIT_TIMEOUT)modules(p);}});
    U resume=qpc();if(ResumeThread(pi.hThread)==DWORD(-1)){error=GetLastError();TerminateJobObject(job,10);}
    DWORD timeout=wcstoul(argv[4],NULL,10);U deadline=resume+U(timeout)*freq.QuadPart/1000;
    while(true){if(!QueryInformationJobObject(job,JobObjectBasicAccountingInformation,&final,sizeof(final),NULL)){error=GetLastError();TerminateJobObject(job,11);break;}if(final.ActiveProcesses==0)break;if(qpc()>deadline){timed_out=true;TerminateJobObject(job,124);break;}Sleep(2);}
    if(timed_out||error){WaitForSingleObject(pi.hProcess,5000);for(int i=0;i<500;i++){if(QueryInformationJobObject(job,JobObjectBasicAccountingInformation,&final,sizeof(final),NULL)&&final.ActiveProcesses==0)break;Sleep(10);}}
    U ended=qpc();PostQueuedCompletionStatus(port,0,1,NULL);watcher.join();
    if(!QueryInformationJobObject(job,JobObjectBasicAccountingInformation,&final,sizeof(final),NULL))error=GetLastError();
    std::string after=environment();DWORD root_rc=STILL_ACTIVE;if(!GetExitCodeProcess(pi.hProcess,&root_rc))error=GetLastError();
    bool complete=procs.size()==final.TotalProcesses;
    for(auto &p:procs){FILETIME c,e,k,u;DWORD w=WaitForSingleObject(p.h,0);if(w!=WAIT_OBJECT_0){p.error=w==WAIT_FAILED?GetLastError():ERROR_IO_INCOMPLETE;complete=false;continue;}if(!GetProcessTimes(p.h,&c,&e,&k,&u)){p.error=GetLastError();complete=false;continue;}if(ft(c)!=p.created){p.error=ERROR_INVALID_DATA;complete=false;continue;}p.user=ft(u);p.kernel=ft(k);p.ended=ft(e);p.read=true;if(!GetExitCodeProcess(p.h,&p.exit_code)){p.error=GetLastError();complete=false;}}
    FILE *f=_wfopen(argv[1],L"wb");if(!f)return 12;
    bool valid=!error&&!timed_out&&final.ActiveProcesses==0&&initial.TotalProcesses==0&&initial.TotalUserTime.QuadPart==0&&initial.TotalKernelTime.QuadPart==0;
    fprintf(f,"{\"schema\":2,\"root_pid\":%lu,\"root_debugged\":false,\"rc\":%lu,\"timed_out\":%s,\"error\":%lu,\"job_total_valid\":%s,\"process_accounting_complete\":%s,\"initial_total_processes\":%lu,\"initial_user\":%llu,\"initial_kernel\":%llu,\"user\":%llu,\"kernel\":%llu,\"TotalProcesses\":%lu,\"ActiveProcesses\":%lu,\"qpc_frequency\":%llu,\"wrapper_begin_qpc\":%llu,\"create_begin_qpc\":%llu,\"resume_qpc\":%llu,\"job_empty_qpc\":%llu,\"environment_before\":%s,\"environment_after\":%s,\"processes\":[",pi.dwProcessId,root_rc,timed_out?"true":"false",error,valid?"true":"false",complete?"true":"false",initial.TotalProcesses,U(initial.TotalUserTime.QuadPart),U(initial.TotalKernelTime.QuadPart),U(final.TotalUserTime.QuadPart),U(final.TotalKernelTime.QuadPart),final.TotalProcesses,final.ActiveProcesses,U(freq.QuadPart),begin,create_begin,resume,ended,before.c_str(),after.c_str());
    for(size_t i=0;i<procs.size();i++){auto &p=procs[i];std::string user=p.read?std::to_string(p.user):"null",kernel=p.read?std::to_string(p.kernel):"null";fprintf(f,"%s{\"pid\":%lu,\"ppid\":%lu,\"created\":%llu,\"ended\":%llu,\"seen_qpc\":%llu,\"image\":%s,\"user\":%s,\"kernel\":%s,\"exit_code\":%lu,\"read_error\":%lu,\"module_snapshot_error\":%lu,\"modules_observed_not_exhaustive\":[",i?",":"",p.pid,p.ppid,p.created,p.ended,p.seen,js(p.image).c_str(),user.c_str(),kernel.c_str(),p.exit_code,p.error,p.module_error);int n=0;for(auto &s:p.modules)fprintf(f,"%s%s",n++?",":"",js(s).c_str());fprintf(f,"]}");}
    fprintf(f,"],\"open_errors\":[");for(size_t i=0;i<open_errors.size();i++)fprintf(f,"%s{\"pid\":%lu,\"api\":\"OpenProcess/GetProcessTimes\",\"error\":%lu}",i?",":"",open_errors[i].first,open_errors[i].second);fprintf(f,"],\"wrapper_end_qpc\":%llu}\n",qpc());bool written=!ferror(f)&&fclose(f)==0;
    for(auto &p:procs)CloseHandle(p.h);CloseHandle(pi.hThread);CloseHandle(log);CloseHandle(nul);CloseHandle(job);CloseHandle(port);
    return valid&&written?0:1;
}
