# Five Guys KY-2065 Dashboard — Full Setup Guide

Everything you need to get this running on a new device. Two paths:
- **Path A (recommended):** Clone from GitHub → GitHub Actions runs everything automatically
- **Path B:** Run the scraper locally on your own machine

---

## Credentials You Need (keep these safe)

| What | Value | Where it's used |
|------|-------|-----------------|
| CrunchTime username | `BOBBY.CLINE` | Net Chef login |
| CrunchTime password | *(your password)* | Net Chef login |
| Microsoft email | e.g. `fg2065@estep-co.com` | SharePoint Excel auth |
| Microsoft password | *(your M365 password)* | SharePoint Excel auth |

---

## Path A — GitHub Actions (Runs Automatically Every Morning)

Everything runs in the cloud. You just need a GitHub account.

### Step 1: Clone the repo
```bash
git clone https://github.com/bobbycline2000/fiveguys-dashboard.git
cd fiveguys-dashboard
```

### Step 2: Add GitHub Secrets
Go to: **GitHub → your repo → Settings → Secrets and variables → Actions → New repository secret**

Add these 4 secrets:

| Secret Name | Value |
|-------------|-------|
| `CRUNCHTIME_USERNAME` | `BOBBY.CLINE` |
| `CRUNCHTIME_PASSWORD` | your Net Chef password |
| `MS_USERNAME` | your Microsoft work email |
| `MS_PASSWORD` | your Microsoft password |

### Step 3: Enable GitHub Actions
Go to: **GitHub → your repo → Actions tab → Enable workflows** (if prompted)

### Step 4: Connect Netlify
1. Go to [netlify.com](https://netlify.com) → Add new site → Import from Git
2. Connect to your GitHub repo `fiveguys-dashboard`
3. Build command: *(leave blank)*
4. Publish directory: `.`
5. Deploy — your live dashboard URL will appear

### That's it
Every morning at 8:05 AM Eastern, GitHub Actions will:
1. Log into CrunchTime, scrape yesterday's numbers
2. Update the Netlify dashboard (auto-deploy)
3. Write numbers into the SharePoint Excel file

To trigger a manual run: **Actions tab → "Daily Dashboard Update" → Run workflow**

---

## Path B — Run Locally on Your Computer

Use this to test or run the scraper from your own machine.

### Requirements
- Python 3.11 (download from python.org)
- Git (download from git-scm.com)

### Step 1: Clone the repo
```bash
git clone https://github.com/bobbycline2000/fiveguys-dashboard.git
cd fiveguys-dashboard
```

### Step 2: Install dependencies
```bash
pip install -r scraper/requirements.txt
python -m playwright install chromium
```

### Step 3: Run the scraper
```bash
# Mac / Linux
CRUNCHTIME_USERNAME=BOBBY.CLINE CRUNCHTIME_PASSWORD=yourpassword python scraper/main.py

# Windows (Command Prompt)
set CRUNCHTIME_USERNAME=BOBBY.CLINE
set CRUNCHTIME_PASSWORD=yourpassword
python scraper/main.py

# Windows (PowerShell)
$env:CRUNCHTIME_USERNAME="BOBBY.CLINE"
$env:CRUNCHTIME_PASSWORD="yourpassword"
python scraper/main.py
```

This creates `dashboard.html` and `data/latest.json` in the project folder.

### Step 4: Run the Excel updater (optional)
```bash
# Mac / Linux
MS_USERNAME=fg2065@estep-co.com MS_PASSWORD=yourpassword python scraper/update_excel.py

# Windows PowerShell
$env:MS_USERNAME="fg2065@estep-co.com"
$env:MS_PASSWORD="yourpassword"
python scraper/update_excel.py
```

---

## File Structure (what each file does)

```
fiveguys-dashboard/
│
├── scraper/
│   ├── main.py              ← Playwright scraper + HTML generator
│   │                           Logs into CrunchTime, extracts all metrics,
│   │                           writes dashboard.html and data/latest.json
│   │
│   ├── update_excel.py      ← SharePoint Excel updater
│   │                           Uses Microsoft Graph API to write numbers
│   │                           into the monthly FG Daily Report.xlsx
│   │
│   └── requirements.txt     ← Python packages (playwright, requests)
│
├── dashboard.html           ← Auto-generated daily, served by Netlify
│                               Committed to main → Netlify auto-deploys
│
├── data/
│   └── latest.json          ← JSON snapshot of yesterday's numbers
│
├── .github/
│   └── workflows/
│       └── daily_dashboard.yml  ← GitHub Actions: runs at 8:05 AM ET daily
│
├── netlify.toml             ← Tells Netlify: no build, just serve static files
├── index.html               ← Redirects / → dashboard.html
└── CLAUDE.md                ← Full technical project notes
```

---

## SharePoint Excel File Details

**File:** "April 2026 FG Daily Report.xlsx" on SharePoint  
**Owner (SharePoint):** bdavis@estep-co.com  
**Item ID:** `B759AD2C-2B91-43AC-AC30-6993207012E7`

> **Important:** This Item ID changes each month when a new workbook is created.
> To update it: open the file in SharePoint, copy the `sourcedoc=` value from the URL,
> then update `ITEM_ID` in `scraper/update_excel.py` line 59.

### Column mapping in the Excel sheet (tab: "2065 Dixie")

| Col | Data | Notes |
|-----|------|-------|
| A | Day of month (1–31) | Scraper finds the right row by matching this |
| B | Net Sales | Written by scraper |
| C | Last Year Same Day | Written |
| D | +/- vs LY | **FORMULA — do NOT touch** |
| E | Budget / Forecast | Written |
| F | +/- vs Budget | **FORMULA — do NOT touch** |
| G | Labor % | Written as decimal (23.83% → 0.2383) |
| H | Scheduled Hours | Written |
| I | Actual Hours | Written |
| J | Hours Variance | **FORMULA =I-H — do NOT touch** |
| K | Total Discounts / Comps | Written |
| L | Cash Over/Short | Written |
| M | Deposit | Not in CrunchTime — left blank |
| N | Burger Bags | Not in CrunchTime — left blank |
| O | Burger Buns | Random 4–45 placeholder |
| P | Hot Dog Buns | Random 4–45 placeholder |

---

## Debugging a Failed Run

1. Go to **GitHub → Actions → click the failed run**
2. Download the `debug-artifacts-{run_id}` artifact
3. Check the screenshots: `01_login.png` → `06_dashboard_bottom.png`
4. Check `02b_page_source.html` — what the browser saw at the location picker
5. Check `page_source.html` — what the browser saw when extracting data
6. Look in the Action logs for lines starting with metric names

---

## Scaling to More Stores (Future)

To add a new store, edit two files:

**`scraper/update_excel.py`** — add the store to `STORE_CONFIG` (line ~64):
```python
STORE_CONFIG = {
    "2065": "2065 Dixie",   # active
    "2066": "2066",          # add new store here
}
```

**`.github/workflows/daily_dashboard.yml`** — duplicate the scrape + Excel steps with `STORE_ID: "2066"`.

---

## Technical Notes (CrunchTime is an ExtJS app)

- The login form has a **hidden submit button** — the scraper presses Enter instead
- After login, the URL redirects to `#ChooseLocation` — must select store 2065 before data loads
- The data grid may render as `<div>` elements, not standard `<table>` elements
- The scraper uses **3 extraction strategies** in order: HTML tables → ExtJS divs → raw text parsing
- CrunchTime **lazy-loads rows** — the scraper scrolls 800px twice before extracting
- The workflow uses `xvfb-run` on Linux (virtual display) because the browser runs headed (not headless) for better ExtJS compatibility
