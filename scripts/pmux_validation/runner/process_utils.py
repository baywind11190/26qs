#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Small cross-platform helpers for terminating a tool and its descendants."""
import os
import subprocess


def process_group_kwargs():
    """Return Popen options that give timeout handling a process-tree boundary."""
    if os.name == "nt":
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP |
                getattr(subprocess, "CREATE_NO_WINDOW", 0)}
    return {"start_new_session": True}


def terminate_process_tree(process):
    """Kill a timed out process and its descendants; tolerate an already exited root."""
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill.exe", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=10, check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except (OSError, subprocess.SubprocessError):
            pass
        if process.poll() is None:
            process.kill()
        return
    try:
        os.killpg(process.pid, 9)
    except ProcessLookupError:
        pass
