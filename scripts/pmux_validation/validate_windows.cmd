@echo off
setlocal
chcp 65001 >nul
set "PACKAGE_DIR=%~dp0"
set "PROJECT_ROOT=%PACKAGE_DIR%..\.."
set "TOOLS_ROOT=%PROJECT_ROOT%\.tools"
set "PATH=%TOOLS_ROOT%\msys64\mingw64\bin;%TOOLS_ROOT%\msys64\usr\bin;%PATH%"
set "PYTHONHOME="
set "PYTHONPATH="
set "PYTHONUSERBASE="
set "PYTHONNOUSERSITE=1"
set "BASH_ENV="
set "ENV="
set "MSYS2_PATH_TYPE=inherit"
set "LC_ALL=C.UTF-8"
set "PYTHON_EXE=%TOOLS_ROOT%\msys64\mingw64\bin\python3.exe"
if not exist "%PYTHON_EXE%" (
  echo [BLOCKED] Fixed Python missing: %PYTHON_EXE%
  exit /b 3
)
set "MSYSTEM=MINGW64"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
pushd "%PACKAGE_DIR%"
"%PYTHON_EXE%" validate.py %*
set "EXIT_CODE=%ERRORLEVEL%"
popd
exit /b %EXIT_CODE%
