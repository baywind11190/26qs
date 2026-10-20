@echo off
setlocal
chcp 65001 >nul
set "PROJECT_ROOT=%~dp0..\.."
set "PATH=%PROJECT_ROOT%\.tools\msys64\mingw64\bin;%PROJECT_ROOT%\.tools\msys64\usr\bin;%PATH%"
set "PYTHONHOME="
set "PYTHONPATH="
set "PYTHONUSERBASE="
set "PYTHONNOUSERSITE=1"
set "BASH_ENV="
set "ENV="
set "MSYS2_PATH_TYPE=inherit"
set "MSYSTEM=MINGW64"
set "LC_ALL=C.UTF-8"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
"%PROJECT_ROOT%\.tools\msys64\mingw64\bin\python3.exe" "%~dp0diagnose_v2.py" %*
exit /b %ERRORLEVEL%
