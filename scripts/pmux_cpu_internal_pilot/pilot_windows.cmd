@echo off
setlocal
"%~dp0..\..\.tools\msys64\mingw64\bin\python3.exe" -X utf8 "%~dp0pilot.py" %*
exit /b %errorlevel%
