#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdio>
#include <cstring>

int main(int argc, char **argv)
{
    if (argc != 2) return 90;
    if (strcmp(argv[1], "--child") == 0) {
        Sleep(INFINITE);
        return 91;
    }
    if (strcmp(argv[1], "--delayed") == 0) {
        std::printf("probe-start\n");
        std::fprintf(stderr, "probe-error-stream-start\n");
        std::fflush(stdout);
        std::fflush(stderr);
        Sleep(350);
        HANDLE marker = CreateFileW(L"late.marker", GENERIC_WRITE, 0, NULL,
                                    CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
        if (marker == INVALID_HANDLE_VALUE) return 92;
        const char value[] = "complete-before-exit";
        DWORD written = 0;
        BOOL ok = WriteFile(marker, value, sizeof(value) - 1, &written, NULL);
        CloseHandle(marker);
        if (!ok || written != sizeof(value) - 1) return 93;
        std::printf("probe-late-output\n");
        std::fprintf(stderr, "probe-error-stream-end\n");
        std::fflush(stdout);
        std::fflush(stderr);
        return 0;
    }
    if (strcmp(argv[1], "--large") == 0) {
        char block[4096];
        std::memset(block, 'O', sizeof(block));
        for (int i = 0; i < 256; ++i) {
            if (std::fwrite(block, 1, sizeof(block), stdout) != sizeof(block)) return 94;
            if (std::fwrite(block, 1, sizeof(block), stderr) != sizeof(block)) return 95;
        }
        std::fflush(stdout);
        std::fflush(stderr);
        return 0;
    }
    if (strcmp(argv[1], "--fail") == 0) {
        std::fprintf(stderr, "intentional-native-exit-7\n");
        std::fflush(stderr);
        return 7;
    }
    if (strcmp(argv[1], "--tree") == 0) {
        wchar_t executable[MAX_PATH];
        DWORD length = GetModuleFileNameW(NULL, executable, MAX_PATH);
        if (!length || length >= MAX_PATH) return 96;
        wchar_t command[MAX_PATH + 32];
        if (swprintf(command, sizeof(command) / sizeof(command[0]),
                     L"\"%ls\" --child", executable) < 0) return 97;
        STARTUPINFOW startup = {};
        PROCESS_INFORMATION child = {};
        startup.cb = sizeof(startup);
        if (!CreateProcessW(executable, command, NULL, NULL, FALSE,
                            CREATE_NO_WINDOW, NULL, NULL, &startup, &child)) return 98;
        CloseHandle(child.hThread);
        FILE *pid_file = std::fopen("child.pid", "wb");
        if (!pid_file) {
            TerminateProcess(child.hProcess, 99);
            CloseHandle(child.hProcess);
            return 99;
        }
        std::fprintf(pid_file, "%lu\n", static_cast<unsigned long>(child.dwProcessId));
        std::fclose(pid_file);
        CloseHandle(child.hProcess);
        Sleep(INFINITE);
        return 100;
    }
    return 101;
}
