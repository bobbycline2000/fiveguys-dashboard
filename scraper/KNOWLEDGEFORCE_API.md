# KnowledgeForce API — Reverse-Engineered Catalog

**Status:** API replay VIABLE. The current Playwright UI scraper is already calling the JSON widget API directly via `page.evaluate(fetch(...))` — the only browser dependency is the cookie session. Replacing Playwright + Xvfb with a pure `requests.Session` is a contained refactor.

**Promoted from:** `KNOWLEDGEFORCE_DISCOVERY.md` (2026-04-27)
**Promoted on:** 2026-05-07
**Vendor:** KnowledgeForce (downstream of Marketforce — KF holds scoring/reporting; MF holds shopper-side submission and the 100%-payout email trigger)

---

## Portal & Auth

| Item | Value |
|---|---|
| Portal root | `https://www.knowledgeforce.com/` |
| Post-login landing | `/reporting/reports/dashboard` |
| Username | `fg2065@estep-co.com` (env: `KNOWLEDGEFORCE_USERNAME`) |
| Password | env: `KNOWLEDGEFORCE_PASSWORD` (already a GitHub Secret per discovery doc) |
| MFA | None observed in the production scraper's login flow (`login()` at `scrape_knowledgeforce.py:62`) — straight `username` + `password` form POST, no second factor |
| Session | Standard cookie-session. After form POST, all subsequent `/reporting/api/*` calls work with `credentials: 'include'`. |

### Auth flow (replayable in pure HTTP)
1. `GET https://www.knowledgeforce.com/` — fetch any CSRF cookies / form action
2. `POST` the login form with `username` + `password` fields (form action determined from step 1; the production scraper uses the green "LOG IN" button which submits a standard form — no AJAX login wrapper observed)
3. Verify success by absence of `/login` in the redirect URL and absence of "username" in the body
4. Reuse the `Session` cookies for all `/reporting/api/*` calls

### Auth approach for the API client
Pure `requests.Session()` — no browser, no Xvfb, no Playwright. Two-step:
```python
s = requests.Session()
s.get("https://www.knowledgeforce.com/")  # land cookies
s.post("https://www.knowledgeforce.com/login", data={"username": USER, "password": PW})
# now s has the auth cookies — hit widget endpoints directly
```

If the login POST endpoint is not literally `/login`, capture it during the first build session via DevTools Network or a one-shot Playwright pass with `page.on('request')` printing all POSTs.

---

## Endpoints discovered

All endpoints are JSON over HTTPS. Cookies from the login session carry auth — no bearer tokens, no separate API key.

### 1. Filter tree (period selector)

```
GET /reporting/api/filters/903?dataset=%5B%5D
```

**Response:** Tree (Year → Quarter → Month → period2). Used to enumerate all available reporting periods so the widget call can pull "all shops ever" by passing every leaf period ID in the dataset.

**Production-scraper usage:** `scrape_knowledgeforce.py:208` — fetches this, walks tree with `_extract_all_period_ids()`, builds the dataset payload for the widget call.

### 2. Widget API — generic shape

```
GET /reporting/api/widget/<widget_id>?isDash=1&reportId=<report_id>&dataset=<encoded-json>
```

**`dataset` param:** URL-encoded JSON. Empty `[]` returns the default range. To pull all shops, build:
```json
[{"id": "period2", "values": [<all leaf period IDs from filter tree>]}]
```
…then `urllib.parse.quote(json.dumps(...))` it.

**Response shape:** DataTables server-side format — `{"aaData": [...]}` or `{"data": [...]}` or a bare list. Each row is an array `[job_id, loc_id, location, date, meal_period, score, optional_href]`.

### 3. Widget catalog (Secret Shop Dashboard, report id `fgmysteryshop`)

| Widget | reportId | Title | Maps to dashboard KPI |
|---|---|---|---|
| **175639** | **923** | **Individual Shops** | **Source of truth for `shops.json` — every shop with score** |
| 175636 | 1 | Secret Shop (gauge) | Latest score % (also derivable from widget 175639) |
| 175637 | 2 | Score Trend | Monthly trend chart |
| 175638 | 585 | Category Trend | SQC by month |
| 175640 | 822 | Top Five Questions | Top-scored questions |
| 175641 | 822 | Bottom Five Questions | Lowest-scored questions |

**Sample row** (verified live 2026-04-27):
```
["20763859", "002065", "Louisville, KY (Dixie Highway)", "04/17/2026", "Lunch", "47.00"]
```
Shape matches existing on-disk `data/raw/marketforce/2065/2026-04-23/shops.json`.

### 4. Per-shop SQC detail

The dashboard view shows SQC averages for the date range. Per-shop SQC values (Service / Quality / Cleanliness / CustomerSatisfaction) live on the individual shop detail page reached by clicking the Job # link in widget 175639.

**Detail URL pattern:** TBD. Capture during build via `page.on('request')` while clicking Job # `20763859`. Discovery doc still flags this as open.

**Workaround until then:** The Marketforce email path already delivers a per-shop PDF (`Report_002065_Louisville,_KY_(Dixie_Highway)...pdf`) with full SQC. The PDF parser pipeline in `scrape_shop_payout_email.py` is the existing source for SQC. KnowledgeForce per-shop endpoint discovery is a "nice to have," not a blocker.

---

## Mapping: dashboard KPI → endpoint

| Dashboard KPI | Source |
|---|---|
| Latest shop score | Widget 175639 — most-recent row by date |
| Rolling W / M / Q averages | Widget 175639 — full history → compute in Python (already done in `build_shop_tracker.py`) |
| Participation rate | `scrape_shop_participation.py` (separate widget — re-run discovery to confirm widget ID; not blocking) |
| 100% shop count (payout trigger) | Marketforce email (`scrape_shop_payout_email.py`) — KF can corroborate via `score == 100` rows in widget 175639 |
| Visit time | Marketforce PDF (already in `scrape_visit_time.py`); KF detail page also has it |
| Per-shop SQC | Marketforce PDF (primary). KF detail-page endpoint TBD. |

**Net:** Widget 175639 + Marketforce email pipeline together cover every dashboard KPI today. No KF endpoint is missing for the existing dashboard wiring.

---

## Pivot recommendation: Playwright → requests

**Pivot.** The current Playwright + Xvfb headed scrape exists for two reasons that no longer hold:
1. It loads the report HTML to read the DataTable. **Already replaced** in-line — `scrape_knowledgeforce.py:254` calls `/reporting/api/widget/175639` directly via `page.evaluate(fetch)`. The browser is doing nothing the API doesn't.
2. It logs in via form fields. **Replayable** in `requests` — no MFA, no captcha observed.

### Recommended next session

1. **Capture the exact login POST** (URL + form field names + redirect chain). One-shot via Playwright with `page.on('request', lambda r: print(r.url, r.method, r.post_data))` while logging in. ~5 min.
2. **Build `scrape_knowledgeforce_api.py`** — pure `requests.Session`. Login → filter tree → widget 175639 → write `shops.json`. Should be ~80 lines vs the current ~700-line Playwright file.
3. **Run side-by-side for one week** — both write to a dated folder, compare row-for-row. If clean, retire the Playwright path and remove Xvfb from the GitHub Actions workflow.
4. **Drop runtime from minutes to seconds** — and remove the brittle "ERR_ABORTED retry" / "wait_for_load_state networkidle" timing dependencies entirely.
5. **Per-shop detail endpoint** — capture during step 1 by also clicking a Job # link with the same network-print harness. Cheap to do in the same session.

### What stays on the existing path
- `scrape_shop_payout_email.py` — Marketforce email pipeline. Different system (Outlook + PDF), already lights-out via Microsoft Graph.
- `scrape_shop_participation.py` — separate widget; same API replay shape applies, do this as a follow-on once the main scraper is API-only.

---

## Open items

1. ~~Login POST URL + field names~~ — **CAPTURED 2026-05-07.** See "Auth — verified replay" below.
2. ~~Per-shop detail endpoint for SQC drilldown~~ — **CAPTURED 2026-05-14.** See "Per-shop Assignment View" section below. Visit time is available at this endpoint via pure requests.
3. After cutover: drop `playwright` + `xvfb-run` from the workflow's secret-shop step; cut CI runtime accordingly.

---

## Auth — verified replay (2026-05-07)

Captured via one Playwright network-tap pass. Replayable in pure `requests`:

| Step | URL | Method | Notes |
|---|---|---|---|
| 1. Land | `https://www.knowledgeforce.com/` | GET | Sets cookies; HTML contains `<input name="_csrf" value="...">` |
| 2. Login | `https://www.knowledgeforce.com/` | POST | form-encoded |

POST body fields (only 3 needed — fingerprint fields `hash` and `object` are optional for replay):
```
_csrf=<token from step 1>
Login[username]=<email>
Login[password]=<pw>
```

Success indicator: response URL is `/reporting/reports/dashboard` (not `/login` or `/`).

**No MFA, no captcha, no fingerprint validation observed.** Pure cookie-session.

## Widget response shape — corrected (2026-05-07)

The widget endpoint does NOT return `{"aaData": [...]}`. It returns:

```json
{"type": "render", "html": "<style>...<script>var dataSet = [[ROW1], [ROW2], ...];</script>..."}
```

Each row is `[job_link_html, location_id, location, date_str, meal_period, score_str]`. The `job_link_html` is `<a href="/reporting/assignment/view?dataset={...}">JOB_ID</a>` — `JOB_ID` is between the `>` and `<`.

Parser regex:
```python
m = re.search(r"var dataSet\s*=\s*(\[\[.*?\]\]);", html, re.S)
rows = json.loads(m.group(1))
```

## Dataset shape — verified

`{"period2": [list_of_ids]}` (flat object) returns full history. Other shapes tested:

| Dataset shape | Rows returned |
|---|---|
| `[]` (empty) | 1 (latest only) |
| `{"period2": [all_71_ids]}` | 115 (full history) ✓ |
| `[{"period2": [pid]} for pid in ids]` (array of objects) | 1 |
| `[ids]` raw IDs | 1 |
| `[{"id": pid} for pid in ids]` | 1 |

## Period2 IDs — source

The filter API (`/reporting/api/filters/903`) returns `{"html": "<rendered filter form>"}`. Period IDs are extractable as checkbox values:
```python
ids = re.findall(r'value="period2-\|\|-(\d+)"', html)
```
71 unique period IDs as of 2026-05-07. Decreasing IDs = older periods (530400279 = most recent week).

## Per-shop period2 attribution

The all-periods query embeds the FULL period list into every row's href, so per-shop period2 is unrecoverable from a single all-periods response. Solution: requery per-period (71 narrow GETs, ~12s total). Each per-period response correctly carries that period's ID. Coverage verified: 115/115 shops attributed to a single period each.

## Production replay results (2026-05-07 19:50 ET)

`scrape_knowledgeforce_api.py` vs `scrape_knowledgeforce.py` (Playwright) on store 2065:

| Field | Old (Playwright) | New (requests) | Match |
|---|---|---|---|
| Latest job | 20764354 | 20764354 | ✓ |
| Latest score | 100.0 | 100.0 | ✓ |
| Latest period2 | 530400279 | 530400279 | ✓ |
| Quarter avg | 86.11% (n=18) | 86.11% (n=18) | ✓ |
| Week avg | 100.0% (n=1) | 100.0% (n=1) | ✓ |
| Month avg | 86.0% (n=6) | 86.0% (n=6) | ✓ |
| Total shops | 23 | 115 | New is superset |
| Common rows w/ core-field diffs | — | 0 / 23 | ✓ |

**One known gap:** SQC fields (`service`, `quality`, `cleanliness`, `customer_satisfaction`) are `null` in new output. The old Playwright scraper hits each shop's detail page to scrape these. The new client skips this — Marketforce email PDF pipeline is the primary SQC source per `project_secret_shops.md`. SQC drilldown can be added if needed (see open item #2).

## Runtime

- Old: ~5–10 min (Playwright + Xvfb + per-shop drilldown navigation)
- New: ~15s (login + filter + per-period × 71 + write)


---

## Per-shop Assignment View (Visit Time) — discovered 2026-05-14

**Endpoint:**
```
GET /reporting/assignment/view?dataset={"jid":<job_id_int>,"period2":[<period2_int>]}
```
(URL-encode the dataset value with `urllib.parse.quote(json.dumps({...}))`)

**Auth:** same session cookies from login — no extra auth.

**Response:** Full HTML page containing the answered shop questionnaire. The "Time In" bucket is in a `<li class="question-answer">` element immediately following the "Time In: (Mark one only:)" label div.

**HTML structure:**
```html
Time In: (Mark one only:) ...</div>
<div class="question-choices">
  <ul class="fa-ul">
    <li class="question-answer"><i class="fa-li fa fa-check-circle fa-md"></i>4 pm-6:59 pm</li>
  </ul>
</div>
```

**Parser (regex):**
```python
idx = txt.find("Time In:")
chunk = txt[idx:idx + 2000]
m = re.search(
    r'class="question-answer"[^>]*>.*?<i[^>]*></i>([^<]+)</li>',
    chunk, re.IGNORECASE | re.DOTALL
)
bucket_raw = m.group(1).strip()  # e.g. "4 pm-6:59 pm"
```

**Bucket → [start_hour, end_hour]:** Parse the time range string. "4 pm-6:59 pm" → [16.0, 18.98] (end :59 rounds up to next hour). See `scrape_visit_time.py:parse_bucket()`.

**Confirmed for:** job 20770900 (May 11, 2026 Dinner) → "4 pm-6:59 pm" = [16.0, 18.98]. Prior hand-entered override was wrong [17.0, 21.0].

**Production usage:** `scrape_visit_time.py` (fully rewritten 2026-05-14 to use this endpoint via pure requests — no Playwright).

**Note on Question Results page:** `GET /reporting/reports/report?id=questionresults&dataset={cqid,jid,period2,scheme}` does NOT return bucket text via requests (content is JS-rendered). The assignment view page above is the correct lights-out path.

---

---

## Case Management — discovered 2026-05-14

### Case detail endpoint

```
GET /casemanagement/casemanagement/details?id=<CASE_ID>
```

**Auth:** same session cookies from login — no extra auth.

**Response:** Full HTML page. Fields are spread across multiple `<table class="ticket-table">` elements (not a single table). Iterate all of them.

### Field → table mapping (verified against case 5NFRW2)

| Field | Label in `<th>` | Table index |
|---|---|---|
| `customer_name` | `Customer Name` | 0 |
| `email` | `Email` | 0 |
| `phone` | `Phone` | 1 |
| `visit_date` | `Occurred` | 2 |
| `order_type` | `Customer Type` | 2 |
| `location_id` | `Location ID` | 3 |
| `issue_category` | `Complaint Category` | 3 |

### Complaint comment

```python
soup.select_one("div.complaint-details-text").get_text(strip=True)
```

### Post-processing required

- **Phone:** KF stores raw digits (`5024927879`); format to `(NXX) NXX-XXXX`.
- **visit_date:** KF stores `"Wed, May 13 2026 00:00:00"`; extract to `MM/DD/YYYY`.
- **customer_name:** KF stores lowercase (`"rebecca pelt"`); apply `.title()`.

### Verified fixture (case 5NFRW2)

```json
{
  "case_id": "5NFRW2",
  "customer_name": "Rebecca Pelt",
  "phone": "(502) 492-7879",
  "email": "rebeccapelt12@gmail.com",
  "visit_date": "05/13/2026",
  "order_type": "Online Ordering Pick-up",
  "issue_category": "L3 - Accuracy of Order",
  "location_id": "002065",
  "comment": "we are missing a large fry from our order"
}
```

**Production script:** `scraper/scrape_kf_case.py` — CLI: `python scraper/scrape_kf_case.py <CASE_ID>`.
Prints JSON to stdout; on failure prints `{"error": "...", "case_id": "..."}` and exits 1.

---

## Pattern source

Discovery 2026-04-27 (live walkthrough via Claude in Chrome). Promoted to `_API.md` 2026-05-07 after confirming the production scraper is already calling the JSON endpoints directly inside Playwright — meaning all that's left is auth replay, which is the one architectural blocker most likely to *not* hold (no MFA observed). Pairs with `~/.claude/rules/reverse-engineer-apis-first.md`.
