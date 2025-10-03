@echo off
echo ============================================================
echo   Creating All Database Tables
echo ============================================================
echo.

call venv\Scripts\activate.bat

echo Step 1: Creating migrations for all apps...
echo.

echo Creating Core app migrations...
python manage.py makemigrations core
echo.

echo Creating Routers app migrations...
python manage.py makemigrations routers
echo.

echo Creating Profiles app migrations...
python manage.py makemigrations profiles
echo.

echo Creating Customers app migrations...
python manage.py makemigrations customers
echo.

echo Creating Payments app migrations...
python manage.py makemigrations payments
echo.

echo Creating Vouchers app migrations...
python manage.py makemigrations vouchers
echo.

echo Creating Reports app migrations...
python manage.py makemigrations reports
echo.

echo Creating Dashboard app migrations...
python manage.py makemigrations dashboard
echo.

echo Step 2: Applying all migrations to Supabase...
echo.
python manage.py migrate
echo.

if errorlevel 1 (
    echo [ERROR] Migrations failed
    echo Check the error messages above
    pause
    exit /b 1
)

echo [OK] All tables created in Supabase!
echo.

echo Step 3: Creating admin user and sample data...
python setup_admin.py
echo.

echo ============================================================
echo   Success! All Tables Created
echo ============================================================
echo.
echo Your Supabase database now has all tables:
echo   - core_activitylog
echo   - core_notification
echo   - core_systemsetting
echo   - routers_router
echo   - routers_routerlog
echo   - profiles_profile
echo   - customers_customer
echo   - customers_customersession
echo   - payments_payment
echo   - payments_paymentgatewaylog
echo   - vouchers_voucher
echo   - vouchers_voucherbatch
echo   - reports_report
echo.
echo View them in Supabase Dashboard:
echo https://supabase.com/dashboard
echo.
echo To start the server:
echo   python manage.py runserver
echo.
echo Then visit: http://127.0.0.1:8000
echo Login: admin / admin123
echo.
pause

