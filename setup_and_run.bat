@echo off
echo ============================================
echo   EduPro Student Management System Setup
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+ from python.org
    pause
    exit /b 1
)

echo [1/5] Creating virtual environment...
python -m venv venv
call venv\Scripts\activate

echo [2/5] Installing dependencies...
pip install -r requirements.txt

echo [3/5] Running database migrations...
python manage.py makemigrations sms
python manage.py migrate

echo [4/5] Loading sample data...
python seed_data.py

echo [5/5] Starting development server...
echo.
echo ============================================
echo  Server running at: http://127.0.0.1:8000/
echo  Press CTRL+C to stop
echo ============================================
echo.
python manage.py runserver

pause
