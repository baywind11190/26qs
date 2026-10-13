/* Fixed work, never clock-conditioned on the counter being calibrated. */
#define UNICODE
#define _UNICODE
#include <windows.h>
#include <stdio.h>
#include <wchar.h>
#include <stdint.h>
#include <stdlib.h>
static uint64_t burn(uint64_t count) {
    volatile uint64_t value=1;
    for(uint64_t i=0;i<count;i++) value=value*1664525u+1013904223u;
    return value;
}
int wmain(int argc,wchar_t **argv) {
    if(argc==3 && !wcscmp(argv[1],L"--child")) { burn(_wcstoui64(argv[2],NULL,10));return 0; }
    if(argc!=2)return 2;
    uint64_t child=75000000;
    if(!wcscmp(argv[1],L"--small"))child=80000000;
    else if(!wcscmp(argv[1],L"--large"))child=95000000;
    else if(wcscmp(argv[1],L"--base"))return 2;
    uint64_t value=burn(25000000);
    wchar_t image[32768],command[32832];
    if(!GetModuleFileNameW(NULL,image,32768))return 3;
    swprintf(command,32832,L"\"%ls\" --child %llu",image,(unsigned long long)child);
    STARTUPINFOW startup={0};startup.cb=sizeof(startup);
    PROCESS_INFORMATION process={0};
    if(!CreateProcessW(image,command,NULL,NULL,TRUE,CREATE_NO_WINDOW,NULL,NULL,&startup,&process))return 4;
    if(WaitForSingleObject(process.hProcess,30000)!=WAIT_OBJECT_0) {TerminateProcess(process.hProcess,5);return 5;}
    DWORD exit_code=6;GetExitCodeProcess(process.hProcess,&exit_code);
    CloseHandle(process.hThread);CloseHandle(process.hProcess);
    printf("fixed root=25000000 child=%llu checksum=%llu\n",(unsigned long long)child,(unsigned long long)value);
    return (int)exit_code;
}
