@echo off
REM ── Five Guys Dashboard — Windows Setup & Run ────────────────────────────────
REM Double-click this file on any Windows machine to set up and run the dashboard.

echo.
echo  Five Guys Dashboard Setup
echo  ==========================
echo.

REM Check Python
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo  ERROR: Python is not installed or not in PATH.
    echo  Download from https://www.python.org/downloads/
    echo  Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

echo  Python found. Installing dependencies...
pip install -r scraper\requirements.txt
IF ERRORLEVEL 1 (
    echo  ERROR: pip install failed.
    pause
    exit /b 1
)

echo  Installing Playwright browser...
python -m playwright install chromium
IF ERRORLEVEL 1 (
    echo  ERROR: Playwright install failed.
    pause
    exit /b 1
)

REM Check for .env file
IF NOT EXIST .env (
    echo.
    echo  WARNING: No .env file found.
    echo  Copy .env.example to .env and fill in your credentials before running.
    echo.
    copy .env.example .env
    echo  .env file created — please edit it with your credentials, then run this script again.
    pause
    exit /b 0
)

echo.
echo  Setup complete. Running dashboard...
echo.
python run.py

echo.
echo  Done. Open dashboard.html to view the result.
pause
