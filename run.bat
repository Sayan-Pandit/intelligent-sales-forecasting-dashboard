@echo off
setlocal enabledelayedexpansion

echo ======================================================================
echo       Intelligent Sales Forecasting Dashboard - One-Click Launcher
echo ======================================================================
echo.

:: 1. Check Python command (try python, then py)
set PYTHON_CMD=
python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python
) else (
    py --version >nul 2>&1
    if not errorlevel 1 (
        set PYTHON_CMD=py
    )
)

if "%PYTHON_CMD%"=="" (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.10, 3.11, or 3.12 from https://www.python.org/
    echo Make sure to check the box "Add python.exe to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: 2. Check and initialize virtual environment
if not exist ".venv" (
    echo [1/5] Creating virtual environment .venv...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [1/5] Virtual environment found: .venv
)

:: 3. Activate virtual environment
echo [2/5] Activating virtual environment...
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo [ERROR] Virtual environment activation script not found.
    pause
    exit /b 1
)

:: 4. Copy .env.example to .env if .env doesn't exist
if not exist ".env" (
    if exist ".env.example" (
        echo Copying .env.example to .env...
        copy .env.example .env >nul
    )
)

:: 5. Install / Verify dependencies
echo [3/5] Checking and installing dependencies from requirements.txt...
python -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [WARNING] Some dependencies could not be installed automatically. Attempting to launch anyway...
)

:: 6. Generate Dataset First before starting the server
echo [4/5] Preparing sales dataset...
python -m src.sample_generator
if not exist "data\sample_sales_data.csv" (
    echo [ERROR] Dataset generation failed. Could not find data\sample_sales_data.csv.
    pause
    exit /b 1
)
echo [4/5] Dataset verified: data\sample_sales_data.csv

:: 7. Launch Application and open browser
echo [5/5] Starting server at http://127.0.0.1:8000 ...
echo Press Ctrl+C in this terminal window to stop the server.
echo.

start "" "http://127.0.0.1:8000"
python -m uvicorn server:app --host 127.0.0.1 --port 8000 --reload

pause
