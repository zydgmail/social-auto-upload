@echo off
setlocal
cd /d %~dp0

REM Check embeddable Python
if not exist python\python.exe (
  echo "[ERROR] Missing embeddable Python at EXE\python\python.exe"
  echo "Please download Windows embeddable Python (same version as dev), unzip into EXE\python\"
  echo "https://www.python.org/downloads/windows/"
  pause
  exit /b 1
)

REM Optional: Playwright browsers path (if used)
set PLAYWRIGHT_BROWSERS_PATH=%CD%\third_party\playwright\ms-playwright

REM Optional: FFmpeg path (if used)
set PATH=%CD%\third_party\ffmpeg\bin;%PATH%

REM PYTHONPATH so backend can import project modules from EXE root
set PYTHONPATH=%CD%;%CD%\uploader;%CD%\myUtils;%CD%\utils

REM Kill any existing process on port 5409
echo [INFO] Checking for existing processes on port 5409...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5409') do (
    echo [INFO] Killing process %%a on port 5409...
    taskkill /PID %%a /F >nul 2>&1
)

REM Start backend in background
start /b python\python.exe main.py

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Open browser to backend port
start "" http://127.0.0.1:5409/

REM Keep window open to see backend output
pause

endlocal

