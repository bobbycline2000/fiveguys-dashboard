#!/bin/bash
# ── Five Guys Dashboard — Mac/Linux Setup & Run ──────────────────────────────
# Run this once on any Mac or Linux machine to set up and run the dashboard.

set -e

echo ""
echo " Five Guys Dashboard Setup"
echo " =========================="
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo " ERROR: Python 3 is not installed."
    echo " Mac: brew install python3  |  Linux: sudo apt install python3"
    exit 1
fi

echo " Python found. Installing dependencies..."
pip3 install -r scraper/requirements.txt

echo " Installing Playwright browser..."
python3 -m playwright install chromium

# Check for .env
if [ ! -f .env ]; then
    echo ""
    echo " WARNING: No .env file found."
    cp .env.example .env
    echo " .env file created — edit it with your credentials, then run this script again."
    echo ""
    exit 0
fi

echo ""
echo " Setup complete. Running dashboard..."
echo ""
python3 run.py

echo ""
echo " Done. Open dashboard.html to view the result."
