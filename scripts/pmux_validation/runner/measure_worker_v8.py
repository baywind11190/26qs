#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Loopback worker for one-process Yosys debug-exit peak collection."""
import json
import os
import socket
import socketserver
import sys
import threading
import time
from pathlib import Path

runner_dir, ready_path, token = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
sys.path.insert(0, runner_dir)
import win_measure

class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

class Handler(socketserver.StreamRequestHandler):
    def setup(self):
        super().setup()
        self.request.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    def handle(self):
        while True:
            raw = self.rfile.readline()
            if not raw:
                return
            try:
                req = json.loads(raw.decode('utf-8'))
                if req.get('token') != token:
                    raise ValueError('worker token mismatch')
                action = req.get('action')
                if action == 'shutdown':
                    self.wfile.write((json.dumps({'ok': True, 'action': 'shutdown'}) + '\n').encode('utf-8'))
                    self.wfile.flush()
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
                    return
                if action == 'ping':
                    result = {'ok': True, 'action': 'ping', 'worker_pid': os.getpid()}
                elif action == 'run':
                    start = time.perf_counter()
                    metrics = win_measure.run_measured(
                        req['cmd'], cwd=req['cwd'], log_path=req['log_path'],
                        timeout_s=float(req.get('timeout_s', 1800)), env=req.get('env'))
                    metrics['worker_call_wall_s'] = time.perf_counter() - start
                    result = {'ok': True, 'action': 'run', 'request_id': req.get('request_id'),
                              'worker_pid': os.getpid(), 'metrics': metrics}
                else:
                    raise ValueError('unknown action')
            except Exception as exc:
                result = {'ok': False, 'error': repr(exc), 'request_id': req.get('request_id') if 'req' in locals() else None}
            self.wfile.write((json.dumps(result, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8'))
            self.wfile.flush()

server = Server(('127.0.0.1', 0), Handler)
port = server.server_address[1]
ready = {'host': '127.0.0.1', 'port': port, 'token': token, 'pid': os.getpid(),
         'python': sys.version, 'runner_path': str(Path(runner_dir).resolve()),
         'memory_method': 'windows-root-exit-event-v1'}
ready_path.parent.mkdir(parents=True, exist_ok=True)
ready_path.write_text(json.dumps(ready, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'state': 'READY', 'port': port, 'pid': os.getpid()}), flush=True)
server.serve_forever(poll_interval=0.05)
server.server_close()
