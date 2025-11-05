@echo off
cd /d %~dp0
echo.
echo ========================================
echo  CondorShop - Django Backend
echo ========================================
echo.
echo Running migrations...
echo.
.venv\Scripts\python.exe manage.py migrate
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo  ERROR: Migration failed
    echo ========================================
    echo.
    echo If you see "Access denied" error:
    echo   1. Open backend\.env file
    echo   2. Change DB_PASSWORD=CAMBIAME to your actual MySQL password
    echo   3. Run this script again
    echo.
    echo If the error persists, check:
    echo   - MySQL server is running
    echo   - Database 'condorshop' exists
    echo   - MySQL credentials are correct
    echo.
    pause
    exit /b %ERRORLEVEL%
)
echo.
echo ========================================
echo  Migrations completed successfully!
echo ========================================
echo.
echo Starting Django server...
echo Server will be available at: http://127.0.0.1:8000/
echo Press Ctrl+C to stop the server
echo.
.venv\Scripts\python.exe manage.py runserver
pause

