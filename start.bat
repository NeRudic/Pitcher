@echo off
chcp 65001 >nul
echo ========================================
echo   Piano Performance Analyzer
echo ========================================
echo.

:: Kill old processes on both ports
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING" 2^>nul') do (
    echo Killing old backend process (PID: %%a^)
    taskkill //F //PID %%a 2>nul
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000" ^| findstr "LISTENING" 2^>nul') do (
    echo Killing old frontend process (PID: %%a^)
    taskkill //F //PID %%a 2>nul
)

echo Starting backend (http://localhost:8000^)...
start "Piano Backend" cmd /k "cd backend && py -3.11 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo Starting frontend (http://localhost:3000^)...
start "Piano Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Both servers started! Open http://localhost:3000
