@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   Piano Performance Analyzer
echo ========================================
echo.

:: Kill any leftover processes on our ports
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING" 2^>nul') do (
    echo Cleaning up old process on port 8000 (PID: %%a^)
    taskkill /F /PID %%a 2>nul
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000" ^| findstr "LISTENING" 2^>nul') do (
    echo Cleaning up old process on port 3000 (PID: %%a^)
    taskkill /F /PID %%a 2>nul
)
echo.

:: Clear stale Python bytecode
for /d /r backend %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul

:: Launch via Python — Ctrl+C kills both
py -3.11 run.py

:: If run.py failed (e.g. no Python), pause so the user sees the error
if errorlevel 1 pause
