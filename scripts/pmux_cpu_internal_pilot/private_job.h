// Frozen PHNT declarations, commit 53fbbdc5b5d2b08761db1c7b26bfa8c820924356.
// See source_refs/identity.json and LICENSE. Experimental Windows x64 ABI only.
// Fields follow ntexapi.h PROCESS_DISK_COUNTERS/PROCESS_ENERGY_VALUES and
// ntpsapi.h JOBOBJECT_EXTENDED_ACCOUNTING_INFORMATION, not guessed offsets.
#pragma once
#include <windows.h>
#include <cstddef>
#include <cstring>

struct PilotDiskCounters {
    ULONGLONG BytesRead, BytesWritten, ReadOperationCount, WriteOperationCount, FlushOperationCount;
};
union PilotEnergyDuration {
    ULONGLONG Value;
    struct { ULONG LastChangeTime; ULONG Duration:31; ULONG IsInState:1; } Parts;
};
struct PilotEnergyValues {
    ULONGLONG Cycles[4][2];
    ULONGLONG DiskEnergy, NetworkTailEnergy, MBBTailEnergy, NetworkTxRxBytes, MBBTxRxBytes;
    PilotEnergyDuration Durations[3];
    ULONG CompositionRendered, CompositionDirtyGenerated, CompositionDirtyPropagated, Reserved1;
    ULONGLONG AttributedCycles[4][2];
    ULONGLONG WorkOnBehalfCycles[4][2];
};
struct PilotJobExtendedAccounting {
    JOBOBJECT_BASIC_ACCOUNTING_INFORMATION BasicInfo;
    IO_COUNTERS IoInfo;
    PilotDiskCounters DiskIoInfo;
    ULONG64 ContextSwitches;
    LARGE_INTEGER TotalCycleTime;
    ULONG64 ReadyTime;
    PilotEnergyValues EnergyValues;
};
static_assert(sizeof(void*) == 8, "frozen x64 ABI required");
static_assert(sizeof(PilotDiskCounters) == 40, "PHNT disk layout");
static_assert(sizeof(PilotEnergyValues) == 272, "PHNT energy layout");
static_assert(offsetof(PilotJobExtendedAccounting,TotalCycleTime) == 144, "PHNT cycle layout");
static_assert(sizeof(PilotJobExtendedAccounting) == 432, "PHNT complete accounting layout");

using PilotNtQueryJob = LONG (WINAPI *)(HANDLE, int, PVOID, ULONG, PULONG);
inline LONG pilot_query_job(HANDLE job, PilotJobExtendedAccounting &row, ULONG &returned) {
    FARPROC address=GetProcAddress(GetModuleHandleW(L"ntdll.dll"),"NtQueryInformationJobObject");
    PilotNtQueryJob query=nullptr;
    static_assert(sizeof(query)==sizeof(address),"Windows function pointer ABI");
    std::memcpy(&query,&address,sizeof(query));
    if (!query) return LONG(0xc0000002);
    returned=0;
    return query(job,19,&row,sizeof(row),&returned);
}
