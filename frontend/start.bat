@echo off
chcp 65001 >nul
echo === Piano Performance Analyzer — Frontend ===

:: Kill any existing process on port 3000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000" ^| findstr "LISTENING" 2^>nul') do (
    echo Killing old process on port 3000 (PID: %%a^)
    taskkill //F //PID %%a 2>nul
)

:: Start Vite dev server
echo Starting frontend on http://localhost:3000
call npm run dev
