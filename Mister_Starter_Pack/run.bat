@echo off
if not exist venv (
    echo [!] Virtual environment not found. Creating...
    python -m venv venv
    call venv\Scripts\activate
    echo [!] Installing dependencies...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)
python scripts/run.py
pause
