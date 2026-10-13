// Common measurement-only patch, identical on both Yosys builds.
// Included in driver.cc after the Windows headers, outside the Yosys namespace.
#ifdef _WIN32
struct WindowsRuntimeCpu {
    HANDLE job = NULL;
    DWORD error = 0;
    WindowsRuntimeCpu() {
        job = CreateJobObjectW(NULL, NULL);
        if (!job || !AssignProcessToJobObject(job, GetCurrentProcess()))
            error = GetLastError();
    }
    bool write(const std::string &path) {
        JOBOBJECT_BASIC_ACCOUNTING_INFORMATION info = {};
        FILETIME creation = {}, exit = {}, kernel = {}, user = {};
        if (!error && !QueryInformationJobObject(job, JobObjectBasicAccountingInformation,
                &info, sizeof(info), NULL)) error = GetLastError();
        if (!error && !GetProcessTimes(GetCurrentProcess(), &creation, &exit, &kernel, &user))
            error = GetLastError();
        bool valid = !error && info.ActiveProcesses == 1 && info.TotalProcesses >= 1;
        // All children have been waited for by the synchronous synthesis flow.
        // The snapshot excludes writing this record and final OS teardown.
        FILE *f = fopen(path.c_str(), "wb");
        if (!f) return false;
        unsigned long long created = ((unsigned long long)creation.dwHighDateTime << 32) | creation.dwLowDateTime;
        fprintf(f, "{\"schema\":1,\"method\":\"windows-yosys-main-job-cpu-v1\","
                   "\"main_pid\":%lu,\"process_create_filetime\":%llu,"
                   "\"cpu_user_ticks\":%llu,\"cpu_kernel_ticks\":%llu,\"cpu_total_ticks\":%llu,"
                   "\"total_processes\":%lu,\"active_processes\":%lu,\"valid\":%s,\"error\":%s,\"win32_error\":%lu}\n",
                GetCurrentProcessId(), created,
                (unsigned long long)info.TotalUserTime.QuadPart,
                (unsigned long long)info.TotalKernelTime.QuadPart,
                (unsigned long long)(info.TotalUserTime.QuadPart + info.TotalKernelTime.QuadPart),
                info.TotalProcesses, info.ActiveProcesses, valid ? "true" : "false",
                valid ? "null" : "\"job accounting failed or descendants still active\"", error);
        bool written = !ferror(f);
        if (fclose(f) != 0) written = false;
        return valid && written;
    }
};
#endif
