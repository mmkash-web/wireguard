@echo off
echo ============================================================
echo   Quick Fix for Setup Issues
echo ============================================================
echo.

echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

echo Step 1: Testing internet connection...
ping -n 1 google.com > nul
if errorlevel 1 (
    echo [ERROR] No internet connection
    echo Please check your internet and try again
    pause
    exit /b 1
) else (
    echo [OK] Internet connection working
)
echo.

echo Step 2: Testing Supabase DNS...
ping -n 1 db.seuzxvthbxowmofxalmm.supabase.co > nul
if errorlevel 1 (
    echo [WARNING] Cannot reach Supabase server
    echo.
    echo This could be:
    echo   1. Firewall blocking connection
    echo   2. DNS issue
    echo   3. Supabase server temporarily unavailable
    echo.
    echo Trying with SQLite database instead...
    
    REM Create SQLite .env
    echo Creating SQLite configuration...
    (
    echo # Django Settings
    echo SECRET_KEY=django-insecure-change-this-in-production
    echo DEBUG=True
    echo ALLOWED_HOSTS=localhost,127.0.0.1
    echo.
    echo # SQLite Database (Local Development^)
    echo DATABASE_ENGINE=django.db.backends.sqlite3
    echo DATABASE_NAME=db.sqlite3
    echo.
    echo # Email Configuration
    echo EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
    ) > .env
    
    echo [OK] Using SQLite database instead
) else (
    echo [OK] Can reach Supabase server
    echo.
    echo Keeping Supabase PostgreSQL configuration
)
echo.

echo Step 3: Running database migrations...
python manage.py migrate
if errorlevel 1 (
    echo [ERROR] Migration failed
    echo Check error messages above
    pause
    exit /b 1
) else (
    echo [OK] Migrations completed
)
echo.

echo Step 4: Creating admin user...
python setup_admin.py
if errorlevel 1 (
    echo [WARNING] Admin setup had issues
    echo You can create admin manually: python manage.py createsuperuser
)
echo.

echo ============================================================
echo   Fix Complete!
echo ============================================================
echo.
echo Your system is now ready!
echo.
echo To start:
echo   python manage.py runserver
echo.
echo Then visit: http://127.0.0.1:8000
echo.
pause

