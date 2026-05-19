@echo off
title WhatsApp Sender Pro

REM Try to find Python in common locations
where python >nul 2>&1 && (python main.py & goto :end)
where py >nul 2>&1 && (py main.py & goto :end)

REM Check user-installed Python 3.11
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" main.py
    goto :end
)

REM Check user-installed Python 3.12
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" main.py
    goto :end
)

echo [ERROR] Python not found! Please install Python 3.11+ or run dist\WhatsAppSenderPro.exe
echo Download: https://www.python.org/downloads/

:end
pause
