@echo off
REM WireGuard MikroTik Management Menu - Windows Launcher
REM This script launches the Python menu system

setlocal enabledelayedexpansion

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

REM Check if running as administrator
net session >nul 2>&1
if errorlevel 1 (
    echo [ERROR] This script must be run as Administrator
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

REM Change to script directory
cd /d "%~dp0"

REM Launch the Python menu
echo Starting WireGuard MikroTik Management Menu...
echo.

python wireguard-menu.py

REM Pause before closing
echo.
echo Press any key to exit...
pause >nul
