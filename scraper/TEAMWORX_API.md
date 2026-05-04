# Teamworx Internal API — Discovery Notes

Reverse-engineered 2026-05-04 via Chrome MCP fetch interceptor. Same parent vendor as
CrunchTime/NetChef (`fiveguysfr77.*` host prefix), shared auth backend.

## Auth

- **Login URL:** `https://fiveguysfr77.ct-teamworx.com/views/auth.jsp`
- **Credentials:** Same as CrunchTime — `CRUNCHTIME_USERNAME` / `CRUNCHTIME_PASSWORD`
- **Session cookies:** Set after successful login, persist on `.ct-teamworx.com`. Send via
  `Cookie:` header (or `requests.Session()` to retain).
- **No CSRF token needed** for these JSON endpoints — browser auth cookies are sufficient.

To mint cookies once and reuse, run the existing `scraper/api_discover.py` pattern but pointed at
`https://fiveguysfr77.ct-teamworx.com/views/auth.jsp` instead of NetChef. Or extract from a live
browser session via Chrome MCP `document.cookie`.

## Base URL

```
https://fiveguysfr77.ct-teamworx.com
```

All endpoints below are relative to this base.

## Endpoints (verified working)

### `POST /json/mn/dailyRoster/getPageData`

**The headline endpoint — replaces `scrape_teamworx_roster.py` entirely.**

```http
POST /json/mn/dailyRoster/getPageData
Content-Type: application/json

{
  "laborDate": "2026-05-04",
  "loadForecastData": false
}
```

**Response (success):**

```json
{
  "success": true,
  "messageList": [],
  "userControlsDto": { ... },
  "data": {
    "businessDateBeginTime": "04:00",
    "userHasManagerRole": false,
    "structures": [{ "id": ..., "name": "...", "positions": [...] }, ...],
    "dailyRosterFilterData": { "positions": [...], "substructures": [...] },
    "dailyRosterPreferences": [...],
    "myStaffingStructureIds": null,
    "dayData": {
      "shifts": [
        {
          "scheduleShiftId": "48288633",
          "employeeId": "930761",
          "employeeName": "Robert Cline",
          "employeeNumber": "E2065314244",
          "initials": "RC",
          "email": "bobby.cline2000@gmail.com",
          "phoneNumber": "...",
          "minor": false,
          "positionId": "2",
          "positionName": "General Manager-Salary",
          "stationId": "...",
          "stationName": "...",
          "substructureId": "37",
          "substructureName": "Payroll",
          "locationName": "KY-2065-Dixie Highway",
          "inTime": 1777874400000,
          "inTimeText": "6:00 AM",
          "outTime": 1777914000000,
          "outTimeText": "5:00 PM",
          "hours": 11,
          "overtimeHours": 0,
          "hasOvertime": false,
          "openShiftId": null,
          "avatarUrl": "/cmn/shared/pics/account/-1/default",
          "lastLoginDateTime": "Never logged in"
        },
        ...
      ],
      "shiftNoteExists": false,
      "promotions": [...],
      "holidays": [...],
      "weekStartEndDto": { ... },
      "dailyForecast": { ... },
      "salesForecastWeek": { ... }
    }
  }
}
```

**What this replaces today:**

The current `scrape_teamworx_roster.py` (Playwright) takes ~30 sec, parses tab-separated
`inner_text()` with a brittle regex, and runs on a Windows Scheduled Task at 7:45 AM. The API
path runs in <500 ms with cookies, returns clean structured JSON, and can move to a GitHub
Actions cron (true lights-out — Windows machine no longer required).

### `POST /json/mn/laborSchedules/getDataForManageSchedulesPage`

```http
POST /json/mn/laborSchedules/getDataForManageSchedulesPage
Content-Type: application/json

{ "year": 2026 }
```

Returns `data.laborSchedules[]` — full list of weekly labor schedules for the year. Useful for
the schedule-build skill (knowing which weeks are draft / published / archived).

### `POST /json/emn/employee-list`

```http
POST /json/emn/employee-list
Content-Type: application/json

{
  "sortInfo":   { "column": "NAME", "asc": true },
  "filter":     { "searchText": "", "positionIds": [], "primaryLocation": true },
  "pagingInfo": { "start": 1, "limit": 100 }
}
```

Returns `data.employees[]` paginated with `id, employeeName, initials, employeeNumber,
employeePhone, employeeEmail, employeePositions, locationName, lastSignInDateTime,
signUpDateTime, minor, avatarUrl`, plus `data.totalCount` for pagination.

**Replaces** `scripts/build_employee_directory.py` hand-maintained EMPLOYEES list (or at minimum
gives us a live source of truth to diff against the hand-list each morning).

### `GET /json/mn/getManagerHomePageData`

Plain GET. Returns the home-page tile counts:

```json
{
  "success": true,
  "data": {
    "openShiftsCount": 0,
    "staffRequestCount": 0,
    "unreadMessageCount": 45,
    "timeClockEnabled": true
  }
}
```

Useful for dashboard "Teamworx alerts" card (open shifts pending, staff requests waiting,
unread messages).

### `POST /json/emn/datepicker/settings`

```http
POST /json/emn/datepicker/settings
Content-Type: application/json

{ "date": "2026-05-04" }
```

Returns valid date ranges + week boundaries — only needed if building a custom datepicker;
ignore for our purposes.

## Endpoints not yet captured (future discovery)

These are the next things to capture by clicking the relevant nav items with the interceptor on:

- `Shift Builder` — write path for creating/editing shifts (would unlock the schedule-build
  skill ending in "Mark As Ready" via API instead of Playwright).
- `Staff Requests` — pending time-off / swap requests.
- `Open Shifts` — open shift list + claim/assign endpoints.
- `Manager Log` — read/write daily manager log notes.

## Migration path for `scrape_teamworx_roster.py`

1. Build `scraper/teamworx_api.py` (Python module) with `get_daily_roster(date_str)` using
   `requests.Session()` + cookie auth.
2. Mint cookies via either:
   - First-time bootstrap with Playwright (one-time per session, persist cookies to
     `data/twx_cookies.json`).
   - Or reuse the CrunchTime cookie minting in `api_discover.py` (same `fiveguysfr77` parent —
     test whether `.ct-teamworx.com` cookies share the same SSO domain).
3. Wrap `get_daily_roster()` to map `dayData.shifts[]` → existing `weekly_schedule.json` schema
   (preserves dashboard wiring).
4. Move from Windows Scheduled Task → GitHub Actions cron (lights-out — laptop closed).
5. Keep the Playwright path under `scraper/scrape_teamworx_roster_playwright_legacy.py` as a
   fallback for if cookies expire and re-mint fails.

## Comparison: Playwright vs API

| Dimension | Playwright (today) | API (this discovery) |
|---|---|---|
| **Latency** | ~30 sec (cold), ~15 sec (warm) | <500 ms |
| **Tokens / run** | n/a (no LLM in the loop) | n/a |
| **Reliability** | Brittle — broke 2x already (URL change, parser change) | Contract-stable JSON |
| **Lights-out fit** | Windows-bound (Scheduled Task) | Pure HTTP — runs in GitHub Actions |
| **Multi-store** | Hard — each store needs its own browser session | Trivial — same code, different cookie/store |

## Pattern source

Discovery session: 2026-05-04. Same approach used for CrunchTime tip entry (`api_discover.py`
→ `api_enter_tips.py`) — Bobby's standing rule per `~/.claude/rules/reverse-engineer-apis-first.md`.
