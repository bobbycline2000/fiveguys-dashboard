# Par Brink API Reference — Store KY-2065

**Status:** DISCOVERY COMPLETE — partial replay viable; not a true JSON API. The Brink admin portal is a server-rendered ASP.NET/MVC app driving DevExpress XtraReports. There are NO JSON endpoints for daily report data — reports are HTML+iframe + DXR.axd PDF/Excel exports.

**Recommendation:** **Stay on email-PDF pickup as the primary path.** Use form-replay (Playwright with persistent profile or a Python `requests` session inheriting Brink cookies) only as a backup for historical / on-demand pulls.

**Last updated:** 2026-05-07 (parbrink-professor agent — initial catalog)

---

## TL;DR

| Question | Answer |
|---|---|
| Does Brink have a usable internal API? | **No JSON API.** It's a server-rendered MVC report runner. Form POST + iframe scrape + DXR.axd PDF export is the only programmatic surface. |
| MFA in the way? | **No.** Username/password login (`fg2065@estep-co.com` / stored pw) succeeds end-to-end without MFA challenge. Verified 2026-05-05 + 2026-05-07 by `bulk_pull_brink_history.py` and Chrome MCP runs. |
| Cookies persist for headless replay? | **Yes** — once authed, `.AspNet.ApplicationCookie` (or equivalent forms-auth cookie) carries session. Persistent Playwright profile at `%LOCALAPPDATA%\scg-brink-profile` confirmed. Cookie-only `requests` replay possible but UNTESTED — DevExpress reports may need anti-forgery tokens. |
| Endpoints discovered for the 4 daily reports? | **One verified end-to-end (Hourly Sales And Labor).** Other 3 (Sales Summary, Discount Summary, Weekly Schedule) follow the same `/Reports/Report/<Name>/` pattern but URL slugs are not yet captured in code. |
| Path forward | Keep email-PDF pickup as primary. Add a Brink-API fallback module for (a) backfill of history and (b) on-demand "pull yesterday again" when an email is missing. Do NOT replace the email pipeline — it's already reliable. |

---

## Portal & login flow

### Hosts
- Customer-facing URL: `https://admin5.brinkpos.net/` → 302 redirects to:
- Actual portal: `https://admin5.parpos.com/`
- Login page: `https://admin5.parpos.com/Public/Login`
- Reports root: `https://admin5.parpos.com/Reports/Report/<ReportName>/`

### Credentials (verified 2026-04-23, used in production scripts)
- Username: `fg2065@estep-co.com`
- Password: `Muscle426$$` (TWO dollar signs — single-$ fails, corrected 2026-04-23)
- Stored in `.env` of `github/fiveguys-dashboard` and inline in `scraper/bulk_pull_brink_history.py`

### Login flow (no MFA)
```
1. GET  https://admin5.parpos.com/Reports/Report/HourlySalesAndLabor/
   -> 302 to /Public/Login if no auth cookie
2. POST /Public/Login (or auto-form-submit page)
   form fields:
     Username     (also accepts 'username' lowercase)
     Password     (also accepts 'password' lowercase)
     submitLogin button OR <input type=submit>
3. -> 302 back to original Reports URL
4. Auth cookie set (forms auth / .AspNet.ApplicationCookie). Cookie persists ~hours.
```

Implemented in `bulk_pull_brink_history.py` lines 124-145.

---

## Location-binding

KY-2065 must be selected on every report request. Brink uses a DevExpress treelist + hidden form fields.

### KY-2065 GUIDs (captured 2026-05-05, in code as constants)
- `LocationsModel.HierarchyControl.LocationValues` = `cb10d857-83f6-4861-8ca7-25952377068f` (replicated 9× comma-joined — Brink's UI does this)
- `LocationsModel.HierarchyControl.LocationGroupValues` = `449,503,502,518,581`
- `LocationsModel.Type` = `SelectLocations`

Two ways to set:
1. **DevExpress JS API (preferred when running in real browser via Chrome MCP):**
   `$('#LocationsTreeListContainer').dxTreeList('instance').selectRows([key], true)`
2. **Form injection (Playwright):** create the three hidden inputs above directly. Used in `bulk_pull_brink_history.py:151-167`.

Server-side `setOrCreate` of these fields persists across the postback. Must re-inject before each new date because the form re-renders.

---

## Report endpoints (HTML+iframe report runner — NOT JSON)

Each report is a server-rendered DevExpress XtraReport viewer page. The pattern is uniform.

### Pattern
```
URL:    https://admin5.parpos.com/Reports/Report/<ReportName>/
Method: GET to load shell, POST same URL to render
Auth:   Forms-auth cookie
Form fields (POST):
  __RequestVerificationToken      (anti-forgery — pulled from page __RequestVerificationToken hidden input)
  DateRangeModel.Date             (M/D/YYYY for single-day reports)
  DateRangeModel.StartDate        (range reports)
  DateRangeModel.EndDate          (range reports)
  LocationsModel.HierarchyControl.LocationValues   (see above, 9× GUID)
  LocationsModel.HierarchyControl.LocationGroupValues
  LocationsModel.Type             ('SelectLocations')
  run-report                      (submit trigger — DOM button id is #run-report)
Response: HTML page containing a DevExpress report viewer iframe.
          The iframe's contentDocument.body.innerText holds the rendered text/grid.
```

### Verified report URLs

| Report | URL slug | Verified |
|---|---|---|
| Hourly Sales And Labor | `/Reports/Report/HourlySalesAndLabor/` | YES — used by bulk pull, captured 49 days |

### Pattern-matched (not yet code-captured but follow same pattern)
| Report | Likely URL slug |
|---|---|
| Sales Summary | `/Reports/Report/SalesSummary/` |
| Discount Summary | `/Reports/Report/DiscountSummary/` |
| Sales And Labor Summary By Location | `/Reports/Report/SalesAndLaborSummaryByLocation/` |
| Sales By Destination | `/Reports/Report/SalesByDestination/` |
| Audit Business Date | `/Reports/Report/AuditBusinessDate/` |
| Hourly Sales And Labor By Section | `/Reports/Report/HourlySalesAndLaborBySection/` |
| Sales By Day | `/Reports/Report/SalesByDay/` |
| Product Mix | `/Reports/Report/ProductMix/` |
| Employee Timecard | `/Reports/Report/EmployeeTimecard/` |
| Labor Cost By Job | `/Reports/Report/LaborCostByJob/` |
| Weekly Labor Schedule | `/Reports/Report/WeeklyLaborSchedule/` |
| Sales Summary By Location | `/Reports/Report/SalesSummaryByLocation/` |

To verify a URL slug, browse to the report once via the Brink left-nav, copy the URL.

### PDF export (DXR.axd)
After report renders in iframe, the toolbar Save/Export button posts to `/DXR.axd` with the rendered ReportInstance ID. This is what `bulk_pull_brink_history.py:210-223` triggers via `page.expect_download()`. The DXR.axd payload is **NOT** easily replayable without browser context — it depends on session-scoped report state. Triggering it via real browser navigation is the path that works.

### Reading without PDF (faster)
For data extraction, scraping the iframe `contentDocument.body.innerText` and regex-parsing rows is faster than PDF download + parse. Working regex for hourly report:
```python
# bulk_pull_brink_history.py:45-47
ROW_RE = re.compile(
    r"(\d{1,2}:\d{2}\s*[AP]M)\s+\$?([\d,]+\.\d{2})\s+(\d+)\s+\$?[\d,]+\.\d{2}\s+(\d+)\s+\$?[\d,]+\.\d{2}\s+([\d,]+\.\d{2})\s+\$?([\d,]+\.\d{2})\s+([\d,]+\.\d{2})%"
)
```
Per-report regexes will need to be written for the other 3 daily reports.

---

## What's NOT a JSON API

To be explicit (Bobby's `reverse-engineer-apis-first.md` rule expected JSON): there is **no `fetch('/api/...')` JSON surface** here. We checked. The Brink admin portal is older-stack ASP.NET MVC + DevExpress server reports. All "data" is rendered server-side into iframe HTML or PDF.

This means the typical lights-out replay (cookie + JSON POST + parse JSON) does NOT apply to Brink the same way it does to CrunchTime/NetChef, Teamworx, or ComplianceMate.

---

## Auth approach summary

| Approach | Status |
|---|---|
| OAuth | Not exposed |
| API key / partner key | Not investigated — would require Brink corporate sales contact |
| Cookie replay (forms auth) | **Working** via Playwright persistent profile |
| Pure `requests` cookie replay | **TESTED 2026-05-07 — INFEASIBLE.** Login + cookie carry works fine. Form POST is hijacked by JavaScript (`#run-report` click runs `runReport()` → `$('form').submit()`; `#download-report` click runs `downloadReport()` → AJAX POST to `/Reports/DownloadReport` with `ForceXlsx=True`). The form POST primes server-side report state but the actual rendered report content is fetched async by the DevExpress XtraReports JS viewer (DXR.axd resource bundle + WebDocumentViewer build/poll/getPage protocol) — that's JS-bound state machine territory. See "Pure-requests spike — what we learned" below. |
| MFA blocker | **None.** This is the surprise — fg2065 has straight password login on Brink even though Microsoft/Office is MFA-locked to Craig. |

---

## Recommended path

### Today (no change)
1. **Email-PDF pickup stays primary.** It's reliable, runs daily, parsers are stable. No reason to disrupt.
2. Daily pipeline: `parbrink_email_pickup.py` → 4 PDF parsers → JSON → `wire_dashboard.py`.

### Next (additive)
3. **Build a Brink-API fallback module** (`scraper/parbrink_api_pull.py`) that wraps the verified bulk-pull pattern, taking `--report <name> --date <iso>` and returning JSON. Use cases:
   - Backfill missing days when email skipped or got eaten
   - On-demand "pull yesterday's discount summary again" without waiting for next email
   - Bulk historical pulls for case-study products (already shipped — `bulk_pull_brink_history.py` is the prototype)
4. **Document each report's regex** in this file as we add them. One-time cost per report.
5. Test pure-`requests` replay (skip Playwright) — if it works, Brink can move from Windows-task to GitHub Actions cron. ~1-2 hour spike.

### Don't
- Replace the email pipeline. It works, it's free, no rate-limit risk, no Brink ToS concern.
- Try to find a JSON API — there isn't one in the admin5 portal.
- Attempt repeated MFA bypass — there's no MFA wall, no need.

---

## Files in this repo that touch the Brink portal directly

| File | Purpose |
|---|---|
| `scraper/bulk_pull_brink_history.py` | Playwright bulk-pull historical Hourly Sales And Labor PDFs |
| `scraper/ingest_brink_downloads.py` | Manual PDF ingest from Bobby's Downloads folder |
| `scraper/pull_brink_history.py` | Earlier Playwright variant (kept for reference) |
| `scraper/parbrink_email_pickup.py` | **Primary path** — Gmail attachment download |
| `scraper/parbrink_parse_*.py` (4 files) | PDF parsers |
| `scraper/build_brink_rolling_curves.py` | Aggregator over historical PDFs/JSONs |

---

## Known data-quality incident — Par Brink source-of-truth labor cost error, 2026-07-16

**This is a POS-side data corruption in the Par Brink report itself, NOT a parser bug.** Logged so a future regression isn't mis-diagnosed as a parser issue and re-investigated from scratch.

- `data/raw/parbrink/2065/2026-07-16/sales_summary.json` had `labor_cost: 11674.10` / `labor_percent: 244.65%` — impossible (would be ~$122/hr average wage on a $4,771.80 net-sales day).
- Confirmed NOT a parsing bug: re-extracted both `Sales Summary.pdf` and the independently-generated `Hourly Sales And Labor.pdf` for the same business date — both PDFs *print* the same bad total ($11,674.10 / 244.65%), and both parsers (`parbrink_parse_sales_summary.py`, `parbrink_parse_hourly_sales_labor.py`) correctly extracted what's on the page.
- Root cause localized via the hourly breakdown: labor $/hr was normal (~$11-12/hr) for every hour EXCEPT 2PM-7PM, where it spiked to $145-$324/hr (e.g. 3PM: $2,146.20 for 7.95 labor-hours). Worked-hours counts for those hours look normal — only the dollar figure is corrupted. Looks like a bad wage-rate/payroll entry on Par Brink's side for whoever worked that window, not a formatting or OCR issue.
- **Corrected using an independent cross-check**: CrunchTime's labor API (`data/labor_today.json` snapshot pulled 2026-07-17T10:50:19 for date=2026-07-16, i.e. the "yesterday" pull) reported `labor_dollars: 1095.87`, `labor_percent: 22.9673%`, `actual_hours: 97.43` — consistent with the 7/15 ($907.68 / 19.74%) and 7/17 ($1,019.62 / 22.94%) figures on either side.
- Fix applied: hand-corrected `data/raw/parbrink/2065/2026-07-16/sales_summary.json` — `labor_cost: 1095.87`, `labor_percent: 22.97`, `labor_hours` left at Brink's own 95.43 (internally consistent, not part of the anomaly). Original bad PDF values preserved in `meta.labor_cost_raw_pdf` / `meta.labor_percent_raw_pdf` for audit trail, plus a `meta.labor_cost_corrected: true` flag and full correction note.
- **No parser code changes** — `parbrink_parse_sales_summary.py` and `parbrink_parse_hourly_sales_labor.py` both did their job correctly; the source PDF itself was wrong. `hourly_sales_labor.json` for 7/16 still contains the raw uncorrected hourly figures (not touched — it's fallback-only per `wire_dashboard.py`, not read by `aggregate_periods.py`, so it doesn't feed the period rollups the watchdog was fixing). If Bobby wants that file corrected too for historical-record cleanliness, flag it — low priority since nothing downstream reads it for 7/16 specifically.
- **If this recurs**: check the Hourly Sales And Labor PDF's per-hour breakdown first — a spike isolated to a few consecutive hours with otherwise-normal worked-hours is the signature of a bad wage-rate entry on Brink's side, not a parser regression. Cross-check against `data/labor_today.json` git history (`git show <commit-for-that-day+1>:data/labor_today.json`) for a same-day CT figure before guessing a corrected number.

## Open work to fully catalog (next sessions)

1. Capture the URL slug for each of the 12 Brink reports listed above (5-min job, browse + copy).
2. Write per-report regex extractors for the 3 daily reports beyond Hourly (Sales Summary, Discount Summary, Audit).
3. ~~Test pure-`requests` cookie replay~~ — **DONE 2026-05-07. INFEASIBLE.** See section below.
4. ~~Inspect the report-shell HTML for `__RequestVerificationToken`~~ — **DONE.** There is none on the report form. Brink's report form has no anti-forgery field; access is gated by the forms-auth `AdminPortal`/`IdToken`/`RefreshToken` cookies set after login.

---

## Pure-requests spike — what we learned (2026-05-07)

**Spike scripts:** swept on 2026-05-07 after the spike concluded — `_brink_requests_spike.py`, `_brink_requests_spike2.py`, `_brink_intercept_playwright.py`, and `_brink_spike_out/` (~796K total) all deleted. Findings below are the conclusion; the scripts are no longer needed.

### What works in pure-requests
- `GET /Reports/Report/HourlySalesAndLabor/` → 302 to `/Public/Login` (when unauthed)
- Login form has `__RequestVerificationToken` hidden input + `ReturnUrl`
- `POST /Public/Login?ReturnUrl=...` with `Username` + `Password` + `__RequestVerificationToken` + `ReturnUrl` → 302 to `/Home/Dashboard/`. Auth cookies set: `AdminPortal`, `IdToken`, `RefreshToken`. **No MFA. Login persists for hours via cookies.**
- Authenticated `GET /Reports/Report/HourlySalesAndLabor/` → 200, returns the report form shell (~83K). Form has NO `__RequestVerificationToken`. All location/date/sales-type fields are visible.

### What breaks
- Authenticated `POST /Reports/Report/HourlySalesAndLabor/` with full form (`ReportType`, `LocationsModel.*` with KY-2065 GUID ×9, `DateRangeModel.*`, `SalesTypeModel.Selected=Net`) → 200, returns ~107K HTML (form shell + DevExpress viewer scaffolding embedded). **Rendered hourly rows are NOT in the response body.** Zero hourly rows; zero iframes with src; no `JSReportLink` config.
- Authenticated `POST /Reports/DownloadReport` (the JS-hijacked endpoint used by `#download-report` button, with `ForceXlsx=False` for PDF or `True` for XLSX) → **500 Application Error**, generic "PAR POS Admin Portal has encountered an error" page. Tried with and without `X-Requested-With: XMLHttpRequest` header.

### Why
The `#run-report` button does NOT do a normal form POST. Inspecting the JS in the report shell:
```js
function runReport() {
    $("#ForceXlsx").val("False");
    blockReportFormAwaitingPostback();
    $('form').submit();
}
function downloadReport() {
    $("#ForceXlsx").val("True");
    $('form').submit(function(event) {
        var data = $(this).serialize();
        var url = '/Reports/DownloadReport';
        submitForm(url, data);
        event.stopImmediatePropagation();
        return false;
    });
}
```
Both paths hand the rendering off to DevExpress XtraReports' JS viewer. The form POST primes server-side report state, then the client-side viewer (`onDocumentViewerInit` + `printHelper.createFrameElement` hooks) drives a multi-step XHR protocol against DXR.axd / WebDocumentViewer endpoints (`StartBuild` → poll `GetBuildStatus` → fetch pages, all using build/instance IDs the JS generates). That state machine is hosted in `/assets/js/main` (DevExpress reporting client SDK).

Replaying it from `requests` would require porting the DevExpress reporting client protocol — multi-hour to multi-day work, and brittle against DevExpress version bumps. The `/Reports/DownloadReport` endpoint that *does* return a file directly returns 500 when called outside the JS context — likely needs the DXR.axd build state to exist first, or different headers/CSRF that we couldn't reproduce.

### Locked recommendation
**Playwright form-replay is the floor for Brink.** Pure-`requests` is infeasible without porting DevExpress client protocol.

The lights-out path for Brink is therefore:
1. **Email-PDF pickup stays primary** (already lights-out via GitHub Actions cron + Gmail/Graph API).
2. Playwright form-replay remains the on-demand / backfill fallback — runs locally on Bobby's Windows tasks, not in CI (Playwright + headed Chrome + DevExpress JS = doesn't fit GH Actions runners cleanly without x11/Xvfb).
3. **Do not invest more time in pure-requests Brink.** The 2-failure pivot per `~/.claude/rules/patch-spiral-prevention.md` is locked: form POST returned shell, DownloadReport returned 500.

### What this DOESN'T affect
- Email-PDF daily pipeline — unchanged, still primary, still works.
- `bulk_pull_brink_history.py` — Playwright form-replay confirmed still works; used for backfill.
- The `parbrink_parse_*.py` parsers — unchanged.

### Spike artifacts (swept 2026-05-07)
All spike scripts and captured response dumps deleted after the spike concluded — conclusion is documented above; raw artifacts no longer needed. Files removed:
- `scraper/_brink_requests_spike.py`
- `scraper/_brink_requests_spike2.py`
- `scraper/_brink_intercept_playwright.py`
- `scraper/_brink_spike_out/` (9 HTML/JSON dumps, ~768K)

Safe to delete in next dedupe sweep.
