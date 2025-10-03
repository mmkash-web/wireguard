@echo off
echo ============================================================
echo   Fixing Supabase Connection for IPv4
echo ============================================================
echo.
echo Issue: Direct Connection requires IPv6
echo Solution: Using IPv4-compatible Session Pooler
echo.

call venv\Scripts\activate.bat

echo Updating .env file with IPv4-compatible settings...
(
echo # MikroTik Billing - Supabase PostgreSQL Configuration
echo # Using Session Pooler (IPv4 Compatible^)
echo.
echo # Django Settings
echo SECRET_KEY=django-insecure-change-this-to-random-string-in-production
echo DEBUG=True
echo ALLOWED_HOSTS=localhost,127.0.0.1
echo.
echo # Supabase PostgreSQL Database Configuration
echo # IPv4-compatible Session Pooler
echo DATABASE_ENGINE=django.db.backends.postgresql
echo DATABASE_NAME=postgres
echo DATABASE_USER=postgres.seuzxvthbxowmofxalmm
echo DATABASE_PASSWORD=Emmkash20
echo DATABASE_HOST=aws-1-eu-west-2.pooler.supabase.com
echo DATABASE_PORT=5432
echo.
echo # Email Configuration
echo EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
echo.
echo # Celery (Optional^)
echo CELERY_BROKER_URL=redis://localhost:6379/0
echo CELERY_RESULT_BACKEND=redis://localhost:6379/0
) > .env

echo [OK] .env file updated
echo.

echo Testing connection to IPv4-compatible pooler...
python -c "import psycopg2; conn = psycopg2.connect(dbname='postgres', user='postgres.seuzxvthbxowmofxalmm', password='Emmkash20', host='aws-1-eu-west-2.pooler.supabase.com', port='5432', connect_timeout=10); print('✓ Connected to Supabase via IPv4 pooler!'); conn.close()"

if errorlevel 1 (
    echo [ERROR] Connection still failed
    echo.
    echo Possible issues:
    echo   1. Firewall blocking port 5432
    echo   2. No internet connection
    echo   3. Supabase project paused
    echo.
    pause
    exit /b 1
)

echo.
echo Running database migrations...
python manage.py migrate
if errorlevel 1 (
    echo [ERROR] Migrations failed
    pause
    exit /b 1
)

echo.
echo Creating admin user...
python setup_admin.py

echo.
echo ============================================================
echo   Success! Supabase PostgreSQL Connected
echo ============================================================
echo.
echo Connection Details:
echo   Host: aws-1-eu-west-2.pooler.supabase.com (IPv4 compatible)
echo   Port: 5432
echo   Database: postgres
echo   User: postgres.seuzxvthbxowmofxalmm
echo.
echo All tables created in Supabase!
echo.
echo To start the server:
echo   python manage.py runserver
echo.
echo Visit: http://127.0.0.1:8000
echo Login: admin / admin123
echo.
echo You can view tables in Supabase Dashboard:
echo https://supabase.com/dashboard
echo.
pause

