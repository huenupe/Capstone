@echo off
cd /d %~dp0
echo Installing/upgrading pip...
.\venv\Scripts\python.exe -m ensurepip --default-pip
echo.
echo Installing requirements...
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt
echo.
echo Starting Django server...
echo Server will be available at: http://127.0.0.1:8000/
echo Press Ctrl+C to stop the server
echo.
.\venv\Scripts\python.exe manage.py runserver
pause

