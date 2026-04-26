# Five Guys Daily Dashboard — Project Context

## What This Is
An automated daily operations dashboard for Five Guys restaurant locations.
It scrapes CrunchTime Net Chef, generates a live HTML dashboard (hosted on **GitHub Pages**),
and updates a SharePoint Excel daily report — all automatically every morning.

**Current active location:** KY-2065 Dixie Highway  
**Live dashboard URL:** https://bobbycline2000.github.io/fiveguys-dashboard/dashboard.html  
**Hosting:** GitHub Pages, deployed automatically from `dashboard.html` on the `main` branch  
**Automation:** GitHub Actions runs daily at 8:05 AM Eastern  
**Note:** Netlify was the original host but the project moved to GitHub Pages. Netlify project may still appear in the account; the live site is GitHub Pages.

---

## Business Goals
- **Sellable product:** This system is being built to sell to Five Guys franchisees
- **Consulting business:** Owner plans to offer this as a service to multiple restaurant groups
- **Scale target:** 11 Five Guys locations to start, then expand to other brands
- **Architecture must support:** easy onboarding of new clients/locations with minimal code changes

---

## Architecture

```
GitHub Actions (cron 8:05 AM ET)
    │
    ├── scraper/main.py          ← Playwright scrapes CrunchTime → generates dashboard.html
    ├── scraper/update_excel.py  ← Microsoft Graph API updates SharePoint Excel
    │
    ├── dashboard.html           ← committed to main → GitHub Pages auto-deploys
    └── data/latest.json         ← JSON snapshot of scraped data
```

### Data Flow
1. Playwright (headless Chromium) logs into `https://fiveguysfr77.net-chef.com`
2. Selects location 2065 from the post-login location picker
3. Scrolls down twice (800px each) to load all lazy-rendered rows
4. Extracts Performance Metrics using 3-strategy fallback (see below)
5. Saves `data/latest.json` snapshot
6. Generates `dashboard.html` and commits it to `main`
7. GitHub Pages auto-deploys the new HTML
8. `update_excel.py` writes the same data into the SharePoint Excel file

---

## CrunchTime Net Chef — Critical Technical Notes

**It is an ExtJS application.** This means:
- The UI renders as `<div>` elements, NOT standard `<table>` elements in some versions
- The login form has a hidden `input[type="submit"]` with `class="x-hidden-submit"` — clicking it times out; use `Enter` key instead
- After login, URL redirects to `#ChooseLocation` — must select location 2065 before the dashboard loads
- Data grid may use `.x-grid-row` / `.x-grid-cell-inner` div selectors

**Login:** `do_login()` fills username/password then presses Enter (skips hidden submit)  
**Location selection:** `select_location()` tries 13 CSS selectors + JS text-search fallback  
**Data extraction:** `extract_performance_metrics()` uses 3 strategies in order:
  1. HTML `<table>/<tr>/<td>` — fastest
  2. ExtJS div grid (`.x-grid-row`, `.x-grid-cell-inner`)
  3. Full page `inner_text()` parsing — searches for known metric label names

**Metrics extracted from CrunchTime:**
- Actual Net Sales, Last Year Same Day, Forecasted Sales
- Net Sales vs LY, Labor $ Cost, Labor % of Net Sales
- Actual Hours, Scheduled Hours, Hours Variance
- Labor Productivity, Total Cash Over/Short
- Comps & Discounts (multiple rows)

**Scroll requirement:** CrunchTime lazy-loads rows. Must scroll 800px twice before extracting.

---

## SharePoint Excel File

**File:** "April 2026 FG Daily Report.xlsx" on SharePoint  
**Owner:** bdavis@estep-co.com  
**Item ID:** `B759AD2C-2B91-43AC-AC30-6993207012E7` — update monthly when new workbook created  
**API:** Microsoft Graph with client credentials OAuth (no user login required)

### Column Mapping (sheet tab = store ID, e.g. "2065")
| Column | Data | Notes |
|--------|------|-------|
| A | Day of month (1–31) | Used to find the right row |
| B | Net Sales | Written |
| C | Last Year Same Day | Written |
| D | +/- vs LY | **FORMULA — do NOT overwrite** |
| E | Budget/Forecast | Written |
| F | +/- vs Budget | **FORMULA — do NOT overwrite** |
| G | Labor % | Written as decimal (e.g. 0.2383) |
| H | Scheduled Hours | Written |
| I | Actual Hours | Written |
| J | Hours Variance | **FORMULA =I-H — do NOT overwrite** |
| K | Total Discounts | Written |
| L | Cash Over/Short | Written |
| M | Deposit | Not available — skipped |
| N | Burger Bags | Not available — skipped |
| O | Burger Buns | `random.randint(4, 45)` placeholder |
| P | Hot Dog Buns | `random.randint(4, 45)` placeholder |

---

## GitHub Secrets Required

| Secret | Description |
|--------|-------------|
| `CRUNCHTIME_USERNAME` | Net Chef login (currently BOBBY.CLINE) |
| `CRUNCHTIME_PASSWORD` | Net Chef password |
| `MS_TENANT_ID` | Azure AD Directory ID |
| `MS_CLIENT_ID` | Azure App Registration client ID |
| `MS_CLIENT_SECRET` | Azure App Registration client secret |

---

## File Structure

```
/
├── CLAUDE.md                  ← this file — read at start of every session
├── dashboard.html             ← auto-generated daily, served by GitHub Pages
├── index.html                 ← redirects / → dashboard.html
├── requirements.txt           ← playwright==1.44.0, requests==2.31.0
├── scraper/
│   ├── main.py               ← Playwright scraper + HTML generator
│   └── update_excel.py       ← SharePoint Excel updater via Graph API
├── data/
│   ├── latest.json           ← JSON snapshot committed daily
│   ├── page_source.html      ← debug: full DOM after scrape (not committed)
│   ├── page_text.txt         ← debug: page inner text (not committed)
│   └── *.png                 ← debug screenshots (not committed)
└── .github/
    └── workflows/
        └── daily_dashboard.yml  ← GitHub Actions workflow
```

---

## Scaling to Multiple Locations

The code is designed to scale. To add a new store:

**`scraper/update_excel.py`** — add to `STORE_CONFIG`:
```python
STORE_CONFIG = {
    "2065": "2065",   # Dixie Highway — ACTIVE
    "2066": "2066",   # add new store here
}
```

**`.github/workflows/daily_dashboard.yml`** — duplicate the scrape + Excel steps with different `STORE_ID` env var.

**`scraper/main.py`** — `NETCHEF_BASE` and login are shared; store selection handles each location.

For a multi-client consulting product, each client would get:
- Their own GitHub repo (fork of this one)
- Their own GitHub Pages site (or other static host)
- Their own GitHub Secrets (credentials)
- Their own SharePoint Excel item ID

---

## Known Issues / Current Status

- **Location selection:** Recently rewritten to handle ExtJS div-based picker with 13-selector fallback + JS text search. Not yet confirmed working — run a manual GitHub Actions workflow to test.
- **Data extraction:** Three-strategy fallback added (tables → ExtJS divs → text parsing). Saves `page_source.html` and `page_text.txt` as debug artifacts every run.
- **SharePoint Excel:** `continue-on-error: true` in workflow — won't block dashboard if Azure secrets not configured.
- **Burger Buns / Hot Dog Buns:** Physical counts not in CrunchTime — using `random.randint(4, 45)` as placeholder.

## How to Debug a Failed Run

1. Go to GitHub → Actions → click the failed run
2. Download the `debug-artifacts-{run_id}` artifact
3. Check `02b_page_source.html` — this is what the browser saw at the location picker
4. Check `page_source.html` — this is what the browser saw when extracting data
5. Check screenshots `01_login.png` through `06_dashboard_bottom.png`
6. Look at the Action logs for lines starting with the metric names

---

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt
python -m playwright install chromium

# Run scraper manually
CRUNCHTIME_USERNAME=BOBBY.CLINE CRUNCHTIME_PASSWORD=yourpassword python scraper/main.py

# Run Excel updater manually
MS_TENANT_ID=... MS_CLIENT_ID=... MS_CLIENT_SECRET=... STORE_ID=2065 python scraper/update_excel.py
```
