@echo off
setlocal enabledelayedexpansion

echo ======================================================================
echo       Intelligent Sales Forecasting Dashboard - One-Click Launcher
echo ======================================================================
echo.

:: 1. Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.10, 3.11, or 3.12 from https://www.python.org/
    pause
    exit /b 1
)

:: 2. Check and initialize virtual environment
if not exist ".venv" (
    echo [1/4] Creating virtual environment (.venv)...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [1/4] Virtual environment found (.venv).
)

:: 3. Activate virtual environment
echo [2/4] Activating virtual environment...
call .venv\Scripts\activate.bat

:: 4. Copy .env.example to .env if .env doesn't exist
if not exist ".env" (
    if exist ".env.example" (
        echo Copying .env.example to .env...
        copy .env.example .env >nul
    )
)

:: 5. Install / Verify dependencies
echo [3/4] Checking and installing dependencies from requirements.txt...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [WARNING] Some dependencies could not be installed automatically. Attempting to launch anyway...
)

:: 6. Launch Application and open browser
echo [4/4] Starting server at http://127.0.0.1:8000 ...
echo Press Ctrl+C in this terminal window to stop the server.
echo.

start "" "http://127.0.0.1:8000"
python -m uvicorn server:app --host 127.0.0.1 --port 8000 --reload

pause
