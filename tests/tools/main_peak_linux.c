// Linux diagnostic only: address-space peak RSS after exec, excluding children.
#include <stdio.h>
#include <unistd.h>
#include <sys/resource.h>
__attribute__((destructor)) static void report_peak(void) {
    long peak = -1;
    FILE *status = fopen("/proc/self/status", "r");
    if (status) {
        char line[256];
        while (fgets(line, sizeof line, status))
            if (sscanf(line, "VmHWM: %ld kB", &peak) == 1) break;
        fclose(status);
    }
    struct rusage usage;
    long inherited = getrusage(RUSAGE_SELF, &usage) == 0 ? usage.ru_maxrss : -1;
    char message[160];
    int n = snprintf(message, sizeof message, "\nMAIN_PEAK_SELF pid=%ld kib=%ld ru_kib=%ld\n",
                     (long)getpid(), peak, inherited);
    if (n > 0 && n < (int)sizeof message) write(2, message, n);
}
