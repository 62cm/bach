@echo off
cd /d "%~dp0"
echo Building BWV772a.exe ...
python -m pip install -q pywebview pyinstaller
python -m PyInstaller --noconfirm --clean --onefile --noconsole --name BWV772a ^
  --add-data "index.html;." ^
  --hidden-import webview ^
  window.py
if errorlevel 1 (
  echo Build failed.
  pause
  exit /b 1
)
copy /Y "dist\BWV772a.exe" "BWV772a.exe" >nul
echo.
echo Done: %~dp0BWV772a.exe
echo Double-click BWV772a.exe  (or launch.bat). Esc closes the window.
pause
