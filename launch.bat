@echo off
cd /d "%~dp0"
REM Prefer packaged exe; else pywebview via pythonw
if exist "%~dp0BWV772a.exe" (
  start "" "%~dp0BWV772a.exe"
  exit /b 0
)
where pyw >nul 2>&1
if %ERRORLEVEL%==0 (
  start "" pyw "%~dp0window.py"
  exit /b 0
)
where pythonw >nul 2>&1
if %ERRORLEVEL%==0 (
  start "" pythonw "%~dp0window.py"
  exit /b 0
)
start "" python "%~dp0window.py"
