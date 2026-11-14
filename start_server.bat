@echo off
title MediApp Development Server
cd /d "%~dp0"
echo ===================================================
echo  Starting MediApp Unified Healthcare Platform
echo  Listening on: http://127.0.0.1:5000 (and http://localhost:5000)
echo ===================================================
echo.
if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe run.py
) else (
    python run.py
)
pause
