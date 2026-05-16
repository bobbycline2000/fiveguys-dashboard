# STERITECH / OnBrand360 API — FG Store 2065

**Discovered:** 2026-05-16
**Portal:** https://fiveguys.steritech.com (redirects from onbrand360.steritech.com)
**Store:** KY-2065, Louisville | Location ID: 273138

---

## Auth

### Quick-Access (Read-Only, Current CAP Only)

The access code `OBO8R8R2T` authenticates via:

1. Navigate to `https://onbrand360.steritech.com/#/quick-access`
2. Type code into `#quickAccessCode` input, press Enter
3. Redirects to `https://fiveguys.steritech.com/#/quick-access/assessment`

Required request headers for all API calls under quick-access:
```
x-api-version: 856a14b9b017e461bd285c6f21522404119d8126
x-quick-access-code: OBO8R8R2T
Accept: application/json
```

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
API_VERSION = "856a14b9b017e461bd285c6f21522404119d8126"
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

`scraper/scrape_steritech.py` — pulls current CAP via quick-access API, and full history via full login when credentials are available.
