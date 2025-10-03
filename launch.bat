@echo off
REM WireGuard MikroTik VPS Project Launcher
REM Easy access to all management tools

setlocal enabledelayedexpansion

title WireGuard MikroTik VPS Management System

:MAIN_MENU
cls
echo.
echo ================================================================================
echo                    WireGuard MikroTik VPS Management System
echo ================================================================================
echo.
echo Choose an option:
echo.
echo   1. 🔧 Management Menu (Full Control)
echo   2. 📊 Real-time Dashboard
echo   3. 🧪 System Test & Validation
echo   4. 🔍 Router Connection Test
echo   5. 📋 Quick Status Check
echo   6. ⚙️  VPS Installation
echo   7. 🔧 Router Config Generator
echo   8. 📚 Documentation
echo   9. 🚀 Deploy to VPS
echo   10. 🚪 Exit
echo.
echo ================================================================================

set /p choice="Enter your choice (1-10): "

if "%choice%"=="1" goto MENU
if "%choice%"=="2" goto DASHBOARD
if "%choice%"=="3" goto TEST
if "%choice%"=="4" goto ROUTER_TEST
if "%choice%"=="5" goto STATUS
if "%choice%"=="6" goto INSTALL
if "%choice%"=="7" goto CONFIG_GEN
if "%choice%"=="8" goto DOCS
if "%choice%"=="9" goto DEPLOY
if "%choice%"=="10" goto EXIT

echo Invalid choice. Please try again.
pause
goto MAIN_MENU

:MENU
echo.
echo Starting Management Menu...
python menu\wireguard-menu.py
pause
goto MAIN_MENU

:DASHBOARD
echo.
echo Starting Real-time Dashboard...
python menu\wireguard-dashboard.py
pause
goto MAIN_MENU

:TEST
echo.
echo Running System Test...
python tools\test-wireguard-setup.py
pause
goto MAIN_MENU

:ROUTER_TEST
echo.
echo Router Connection Test
echo =====================
set /p router_ip="Enter router VPN IP address: "
if "%router_ip%"=="" (
    echo No IP address provided.
    pause
    goto MAIN_MENU
)

python tools\validate-mikrotik-connection.py --router-ip %router_ip%
pause
goto MAIN_MENU

:STATUS
echo.
echo Quick Status Check
echo ==================
echo.
echo Note: This requires WireGuard to be installed on the system.
echo.
pause
goto MAIN_MENU

:INSTALL
echo.
echo VPS Installation
echo ================
echo This will install WireGuard on your VPS.
echo Make sure you have root access and are on the VPS.
echo.
set /p confirm="Continue with installation? (y/N): "
if /i not "%confirm%"=="y" goto MAIN_MENU

bash scripts\install-wireguard-vps.sh
pause
goto MAIN_MENU

:CONFIG_GEN
echo.
echo Router Configuration Generator
echo =============================
set /p vps_ip="Enter VPS IP address: "
if "%vps_ip%"=="" (
    echo VPS IP is required.
    pause
    goto MAIN_MENU
)

set /p vps_key="Enter VPS public key: "
if "%vps_key%"=="" (
    echo VPS public key is required.
    pause
    goto MAIN_MENU
)

set /p router_count="Number of routers (default 5): "
if "%router_count%"=="" set router_count=5

bash scripts\mikrotik-wireguard-setup.sh -v %vps_ip% -k %vps_key% -c %router_count%
pause
goto MAIN_MENU

:DOCS
echo.
echo Opening Documentation...
if exist "docs\WIREGUARD_MIKROTIK_SETUP.md" (
    start docs\WIREGUARD_MIKROTIK_SETUP.md
) else (
    echo Documentation file not found.
    echo Please make sure docs\WIREGUARD_MIKROTIK_SETUP.md exists.
)
pause
goto MAIN_MENU

:DEPLOY
echo.
echo Deploy to VPS
echo =============
set /p vps_ip="Enter VPS IP address: "
if "%vps_ip%"=="" (
    echo VPS IP is required.
    pause
    goto MAIN_MENU
)

set /p vps_user="Enter VPS username (default: root): "
if "%vps_user%"=="" set vps_user=root

echo.
echo Deploying to VPS: %vps_ip%
echo VPS User: %vps_user%
echo.
set /p confirm="Continue with deployment? (y/N): "
if /i not "%confirm%"=="y" goto MAIN_MENU

bash deploy.sh -v %vps_ip% -u %vps_user%
pause
goto MAIN_MENU

:EXIT
echo.
echo Goodbye!
exit /b 0
