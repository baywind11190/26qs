# This batch is invalid for peak-memory acceptance

The measurement parent hashed complete ~28MB binaries using read_bytes(), reaching 45448 KiB. Its children inherited that resource high-water mark, and getrusage(RUSAGE_SELF).ru_maxrss reported 45448 KiB for every case. The identical zero-percent memory changes are not valid main-Yosys post-exec peaks.

No algorithm change was made. The corrected runner hashes in chunks and the diagnostic library reads VmHWM from the executing process address space. The corrected batch is final_performance_corrected. This batch is retained, not silently replaced or selected on score.
