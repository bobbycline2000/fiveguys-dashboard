# Teamworx Internal API — Discovery Notes

Reverse-engineered 2026-05-04 → 2026-05-05 via Chrome MCP fetch interceptor + jQuery `$.ajax`
hook + `AJAX_UTILS.postJson` patch + Performance API resource timings. Same parent vendor as
CrunchTime/NetChef (`fiveguysfr77.*` host prefix), shared auth backend.

**Coverage:** Every section in the manager sidebar walked end-to-end with capture on. 35+
endpoints catalogued — see "Complete endpoint inventory" section at the bottom for the
flat list grouped by sidebar section.

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

### `POST /json/mn/laborSchedule/getWbForecastData`

**Weekly forecast — 7 days of summary forecast data including labor totals.**

```http
POST /json/mn/laborSchedule/getWbForecastData
Content-Type: application/json

{ "laborDate": null, "weekEndingDate": "2026-05-10" }
```

Returns `data.dayForecast` (single day) + `data.weekForecast` (full week).

`weekForecast.salesForecastDays[]` — 7 entries, one per day:
- `date`, `totalSales`, `totalGuests`, `totalChecks`
- `idealHours`, `scheduledHours`, `idealLaborPct`, `scheduledLaborPct`
- `idealSalesHours`, `scheduledSalesHours` (= SPLH)
- `idealGPLH`, `scheduledGPLH`, `varianceGPLH`, `varianceSPLH`
- `fohScheduledHours`, `bohScheduledHours`, `fohScheduledWages`, `bohScheduledWages`
- `scheduledVariance`, `overtimeHours`, `overtimeValue`
- `salesForecastList: []` — **always empty in this response** (hourly bars not here)

**Replaces** the per-day looping needed via Daily Roster — one call returns the week.

### `POST /json/mn/dailyRoster/getForecastData`

```http
POST /json/mn/dailyRoster/getForecastData
Content-Type: application/json

{ "laborDate": "2026-05-05", "weekEndingDate": "2026-05-10" }
```

Returns the same single-day forecast summary as the daily-roster Forecast section
(Sales/Guests/Checks/Ideal hrs/Scheduled hrs/SPLH/GPLH/Variance).

### `POST /json/mn/dailyRoster/getTDailyShiftMetrics`

Form-encoded body: `weekEndingDate=2026-05-10`

Returns the "Labor Schedule Metrics" modal contents — Daily Total Value, OT hours/value,
Avg Wage, Forecasted Sales, SPLH, Labor %, Total Hours by Position, Total Hours by P&L
Substructure, Total Value by Position. Useful for the dashboard "Schedule cost roll-up"
card.

## Forecast Graph (hourly Sales / Ideal Hours / Scheduled Hours)

The Forecast Graph modal (the popup with Sales bars + Ideal/Scheduled hour lines per
position) is **rendered client-side** — its hourly data is computed in-browser from
preloaded schedule data, NOT served by a single dedicated API endpoint.

**Reverse-engineered access path (verified 2026-05-05):**

1. Navigate to `https://fiveguysfr77.ct-teamworx.com/views/manager/tablet/laborSchedule.jsp?lsi=<labor_schedule_id>`
   - The `lsi` query param is the labor schedule ID. Get it from the
     `getDataForManageSchedulesPage` response (`data.laborSchedules[].id`).
2. Wait for page-load XHRs to settle (`startEditLaborSchedule`,
   `populateAvailabilityDataInWbTable`, `getWbForecastData`).
3. Click the chart icon (`<span class="grey-graph-icon">`) next to any
   `Sched./Ideal Hrs.` cell in the schedule grid (one per day per P&L substructure
   like "2. Crew").
4. Once the popup opens (`#forecastDetailsPopup` / `.sales-forecast-content`),
   extract the chart data from `Chart.instances`:

```js
const chart = Object.values(Chart.instances)[0];
const data = {
  hourLabels: chart.data.labels,                     // ["6AM","7AM",...,"11PM"] — 18 hrs
  idealHoursByHour: chart.data.datasets[0].data,     // line series
  scheduledHoursByHour: chart.data.datasets[1].data, // line series
  salesByHour: chart.data.datasets[2].data           // bar series
};
```

**Verified output (2026-05-06, 2. Crew, KY-2065):**
```
hours:                ["6AM","7AM","8AM","9AM","10AM","11AM","12PM","1PM","2PM","3PM","4PM","5PM","6PM","7PM","8PM","9PM","10PM","11PM"]
idealHoursByHour:     [9.86, 0,    0,    0,    0,     6,     4,     4,    4,    4,    4,    5,    7,    7,    6,    4,    5,     0   ]
scheduledHoursByHour: [0,    0,    1,    1,    2,     3,     3,     3,    3,    2,    1,    3,    4,    4,    4,    3,    3,     0   ]
salesByHour:          [0,    0,    0,    0,    0,     483,   308,   261,  278,  257,  310,  452,  678,  611,  475,  244,  0,     0   ]
```

The chart's `idealHours` total (69.86) ties to `salesForecastDays[2].idealHours` (69.857143)
within rounding — confirms the chart is rendering authoritative numbers.

**Implication for lights-out:** Pure-HTTP API is partial here. Full Forecast Graph
extraction requires Playwright headless to load the schedule page, click each day's chart
icon, and read `Chart.instances`. ~10 sec for a full week × N positions. Acceptable for a
weekly cron — schedule it to run once Sunday night after the schedule is finalized.

**Open follow-up:** Probe `populateAvailabilityDataInWbTable` and `startEditLaborSchedule`
with proper params (likely need `laborScheduleId`) — those responses may contain the
hourly Sales-by-hour forecast directly. If found, it eliminates the Playwright dependency.

## Endpoints not yet captured (future discovery)

These are the next things to capture by clicking the relevant nav items with the interceptor on:

- `Shift Builder` — write path for creating/editing shifts (would unlock the schedule-build
  skill ending in "Mark As Ready" via API instead of Playwright).
- `Staff Requests` — pending time-off / swap requests.
- `Open Shifts` — open shift list + claim/assign endpoints.
- `Manager Log` — read/write daily manager log notes.
- `populateAvailabilityDataInWbTable` / `startEditLaborSchedule` — proper params to unlock
  hourly Sales forecast (would replace the Playwright dependency for Forecast Graph).

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

## Complete endpoint inventory (2026-05-05 walk)

Every sidebar section visited with capture on. Endpoints grouped by trigger.

### Auth / page bootstrap (fires on most pages)
- `GET  /json/emn/user-info` — current user, location, roles
- `GET  /json/mn/getManagerHomePageData` — home tile counts (open shifts, staff requests, unread messages, timeClockEnabled)
- `GET  /json/side-menu` — sidebar config (Message Center route only)
- `GET  /json/mn/get/getLocationWeekStartDay` — week start day for the location
- `POST /json/emn/datepicker/settings` — body `{date}` — date picker bounds + week info

### Schedule Overview (`Schedule Overview` nav)
- `POST /json/n/scheduleOverview/getScheduleOverviewPageData` — multi-store week roll-up: per-location Sales Forecast, Ideal Hours, Scheduled Hours, Variance Hours, Scheduled Value, Labor Cost %

### Daily Roster (`Daily Roster` nav)
- `POST /json/mn/dailyRoster/getPageData` — body `{laborDate, loadForecastData}` — daily shifts + roster (headline endpoint, see top of doc)
- `POST /json/mn/dailyRoster/getForecastData` — body `{laborDate, weekEndingDate}` — daily forecast summary
- `POST /json/mn/dailyRoster/getTDailyShiftMetrics` — form body `weekEndingDate=...` — Labor Schedule Metrics modal data
- `POST /json/mn/dailyRoster/saveScreenPreferences` — UI preferences (collapse states, sort order)

### Manage Schedules (`Manage Schedules` nav)
- `POST /json/mn/laborSchedules/getDataForManageSchedulesPage` — body `{year}` — list of weekly schedules with status

### Labor Schedule Edit (deep link `/views/manager/tablet/laborSchedule.jsp?lsi=<id>`)
- `POST /json/mn/laborSchedule/startEditLaborSchedule` — claims edit lock
- `POST /json/mn/laborSchedule/populateAvailabilityDataInWbTable` — employee availability for the week
- `POST /json/mn/laborSchedules/refreshWBLaborScheduleData` — refresh schedule grid
- `POST /json/mn/laborSchedule/getWbForecastData` — body `{laborDate, weekEndingDate}` — weekly forecast summary (see Forecast Graph section above)
- `POST /json/mn/laborSchedule/getWbDailyShiftMetrics` — daily shift metrics
- `POST /json/mn/laborSchedule/getWbWeeklyShiftMetrics` — weekly shift metrics roll-up
- `POST /json/mn/laborSchedule/getFilteredEmployeeList` — employee filter for "Add Employee" dropdown
- `POST /json/mn/laborSchedule/preferencesForAutoScheduler` — auto-scheduler config
- `POST /json/mn/laborSchedule/getDataForAutoScheduler` — input bundle for auto-scheduler run
- `POST /json/mn/laborSchedule/overtimeLimitsForAutoScheduler` — OT caps
- `POST /json/mn/laborSchedule/addMultipleEmployeePositionRowsAndLoadEmployeesData`
- `POST /json/mn/laborSchedules/addEmployeePositionRowAndLoadEmployeeData`
- `POST /json/mn/laborSchedule/staffing-level-templates` — staffing distribution templates by daypart (the source of "Ideal Hours by hour" in the Forecast Graph)
- `POST /json/mn/labor-schedule/add-unscheduled-employees`
- `GET  /json/mn/labor-schedule/online-users/info` — who else is editing this schedule
- `POST /json/mn/report/createTextFileForLaborScheduleExport`
- `POST /json/mn/laborSchedule/getDataForExportingLaborSchedule`
- `POST /json/mn/report/exportLaborScheduleViaEmail`
- `POST /json/mn/message/getManagerShiftNotes` — manager log notes attached to shifts

### Shift Builder (`Shift Builder` nav)
- `POST /json/mn/templates/getSchedulingTemplatesData` — list of templates (Active filter applied)
- `POST /json/mn/templates/getSchedulingTemplate` — body `{templateId}` — full template with staffing distribution per 10/15/30/60-min interval (from URL `shiftBuilderSetup.jsp?templateId=29661`)

### Manager Log (`Manager Log` nav)
- `POST /json/mn/manager-log/log-entries` — daily manager log entries

### Staff Requests (`Staff Requests` nav)
- `POST /json/mn/staff-requests` — Swaps, Pick Ups, Time Off Requests, Availability Changes, Employee Record requests

### Message Center (`Message Center` nav, `/view#message-center` SPA route)

The Message Center is on a **separate SPA** (`/view#...` hash routing) with its own
dedicated endpoints under `/json/message-center/`. These are distinct from the
`/json/emn/message/...` endpoints used by the Manager Console.

- `GET  /json/message-center/controls` — UI controls/permissions
- `POST /json/message-center/messages/filter` — message list with filters (Inbox / Sent tabs share this endpoint, different filter param)
- `GET  /json/message-center/inbox-messages/{messageId}` — open a single message thread
- `POST /json/message-center/inbox-messages/{messageId}/read` ⚠️ **WRITE** — mark message read (auto-fires when opening)
- `GET  /json/message-center/inbox-messages/{messageId}/recipients/{senderId}` — recipient list + per-recipient read status (the "eye" icons in "Sent to: All" dropdown)
- `GET  /json/message-center/create-new-message/controls` — New Message composer config
- `GET  /json/message-center/message/recipients` — recipient picker list (employees/positions to message)
- **Not yet captured (would only fire on actual send):** the `POST /json/message-center/message` (or similar) endpoint that sends a new message. Catch by composing+sending a real test message with capture on.

### Employee List (`Employee List` nav)
- `POST /json/emn/employee-list` — body `{sortInfo, filter, pagingInfo}` — full employee directory (paginated)

### Open Shifts (`Open Shifts` nav)
- `POST /json/mn/openShift/getAllOpenShifts` — list of open shifts available to claim

### Blackout Dates (`Blackout Dates` nav)
- `POST /json/mn/blackoutDates` — list of blackout date ranges (e.g. holidays where requests are blocked)

### Staffing Organizer (`Staffing Organizer` nav)
- `POST /json/n/getStaffingOrganizerPageData` — staffing template builder (drag-out hours by daypart per position)

### Activity Log (`Activity Log` nav)
- `POST /json/mn/activityLog/get/forDate` — audit trail by date

## Highest-leverage endpoints for Bobby's automations

For the **lights-out dashboard** product:
1. `getDataForManageSchedulesPage` → discover the current `lsi` for "this week"
2. `getWbForecastData` → 7-day Sales/Ideal/Scheduled/Labor% summary in one call (powers the Forecast section in the daily brief and the dashboard "Labor at a glance" card)
3. `dailyRoster/getPageData` → today's roster (already wired into `weekly_schedule.json`)
4. `dailyRoster/getForecastData` → today's forecast metrics (Sales/Guests/Checks/SPLH/GPLH/Variance) — feed the dashboard's "Today" panel

For the **schedule build skill** moving to API-only (replacing Playwright):
1. `getSchedulingTemplate` → pull "DIXIE LABOR Monday" staffing template
2. `getDataForAutoScheduler` → see what Teamworx's own auto-scheduler considers (employee availability, OT limits, position requirements)
3. **Open follow-up:** capture the SAVE-shift endpoint (drag a shift on the Labor Schedule Edit page with capture on) — this is the missing write path that closes the lights-out loop. Likely something like `POST /json/mn/laborSchedule/saveShifts`.

For **multi-location consulting product** (selling to other Five Guys franchisees):
- The `n/scheduleOverview/getScheduleOverviewPageData` endpoint returns per-location data — one API call gives the multi-store dashboard view. Trivial to scale across 11 locations.

## Full endpoint catalog — 135 URLs (2026-05-05 deep scan)

Extracted by recursive scan of every JS function on the Labor Schedule edit page,
matching the regex `/json/[a-zA-Z0-9\-/_.]+`. This is the union of every endpoint the
manager-console JS *could* call. Coverage spans manager (`/mn/`), employee (`/e/`),
shared (`/emn/`), cross-location (`/n/`), and account (`/a/`, `/em/`) namespaces.

### `/mn/` — Manager Console (the bulk of what we'll automate)

**Labor Schedule (read + WRITE)**
- POST `/json/mn/laborSchedule/createLaborSchedule` ⚠️ **WRITE** — creates new weekly schedule
- POST `/json/mn/laborSchedule/publishLaborSchedule` ⚠️ **WRITE** — "Mark As Ready" / publish
- POST `/json/mn/laborSchedule/getDataForAutoScheduler` — input bundle for auto-scheduler
- POST `/json/mn/laborSchedule/preferencesForAutoScheduler` — auto-scheduler config
- POST `/json/mn/laborSchedule/overtimeLimitsForAutoScheduler` — OT caps
- POST `/json/mn/laborSchedule/getFilteredEmployeeList` — employee dropdown filter
- POST `/json/mn/laborSchedule/getWbDailyShiftMetrics`
- POST `/json/mn/laborSchedule/getWbWeeklyShiftMetrics`
- POST `/json/mn/laborSchedule/staffing-level-templates`
- POST `/json/mn/laborSchedule/getDataForExportingLaborSchedule`
- POST `/json/mn/laborSchedule/addMultipleEmployeePositionRowsAndLoadEmployeesData`
- POST `/json/mn/labor-schedule/add-unscheduled-employees`
- POST `/json/mn/laborSchedules/checkShiftsExist`
- POST `/json/mn/manageSchedules/checkIfEditingScheduleMayCauseScheduleChangeViolations`
- POST `/json/mn/manageSchedules/validate-schedule-before-open`

**Shift Templates (read + WRITE)**
- POST `/json/mn/templates/getSchedulingTemplatesData` — list templates
- POST `/json/mn/templates/storeColumnsState` — UI prefs
- POST `/json/mn/templates/updateSchedulingTemplate` ⚠️ **WRITE** — save template changes
- POST `/json/mn/templates/validateSchedulingTemplate` — validate before save

**Open Shifts (read + WRITE)**
- POST `/json/mn/openShift/create` ⚠️ **WRITE** — create open shift
- POST `/json/mn/openShift/approveShift` ⚠️ **WRITE** — approve employee claim
- POST `/json/mn/openShift/getDataForPostAnOpenShiftsPage`
- POST `/json/mn/openShift/getViolationsForShiftApproveAction`
- GET  `/json/mn/openShifts/countOpenShifts`

**Availability + Time Off**
- POST `/json/mn/myAvailability/approveAvailabilityRequest` ⚠️ **WRITE**
- POST `/json/mn/myAvailability/denyAvailabilityRequest` ⚠️ **WRITE**
- GET  `/json/mn/myAvailability/getAvailabilitiesForCurrentWeek`
- POST `/json/mn/blackoutDates/get/getTimeOffRequestsByDate`
- POST `/json/mn/timeOff/`

**Employee Records + Notes**
- POST `/json/mn/employeeNote/saveEmployeeNote` ⚠️ **WRITE**
- POST `/json/mn/employeeNote/logicallyRemoveEmployeeNote` ⚠️ **WRITE**
- POST `/json/mn/employeeRecord/`
- POST `/json/mn/getEmployeesByPosition`

**Tasks (Steritech-style daily checklists)**
- POST `/json/mn/getEmployeeTasksPageData`
- POST `/json/mn/getEditTaskSeriesPageData`
- POST `/json/mn/saveTaskSeries` ⚠️ **WRITE**
- POST `/json/mn/deleteTaskSeries` ⚠️ **WRITE**

**Reports (PDF/CSV exports — kicks off async report generation)**
- POST `/json/mn/report/createApprovedTimeOffRequestsReport`
- POST `/json/mn/report/createEmployeeNotesReport`
- POST `/json/mn/report/createEmployeeTasksReport`
- POST `/json/mn/report/createInvalidShiftsReport`
- POST `/json/mn/report/createLaborScheduleAlertsReport`
- POST `/json/mn/report/createManageBlackoutDatesReport`
- POST `/json/mn/report/createOpenShiftsReport`
- POST `/json/mn/report/createScheduleMetricsReport`
- POST `/json/mn/report/createTextFileForLaborScheduleExport`
- POST `/json/mn/report/exportLaborScheduleViaEmail`
- POST `/json/mn/report/manageSchedules/createWeeklyShiftsReport`
- POST `/json/mn/reports/manager-employee-list`

**Activity Log**
- POST `/json/mn/get/activityLogDetails/pickup`
- POST `/json/mn/get/activityLogDetails/swap`

**Account / location switching**
- POST `/json/mn/account/changeManagerConsoleLocation` — switch active store
- POST `/json/mn/account/getLocationSelectPageData` — list of stores user has access to
- POST `/json/mn/account/loginToManagerConsole`

**Other**
- GET  `/json/mn/get/getLocationWeekStartDay`
- GET  `/json/mn/myRequest/countStaffRequest`
- POST `/json/mn/message/getManagerShiftNotes`

### `/n/` — Cross-Location / Network-level

- POST `/json/n/scheduleOverview/getScheduleOverviewPageData` — multi-store schedule roll-up
- POST `/json/n/scheduleOverview/getStaffingStructuresWithMetrics`
- POST `/json/n/getEditStaffingOrganizerPageData`
- POST `/json/n/saveStaffingStructure` ⚠️ **WRITE**
- POST `/json/n/deleteStaffingStructure` ⚠️ **WRITE**
- POST `/json/n/laborSchedule/publishLaborScheduleWithLocationChange` ⚠️ **WRITE**
- POST `/json/n/laborSchedule/startEditScheduleAndGetRuleViolationsWithLocationChange`
- POST `/json/n/employee/getEmployeePrioritySettings`
- POST `/json/n/employee/updateEmployeePrioritiesSettings` ⚠️ **WRITE**
- POST `/json/n/message/getBroadcastDialogData`
- POST `/json/n/message/sendCrossLocationMessage` ⚠️ **WRITE**
- POST `/json/n/report/createEmployeePrioritiesReport`
- POST `/json/n/report/createScheduleOverviewReport`
- POST `/json/n/report/createStaffingStructureReport`
- POST `/json/n/account-reset/email`, `/email/validate`, `/get-data`, `/phone`, `/phone/validate`

### `/emn/` — Shared Employee + Manager

- POST `/json/emn/employee-list` — paginated employee directory (used in schedule build)
- POST `/json/emn/employee-list/filter-data`
- POST `/json/emn/employee-list/save-legend-state`
- POST `/json/emn/employee-list-priority/save-legend-state`
- POST `/json/emn/datepicker/settings`
- GET  `/json/emn/message/countUnReadMessage`
- POST `/json/emn/message/sendNewMessage` ⚠️ **WRITE**
- POST `/json/emn/message/sendReplyToMessage` ⚠️ **WRITE**
- POST `/json/emn/message/getAllMessageRecipients`
- POST `/json/emn/message/getMessageRecipients`
- POST `/json/emn/message/getMessageDetails`
- POST `/json/emn/message/getMessageThreadDetails`
- POST `/json/emn/message/getReplyToMessagePermission`
- POST `/json/emn/message/readMessage` ⚠️ **WRITE**
- POST `/json/emn/message/readMessageThread` ⚠️ **WRITE**
- POST `/json/emn/myAvailability/getMyAvailabilitiesDialogDataByRequestId/`
- POST `/json/emn/getChecklistItemsForTaskOccurrence`
- POST `/json/emn/getManagerialTaskComment`
- POST `/json/emn/getTaskHistoryData`
- POST `/json/emn/completeTask` ⚠️ **WRITE**
- POST `/json/emn/reopenTask` ⚠️ **WRITE**
- POST `/json/emn/updateOccurrenceChecklist` ⚠️ **WRITE**
- POST `/json/emn/report/createCheckListReport`
- POST `/json/emn/reports/employee-list`
- POST `/json/emn/accountChangeItems/getByAccountGroupId/`
- POST `/json/emn/account/verification/send/validate`
- POST `/json/emn/ctsso/send.ct` — single-sign-on shared secret with NetChef

### `/e/` — Employee-side (for the employee app, useful when building a "what employees see" view)

- POST `/json/e/myProfile/getPageData`
- POST `/json/e/myRequest/getEmployeeHomePageData`
- POST `/json/e/myRequest/countAvailableShifts`
- POST `/json/e/myRequest/countMyRequest`
- POST `/json/e/getMyTasksPageData`
- POST `/json/e/schedule/`
- POST `/json/e/schedule/coworkersDataByAvailableShift`
- POST `/json/e/schedule/shift/coworkers`
- POST `/json/e/schedule/shift/getShiftsForEmployeeForSwap`
- POST `/json/e/schedule/shift/offer` ⚠️ **WRITE** — offer shift to coworker
- POST `/json/e/schedule/shift/swap` ⚠️ **WRITE** — propose shift swap
- POST `/json/e/schedule/shift/takeBack` ⚠️ **WRITE** — withdraw offer
- POST `/json/e/shifts-worked`
- POST `/json/e/activityLog/getPickupInfo`
- POST `/json/e/activityLog/swap`
- POST `/json/e/account/currentUser/saveProfile` ⚠️ **WRITE**
- POST `/json/e/myAvailabilities/cancelAvailabilityRequest` ⚠️ **WRITE**
- POST `/json/e/timeOffRequest/cancelTimeOffRequest` ⚠️ **WRITE**
- POST `/json/e/employeeChangeRecord/cancelEmployeeRecord` ⚠️ **WRITE**
- POST `/json/e/message/getEmployeeMessageCenterData`
- POST `/json/e/message/getAllMessageRecipientsForEmployee`
- POST `/json/e/report/createMyTasksReport`
- POST `/json/e/report/createMyShiftsWorkedReport`

### `/a/`, `/em/` — Auth + account

- GET  `/json/a/isUserSessionValid` — health check (also great for cookie validation)
- POST `/json/a/account/verification/phone/token/validate`
- POST `/json/em/account/loginToEmployeeConsole`

## Lights-out unlock summary

The **WRITE endpoints** above close the lights-out loop for:

1. **Schedule builder (the big one):**
   `createLaborSchedule` → add shifts via `addMultipleEmployeePositionRowsAndLoadEmployeesData`
   → `publishLaborSchedule`. Pure HTTP. No Playwright. Runs on a $200 store-side mini-PC
   or in GitHub Actions every Sunday night.

2. **Shift template authoring:** `templates/validateSchedulingTemplate` →
   `templates/updateSchedulingTemplate`. Means we can iterate templates from a script
   based on Bobby's edit history.

3. **Open shift posting:** `openShift/create` + `openShift/approveShift`. Could automate
   "if Tuesday afternoon ideal hours > scheduled hours by 2+ and there's an unfilled
   shift, post it as an open shift to the team."

4. **Employee notes:** `employeeNote/saveEmployeeNote`. Tie incidents directly to employee
   records from the dashboard.

5. **Cross-location messaging:** `message/sendCrossLocationMessage`. Useful when SCG
   onboards a multi-location franchisee.

## The SAVE endpoint — `import-changes` (closes the lights-out loop)

**Captured 2026-05-05** by clicking the orange "Save" button on the Labor Schedule edit
page with the AJAX_UTILS.postJson interceptor patched in.

```http
POST /json/mn/labor-schedule/import-changes
Content-Type: application/json

{
  "weekEndingDate": "2026-05-10",
  "staffingStructureIds": null,
  "scheduleSubLineFlag": false
}
```

**Important: the body contains NO shift data.** This endpoint commits whatever shifts
have been staged client-side (or in a server-side staging area for this user's edit
session) for the named week. The actual shift creation/edit happens via:

- `POST /json/mn/laborSchedule/addMultipleEmployeePositionRowsAndLoadEmployeesData` (stage)
- `POST /json/mn/laborSchedules/addEmployeePositionRowAndLoadEmployeeData` (stage)

After save, the page automatically calls:
- `POST /json/mn/laborSchedules/refreshWBLaborScheduleData` — reload schedule grid with violations
- `POST /json/mn/laborSchedules/getRuleViolations` — rule violation check (overtime, minor laws, double-booking)

**Full lights-out flow for the schedule builder:**

```
1. POST /json/mn/laborSchedules/getDataForManageSchedulesPage   { "year": 2026 }
   → discover the lsi for the target week

2. POST /json/mn/laborSchedule/startEditLaborSchedule           { "laborScheduleId": <lsi> }
   → claim edit lock

3. POST /json/mn/templates/getSchedulingTemplate                { "templateId": 29661 }
   → pull "DIXIE LABOR Monday" template

4. for each day, for each position, for each shift in template:
   POST /json/mn/laborSchedule/addMultipleEmployeePositionRowsAndLoadEmployeesData
   → stage shifts

5. POST /json/mn/labor-schedule/import-changes                  { weekEndingDate, ... }
   → commit staged shifts ⚠️ WRITE

6. POST /json/mn/laborSchedules/getRuleViolations               (auto-fires)
   → confirm no violations introduced

7. POST /json/mn/laborSchedule/publishLaborSchedule             { laborScheduleId }
   → "Mark As Ready" / publish ⚠️ WRITE
```

Pure HTTP. Total time: ~3 seconds. Runs from a Windows mini-PC, GitHub Actions cron, or
anywhere with Python + Teamworx cookies.

## Next discovery passes

When time permits — same pattern (interceptor + click target):
- **The exact stage-shift payload** — drag a shift cell or click "+" with capture on. The
  endpoint is `addMultipleEmployeePositionRowsAndLoadEmployeesData` but the body shape
  (employeeId, positionId, inTime, outTime, station, etc.) needs to be confirmed.
- **Auto-scheduler RUN endpoint** — different from `getDataForAutoScheduler`. Click the
  "wand" icon on the labor schedule edit page header.
- **Promotions / Holidays / Closed-calendar setup** — referenced in `dayForecast` schema
  but not yet captured.
- **Send Message endpoint** — `POST /json/message-center/message` likely. Fires only on
  actual send from "+ New Message" composer.

## Pattern source

Discovery sessions:
- 2026-05-04 — initial 5 endpoints via fetch interceptor
- 2026-05-05 — full sidebar walk + JS-source-scan = 135 unique endpoints catalogued

Same approach as CrunchTime tip entry (`api_discover.py` → `api_enter_tips.py`) — Bobby's
standing rule per `~/.claude/rules/reverse-engineer-apis-first.md`.

The 2026-05-05 expansion was triggered by Bobby's directive: *"I need for as many endpoints
to be reached as possible. I need for you to know teamworx inside and out literally."*
Context: dashboard wants hourly Sales / Ideal / Scheduled visualization next to the roster
(per Bobby's profitability-training thesis: GMs control Labor + COGS; visual hourly trend
data trains them to schedule better). Plus the long-game roadmap is a Python schedule
builder running on a store-side mini-PC with no Claude required at runtime — these write
endpoints are how that ships.
