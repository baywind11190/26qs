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
set "PYTHON_EXE=%PROJECT_ROOT%\.tools\msys64\mingw64\bin\python3.exe"
if not exist "%PYTHON_EXE%" exit /b 3
"%PYTHON_EXE%" "%~dp0diagnose.py" %*
exit /b %ERRORLEVEL%
