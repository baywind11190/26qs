#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Windows Job Object CPU and root exit-event peak working set measurement."""
from __future__ import annotations

import ctypes
import os
import shutil
import subprocess
import time
from ctypes import wintypes
from pathlib import Path


CREATE_SUSPENDED = 0x00000004
CREATE_UNICODE_ENVIRONMENT = 0x00000400
CREATE_NO_WINDOW = 0x08000000
STARTF_USESTDHANDLES = 0x00000100
GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
CREATE_NEW = 1
OPEN_EXISTING = 3
FILE_ATTRIBUTE_NORMAL = 0x00000080
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS = 9
JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION_CLASS = 1
WAIT_OBJECT_0 = 0
WAIT_TIMEOUT = 0x00000102
INFINITE = 0xFFFFFFFF
_INVALID_HANDLE = ctypes.c_void_p(-1).value
_TICKS_PER_SECOND = 10_000_000
DEBUG_ONLY_THIS_PROCESS = 0x00000002
EXCEPTION_DEBUG_EVENT = 1
CREATE_PROCESS_DEBUG_EVENT = 3
EXIT_PROCESS_DEBUG_EVENT = 5
LOAD_DLL_DEBUG_EVENT = 6
DBG_CONTINUE = 0x00010002
DBG_EXCEPTION_NOT_HANDLED = 0x80010001
EXCEPTION_BREAKPOINT = 0x80000003
ERROR_SEM_TIMEOUT = 121
MEMORY_METHOD_VERSION = 'windows-root-exit-event-v1'
PERFORMANCE_SCHEME = 'pmux-perf-15p-windows-separate-cpu-exitpeak-v3'


class SECURITY_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("nLength", wintypes.DWORD),
        ("lpSecurityDescriptor", ctypes.c_void_p),
        ("bInheritHandle", wintypes.BOOL),
    ]


class STARTUPINFOW(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD), ("lpReserved", wintypes.LPWSTR),
        ("lpDesktop", wintypes.LPWSTR), ("lpTitle", wintypes.LPWSTR),
        ("dwX", wintypes.DWORD), ("dwY", wintypes.DWORD),
        ("dwXSize", wintypes.DWORD), ("dwYSize", wintypes.DWORD),
        ("dwXCountChars", wintypes.DWORD), ("dwYCountChars", wintypes.DWORD),
        ("dwFillAttribute", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
        ("wShowWindow", wintypes.WORD), ("cbReserved2", wintypes.WORD),
        ("lpReserved2", ctypes.POINTER(wintypes.BYTE)),
        ("hStdInput", wintypes.HANDLE), ("hStdOutput", wintypes.HANDLE),
        ("hStdError", wintypes.HANDLE),
    ]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("hProcess", wintypes.HANDLE), ("hThread", wintypes.HANDLE),
        ("dwProcessId", wintypes.DWORD), ("dwThreadId", wintypes.DWORD),
    ]


class IO_COUNTERS(ctypes.Structure):
    _fields_ = [(name, ctypes.c_ulonglong) for name in (
        "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
        "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]


class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ("IoInfo", IO_COUNTERS),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class JOBOBJECT_BASIC_ACCOUNTING_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("TotalUserTime", ctypes.c_longlong),
        ("TotalKernelTime", ctypes.c_longlong),
        ("ThisPeriodTotalUserTime", ctypes.c_longlong),
        ("ThisPeriodTotalKernelTime", ctypes.c_longlong),
        ("TotalPageFaultCount", wintypes.DWORD),
        ("TotalProcesses", wintypes.DWORD),
        ("ActiveProcesses", wintypes.DWORD),
        ("TotalTerminatedProcesses", wintypes.DWORD),
    ]


class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivateUsage", ctypes.c_size_t),
    ]


class EXCEPTION_RECORD(ctypes.Structure):
    _fields_ = [('ExceptionCode', wintypes.DWORD), ('ExceptionFlags', wintypes.DWORD),
                ('ExceptionRecord', ctypes.c_void_p), ('ExceptionAddress', ctypes.c_void_p),
                ('NumberParameters', wintypes.DWORD), ('ExceptionInformation', ctypes.c_size_t * 15)]


class EXCEPTION_DEBUG_INFO(ctypes.Structure):
    _fields_ = [('ExceptionRecord', EXCEPTION_RECORD), ('dwFirstChance', wintypes.DWORD)]


class CREATE_PROCESS_DEBUG_INFO(ctypes.Structure):
    _fields_ = [('hFile', wintypes.HANDLE), ('hProcess', wintypes.HANDLE), ('hThread', wintypes.HANDLE),
                ('lpBaseOfImage', ctypes.c_void_p), ('dwDebugInfoFileOffset', wintypes.DWORD),
                ('nDebugInfoSize', wintypes.DWORD), ('lpThreadLocalBase', ctypes.c_void_p),
                ('lpStartAddress', ctypes.c_void_p), ('lpImageName', ctypes.c_void_p),
                ('fUnicode', wintypes.WORD)]


class LOAD_DLL_DEBUG_INFO(ctypes.Structure):
    _fields_ = [('hFile', wintypes.HANDLE), ('lpBaseOfDll', ctypes.c_void_p),
                ('dwDebugInfoFileOffset', wintypes.DWORD), ('nDebugInfoSize', wintypes.DWORD),
                ('lpImageName', ctypes.c_void_p), ('fUnicode', wintypes.WORD)]


class EXIT_PROCESS_DEBUG_INFO(ctypes.Structure):
    _fields_ = [('dwExitCode', wintypes.DWORD)]


class DEBUG_EVENT_UNION(ctypes.Union):
    _fields_ = [('Exception', EXCEPTION_DEBUG_INFO), ('CreateProcessInfo', CREATE_PROCESS_DEBUG_INFO),
                ('LoadDll', LOAD_DLL_DEBUG_INFO), ('ExitProcess', EXIT_PROCESS_DEBUG_INFO)]


class DEBUG_EVENT(ctypes.Structure):
    _fields_ = [('dwDebugEventCode', wintypes.DWORD), ('dwProcessId', wintypes.DWORD),
                ('dwThreadId', wintypes.DWORD), ('u', DEBUG_EVENT_UNION)]


def _api():
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel.CreateJobObjectW.restype = wintypes.HANDLE
    kernel.SetInformationJobObject.argtypes = [
        wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel.SetInformationJobObject.restype = wintypes.BOOL
    kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel.AssignProcessToJobObject.restype = wintypes.BOOL
    kernel.CreateProcessW.argtypes = [
        wintypes.LPCWSTR, wintypes.LPWSTR, ctypes.c_void_p, ctypes.c_void_p,
        wintypes.BOOL, wintypes.DWORD, ctypes.c_void_p, wintypes.LPCWSTR,
        ctypes.POINTER(STARTUPINFOW), ctypes.POINTER(PROCESS_INFORMATION)]
    kernel.CreateProcessW.restype = wintypes.BOOL
    kernel.CreateFileW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
        ctypes.POINTER(SECURITY_ATTRIBUTES), wintypes.DWORD, wintypes.DWORD,
        wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.ResumeThread.argtypes = [wintypes.HANDLE]
    kernel.ResumeThread.restype = wintypes.DWORD
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel.TerminateJobObject.restype = wintypes.BOOL
    kernel.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel.TerminateProcess.restype = wintypes.BOOL
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.GetExitCodeProcess.restype = wintypes.BOOL
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE, *([ctypes.POINTER(wintypes.FILETIME)] * 4)]
    kernel.GetProcessTimes.restype = wintypes.BOOL
    kernel.QueryInformationJobObject.argtypes = [
        wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD)]
    kernel.QueryInformationJobObject.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    kernel.WaitForDebugEvent.argtypes = [ctypes.POINTER(DEBUG_EVENT), wintypes.DWORD]
    kernel.WaitForDebugEvent.restype = wintypes.BOOL
    kernel.ContinueDebugEvent.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.DWORD]
    kernel.ContinueDebugEvent.restype = wintypes.BOOL
    kernel.DebugActiveProcessStop.argtypes = [wintypes.DWORD]
    kernel.DebugActiveProcessStop.restype = wintypes.BOOL
    psapi.GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX), wintypes.DWORD]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    return kernel, psapi


def _last_error(action: str) -> OSError:
    code = ctypes.get_last_error()
    return OSError(code, "{} failed: {}".format(action, ctypes.FormatError(code)))


def _environment_block(env):
    values = dict(os.environ if env is None else env)
    entries = sorted(values.items(), key=lambda item: (not item[0].startswith("="), item[0].upper()))
    block = "\0".join("{}={}".format(key, value) for key, value in entries) + "\0\0"
    return ctypes.create_unicode_buffer(block, len(block))


def _job_accounting(kernel, job):
    counters = JOBOBJECT_BASIC_ACCOUNTING_INFORMATION()
    returned = wintypes.DWORD()
    if not kernel.QueryInformationJobObject(
            job, JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION_CLASS,
            ctypes.byref(counters), ctypes.sizeof(counters), ctypes.byref(returned)):
        raise _last_error("QueryInformationJobObject")
    return counters


def _process_peak_working_set(psapi, process):
    counters = PROCESS_MEMORY_COUNTERS_EX()
    counters.cb = ctypes.sizeof(counters)
    if not psapi.GetProcessMemoryInfo(process, ctypes.byref(counters), counters.cb):
        raise _last_error("GetProcessMemoryInfo")
    return int(counters.PeakWorkingSetSize)


def _run(cmd, *, cwd, log_path, timeout_s=1800, env=None, capture_memory=True):
    """Run a command suspended, assign it to a Job Object, then resume it.

    CPU is the Job Object's accumulated user plus kernel time (including exited
    descendants). Memory is the root process's cumulative PeakWorkingSetSize,
    read at EXIT_PROCESS_DEBUG_EVENT before ContinueDebugEvent releases kernel
    teardown. Only the root is debugged. Ordinary CPU runs disable debugging.
    """
    if os.name != "nt":
        raise OSError("Windows Job Object measurement is available only on Windows")
    if not cmd:
        raise ValueError("empty command")
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if log_path.exists():
        raise FileExistsError("refusing to overwrite measurement log: {}".format(log_path))
    exe = str(cmd[0])
    if not os.path.isabs(exe):
        exe = shutil.which(exe) or ""
    if not exe or not Path(exe).is_file():
        raise FileNotFoundError("measurement executable is missing: {}".format(cmd[0]))

    kernel, psapi = _api()
    security = SECURITY_ATTRIBUTES(ctypes.sizeof(SECURITY_ATTRIBUTES), None, True)
    log_handle = null_handle = job = None
    info = PROCESS_INFORMATION()
    started = time.perf_counter()
    timed_out = False
    error = None
    memory_sampling_error = None
    cpu_user_s = cpu_system_s = None
    cpu_user_ticks = cpu_kernel_ticks = None
    process_create_filetime = process_exit_filetime = job_total_processes = None
    peak_working_set_bytes = None
    memory_sample_count = 0
    rc = None
    main_pid = None
    exit_event_seen = False
    capture_complete = False
    debug_attached = False
    initial_breakpoint_seen = False
    debug_event_count = 0
    exception_events = []
    root_exit_code = None
    try:
        log_handle = kernel.CreateFileW(
            str(log_path.resolve()), GENERIC_WRITE, FILE_SHARE_READ,
            ctypes.byref(security), CREATE_NEW, FILE_ATTRIBUTE_NORMAL, None)
        if log_handle == _INVALID_HANDLE:
            raise _last_error("CreateFileW(log)")
        null_handle = kernel.CreateFileW(
            "NUL", GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE,
            ctypes.byref(security), OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, None)
        if null_handle == _INVALID_HANDLE:
            raise _last_error("CreateFileW(NUL)")

        job = kernel.CreateJobObjectW(None, None)
        if not job:
            raise _last_error("CreateJobObjectW")
        limits = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not kernel.SetInformationJobObject(
                job, JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS,
                ctypes.byref(limits), ctypes.sizeof(limits)):
            raise _last_error("SetInformationJobObject")

        startup = STARTUPINFOW()
        startup.cb = ctypes.sizeof(startup)
        startup.dwFlags = STARTF_USESTDHANDLES
        startup.hStdInput = null_handle
        startup.hStdOutput = log_handle
        startup.hStdError = log_handle
        application = str(Path(exe).resolve())
        command_line = ctypes.create_unicode_buffer(subprocess.list2cmdline([application, *cmd[1:]]))
        env_buffer = _environment_block(env)
        flags = CREATE_SUSPENDED | CREATE_UNICODE_ENVIRONMENT | CREATE_NO_WINDOW
        if capture_memory:
            flags |= DEBUG_ONLY_THIS_PROCESS
        if not kernel.CreateProcessW(
                application, command_line, None, None, True, flags, env_buffer,
                str(Path(cwd).resolve()), ctypes.byref(startup), ctypes.byref(info)):
            raise _last_error("CreateProcessW")
        main_pid = int(info.dwProcessId)
        debug_attached = capture_memory
        if not kernel.AssignProcessToJobObject(job, info.hProcess):
            kernel.TerminateProcess(info.hProcess, 1)
            raise _last_error("AssignProcessToJobObject")
        if kernel.ResumeThread(info.hThread) == 0xFFFFFFFF:
            kernel.TerminateJobObject(job, 1)
            raise _last_error("ResumeThread")

        deadline = started + timeout_s
        shutdown_deadline = None
        while True:
            if not timed_out and time.perf_counter() >= deadline:
                timed_out = True
                if not kernel.TerminateJobObject(job, 124):
                    raise _last_error('TerminateJobObject(timeout)')
                shutdown_deadline = time.perf_counter() + 5.0
            if shutdown_deadline and time.perf_counter() >= shutdown_deadline:
                raise OSError('root exit event did not complete after timeout termination')
            if not capture_memory:
                state = kernel.WaitForSingleObject(info.hProcess, 20)
                if state == WAIT_OBJECT_0:
                    break
                if state != WAIT_TIMEOUT:
                    raise _last_error('WaitForSingleObject(CPU run)')
                continue
            event = DEBUG_EVENT()
            if not kernel.WaitForDebugEvent(ctypes.byref(event), 20):
                if ctypes.get_last_error() == ERROR_SEM_TIMEOUT:
                    continue
                raise _last_error('WaitForDebugEvent')
            debug_event_count += 1
            continue_status = DBG_CONTINUE
            try:
                if event.dwProcessId != main_pid:
                    raise OSError('unexpected child debug event; root-only identity violated')
                if event.dwDebugEventCode == CREATE_PROCESS_DEBUG_EVENT:
                    if event.u.CreateProcessInfo.hFile:
                        kernel.CloseHandle(event.u.CreateProcessInfo.hFile)
                elif event.dwDebugEventCode == LOAD_DLL_DEBUG_EVENT:
                    if event.u.LoadDll.hFile:
                        kernel.CloseHandle(event.u.LoadDll.hFile)
                elif event.dwDebugEventCode == EXCEPTION_DEBUG_EVENT:
                    ex = event.u.Exception
                    exception_events.append({'code': int(ex.ExceptionRecord.ExceptionCode),
                                             'first_chance': bool(ex.dwFirstChance)})
                    if (ex.ExceptionRecord.ExceptionCode == EXCEPTION_BREAKPOINT
                            and ex.dwFirstChance and not initial_breakpoint_seen):
                        initial_breakpoint_seen = True
                    else:
                        continue_status = DBG_EXCEPTION_NOT_HANDLED
                elif event.dwDebugEventCode == EXIT_PROCESS_DEBUG_EVENT:
                    exit_event_seen = True
                    root_exit_code = int(event.u.ExitProcess.dwExitCode)
                    try:
                        peak_working_set_bytes = _process_peak_working_set(psapi, info.hProcess)
                        if peak_working_set_bytes <= 0:
                            raise OSError('exit-event PeakWorkingSetSize is not positive')
                        memory_sample_count = 1
                    except OSError as exc:
                        memory_sampling_error = str(exc)
            finally:
                if not kernel.ContinueDebugEvent(event.dwProcessId, event.dwThreadId, continue_status):
                    raise _last_error('ContinueDebugEvent')
            if exit_event_seen:
                # All user threads are gone; release is after the only final read.
                capture_complete = memory_sample_count == 1 and memory_sampling_error is None
                debug_attached = False
                break

        if kernel.WaitForSingleObject(info.hProcess, 5000) != WAIT_OBJECT_0:
            raise OSError('root process did not finish kernel teardown')

        while not timed_out:
            accounting = _job_accounting(kernel, job)
            if accounting.ActiveProcesses == 0:
                break
            if time.perf_counter() >= deadline:
                timed_out = True
                kernel.TerminateJobObject(job, 124)
                break
            time.sleep(0.01)

        if timed_out:
            kernel.WaitForSingleObject(info.hProcess, 5000)
        exit_code = wintypes.DWORD()
        if kernel.GetExitCodeProcess(info.hProcess, ctypes.byref(exit_code)):
            rc = 124 if timed_out else int(exit_code.value)
            if not timed_out and rc >= 0x80000000:
                rc -= 0x100000000
        else:
            error = str(_last_error("GetExitCodeProcess"))
        try:
            accounting = _job_accounting(kernel, job)
            cpu_user_ticks = int(accounting.TotalUserTime)
            cpu_kernel_ticks = int(accounting.TotalKernelTime)
            job_total_processes = int(accounting.TotalProcesses)
            creation, ended, kernel_time, user_time = (wintypes.FILETIME() for _ in range(4))
            if not kernel.GetProcessTimes(info.hProcess, ctypes.byref(creation), ctypes.byref(ended),
                                          ctypes.byref(kernel_time), ctypes.byref(user_time)):
                raise _last_error('GetProcessTimes')
            process_create_filetime = (int(creation.dwHighDateTime) << 32) | int(creation.dwLowDateTime)
            process_exit_filetime = (int(ended.dwHighDateTime) << 32) | int(ended.dwLowDateTime)
            cpu_user_s = accounting.TotalUserTime / _TICKS_PER_SECOND
            cpu_system_s = accounting.TotalKernelTime / _TICKS_PER_SECOND
        except OSError as exc:
            error = (error + "; " if error else "") + str(exc)
        if memory_sampling_error:
            error = (error + "; " if error else "") + memory_sampling_error
        elif capture_memory and not capture_complete:
            memory_sampling_error = (
                "root process final exit-event peak capture is incomplete")
            error = (error + "; " if error else "") + memory_sampling_error
    except Exception as exc:
        error = str(exc)
        if job:
            kernel.TerminateJobObject(job, 1)
        elif info.hProcess:
            kernel.TerminateProcess(info.hProcess, 1)
        if info.hProcess:
            if debug_attached:
                # Release pending events even on API failure; no suspended orphan.
                kernel.DebugActiveProcessStop(main_pid)
            kernel.WaitForSingleObject(info.hProcess, 5000)
    finally:
        for handle in (info.hThread, info.hProcess, null_handle, log_handle, job):
            if handle:
                kernel.CloseHandle(handle)

    wall_s = time.perf_counter() - started
    metrics_valid = cpu_user_s is not None and cpu_system_s is not None \
        and error is None and (not capture_memory or capture_complete)
    if error and log_path.exists():
        with log_path.open("a", encoding="utf-8", errors="replace") as log:
            log.write("\n[measurement error] {}\n".format(error))
    return {
        "rc": rc,
        "timed_out": bool(timed_out),
        "wall_s": round(wall_s, 4),
        "cpu_user_ticks": cpu_user_ticks,
        "process_create_filetime": process_create_filetime,
        "process_exit_filetime": process_exit_filetime,
        "job_total_processes": job_total_processes,
        "cpu_kernel_ticks": cpu_kernel_ticks,
        "cpu_total_ticks": (cpu_user_ticks + cpu_kernel_ticks
                            if cpu_user_ticks is not None and cpu_kernel_ticks is not None else None),
        "cpu_user_s": round(cpu_user_s, 4) if cpu_user_s is not None else None,
        "cpu_system_s": round(cpu_system_s, 4) if cpu_system_s is not None else None,
        "cpu_total_s": round(cpu_user_s + cpu_system_s, 4)
        if cpu_user_s is not None and cpu_system_s is not None else None,
        "yosys_peak_working_set_bytes": peak_working_set_bytes,
        "yosys_peak_working_set_mib": (peak_working_set_bytes / (1024 * 1024)
                                        if peak_working_set_bytes is not None else None),
        "memory_metric": "yosys_peak_working_set_bytes" if capture_memory else None,
        "memory_method": "PeakWorkingSetSize at root EXIT_PROCESS_DEBUG_EVENT before ContinueDebugEvent" if capture_memory else None,
        "memory_method_version": MEMORY_METHOD_VERSION if capture_memory else None,
        "memory_sample_interval_ms": None,
        "memory_sample_count": memory_sample_count,
        "memory_sampled_before_exit": memory_sample_count > 0,
        "memory_capture_complete": capture_complete,
        "memory_exit_event_observed": exit_event_seen,
        "memory_exit_event_pid": main_pid if exit_event_seen else None,
        "memory_exit_event_code": root_exit_code,
        "debug_event_count": debug_event_count,
        "debug_exception_events": exception_events,
        "root_debugged": capture_memory,
        "cpu_method": "JobObjectBasicAccountingInformation",
        "cpu_descendants_included": True,
        "memory_root_process_only": True,
        "main_pid": main_pid,
        "metrics_valid": metrics_valid,
        "measurement_error": error,
    }


def run_measured(cmd, *, cwd, log_path, timeout_s=1800, env=None):
    return _run(cmd, cwd=cwd, log_path=log_path, timeout_s=timeout_s, env=env, capture_memory=True)


def run_cpu_measured(cmd, *, cwd, log_path, timeout_s=1800, env=None):
    """Ordinary Job Object run, without debugger or periodic memory polling."""
    return _run(cmd, cwd=cwd, log_path=log_path, timeout_s=timeout_s, env=env, capture_memory=False)
