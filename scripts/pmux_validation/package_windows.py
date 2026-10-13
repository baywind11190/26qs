"""Build a new Windows reproduction ZIP from the preserved p6 delivery tree.

No historical ZIP or extraction is modified. QA runs after extraction, and
evidence is external to the ZIP so its identity stays fixed.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

REPO = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def bundle_msys_tools(root):
    source = REPO / '.tools/msys64/usr/bin'
    target = root / 'runtime/msys/usr/bin'
    target.mkdir(parents=True)
    queue = ['bash.exe', 'sh.exe', 'grep.exe', 'env.exe']
    copied = set()
    objdump = REPO / '.tools/msys64/mingw64/bin/objdump.exe'
    while queue:
        name = queue.pop()
        if name.lower() in copied:
            continue
        path = source / name
        shutil.copy2(path, target / name)
        copied.add(name.lower())
        output = subprocess.check_output([str(objdump), '-p', str(path)], encoding='utf-8')
        for dll in re.findall(r'DLL Name:\s*(\S+)', output):
            if (source / dll).is_file():
                queue.append(dll)
    save(root / 'versions/msys-runtime.json',
         {p.name: sha(p) for p in sorted(target.iterdir())})


def build(name):
    target = REPO / '.tools/deliverables' / name
    if target.exists() or target.with_suffix('.zip').exists():
        raise RuntimeError('Refusing to overwrite delivery: ' + str(target))
    old = REPO / '.tools/deliverables/official4-p6-windows_2026-10-10'
    shutil.copytree(old, target, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    bundle_msys_tools(target)
    wrapper = r'''@echo off
setlocal
set "PACKAGE_ROOT=%~dp0"
set "PATH=%PACKAGE_ROOT%runtime\mingw64\bin;%PACKAGE_ROOT%runtime\msys\usr\bin;%PACKAGE_ROOT%tools\baseline\bin;%SystemRoot%\System32;%SystemRoot%"
set "PYTHONHOME=%PACKAGE_ROOT%runtime\mingw64"
set "PYTHONPATH=%PACKAGE_ROOT%runtime\mingw64\lib\python3.14\site-packages"
set "PYTHONUSERBASE="
set "PYTHONNOUSERSITE=1"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "BASH_ENV="
set "ENV="
set "LC_ALL=C.UTF-8"
set "MSYSTEM=MINGW64"
set "MSYS2_PATH_TYPE=inherit"
set "YOSYS=%PACKAGE_ROOT%tools\baseline\bin\yosys.exe"
set "ABC=%PACKAGE_ROOT%tools\baseline\bin\yosys-abc.exe"
set "YOSYS_DATDIR=%PACKAGE_ROOT%tools\baseline\share\yosys"
for %%F in ("%PACKAGE_ROOT%runtime\mingw64\bin\python3.exe" "%PACKAGE_ROOT%runtime\mingw64\bin\make.exe" "%PACKAGE_ROOT%runtime\msys\usr\bin\bash.exe" "%PACKAGE_ROOT%runtime\msys\usr\bin\grep.exe") do (
 if not exist %%F (
  echo [BLOCKED] Package dependency missing: %%F
  exit /b 3
 )
)
"%PACKAGE_ROOT%runtime\mingw64\bin\python3.exe" "%PACKAGE_ROOT%tools\eqy\bin\eqy-script.py" %*
exit /b %ERRORLEVEL%
'''
    (target / 'eqy-portable.cmd').write_text(wrapper, encoding='utf-8')
    job = target / 'tools/eqy/share/yosys/python3/eqy_job.py'
    text = job.read_text(encoding='utf-8')
    needle = 'self.p.stdout.readline().decode("utf-8")'
    if text.count(needle) != 1:
        raise RuntimeError('EQY decoding anchor changed')
    helper = '''
def decode_process_output(raw):
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        if os.name == "nt":
            import ctypes
            return raw.decode("cp{}".format(ctypes.windll.kernel32.GetACP()), errors="backslashreplace")
        return raw.decode("utf-8", errors="backslashreplace")

'''
    text = text.replace(needle, 'decode_process_output(self.p.stdout.readline())')
    text = text.replace('class EqyAbort(', helper + 'class EqyAbort(')
    job.write_text(text, encoding='utf-8')
    (target / 'versions/eqy-windows-output-compat.md').write_text(
        '# EQY Windows 输出兼容\n\n仅包内 eqy_job.py 增加 UTF-8 解码失败时使用 Windows ACP 的兼容；仍保留失败退出码与证明状态。不能解码的字节保留转义。未修改证明策略。\n', encoding='utf-8')
    shutil.copy2(Path(__file__).with_name('package_qa.py'), target / 'qa/package_qa.py')
    (target / 'qa/smoke.ps1').write_text(r'''$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root 'runtime\mingw64\bin\python3.exe'
$env:PYTHONHOME = Join-Path $root 'runtime\mingw64'
$env:PYTHONPATH = Join-Path $root 'runtime\mingw64\lib\python3.14\site-packages'
$env:PYTHONUTF8 = '1'
$env:PYTHONNOUSERSITE = '1'
& $python (Join-Path $PSScriptRoot 'package_qa.py')
if ($LASTEXITCODE -ne 0) { throw "Package QA failed: $LASTEXITCODE" }
''', encoding='utf-8')
    base_source = target / 'source/yosys-0.69-base.tar'
    subprocess.run(['git', '-C', str(REPO / '.tools/yosys-source-lf'), 'archive',
                    '--format=tar', '-o', str(base_source),
                    '9f75ca1f9834a39a863915b5dae0c7b1e33533bc'], check=True)
    # Include the fixed four-case input and current stage/model information.
    shutil.copytree(Path(__file__).parent / 'suite-official4', target / 'qa/fourcase-inputs')
    shutil.copy2(Path(__file__).parent / 'runner/form_cells_cycloneiv.v', target / 'qa/form_cells_cycloneiv.v')
    readme = (target / 'README.md').read_text(encoding='utf-8')
    readme += '\n## 2026-10-11 修复\n\n新增固定 Bash/sh/grep/env 与递归 DLL 依赖、系统输出编码兼容及源码基础归档。入口优先包内 Python/make/Bash，收窄 PATH。QA 用同一个输入和脚本进行两侧综合，并包含 EQY 正例、故意错误负例、非 UTF-8 工具错误日志检查。只声明小用例启动和基本运行验收，四例完整包内复现未执行；历史 evidence 为工程内结果。\n'
    (target / 'README.md').write_text(readme, encoding='utf-8')
    manifest = json.loads((target / 'package_manifest.json').read_text(encoding='utf-8'))
    manifest['created_at'] = '2026-10-11'
    manifest['files'] = [dict(path=p.relative_to(target).as_posix(), size_bytes=p.stat().st_size, sha256=sha(p))
                         for p in sorted(target.rglob('*'))
                         if p.is_file() and p.name != 'package_manifest.json']
    save(target / 'package_manifest.json', manifest)
    archive = target.with_suffix('.zip')
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in sorted(target.rglob('*')):
            if p.is_file():
                z.write(p, str(Path(target.name) / p.relative_to(target)))
    print(json.dumps(dict(package=str(archive), sha256=sha(archive)), indent=2))


if __name__ == '__main__':
    build(sys.argv[1])
