#ifdef _WIN32
#include "diag_v2_shared.h"
namespace {
struct V2Mark {std::string label;uint64_t ru=0,rk=0,ju=0,jk=0,qpc=0;DWORD total=0,active=0,error=0;};
struct V2Call {std::string command,tempdir;uint64_t user=0,kernel=0,ended=0,wait_qpc=0;DWORD error=0;int rc=-1;bool read=false;};
HANDLE v2job=NULL,v2mapping=NULL;V2Shared *v2data=NULL;
std::vector<V2Mark> v2marks;std::vector<V2Call> v2calls;
DWORD v2error=0;bool v2enabled=false,v2keep=false,v2skip=false;
std::string v2path;
std::string v2json(const std::string &s){std::string r="\"";for(unsigned char c:s){if(c=='\\'||c=='"'){r+='\\';r+=c;}else if(c<32){char b[7];snprintf(b,sizeof(b),"\\u%04x",c);r+=b;}else r+=c;}return r+'"';}
}
void diag_v2_mark(const char *label){
    if(!v2enabled)return;
    V2Mark m;m.label=label;FILETIME c,e,k,u;JOBOBJECT_BASIC_ACCOUNTING_INFORMATION j={};
    if(!GetProcessTimes(GetCurrentProcess(),&c,&e,&k,&u))m.error=GetLastError();
    else {m.ru=v2ft(u);m.rk=v2ft(k);}
    if(!QueryInformationJobObject(v2job,JobObjectBasicAccountingInformation,&j,sizeof(j),NULL))m.error=GetLastError();
    m.ju=j.TotalUserTime.QuadPart;m.jk=j.TotalKernelTime.QuadPart;m.total=j.TotalProcesses;m.active=j.ActiveProcesses;m.qpc=v2qpc();
    if(m.error)v2error=m.error;
    v2marks.push_back(m);
}
void diag_v2_bind(void *job){
    const char *path=getenv("PMUX_DIAG_V2_JSON");if(!path||!*path)return;
    v2job=job;v2enabled=true;v2path=path;v2marks.reserve(256);v2calls.reserve(V2_MAX_ABC);
    v2keep=getenv("PMUX_DIAG_V2_KEEP_ABC")&&strcmp(getenv("PMUX_DIAG_V2_KEEP_ABC"),"1")==0;
    v2skip=getenv("PMUX_DIAG_V2_SKIP_PASS")&&strcmp(getenv("PMUX_DIAG_V2_SKIP_PASS"),"1")==0;
    diag_v2_mark("main_entry");
    std::string name="Local\\pmux_diag_v2_"+std::to_string(GetCurrentProcessId())+"_"+std::to_string(v2qpc());
    v2mapping=CreateFileMappingA(INVALID_HANDLE_VALUE,NULL,PAGE_READWRITE,0,sizeof(V2Shared),name.c_str());
    if(!v2mapping||GetLastError()==ERROR_ALREADY_EXISTS){v2error=GetLastError()?GetLastError():ERROR_ALREADY_EXISTS;return;}
    v2data=(V2Shared*)MapViewOfFile(v2mapping,FILE_MAP_ALL_ACCESS,0,0,sizeof(V2Shared));if(!v2data){v2error=GetLastError();return;}
    memset(v2data,0,sizeof(*v2data));v2data->magic=V2_MAGIC;v2data->pid=GetCurrentProcessId();
    if(!SetEnvironmentVariableA("PMUX_DIAG_V2_MAPPING",name.c_str()))v2error=GetLastError();
}
bool diag_v2_skip(){return v2enabled&&v2skip;}
bool diag_v2_keep(){return v2enabled&&v2keep;}
void diag_v2_abc_begin(const std::string &command,const std::string &tempdir){
    if(!v2enabled)return;
    if(v2calls.size()>=V2_MAX_ABC){v2error=ERROR_INSUFFICIENT_BUFFER;return;}
    V2Call c;c.command=command;c.tempdir=tempdir;v2calls.push_back(c);
    if(v2data)InterlockedExchange(&v2data->current,(LONG)v2calls.size());
    diag_v2_mark("abc_call_begin");
}
void diag_v2_abc_end(int rc){
    if(!v2enabled||v2calls.empty())return;
    V2Call &c=v2calls.back();c.rc=rc;
    if(!v2data){c.error=ERROR_INVALID_HANDLE;return;}
    V2Abc &r=v2data->records[v2calls.size()-1];HANDLE h=(HANDLE)(uintptr_t)r.handle;
    if(!h||r.ready!=2){c.error=ERROR_INVALID_DATA;}
    else {DWORD wait=WaitForSingleObject(h,10000);c.wait_qpc=v2qpc();if(wait!=WAIT_OBJECT_0)c.error=wait==WAIT_FAILED?GetLastError():ERROR_TIMEOUT;
        else {FILETIME created,ended,k,u;if(!GetProcessTimes(h,&created,&ended,&k,&u))c.error=GetLastError();else if(v2ft(created)!=r.created)c.error=ERROR_INVALID_DATA;else{c.user=v2ft(u);c.kernel=v2ft(k);c.ended=v2ft(ended);c.read=true;}}CloseHandle(h);r.handle=0;}
    if(c.error)v2error=c.error;
    InterlockedExchange(&v2data->current,0);diag_v2_mark("abc_call_end");
}
void diag_v2_final(const void *ji,const void *ui,const void *ki){
    const auto &j=*(const JOBOBJECT_BASIC_ACCOUNTING_INFORMATION*)ji;const auto &u=*(const FILETIME*)ui;const auto &k=*(const FILETIME*)ki;
    if(!v2enabled)return;
    V2Mark m;m.label="final";m.ru=v2ft(u);m.rk=v2ft(k);m.ju=j.TotalUserTime.QuadPart;m.jk=j.TotalKernelTime.QuadPart;m.total=j.TotalProcesses;m.active=j.ActiveProcesses;m.qpc=v2qpc();v2marks.push_back(m);
}
bool diag_v2_write(){
    if(!v2enabled)return true;
    bool valid=!v2error&&v2data&&v2data->errors==0&&!v2marks.empty()&&v2marks.back().active==1;
    for(size_t i=0;i<v2calls.size();i++)if(!v2calls[i].read||v2calls[i].rc||v2data->records[i].error||v2data->records[i].exit_code)valid=false;
    FILE *f=fopen(v2path.c_str(),"wb");if(!f)return false;LARGE_INTEGER freq;QueryPerformanceFrequency(&freq);
    fprintf(f,"{\"schema\":2,\"valid\":%s,\"error\":%lu,\"skip_pass\":%s,\"keep_abc\":%s,\"qpc_frequency\":%llu,\"marks\":[",valid?"true":"false",v2error,v2skip?"true":"false",v2keep?"true":"false",(unsigned long long)freq.QuadPart);
    for(size_t i=0;i<v2marks.size();i++){auto &m=v2marks[i];fprintf(f,"%s{\"label\":%s,\"root_user\":%llu,\"root_kernel\":%llu,\"job_user\":%llu,\"job_kernel\":%llu,\"qpc\":%llu,\"TotalProcesses\":%lu,\"ActiveProcesses\":%lu,\"error\":%lu}",i?",":"",v2json(m.label).c_str(),(unsigned long long)m.ru,(unsigned long long)m.rk,(unsigned long long)m.ju,(unsigned long long)m.jk,(unsigned long long)m.qpc,m.total,m.active,m.error);}
    fprintf(f,"],\"abc\":[");for(size_t i=0;i<v2calls.size();i++){auto &c=v2calls[i];auto &r=v2data->records[i];std::string u=c.read?std::to_string(c.user):"null",k=c.read?std::to_string(c.kernel):"null";
        fprintf(f,"%s{\"id\":%lu,\"pid\":%lu,\"root_pid\":%lu,\"created\":%llu,\"ended\":%llu,\"user\":%s,\"kernel\":%s,\"entry_user\":%llu,\"entry_kernel\":%llu,\"body_end_user\":%llu,\"body_end_kernel\":%llu,\"entry_qpc\":%llu,\"body_end_qpc\":%llu,\"wait_qpc\":%llu,\"error\":%lu,\"entry_error\":%lu,\"rc\":%d,\"command\":%s,\"tempdir\":%s}",i?",":"",r.id,r.pid,GetCurrentProcessId(),(unsigned long long)r.created,(unsigned long long)c.ended,u.c_str(),k.c_str(),(unsigned long long)r.entry_user,(unsigned long long)r.entry_kernel,(unsigned long long)r.end_user,(unsigned long long)r.end_kernel,(unsigned long long)r.entry_qpc,(unsigned long long)r.end_qpc,(unsigned long long)c.wait_qpc,c.error,r.error,c.rc,v2json(c.command).c_str(),v2json(c.tempdir).c_str());}
    fprintf(f,"]}\n");bool written=!ferror(f);if(fclose(f)!=0)written=false;return valid&&written;
}
#endif
