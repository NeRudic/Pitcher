@echo off
chcp 65001 >nul
echo === Piano Performance Analyzer — Backend ===

:: Kill any existing process on port 8000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING" 2^>nul') do (
    echo Killing old process on port 8000 (PID: %%a^)
    taskkill //F //PID %%a 2>nul
)

:: Start the server with auto-reload on code changes
echo Starting backend on http://localhost:8000
py -3.11 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
