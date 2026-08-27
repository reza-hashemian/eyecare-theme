@echo off
REM eyecare-theme launcher (Windows)
setlocal
set "DIR=%~dp0"
where python >nul 2>nul
if %errorlevel%==0 (
    python "%DIR%lib\cli.py" %*
    exit /b %errorlevel%
)
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 "%DIR%lib\cli.py" %*
    exit /b %errorlevel%
)
echo error: python not found in PATH 1>&2
exit /b 1
