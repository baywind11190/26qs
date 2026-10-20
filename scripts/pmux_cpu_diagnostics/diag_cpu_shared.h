#ifndef PMUX_DIAG_CPU_SHARED_H
#define PMUX_DIAG_CPU_SHARED_H
#include <windows.h>
#include <stdint.h>
#include <stdlib.h>
#define DIAG_MAGIC 0x504d4451u
#define DIAG_MAX_ABC 64
typedef struct {
    volatile LONG ready;
    DWORD call_id, pid;
    uint64_t created, start_user, start_kernel, end_user, end_kernel;
    int exit_code;
} DiagAbcRecord;
typedef struct {
    DWORD magic, root_pid;
    uint64_t root_created;
    volatile LONG current_call, errors;
    DiagAbcRecord records[DIAG_MAX_ABC];
} DiagShared;
static uint64_t diag_filetime(FILETIME t) {
    return ((uint64_t)t.dwHighDateTime << 32) | t.dwLowDateTime;
}
static int diag_process_times(HANDLE p, uint64_t *created, uint64_t *user, uint64_t *kernel) {
    FILETIME c,e,k,u;
    if (!GetProcessTimes(p,&c,&e,&k,&u)) return 0;
    *created=diag_filetime(c); *user=diag_filetime(u); *kernel=diag_filetime(k);
    return 1;
}
// ABC uses the original main/launcher. Only a bounded in-memory record is added.
static DiagShared *diag_abc_shared = NULL;
static HANDLE diag_abc_mapping = NULL;
static DiagAbcRecord *diag_abc_record = NULL;
static inline void diag_abc_entry(void) {
    const char *name=getenv("PMUX_CPU_DIAG_MAPPING");
    if (!name || !*name) return;
    diag_abc_mapping=OpenFileMappingA(FILE_MAP_ALL_ACCESS,FALSE,name);
    if (!diag_abc_mapping) return;
    diag_abc_shared=(DiagShared*)MapViewOfFile(diag_abc_mapping,FILE_MAP_ALL_ACCESS,0,0,sizeof(DiagShared));
    if (!diag_abc_shared || diag_abc_shared->magic!=DIAG_MAGIC) return;
    LONG id=diag_abc_shared->current_call;
    if (id<1 || id>DIAG_MAX_ABC) { InterlockedIncrement(&diag_abc_shared->errors); return; }
    DiagAbcRecord *r=&diag_abc_shared->records[id-1];
    if (InterlockedCompareExchange(&r->ready,1,0)!=0) { InterlockedIncrement(&diag_abc_shared->errors); return; }
    diag_abc_record=r; r->call_id=(DWORD)id; r->pid=GetCurrentProcessId();
    if (!diag_process_times(GetCurrentProcess(),&r->created,&r->start_user,&r->start_kernel))
        InterlockedIncrement(&diag_abc_shared->errors);
}
static inline void diag_abc_exit(int result) {
    if (!diag_abc_record) return;
    uint64_t created;
    if (!diag_process_times(GetCurrentProcess(),&created,&diag_abc_record->end_user,&diag_abc_record->end_kernel) || created!=diag_abc_record->created)
        InterlockedIncrement(&diag_abc_shared->errors);
    diag_abc_record->exit_code=result;
    InterlockedExchange(&diag_abc_record->ready,2);
    // OS closes the mapping at exit. No files or diagnostic stdout are written.
}
#endif
