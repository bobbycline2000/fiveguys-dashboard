# ComplianceMate Internal API — Discovery Notes

Reverse-engineered 2026-05-04 via Chrome MCP fetch interceptor. Replaces the Playwright-driven
`scrape_compliancemate.py`.

## Key finding

ComplianceMate's reports app is a classic Rails server-rendered web form. Apply submits a **GET
with URL params**, server returns full HTML with all data already inline. The drill-down click
on a location row is a Bootstrap collapse toggle of pre-rendered HTML — there's no second AJAX
fetch needed for the per-checklist breakdown.

**This contradicts the prior lesson** in `~/.claude/rules/tonight-setup-preferences.md` rule #5
("ComplianceMate does NOT apply report filters via URL GET parameters"). The prior attempt
likely sent only `date_range` without the rest of the `report_filters_presenter[*]` set or the
`authenticity_token`. Lesson stands as a partial truth — full URL pattern below works.

## Auth

- **Base:** `https://fg-beta.compliancemate.com`
- **Credentials:** `COMPLIANCEMATE_USERNAME` / `COMPLIANCEMATE_PASSWORD` (already in `.env`
  + GH Secrets)
- **Session:** Standard Rails `_session_id` cookie (HttpOnly). Mint via login form POST
  (mirroring the existing `scrape_compliancemate.py` login flow but without Playwright — pure
  `requests.Session()`). Discover the exact login form fields once, then it's lights-out.
- **CSRF:** Every report request must include the `authenticity_token` from the page's
  `<meta name="csrf-token">`. Token rotates per session — fetch the dashboard once, scrape the
  meta, then use the same token for the report call.

## Group + Location IDs (KY-2065)

- `GROUP_ID`    = `21792` (Five Guys / Estep & Affiliates / 2065 - Louisville, KY)
- `LOCATION_ID` = `18170`

These appear in the URL paths and as `location` query params.

## The headline endpoint

### `GET /groups/{GROUP_ID}/report/list_completions`

```http
GET /groups/21792/report/list_completions
    ?authenticity_token=<csrf>
    &commit=Apply
    &report_filters_presenter[date_range]=yesterday
    &report_filters_presenter[start_date]=2026-05-03
    &report_filters_presenter[end_date]=2026-05-03
    &report_filters_presenter[filter_for]=reports_form
    &report_filters_presenter[filter_type]=lists
    &report_filters_presenter[name]=
    &report_filters_presenter[report_type]=list_completions
    &report_form_submit=true
    &requested_timezone=America/New_York
```

Returns the full Rails view (~35 KB HTML). The data lives in repeating
`<div class="card mb-0">` blocks under `<div id="location_<LOCATION_ID>_lists" class="collapse show">`:

```html
<div class="card-header flex justify-between">
  2065 - Louisville, KY     <!-- location -->
  5                         <!-- list count badge -->
  100% | 100%               <!-- required % | all % -->
</div>
<div id="location_18170_lists" class="collapse show">
  <div class="card mb-0">
    11AM: Time and Temp
    100% | 100%
  </div>
  <div class="card mb-0">
    1PM: Time and Temp
    100% | 100%
  </div>
  ...
</div>
```

**Parse target:** every `div.card.mb-0` whose `innerText` matches `<list-name>\n<n>% | <n>%`.

### `report_type` values

**CORRECTION (2026-07-11):** the "INVALID" value below was wrong — it was a guess, never actually
tested against the live server. The real second report type, confirmed working by reading
`scrape_compliancemate.py`'s `navigate_to_list_completion()` (which selects
`select#report_filters_presenter_report_type` with `value="all_list_completions"`) and replaying
it via pure `requests`, is `all_list_completions` — one word, no underscore before "list".

| Value | Meaning |
|---|---|
| `list_completions`     | **Narrower than the name suggests.** Returns only a subset of lists — observed to include just the `*: Time and Temp` rounds + the day-named Milkshake Cleaning Check. It does **NOT** include `AM Pre-Shift Check`, `PM Pre-Shift Check`, `Shift Change`, or any of the periodic/audit lists, even on days those were completed at 100%. Do not use this report type alone to reason about checklist compliance — it silently omits real, active lists. |
| `all_list_completions` | The **complete** list roster for the location/date, whether "required" or not — matches what `scrape_compliancemate.py` (Playwright) and the canonical `data/compliancemate.json` dashboard feed show (20 lists for KY-2065: 6× Time and Temp, AM/PM Pre-Shift Check, Shift Change, day-named Milkshake Cleaning Check, plus periodic/audit lists — see taxonomy below). **Use this for any report that needs Pre-Shift Check or Shift Change status**, or for any historical/date-range pull where completeness matters more than a single "required %" headline number. `compliancemate_api.get_list_completions()` takes an optional `report_type=` kwarg (default stays `list_completions` to preserve the existing CI/dashboard pipeline's behavior unchanged) — pass `report_type="all_list_completions"` explicitly to get the full roster. |

### Known list-name taxonomy (store 2065, discovered 2026-07-11 via a 4-week `all_list_completions` pull)

ComplianceMate has no native "AM temp / PM temp / shift-change temp / checklist" bucketing — this
mapping is our interpretation, used by `scraper/report_missing_temps_checklists.py`:

| Bucket | List names |
|---|---|
| `AM_TEMP` | `11AM: Time and Temp` |
| `SHIFT_CHANGE_TEMP` | `Shift Change`, `1PM: Time and Temp`, `3PM: Time and Temp` |
| `PM_TEMP` | `5PM: Time and Temp`, `7PM: Time and Temp`, `9PM: Time and Temp` |
| `CHECKLIST` (confirmed daily-active) | `AM Pre-Shift Check`, `PM Pre-Shift Check`, day-named `<Day> Milkshake Cleaning Check` (e.g. `Tuesday Milkshake Cleaning Check`, `Friday Milkshake Cleaning Check` — NOT Friday-only, appears on multiple weekdays) |
| `CHECKLIST` (active-but-intermittent, observed 2026-06-14→2026-07-11) | `Closing Checklist` — showed real completion activity (44–55%) on several days, so it's a live list, just chronically under-completed |
| Unconfirmed cadence — **excluded from missing-item reports unless observed active** | `Weekly Store Inspection`, `Delivery Check`, `Temperature Sample`, `Calibration Test`, `Operational Spot Check`, `Battery Swap Checklist`, `MMCCA`, `Pre Open`, `Closing` — all sat at a flat 0%\|0% on **every single day** of a 28-day window (2026-06-14→2026-07-11). That pattern reads as inactive/superseded CM list config (e.g. `Pre Open`/`Closing` look like legacy names predated by `AM/PM Pre-Shift Check`) rather than a genuine daily miss — flagging 28 straight "MISSED" rows for a list nobody is expected to touch would be a false alarm, not a real compliance gap. If any of these turn out to be genuinely required, promote them into the confirmed-daily set and re-run.
| Unknown / not yet catalogued | `Milkshake Pump Cleaning Check` — distinct from the day-named milkshake list, cause/cadence not yet confirmed; currently falls back to `CHECKLIST` bucket by default so it isn't silently dropped |

**LATE status is not derivable** from either report type — no per-entry timestamp vs. due-time is
exposed at this level. Only `MISSED` (0%) and `INCOMPLETE` (1–99%) can be reported. A true `LATE`
read would require drilling into each list's `/responses?date=...&list_id=...` page per entry —
not yet attempted; flag as a future discovery pass if Bobby wants LATE granularity.

### `date_range` values

| Value | Behavior |
|---|---|
| `today`     | start_date and end_date should both equal today's ISO date |
| `yesterday` | start_date and end_date should both equal yesterday's ISO date |
| `custom`    | use whatever start_date / end_date you want |

The server appears tolerant — sending `date_range=today` with arbitrary start/end dates still
worked in testing. But matching them is the safe pattern.

### Drill-down (per-list breakdown — SOLVED)

The "click on 2065 - Louisville, KY to expand" interaction fires a follow-up XHR:

```
GET /groups/{group_id}/report/list_completions
    ?authenticity_token=...
    &location={location_id}
    &start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
    &target_selector=#location-lists-{location_id}    # hyphens, not underscores
    &report_filters_presenter[*]=...                  # same as Apply, MINUS `commit` and `report_form_submit`

X-Requested-With: XMLHttpRequest
Accept: text/javascript
```

**The trick — the response content type is `text/javascript`, not HTML.** Rails uses the classic
`.js.erb` responder pattern: the response body is a jQuery snippet that calls `.html(...)` on
the target selector with the per-list HTML embedded as a JS string literal:

```js
$("#location-lists-18170").
    html(
      "  <div class=\"card mb-0\">\n    <div class=\"card-header flex justify-between\" ...
       11AM: Time and Temp ...
       <a class=\"report-numbers--good ...\" href=\"/groups/.../responses?date=...&list_id=189006\">100%</a> |
       <a ...>100%</a>
       ..."
    )
```

**Why pure-`requests` returned the wrong response without the right Accept header:** Rails'
`respond_to do |format|` block in the controller branches on the request's Accept header.
With `Accept: text/html` (Python's default), it served the FULL page HTML (29 KB). With
`Accept: text/javascript` (what XHR sends by default), it serves the per-list fragment as JS
(~5 KB). The same URL serves two different responses based on `Accept`.

**Parsing path:**

1. Extract the JS string literal between `html("` and the trailing `")`.
2. JSON-decode the escapes (`\/` → `/`, `\"` → `"`, `\n` → newline) — Python's
   `bytes.decode('unicode_escape')` after a manual `\/` → `/` swap works.
3. Parse the resulting HTML with BeautifulSoup; each per-list row is a `div.card.mb-0` with
   `.list-name` (name) and two `.daily-percentages a` anchors (required %, all %).
4. Bonus: each anchor's `href` carries `list_id=<n>` — useful for further drill-downs into
   individual list responses.

**Validated 2026-05-04:** Returns 6 checklists for KY-2065 with names, list IDs, and percentages
matching the live dashboard exactly.

## Other endpoints (not yet captured but visible in nav)

These would be the next discovery passes:

- **Anomalies** — `Statistics → Anomalies` — likely `/groups/{GROUP_ID}/report/anomalies`
- **Tasks (Incomplete)** — `Tasks` nav — likely `/groups/{GROUP_ID}/tasks` or `.json`
- **Sensors / Timed Logs** — `Statistics → Sensors / Timed Logs`
- **Notifications** — `Notifications` nav — for catching open compliance issues that need a
  manager prompt (the `compliance-sweep-daily` agent's input)

The same URL-driven pattern almost certainly applies — just different `report_type` values and
maybe different paths under `/groups/{GROUP_ID}/`.

## Migration path for `scrape_compliancemate.py`

1. Build `scraper/compliancemate_api.py` — pure `requests` + `BeautifulSoup`:
   - `login(session, username, password)` — POST to login form; minted cookies persist on the
     session.
   - `get_csrf_token(session, group_id)` — GET the dashboard, scrape `<meta name="csrf-token">`.
   - `get_list_completions(session, group_id, location_id, date)` → list of
     `{name, required_pct, all_pct}`.
2. Run side-by-side against the Playwright scraper for a week to validate parity.
3. Once parity confirmed, swap the dashboard wire and retire `scrape_compliancemate.py`.
4. Move the daily run from CI Playwright step → lighter CI step (no Playwright = faster, cheaper,
   no headless Chromium install).

## Historical / date-range reporting (added 2026-07-11)

`scraper/report_missing_temps_checklists.py` loops `compliancemate_api.get_list_completions()`
(with `report_type="all_list_completions"`) over an arbitrary `--start`/`--end` date window and
produces a single JSON report of every MISSED/INCOMPLETE item, bucketed into
AM_TEMP/PM_TEMP/SHIFT_CHANGE_TEMP/CHECKLIST per the taxonomy above:

```
python scraper/report_missing_temps_checklists.py --store 2065 \
    --start 2026-06-14 --end 2026-07-11 \
    --out data/missing_temps_checklists_4wk.json
```

~2 requests/day (summary + drill-down), so a 28-day pull is ~56 requests, well under a minute.
This is a real API-side capability the URL-replay path unlocks that the legacy Playwright script
(`scrape_compliancemate.py`) does NOT have — that script is hardcoded to `date_range="yesterday"`
with no date-range looping (see the "known facts" correction dated 2026-07-11 in the
compliancemate-professor agent knowledge). For any future "how did we do over period X" ask, this
script is the answer — don't rebuild it, extend it.

## Comparison: Playwright vs API

| Dimension | Playwright (today) | URL-replay (this discovery) |
|---|---|---|
| **Latency** | ~30–45 sec | <2 sec |
| **CI cost** | Headless Chromium + Xvfb, ~2 min job | Pure Python `requests`, ~5 sec job |
| **Reliability** | Brittle on UI changes (lessons-learned shows 2 prior breaks) | URL contract is stable across UI redesigns |
| **Multi-store** | One session per store (slow) | Trivially parallel — one fetch per location |
| **Lights-out fit** | Already lights-out via Windows Task | Same, but cheaper and faster in CI |

## Pattern source

Discovery session: 2026-05-04 (same Bobby green-light to reverse-engineer all his vendor APIs
that produced CrunchTime tip entry, Outlook drafts, and Teamworx daily roster on the same day).
