#!/bin/bash
echo "============================================"
echo "  EduPro Student Management System Setup"
echo "============================================"
echo ""

echo "[1/5] Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "[2/5] Installing dependencies..."
pip install -r requirements.txt

echo "[3/5] Running database migrations..."
python manage.py makemigrations sms
python manage.py migrate

echo "[4/5] Loading sample data..."
python seed_data.py

echo "[5/5] Starting development server..."
echo ""
echo "============================================"
echo " Server running at: http://127.0.0.1:8000/"
echo " Press CTRL+C to stop"
echo "============================================"
echo ""
python manage.py runserver
