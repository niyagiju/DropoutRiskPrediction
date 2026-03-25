@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    py -m venv .venv
)

echo Activating virtual environment...
call ".venv\Scripts\activate.bat"

echo Ensuring Flask is installed...
python -m pip install flask >nul 2>&1

echo Starting app on http://127.0.0.1:5000
python app.py

endlocal
