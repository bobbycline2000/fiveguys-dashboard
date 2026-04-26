@echo off
REM ── Savior Consulting Group Dashboard — First-Install Setup ────────────────
REM Double-click this file once when you first install the dashboard.
REM It will guide you through connecting your store's Gmail account.

cd /d "%~dp0"

python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo.
    echo  ERROR: Python is not installed on this PC.
    echo.
    echo  Download Python from: https://www.python.org/downloads/
    echo  During install, check the box that says "Add Python to PATH".
    echo  Then come back and double-click this file again.
    echo.
    pause
    exit /b 1
)

python "%~dp0scraper\scg_setup.py"
set RC=%ERRORLEVEL%

echo.
pause
exit /b %RC%
