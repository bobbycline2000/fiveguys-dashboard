@echo off
REM ── Teamworx Daily Roster Scrape — runs at 7:45 AM via Windows Task Scheduler ──
REM Scrapes today's published roster from Teamworx and pushes the JSON to GitHub
REM so the 8:05 AM CI run can wire it into dashboard.html.
REM
REM Log file: data\teamworx_task_log.txt  (appended each run)
REM ─────────────────────────────────────────────────────────────────────────────

set REPO=C:\Users\bobby\OneDrive\BobbyWorkspace\github\fiveguys-dashboard
set LOG=%REPO%\data\teamworx_task_log.txt

cd /d "%REPO%"

echo. >> "%LOG%"
echo ======================================== >> "%LOG%"
echo %DATE% %TIME% — Teamworx daily scrape started >> "%LOG%"
echo ======================================== >> "%LOG%"

REM ── Load credentials from .env ───────────────────────────────────────────────
for /f "usebackq tokens=1,* delims==" %%A in ("%REPO%\.env") do (
    if not "%%A"=="" if not "%%A:~0,1%"=="#" set "%%A=%%B"
)

REM ── Run Teamworx roster scraper ───────────────────────────────────────────────
echo [SCRAPE] Running scrape_teamworx_roster.py --store 2065 >> "%LOG%"
python "%REPO%\scraper\scrape_teamworx_roster.py" --store 2065 >> "%LOG%" 2>&1

if errorlevel 1 (
    echo [ERROR] Teamworx scraper failed — skipping git push >> "%LOG%"
    echo %DATE% %TIME% — FAILED >> "%LOG%"
    exit /b 1
)

echo [OK] Scrape succeeded >> "%LOG%"

REM ── Stage only today's schedule JSON ─────────────────────────────────────────
for /f "tokens=1-3 delims=-/" %%a in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do (
    set TODAY=%%a-%%b-%%c
)
set JSON_PATH=data\raw\parbrink\2065\%TODAY%\weekly_schedule.json

if not exist "%REPO%\%JSON_PATH%" (
    echo [ERROR] Expected file not found: %JSON_PATH% >> "%LOG%"
    echo %DATE% %TIME% — FAILED (file missing) >> "%LOG%"
    exit /b 1
)

echo [GIT] Staging %JSON_PATH% >> "%LOG%"
git add "%JSON_PATH%" >> "%LOG%" 2>&1

REM Check if there's anything to commit
git diff --cached --quiet
if not errorlevel 1 (
    echo [GIT] No changes to commit — roster already up to date >> "%LOG%"
    echo %DATE% %TIME% — OK (no-op) >> "%LOG%"
    exit /b 0
)

REM ── Commit and push ──────────────────────────────────────────────────────────
git commit -m "chore: Teamworx roster %TODAY% (local task)" >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [ERROR] git commit failed >> "%LOG%"
    echo %DATE% %TIME% — FAILED (commit) >> "%LOG%"
    exit /b 1
)

git pull --rebase -X theirs --autostash origin main >> "%LOG%" 2>&1
git push origin main >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [ERROR] git push failed >> "%LOG%"
    echo %DATE% %TIME% — FAILED (push) >> "%LOG%"
    exit /b 1
)

echo [OK] Pushed to origin/main >> "%LOG%"
echo %DATE% %TIME% — SUCCESS >> "%LOG%"
exit /b 0
