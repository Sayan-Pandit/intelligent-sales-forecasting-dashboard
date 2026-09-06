#!/usr/bin/env bash

# ======================================================================
#       Intelligent Sales Forecasting Dashboard - One-Click Launcher
# ======================================================================

set -e

echo "======================================================================"
echo "      Intelligent Sales Forecasting Dashboard - Setup & Launch        "
echo "======================================================================"
echo ""

# 1. Determine Python command (python3 or python)
if command -v python3 &>/dev/null; then
    PYTHON_CMD=python3
elif command -v python &>/dev/null; then
    PYTHON_CMD=python
else
    echo "[ERROR] Python is not installed or not in PATH."
    echo "Please install Python (3.10-3.12 recommended) from https://www.python.org/"
    exit 1
fi

# 2. Check and initialize virtual environment
if [ ! -d ".venv" ]; then
    echo "[1/4] Creating virtual environment (.venv)..."
    $PYTHON_CMD -m venv .venv
else
    echo "[1/4] Virtual environment found (.venv)."
fi

# 3. Activate virtual environment
echo "[2/4] Activating virtual environment..."
source .venv/bin/activate

# 4. Copy .env.example to .env if .env doesn't exist
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "Copying .env.example to .env..."
    cp .env.example .env
fi

# 5. Install / Verify dependencies
echo "[3/5] Checking and installing dependencies from requirements.txt..."
pip install -r requirements.txt --quiet || echo "[WARNING] Some dependencies had warnings. Continuing..."

# 6. Generate Dataset First before starting the server
echo "[4/5] Preparing sales dataset..."
python -m src.sample_generator
if [ ! -f "data/sample_sales_data.csv" ]; then
    echo "[ERROR] Dataset generation failed. Could not find data/sample_sales_data.csv."
    exit 1
fi
echo "[4/5] Dataset verified: data/sample_sales_data.csv"

# 7. Launch Application and open browser
echo "[5/5] Starting server at http://127.0.0.1:8000 ..."
echo "Press Ctrl+C to stop the server."
echo ""

# Try opening the browser in the background based on OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    (sleep 1 && open "http://127.0.0.1:8000") &
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    (sleep 1 && xdg-open "http://127.0.0.1:8000" 2>/dev/null) &
fi

python -m uvicorn server:app --host 127.0.0.1 --port 8000 --reload

