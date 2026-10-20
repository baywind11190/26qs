#ifndef PMUX_DIAG_V2_SHARED_H
#define PMUX_DIAG_V2_SHARED_H
#include <windows.h>
#include <stdint.h>
#include <stdlib.h>
#define V2_MAGIC 0x504d5632u
#define V2_MAX_ABC 64
typedef struct {volatile LONG ready;DWORD id,pid,error;uint64_t created,entry_user,entry_kernel,end_user,end_kernel,handle,entry_qpc,end_qpc;int exit_code;} V2Abc;
typedef struct {DWORD magic,pid;volatile LONG current,errors;V2Abc records[V2_MAX_ABC];} V2Shared;
static inline uint64_t v2ft(FILETIME f){return ((uint64_t)f.dwHighDateTime<<32)|f.dwLowDateTime;}
static inline uint64_t v2qpc(void){LARGE_INTEGER v;QueryPerformanceCounter(&v);return (uint64_t)v.QuadPart;}
static V2Shared *v2shared=NULL;
static V2Abc *v2record=NULL;
static inline void v2abc_entry(void){
    const char *name=getenv("PMUX_DIAG_V2_MAPPING");if(!name||!*name)return;
    HANDLE m=OpenFileMappingA(FILE_MAP_ALL_ACCESS,FALSE,name);if(!m)return;
    v2shared=(V2Shared*)MapViewOfFile(m,FILE_MAP_ALL_ACCESS,0,0,sizeof(V2Shared));
    if(!v2shared||v2shared->magic!=V2_MAGIC)return;
    LONG n=v2shared->current;if(n<1||n>V2_MAX_ABC){InterlockedIncrement(&v2shared->errors);return;}
    v2record=&v2shared->records[n-1];
    if(InterlockedCompareExchange(&v2record->ready,1,0)!=0){InterlockedIncrement(&v2shared->errors);return;}
    v2record->id=(DWORD)n;v2record->pid=GetCurrentProcessId();v2record->entry_qpc=v2qpc();
    FILETIME c,e,k,u;if(GetProcessTimes(GetCurrentProcess(),&c,&e,&k,&u)){v2record->created=v2ft(c);v2record->entry_user=v2ft(u);v2record->entry_kernel=v2ft(k);}else v2record->error=GetLastError();
    HANDLE root=OpenProcess(PROCESS_DUP_HANDLE,FALSE,v2shared->pid),copy=NULL;
    if(!root)v2record->error=GetLastError();
    else {if(!DuplicateHandle(GetCurrentProcess(),GetCurrentProcess(),root,&copy,PROCESS_QUERY_LIMITED_INFORMATION|SYNCHRONIZE,FALSE,0))v2record->error=GetLastError();else v2record->handle=(uint64_t)(uintptr_t)copy;CloseHandle(root);}
}
static inline void v2abc_exit(int code){
    if(!v2record)return;
    FILETIME c,e,k,u;
    if(GetProcessTimes(GetCurrentProcess(),&c,&e,&k,&u)&&v2ft(c)==v2record->created){v2record->end_user=v2ft(u);v2record->end_kernel=v2ft(k);}else v2record->error=GetLastError()?GetLastError():ERROR_INVALID_DATA;
    v2record->exit_code=code;v2record->end_qpc=v2qpc();InterlockedExchange(&v2record->ready,2);
}
#endif
