// A small method selfcheck, not an algorithm/stress/performance test case.
#include <windows.h>
#include <cstdio>
#include <string>
#include "runtime_cpu_windows.inc"
int main(int argc, char **argv) {
    if (argc > 1) {
        // Spend CPU, not sleep; stop after 0.25 seconds of process CPU.
        FILETIME c,e,k,u;
        volatile unsigned long long v=0;
        do {
            for (int i=0;i<10000;i++) v=v*1664525+1013904223;
            if (!GetProcessTimes(GetCurrentProcess(),&c,&e,&k,&u)) return 2;
        } while ((((unsigned long long)k.dwHighDateTime<<32)|k.dwLowDateTime)+
                 (((unsigned long long)u.dwHighDateTime<<32)|u.dwLowDateTime)<2500000);
        return 0;
    }
    WindowsRuntimeCpu cpu;
    if (cpu.error) return 3;
    char path[MAX_PATH]; if (!GetModuleFileNameA(NULL,path,MAX_PATH)) return 4;
    std::string command=std::string("\"")+path+"\" child";
    STARTUPINFOA start={};start.cb=sizeof(start); PROCESS_INFORMATION process={};
    if (!CreateProcessA(NULL,&command[0],NULL,NULL,FALSE,0,NULL,NULL,&start,&process)) return 5;
    if (WaitForSingleObject(process.hProcess,10000)!=WAIT_OBJECT_0) return 6;
    DWORD code;GetExitCodeProcess(process.hProcess,&code);
    CloseHandle(process.hThread);CloseHandle(process.hProcess);
    if (code) return 7;
    return cpu.write("runtime.json") ? 0 : 8;
}
