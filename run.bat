@echo off
:: Kill any existing python processes to avoid "Conflict" errors
taskkill /F /IM python.exe /T 2>nul
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
