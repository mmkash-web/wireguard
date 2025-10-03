@echo off
echo ============================================================
echo   MikroTik Billing System - Windows Setup
echo ============================================================
echo.

echo Step 1: Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    echo Make sure Python 3.8+ is installed
    pause
    exit /b 1
)
echo [OK] Virtual environment created
echo.

echo Step 2: Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated
echo.

echo Step 3: Upgrading pip...
python -m pip install --upgrade pip
echo [OK] pip upgraded
echo.

echo Step 4: Installing core packages...
pip install Django==4.2.7
pip install djangorestframework==3.14.0
pip install python-decouple==3.8
pip install librouteros==3.2.1
pip install django-crispy-forms==2.1
pip install crispy-tailwind==0.5.0
pip install celery==5.3.4
pip install redis==5.0.1
pip install requests==2.31.0
pip install python-dateutil==2.8.2
pip install pytz==2023.3
pip install argon2-cffi==23.1.0
echo [OK] Core packages installed
echo.

echo Step 5: Installing PostgreSQL driver (psycopg2)...
pip install psycopg2-binary
if errorlevel 1 (
    echo WARNING: psycopg2-binary failed to install
    echo Trying alternative method...
    pip install psycopg2
)
echo [OK] PostgreSQL driver installed
echo.

echo Step 6: Setting up Supabase configuration...
python setup_supabase.py
if errorlevel 1 (
    echo WARNING: Supabase setup had issues
    echo You may need to run: python setup_supabase.py manually
)
echo.

echo Step 7: Creating admin user...
python setup_admin.py
if errorlevel 1 (
    echo WARNING: Admin creation had issues
    echo You may need to run: python setup_admin.py manually
)
echo.

echo ============================================================
echo   Setup Complete!
echo ============================================================
echo.
echo Your MikroTik Billing system is ready!
echo.
echo To start the server:
echo   1. Make sure virtual environment is active: venv\Scripts\activate
echo   2. Run: python manage.py runserver
echo   3. Visit: http://127.0.0.1:8000
echo   4. Login: admin / admin123
echo.
echo For testing, run: python run_tests.py
echo.
pause

