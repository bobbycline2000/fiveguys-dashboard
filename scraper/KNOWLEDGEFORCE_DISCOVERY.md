# KnowledgeForce (Marketforce) Scraper — Discovery Notes

**Verified live 2026-04-27** by walking the site via Claude in Chrome. The recurring scraper can be built directly from this — no further discovery needed.

## Login
- **URL:** `https://www.knowledgeforce.com/`
- **Username:** `fg2065@estep-co.com`
- **Password:** stored in Chrome on Bobby's machine; for CI → needs `KNOWLEDGEFORCE_PASSWORD` GitHub Secret added by Bobby
- After login, lands on `/reporting/reports/dashboard`

## Where the data lives
**Report:** `https://www.knowledgeforce.com/reporting/reports/report?id=fgmysteryshop` ("Secret Shop Dashboard")

**Key widgets (XHR endpoint pattern: `/reporting/api/widget/<widget_id>?isDash=1&reportId=<report_id>&dataset=<encoded-filter>`):**

| Widget | reportId | Title | Use |
|---|---|---|---|
| 175636 | 1 | Secret Shop (gauge) | Latest score % |
| 175637 | 2 | Score Trend | Monthly trend chart |
| 175638 | 585 | Category Trend | SQC by month |
| **175639** | **923** | **Individual Shops** | **DataTable — Job# / Location ID / Location / Date / Meal Period / Score** |
| 175640 | 822 | Top Five Questions | Top-scored questions |
| 175641 | 822 | Bottom Five Questions | Lowest-scored questions |

**The Individual Shops DataTable is the source of truth for `shops.json`.** Sample row read live:
```
["20763859", "002065", "Louisville, KY (Dixie Highway)", "04/17/2026", "Lunch", "47.00"]
```
Matches existing `data/raw/marketforce/2065/2026-04-23/shops.json` exactly.

## Filter API
- `GET /reporting/api/filters/903?dataset=%5B%5D` — returns filter tree (Year → Quarter → Month → period2)
- Date scope changes via the `dataset` URL parameter (URL-encoded JSON of selected periods)
- For "all available shops" → select all year checkboxes via DataTables, OR pass empty dataset and read whatever the default is, then iterate

## SQC Per-Shop Breakdown
- The dashboard view shows SQC **averages for the selected date range** (Service / Quality / Cleanliness near top of page)
- For per-shop SQC values (what `shops.json` has), click the Job # link → opens the individual shop detail page
- Detail page URL pattern: TBD — capture during build

## Recurring Scraper Architecture (proposed)

**Trigger:** event-driven, NOT daily cron.
1. `~/.claude/scheduled-tasks/outlook-daily-pull-7am/SKILL.md` (already running 7 AM ET) detects email from `clientserviceshelpdeskuk@marketforce.com` with subject `Five Guys Completed Secret Shop ...`
2. On detection → kicks off `scraper/scrape_knowledgeforce.py`
3. Scraper:
   - Playwright login to knowledgeforce.com (env: `KNOWLEDGEFORCE_USERNAME`, `KNOWLEDGEFORCE_PASSWORD`)
   - Navigate to `/reporting/reports/report?id=fgmysteryshop`
   - Select "All" filters (or pass widened `dataset` param directly to the widget API)
   - Read Individual Shops DataTable (Job # / Location ID / Location / Date / Meal Period / Score)
   - For each new shop (Job # not already in `shops.json`), navigate to that shop's detail page → extract Service / Quality / Cleanliness / CustomerSatisfaction
   - Recompute Week / Month / Quarter rolling averages
   - Write `data/raw/marketforce/2065/<today>/shops.json`
4. `wire_dashboard.py` already reads this file (line 553-587) — Secret Shop card refreshes automatically
5. **If latest shop is 100%** → also draft the names email to `secretshop@estep-co.com` per `_memory/project_secret_shops.md` (payout trigger)

## Open items before build
1. **Bobby:** add `KNOWLEDGEFORCE_USERNAME` and `KNOWLEDGEFORCE_PASSWORD` to GitHub Secrets on `fiveguys-dashboard` repo
2. **Build session:** capture per-shop detail page URL + SQC selectors during the live build (one click on Job # 20763859)
3. **Build session:** wire the email-trigger hook into `outlook-daily-pull-7am` SKILL — when Marketforce shop email is detected, run `scrape_knowledgeforce.py` then re-run `wire_dashboard.py`

## Why this exists
Discovery session 2026-04-27. Captures all live findings so the next session can write `scrape_knowledgeforce.py` end-to-end without re-walking the site. Pairs with `~/.claude/rules/check-the-books-before-building.md`.
