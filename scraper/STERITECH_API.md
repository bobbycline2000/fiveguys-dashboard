# STERITECH / OnBrand360 API — FG Store 2065

**Discovered:** 2026-05-16 | **Updated:** 2026-07-11
**Portal:** https://fiveguys.steritech.com (redirects from onbrand360.steritech.com)
**Store:** KY-2065, Louisville | Location ID: 273138

## 2026-07-11 update — dashboard wiring + two live bugs found and fixed

The dashboard's Steritech card (`dashboard.html` ~line 1074) was **hardcoded** ("100", "Last Audit Mar 28", "Next Audit Due May 28") — never actually wired to real data, even though this API catalog and `scrape_steritech.py` had existed since 2026-05-16. Fixed:

1. **`x-api-version` header drift.** The hardcoded value from 2026-05-16 (`856a14b9b017e461bd285c6f21522404119d8126`) now returns `412 {"errors":["Wrong api version"]}`. The live value (confirmed 2026-07-11) is `588d53564a96485db9be0dca2bcc09564107847e`, extracted from `constant("apiVersion","...")` inside `/assets/app_prod/app-*.js`. **This header is NOT stable across Steritech frontend deploys** — `scrape_steritech.py` now self-discovers it on every run (`discover_api_version()`) instead of hardcoding it, so this won't need a manual patch again.
2. **Quick-access code `OBO8R8R2T` is EXPIRED** as of 2026-07-11 — `/api/quick_access/assessment/sign_in` returns `401 {"errors":{"base":["Quick Access Code expired"]}}` even with the correct api-version. This is a hard blocker: a new code must be generated from the OnBrand360/Steritech portal (or Bobby's rep), OR `STERITECH_PASSWORD` needs to be added as a GitHub Actions secret so `--full-history` (email+password) can be used instead. `scrape_steritech.py` now raises `QuickAccessCodeExpired` and exits code 2 cleanly rather than crashing on this.
3. **New canonical data file: `data/steritech.json`.** `scrape_steritech.py` now writes this via `build_canonical()` in addition to its raw `--output` dump. Schema: `latest_score`, `status` (Pass/Fail/Unknown), `last_audit_date`, `round_title`, `next_audit_window`, `cap_due_date`, `critical_violations`, `non_critical`, `findings[]` (code/title/severity/repeat), `line_item_checks` (`hand_wash_stations`/`cooler_temps`/`grill_hold_temps`/`date_labels` — these 4 are the dashboard card's fixed spot-check rows, not a Steritech-native grouping; a finding flags the matching row "watch" if its title mentions the keyword).
4. **`scraper/wire_dashboard.py`** now has a Steritech block (search `# ── Steritech (food safety) card`) that reads `data/steritech.json` and replaces every previously-hardcoded value in the card via `id`-anchored regex (`st-score`, `st-goal`, `st-meta`, `st-status-overall`, `st-critical-val`, `st-noncritical-val`, `st-check-handwash`, `st-check-cooler`, `st-check-grill`, `st-check-datelabels`, `st-next-audit`).
5. **New monthly workflow: `.github/workflows/steritech_monthly.yml`** — runs 1st of month, 6 AM ET. Snapshots the old `data/steritech.json`, scrapes (full-history if `STERITECH_PASSWORD` secret present, else quick-access), wires the dashboard, runs `scraper/steritech_alert_check.py` to detect a NEW audit / sub-100 / sub-90 score and append an alert to `data/team_notes.json`, commits + pushes. `continue-on-error` on the scrape step so an auth failure doesn't kill the job.
6. **Last verified real score used to seed `data/steritech.json`:** 98%, visit 2026-05-14 (Q2 2026, Max Luken), 0 critical / 2 non-critical findings (item 225 ceiling debris, item 236 tile/grout), CAP due 2026-05-19. This matches the documented history table below and `_memory/handoffs/2026-05-14-1632-steritech-cap-and-mmcca-q2-workbook.md`.

---

## Auth

### Quick-Access (Read-Only, Current CAP Only)

The access code `OBO8R8R2T` authenticates via:

1. Navigate to `https://onbrand360.steritech.com/#/quick-access`
2. Type code into `#quickAccessCode` input, press Enter
3. Redirects to `https://fiveguys.steritech.com/#/quick-access/assessment`

**⚠ Confirmed EXPIRED 2026-07-11** — step 1 (`/api/quick_access/assessment/sign_in`) now returns `401 {"errors":{"base":["Quick Access Code expired"]}}`. Needs a new code from the OnBrand360/Steritech portal or Bobby's rep contact, updated in `QUICK_ACCESS_CODE` in `scrape_steritech.py`.

Required request headers for all API calls under quick-access:
```
x-api-version: 588d53564a96485db9be0dca2bcc09564107847e   (confirmed 2026-07-11; drifts on Steritech deploys — see below)
x-quick-access-code: OBO8R8R2T
Accept: application/json
```

**`x-api-version` is NOT a stable constant.** It changed at least once already: `856a14b9b017e461bd285c6f21522404119d8126` (2026-05-16) → `588d53564a96485db9be0dca2bcc09564107847e` (2026-07-11), and using the stale value returns `412 {"errors":["Wrong api version"]}`. `scrape_steritech.py`'s `discover_api_version()` extracts the live value from the app's JS bundle (`GET /` → find `/assets/app_prod/app-*.js` script src → `GET` it → regex `constant\("apiVersion","([0-9a-f]{40})"\)`) on every run, so this doc's value is a snapshot, not a source of truth — trust the scraper's live discovery over this file.

**Session:** Cookie-based. The browser session is established on redirect. No Bearer token needed — cookies carry the session.

### Full Login (Required for Historical Data)

- URL: `https://fiveguys.steritech.com/#/sign-in`
- Email: `rcline@estep-co.com`
- Password: **not stored — Bobby must provide**
- Auth endpoint: `POST /api/users/sign_in` (standard Devise, inferred)
- Grants access to: all historical assessments, full reporting, location performance

---

## Endpoints

### Quick-Access Tier (access code only)

| Method | Endpoint | Returns |
|--------|----------|---------|
| GET | `/api/quick_access/assessment/sign_in` | Validates access code, sets session |
| GET | `/api/quick_access/assessment` | **Current open CAP only** — JSON (see schema below) |
| POST | `/api/quick_access/announcements/not_viewed?page=0&per_page=25` | Unread announcements |
| GET | `/api/environment_variables/cookie_policy_link` | Cookie policy URL |
| GET | `/api/environment_variables/support_cell_phone` | Support number |
| GET | `/api/whitelabeling?subdomain=fiveguys` | Branding config |
| GET | `/api/localizations/en` | UI strings |
| GET | `/api/links` | Navigation links |

**CRITICAL:** Quick-access only exposes the **current open CAP**. There is no `/history`, `/past_assessments`, or `/reports` endpoint under the quick-access tier. All return 404. Historical data requires full login.

### Full Login Tier (email + password — not yet implemented)

| Method | Endpoint | Expected Returns |
|--------|----------|-----------------|
| GET | `/api/corrective_action_plans?location_id=273138` | All CAPs for location (returns 401 without full login) |
| GET | `/api/assessments?location_id=273138` | All assessment results (returns 401 without full login) |

These return `{"errors": "You need to sign in before continuing."}` with quick-access cookie only.

---

## Current Assessment Response Schema

`GET /api/quick_access/assessment` returns:

```json
{
  "corrective_action_plan": {
    "id": 2309335,
    "status": "in_review",
    "due_date": "2026-05-20T03:59:59Z",
    "submitted_at": "2026-05-14T16:31:02Z",
    "time": "on_schedule",
    "quick_access_code": "OBO8R8R2T",
    "line_items": [
      {
        "code": "225",
        "title": "Floors, walls, and ceilings free of dust, debris...",
        "risk_level": 2,
        "repeat": false,
        "action_items": [
          {
            "id": 20777496,
            "status": "addressed",
            "issue_lbr_result": "Other",
            "location_lbr_result": "Cook line",
            "details_lbr_result": "Ceiling",
            "department": "Food Safety",
            "required_date": "2026-05-14",
            "course_of_action": "...",
            "photos": [...],
            "attachments": [...]
          }
        ]
      }
    ]
  },
  "assessment": {
    "id": 5662370,
    "assessment_type": "assessment",
    "finish_date": "2026-05-14T10:42:03Z",
    "score": "98",
    "round": { "id": 77575, "title": "Q2 2026", "start_date": "2026-04-01", "end_date": "2026-06-23" },
    "service": { "id": 153, "title": "Five Guys Enterprises LLC" },
    "location": { "id": 273138, "title": "2065", "city": "Louisville", "state": "KY" },
    "reports": {
      "lbr": { "filename": "Assessment Report", "token": "01d02fb3e28e99..." },
      "performance_summary_report": { "filename": "Performance Summary Report", "token": "7769d2..." }
    }
  },
  "configuration": {
    "days_to_respond": 3,
    "include_weekends": false
  }
}
```

**risk_level mapping:** 1 = Critical, 2 = Non-Critical

---

## Known Historical Visit Dates (from report chart, store 2065)

Extracted from Q2 2026 assessment PDF chart — both assessments track the same visit dates:

| Visit Date | Quarter | Steritech Score | MMCCA Score (lower=better) |
|------------|---------|----------------|---------------------------|
| Nov 27, 2024 | Q4 2024 | 88 | 19 |
| Jan 2, 2025 | Q1 2025 | 97 | 14 |
| Jun 12, 2025 | Q2 2025 | 97 | 13 |
| Aug 30, 2025 | Q3 2025 | 97 | 9 |
| Nov 25, 2025 | Q4 2025 | ~97 | 9 |
| Feb 19, 2026 | Q1 2026 | 100 | 4 |
| May 14, 2026 | Q2 2026 | 98 | 6 |

**Line-item detail** for visits prior to Q2 2026 requires full portal login.

---

## Login Flow (for full history pull — awaiting credentials)

```python
import requests

BASE = "https://fiveguys.steritech.com"
API_VERSION = "588d53564a96485db9be0dca2bcc09564107847e"  # discover live, don't hardcode — see note above
LOCATION_ID = 273138

session = requests.Session()
session.headers.update({
    "x-api-version": API_VERSION,
    "Accept": "application/json",
    "Content-Type": "application/json",
})

# Step 1: Login
resp = session.post(f"{BASE}/api/users/sign_in", json={
    "user": {"email": "rcline@estep-co.com", "password": "PASSWORD_NEEDED"}
})
# On success: cookies set, user object returned

# Step 2: Pull all CAPs for location
caps = session.get(f"{BASE}/api/corrective_action_plans", params={"location_id": LOCATION_ID})

# Step 3: Pull all assessments
assessments = session.get(f"{BASE}/api/assessments", params={"location_id": LOCATION_ID})
```

---

## MMCCA vs Steritech — Critical Distinction

These are TWO SEPARATE assessments per visit, both by Max Luken, same day:
- **Steritech Food Safety Assessment** — scored 0-100%, lower score = more points deducted. Files: `FiveGuysFoodSafetyAssessment__*.pdf`
- **MMCCA (Matt Murrell Cleanliness & Condition Assessment)** — scored as "Core Issues" count, LOWER IS BETTER. Files: `FiveGuysMattMurrellCleanliness_ConditionAssessment__*.pdf`

Never combine or conflate these two.

---

## Playwright Login Notes

- The quick-access code input has `id="quickAccessCode"` but value must be set via `pressSequentially()` with submit=True (type + Enter). `form_input` and native Angular binding methods do not register.
- `form_input` and JS value injection do NOT trigger Angular's change detection — use Playwright native `pressSequentially` + Enter.
- File upload is hard-blocked (`mcp__Claude_in_Chrome__file_upload` returns 403; CDP upload blocked).

---

## Scraper Script

`scraper/scrape_steritech.py` — pulls current CAP via quick-access API, and full history via full login when credentials are available. Writes two files:
- `--output` (default `data/steritech_current.json`) — raw API payload, archival/debug.
- `--canonical-output` (default `data/steritech.json`) — the dashboard-schema file `wire_dashboard.py` actually reads (see `build_canonical()`).

Exit codes: `0` success, `1` missing `STERITECH_PASSWORD` for `--full-history`, `2` quick-access code expired (`QuickAccessCodeExpired`).

## Dashboard Wiring

`scraper/wire_dashboard.py` (search `# ── Steritech (food safety) card`) reads `data/steritech.json` and replaces the card's score, last-audit date, overall status, critical/non-critical counts, the 4 spot-check rows (hand wash / cooler / grill hold / date labels), and the next-audit-window label — all via `id`-anchored regex, idempotent across repeated runs.

## Alert Routing

`scraper/steritech_alert_check.py` compares the pre-scrape snapshot of `data/steritech.json` to the freshly-scraped one. If the audit date or score changed AND the new score is below 100, it appends an alert (`role: "alert"`, `from: "Steritech"`) to `data/team_notes.json` so both the dashboard Team Notes card and the daily brief surface it. Silent no-op if nothing changed or the score is a clean 100 — avoids monthly noise for an already-known quarterly result.

## Monthly Workflow

`.github/workflows/steritech_monthly.yml` — 1st of month, 6 AM ET (`cron: "0 10 1 * *"`, flip to `11` when EST returns). Order: snapshot old `steritech.json` → scrape (full-history if `STERITECH_PASSWORD` secret set, else quick-access) → `wire_dashboard.py` → `steritech_alert_check.py` → commit + push. Scrape step uses `continue-on-error` so an expired quick-access code logs a `::warning::` and keeps last-known data instead of failing the whole job.
