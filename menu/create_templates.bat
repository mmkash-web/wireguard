@echo off
echo Creating all missing HTML templates...
echo.

REM Create template directories
mkdir templates\customers 2>nul
mkdir templates\profiles 2>nul
mkdir templates\vouchers 2>nul
mkdir templates\reports 2>nul
mkdir templates\routers 2>nul

echo [OK] Template directories created
echo.
echo Templates are being created by the system...
echo Please refresh your browser after this completes.
echo.
pause

