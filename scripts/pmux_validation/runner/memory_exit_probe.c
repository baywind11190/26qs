#include <windows.h>
#include <psapi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void *allocate_touch(size_t mb) {
    size_t size = mb * 1024 * 1024;
    volatile unsigned char *p = VirtualAlloc(NULL, size, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    if (!p) ExitProcess(90);
    for (size_t i = 0; i < size; i += 4096) p[i] = 1;
    return (void *)p;
}

int main(int argc, char **argv) {
    const char *mode = argc > 1 ? argv[1] : "burst";
    SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX);
    if (!strcmp(mode, "empty")) return 0;
    if (!strcmp(mode, "child")) {
        void *p = allocate_touch(128);
        printf("CHILD_DEBUGGED=%d\n", IsDebuggerPresent()); fflush(stdout);
        ULONGLONG until = GetTickCount64() + 250;
        volatile size_t value = 0;
        while (GetTickCount64() < until) ++value;
        VirtualFree(p, 0, MEM_RELEASE);
        return 0;
    }
    if (!strcmp(mode, "tiny")) Sleep(25);
    void *p = allocate_touch(!strcmp(mode, "parent") ? 12 : !strcmp(mode, "tiny") ? 4 : 96);
    if (!strcmp(mode, "parent")) {
        STARTUPINFOA si = {0}; si.cb = sizeof(si);
        si.dwFlags = STARTF_USESTDHANDLES;
        si.hStdInput = GetStdHandle(STD_INPUT_HANDLE);
        si.hStdOutput = GetStdHandle(STD_OUTPUT_HANDLE);
        si.hStdError = GetStdHandle(STD_ERROR_HANDLE);
        PROCESS_INFORMATION pi = {0};
        char command[4096]; snprintf(command, sizeof(command), "\"%s\" child", argv[0]);
        if (!CreateProcessA(argv[0], command, NULL, NULL, TRUE, CREATE_NO_WINDOW, NULL, NULL, &si, &pi)) return 91;
        WaitForSingleObject(pi.hProcess, INFINITE);
        CloseHandle(pi.hThread); CloseHandle(pi.hProcess);
    }
    if (!strcmp(mode, "late")) Sleep(40);
    // Independent reference, recorded after all output buffering is initialized.
    printf("ROOT_DEBUGGED=%d\n", IsDebuggerPresent()); fflush(stdout);
    PROCESS_MEMORY_COUNTERS counters = {0}; counters.cb = sizeof(counters);
    if (!GetProcessMemoryInfo(GetCurrentProcess(), &counters, sizeof(counters))) return 92;
    printf("SELF_PEAK=%llu\n", (unsigned long long)counters.PeakWorkingSetSize); fflush(stdout);
    VirtualFree(p, 0, MEM_RELEASE);
    if (!strcmp(mode, "terminate")) TerminateProcess(GetCurrentProcess(), 3);
    if (!strcmp(mode, "thread")) ExitThread(0);
    if (!strcmp(mode, "crash")) *(volatile int *)0 = 1;
    if (!strcmp(mode, "breakpoint")) DebugBreak();
    if (!strcmp(mode, "timeout")) Sleep(10000);
    return 0;
}
