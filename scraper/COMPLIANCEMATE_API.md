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

| Value | Meaning |
|---|---|
| `list_completions`     | Required-only completion (the "Req" column) — what we use today |
| `list_completions_all` | INVALID — server returns 500. Use `list_completions` and read the second percentage in the "X% \| Y%" pair for "All" |

### `date_range` values

| Value | Behavior |
|---|---|
| `today`     | start_date and end_date should both equal today's ISO date |
| `yesterday` | start_date and end_date should both equal yesterday's ISO date |
| `custom`    | use whatever start_date / end_date you want |

The server appears tolerant — sending `date_range=today` with arbitrary start/end dates still
worked in testing. But matching them is the safe pattern.

### Drill-down (per-list breakdown — OPEN)

The "click on 2065 - Louisville, KY to expand" interaction fires a follow-up GET like:

```
GET /groups/{group_id}/report/list_completions
    ?authenticity_token=...
    &location={location_id}
    &start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
    &target_selector=#location-lists-{location_id}    # NOTE: hyphens, not underscores
    &report_filters_presenter[*]=...                  # same set as Apply (no `commit`, no `report_form_submit`)
```

**Initial assumption was wrong** — the per-checklist cards are NOT in the Apply response. They
are loaded by this drill-down call. The browser-side fetch returns the HTML and Rails Turbo
injects it into `#location-lists-{location_id}`.

**Open in pure-Python:** replaying this GET from a `requests.Session()` with the same cookies +
CSRF returns the FULL page HTML (29KB), NOT a Turbo Stream fragment. The per-list cards are
absent from that response. Likely causes (not yet confirmed):

1. Server requires a specific cookie set that Devise issues only after a login flow that hits
   the dashboard once first (we currently jump straight to the report URL).
2. Server checks `Sec-Fetch-*` or other client hints that pure-`requests` doesn't send.
3. There's a stateful "filter applied" flag in the session that the Apply call sets and the
   drill-down call requires; our Apply succeeds but maybe doesn't set the flag the same way.

**Workaround for now:** the existing Playwright scraper (`scrape_compliancemate.py`) still
runs daily for the per-checklist data. The new URL-replay client provides the overall summary
(faster, lighter — useful for the daily confirmation email's CM line + a summary card).

**Next discovery pass:**

- Capture the EXACT request headers Chrome sends on the drill-down (especially `Cookie` value
  — pure requests + `session.cookies` may be missing one Devise sets only on dashboard load).
- Replay with `curl` from the captured headers, see if it works.
- If yes → diff against the requests session's headers, find the missing piece.
- If no → maybe the per-list view requires a different report URL entirely.

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
