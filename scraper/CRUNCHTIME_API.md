# CrunchTime / NetChef API Reference — Store 2065

**Status:** TEST PHASE. Production scraper (`main.py`, `scrape_cogs.py`, etc.) is unchanged. The cookie-replay rebuild lives in `api_*.py` files alongside.

**Last updated:** 2026-05-03 (Prometheus session — 119 endpoints across 34 screens)

## Capture totals
- 119 unique JSON endpoints, all 200 OK with cookie auth
- 34 distinct screens (warmup + 33 navigated reports)
- Auth verified end-to-end (login mint → cookie reuse → POST replay)
- Largest payload: `/resource/labor/todays/operatingMetrics` (113 KB hourly grid)
- Smallest useful: `/resource/recommended-actions/status` (22 b session probe)

---

## TL;DR

CrunchTime exposes **two distinct API surfaces**:

| Surface | Host | Auth | Use case |
|---|---|---|---|
| **Internal Net Chef UI API** (this doc, primary) | `fiveguysfr77.net-chef.com/resource/*` | Cookie (JSESSIONID + hazelcast.sessionId + session_idUTF) | Powers the Net Chef UI. All daily operational data (KPIs, COGS, labor, sales drilldowns, employee records). What the daily scraper currently DOM-parses. |
| **Public Integration API** (documented at developer.crunchtime.com) | `webservices.net-chef.com/<service>/v1/...` | Header-based: `authenticationtoken`, `userid`, `password`, `sitename` | Partner / batch integration. Sales forecast push/pull, employee export, time clock import, sales mix import. Requires partner credentials we do not yet have. |

The dashboard rebuild targets **#1**. The Public API is documented below for completeness in case Bobby pursues partner credentials later.

---

## Section 1 — Internal Net Chef UI API (cookie-replay)

### 1.1 Auth flow

```
1. GET  https://fiveguysfr77.net-chef.com/resource/ceslogin/resources
2. POST https://fiveguysfr77.net-chef.com/resource/ceslogin/auth
   body: {"username": "...", "password": "..."}    (form fields)
3. GET  https://fiveguysfr77.net-chef.com/resource/ceslogin/locations?page=1&start=0&limit=25
4. POST https://fiveguysfr77.net-chef.com/resource/ceslogin/choose-location
   body: {"locationId": 13969}     (KY-2065 = 13969)
5. After step 4, the session is bound to the chosen location.
   Subsequent /resource/* calls use cookies set during this flow.
```

**Session cookies that matter** (httpOnly):
- `JSESSIONID`
- `hazelcast.sessionId`
- `session_idUTF`

**Session timeout:** ~30 min idle. Session-alive probe: `GET /resource/recommended-actions/status` (22 bytes, fast). 200 → reuse. 401/403/redirect → re-mint via Playwright login flow.

**Required headers for replay:**
```python
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json;charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin":  "https://fiveguysfr77.net-chef.com",
    "Referer": "https://fiveguysfr77.net-chef.com/ncext/modern.ct",
}
```

**No CSRF, no signed query params, no second handshake.** Verified 2026-05-03 against `/resource/dashboard/performance/metrics`.

### 1.2 Discovery + replay scripts (this repo)

| Script | Purpose |
|---|---|
| `scraper/api_discover.py` | Single-pass Playwright login → response hook → dump dashboard XHRs + cookies. |
| `scraper/api_discover_targeted.py` | Same login, then walks specific menu labels (uses `ct_menu_inventory.json`). 89 endpoints captured 2026-05-03. |
| `scraper/api_enumerate_menu.py` | Dumps every ExtJS `menuitem` / `treeitem` / `button` to `data/ct_menu_inventory.json` — 241 items. Use this to discover screen names without guessing. |
| `scraper/api_test_cookie.py` | Pure-`requests` POST to `/resource/dashboard/performance/metrics` using captured cookies. Sanity check that cookie auth still works. |
| `scraper/api_query.py` | Production-shape: cached cookies + session-alive probe + auto re-mint via subprocess. Pulls yesterday's Net Sales + Labor%. Pattern for `api_main.py`. |
| `scraper/api_discover_one.py` | Single-target run for incremental sweeps when one screen needs re-capture. |

Captured artifacts:
- `data/ct_api_endpoints_deep.json` — 89 endpoints with method + request body + truncated response (1500 chars) + size + first-seen-screen
- `data/ct_endpoints_by_screen.json` — `{screen: [urls...]}`
- `data/ct_menu_inventory.json` — 241 ExtJS menu items
- `data/ct_cookies.json` — last successful session (overwrites on each Playwright run)

---

### 1.3 Par Brink → NetChef API replacement map

**Bobby's insight (2026-05-03):** Brink is the POS, NetChef is the BOH that consumes Brink data. So most Brink reports we currently email-pickup-and-parse-PDFs for are *already in NetChef* via the API. This kills an entire workflow.

| Current Brink PDF report | Currently parsed by | NetChef API replacement | Status |
|---|---|---|---|
| Sales Summary | `parbrink_parse_sales_summary.py` | `POST /resource/sales/sales/registerSales/summary` (14 KB) — net sales, gross sales, taxable, catering, tips, voids, complimentary, paid outs, bank deposits, **over/short**, guest count, per-register-per-day | ✅ direct replacement; richer fields |
| Hourly Sales And Labor | `parbrink_parse_hourly_sales_labor.py` | `POST /resource/labor/todays/operatingMetrics` (113 KB) — 15-min intervals with sales, checks, guests, actLab, actHrs, FOH/BOH split, forecasted sales/guests/checks, scheduled labor, variance | ✅ direct replacement; finer granularity (15-min vs hourly) |
| Discount Summary | `parbrink_parse_discounts.py` | `POST /resource/sales/sales/registerSales/summary` returns `totComplimentary` per day. Per-discount-code drill via `/resource/menumix/...` if needed | ✅ aggregate covered; per-code drill available |
| Weekly Labor Schedule | `parbrink_parse_weekly_schedule.py` | `POST /resource/nc/scheduleshiftaudit/` (31.5 KB) — every shift change with employeeName, businessDate, timeIn, timeOut, edit history. Schedule itself derivable from this + `/resource/labor/hours` | ✅ data is there; format differs from Brink schedule PDF — needs new parser |
| Sales By Destination (dine-in/togo) | (not parsed today) | NOT in NetChef API surface visible to this user role. Channel split is a Brink-side concept. | ❌ Brink-only |
| Sales Summary By Location | (not parsed today, multi-store) | `/resource/sales/sales/registerSales/summary` with `allLocations:true` body would do this if Bobby had multi-store auth | ✅ available (multi-store) |
| Audit Business Date | (not parsed today) | NOT directly. NetChef has period-end dates via `/resource/postperiods` (12.4 KB) | ⚠️ different shape; periods only |
| Employee Timecard | `parbrink_parse_*` (in week-ending bundle) | `POST /resource/nc/employee/timedetail/summary` (129 KB) — full time-detail grid with regular/overtime/breaks per employee per day | ✅ direct replacement; richer fields |
| Sales By Day | (in weekly bundle) | `POST /resource/sales/sales/registerSales/summary` with `salesDate` range filter returns one row per day | ✅ direct replacement |
| Product Mix | (in weekly bundle) | `POST /resource/dashboard/menu/mix` (2.4 KB) — items with sales/cost/grossProfit/transactionCount. Or `/resource/menumix/...` for fuller hierarchy | ✅ direct replacement |
| Labor Cost By Job | (in weekly bundle) | `POST /resource/nc/labor/productivity/summary` (59 KB) — FOH/BOH split with ideal/scheduled/actual/variance | ✅ direct replacement |

**What this kills:** the Par Brink Gmail pickup → 11+ PDF parsers → JSON path. One vendor pipeline retired. Schedule for retirement: AFTER `api_main.py` parity is proven (Section 3 plan).

**What stays:** ComplianceMate (different vendor), KnowledgeForce (different vendor), Microsoft Graph (already API), Outlook (already token-based), Teamworx if used (different vendor).

### 1.4 Bobby's specific targets — endpoint mapping

| Bobby asked for | Internal endpoint | Method | Sample size | Body shape |
|---|---|---|---|---|
| **Employee Time Detail** | `/resource/nc/employee/timedetail/summary` | POST | 129 KB | `{"pagingInfo":{"page":1,"start":0,"limit":150}, "extraCriteriaMap":{"includeAltLocations":false,"excludeManagers":true,"summarizeBy":"","startDate":"04/27/2026 00:00:00","weekEndingDate":"05/03/2026 00:00:00",...}}` |
| **Projected Sales** | `/resource/sales/sales/forecast` | POST | 26 KB | `{"node":"root","extraFilter":[]}` — returns weeks with day1..day7 + total |
| **Cash Over/Short Deposits** | `/resource/dashboard/performance/metrics` (KPI rows "Total Cash Over/Shorts" + "Cash Over/Shorts by Cash Register") **OR** `/resource/sales/sales/registerSales/summary` (cash register totals per day) **OR** `/resource/salesjournal/resources` (post period structure) | POST | 21 KB / 14 KB / 9 KB | See payload fields |
| **Weekly Sales** | `/resource/tilereports/snapshot/week/sales` (current week tile) **OR** `/resource/sales/sales/forecast` (forecast vs actual by week) | POST | 259 b / 26 KB | Trivial bodies |
| **Historical Sales** | `/resource/sales/sales/registerSales/summary` (accepts `salesDate` filter range) **OR** `/resource/labor/actual/2026` (week-level history per fiscal year) **OR** `/resource/dailypayrollcontrol/summary` (forecast/actual/variance by day across a date range) | POST | 14 KB / 9 KB / 2.9 KB | See payload fields |
| **Employee Maintenance (records)** | `/resource/labor/employee/maintenance` | POST | 36 KB | `{"page":1,"start":0,"limit":75,"extraFilter":[{"type":"string","value":"Active","field":"filter_by_status"},{"type":"string","value":"All","field":"filter_by_location"},...]}` — returns full employee roster |

---

### 1.5 Full endpoint catalog (119 captured across 34 screens)

#### Login / session
| Method | Path | Notes |
|---|---|---|
| GET | `/resource/ceslogin/resources` | Pre-login config (returns `appShortVersion`, languages, `contactUsUrl: https://crunchtime.zendesk.com`) |
| POST | `/resource/ceslogin/auth` | Submit creds. Response `{"success":true,"contentMap":{}}` |
| GET | `/resource/ceslogin/locations?page=1&start=0&limit=25` | List locations user can see. Response `{success:true, contentMap:{locations:[{locationName, locationId, locationCode}]}}` |
| POST | `/resource/ceslogin/choose-location` | Pin session to a location |
| GET | `/resource/recommended-actions/status` | **Session-alive canary** (22 bytes) |
| POST | `/resource/ui-settings/navigationMenu` | Saves nav state |

#### Dashboard (warmup screen)
| Method | Path | Body | Returns |
|---|---|---|---|
| POST | `/resource/dashboard/performance/metrics` | `{"allLocations":false,"pagingInfo":{"infinite":false}}` | 35 KPIs by day1..day7 + WTD + PTD (21.5 KB) — **the main metric source** |
| POST | `/resource/dashboard/top/actual/vs/theoretical` |  | COGS variance top-N items (2.5 KB) |
| POST | `/resource/labor/hours` |  | Employee labor hours grid (10.8 KB) |
| POST | `/resource/labor/todays/operatingMetrics` |  | Hourly labor today (113 KB) |
| POST | `/resource/tilereports/snapshot/today/sales` |  | Today sales tile (343 b) |
| POST | `/resource/tilereports/snapshot/week/sales` |  | Week sales tile (259 b) |
| POST | `/resource/dashboard/widget/chart/daily/sales/trend/false` |  | Daily sales trend chart (889 b) |
| POST | `/resource/inventory/value/trend/false` |  | Inventory value trend (763 b) |
| POST | `/resource/dashboard/menu/mix` |  | Menu mix (2.4 KB) |
| POST | `/resource/dashboard/todaytasks/details` |  | Today's tasks (5.2 KB) |
| GET | `/resource/dashboard/dailynews/all/status` |  | Daily news flag |
| GET | `/resource/dashboard/dailynews/all?page=1&start=0&limit=25` |  | Daily news content |
| GET | `/resource/dashboard-layout/personal/ncMain?page=1&start=0&limit=25` |  | Personal dashboard layout config (4.4 KB) |
| POST | `/resource/dashboard-layout/personal/ncMain/config` |  | Save personal layout |
| GET | `/resource/dashboard/performance/metrics/kpi/list/count` |  | KPI count (2 b) |
| GET | `/resource/layout/configuration/dashboard-widget-performance-metrics-grid` |  | Layout: KPI grid columns (1.2 KB) — defines column→day mapping |
| GET | `/resource/layout/configuration/dashboard-widget-today-operating-metrics-list-94861` |  | Layout: hourly metrics (7.9 KB) |
| GET | `/resource/layout/configuration/dashboard-widget-labor-hours-list` |  | Layout: labor hours (1.2 KB) |

#### Employee Time Detail
| Method | Path | Notes |
|---|---|---|
| POST | `/resource/nc/employee/timedetail/retrieveResources` | Page bootstrap |
| GET | `/resource/nc/employee/timedetail/currentPeriodDateRange` | Returns current pay period dates |
| POST | `/resource/nc/employee/timedetail/summary` | **THE BIG ONE**, 129 KB — full time-detail grid for all employees in the period |
| GET | `/resource/layout/configuration/employeetimedetail-summarygrid-basic` | Grid layout (2.8 KB) |

#### Consolidated Employee Time Detail
| Method | Path |
|---|---|
| POST | `/resource/nc/employee/timedetail/consolidated/retrieveResources` |
| GET | `/resource/layout/configuration/consolidatedemployeetimedetail-summarygrid` (5.8 KB) |

#### Time Clock Audit
| Method | Path |
|---|---|
| POST | `/resource/laboraudit/currentPeriodDateRange` |
| GET | `/resource/layout/configuration/laborAuditGridReport_All` |

#### Employee Maintenance
| Method | Path | Notes |
|---|---|---|
| POST | `/resource/labor/employee/maintenance` | **Full employee roster** with name, position, location, status, hire date, last edited (36 KB) |
| GET | `/resource/layout/configuration/nc-employee-information-grid` | Grid layout (1.4 KB) |
| GET | `/resource/labor/employee/primarylocations?page=1&start=0&limit=25` | Available primary locations |
| GET | `/resource/labor/employee/positions?page=1&start=0&limit=25` | Available positions |
| GET | `/resource/labor/employee/statuses?page=1&start=0&limit=25` | Available statuses |
| GET | `/resource/layout/corporate/laborPanel/default` | Labor panel layout (843 b) |

#### Employee Payroll Info Summary
| Method | Path | Notes |
|---|---|---|
| POST | `/resource/nc/labor/employeepayrollinformation/summary` | 241 employees with pay rate, marital status, exemptions (22.7 KB) |
| POST | `/resource/nc/labor/employeepayrollinformation/resources` | Page bootstrap |
| GET | `/resource/layout/configuration/employeepayrollinformation-summarygrid` | Grid layout |
| GET | `/resource/nc/labor/employeepayrollinformation/maritalstatuses` | Lookup |

#### Daily Payroll Control
| Method | Path | Notes |
|---|---|---|
| POST | `/resource/dailypayrollcontrol/summary` | **Forecast vs Actual sales + payroll by day, with WTD variances** (2.9 KB). Body: `{"pagingInfo":{...},"extraCriteriaMap":{"startDate":"04/27/2026 00:00:00","endDate":"05/03/2026 00:00:00"}}` |
| POST | `/resource/dailypayrollcontrol/retrieveResources` | Page bootstrap |
| GET | `/resource/dailypayrollcontrol/currentPeriodDateRange` |
| GET | `/resource/layout/configuration/dailypayrollcontrol-grid` |

#### Sales — Manage Sales Forecasts (Projected Sales)
| Method | Path | Notes |
|---|---|---|
| POST | `/resource/sales/sales/forecast` | **Projected sales weekly + day1..day7 forecast vs actual** (26 KB). Body: `{"node":"root","extraFilter":[]}` |
| POST | `/resource/sales/sales/comboboxData/salesForecast` | Combo data |
| GET | `/resource/sales/forecast/day/percent` | Day-of-week % distribution |
| GET | `/resource/sales/forecast/show/check/counts/checkbox` | UI flag |
| GET | `/resource/sales/forecast/initial/checkbox/values` | UI defaults |
| GET | `/resource/layout/corporate/salesPanel/default` | Sales panel layout |
| GET | `/resource/layout/configuration/salesForecastGrid` | Forecast grid layout |

#### Sales Overview — Register Sales Summary
| Method | Path | Notes |
|---|---|---|
| POST | `/resource/sales/sales/registerSales/summary` | **Per-register sales** (totTaxableSales, totGrossSales, chargedTips, overrings, complimentary). 14 KB. Body: `{"page":1,"start":0,"limit":75,"extraFilter":[{"type":"date","value":"04/23/2026","field":"salesDate","comparison":"gt"},{"type":"date","value":"05/03/2026","field":"salesDate","comparison":"lt"}]}` — accepts `salesDate` range. |
| GET | `/resource/sales/sales/registerSales/defaultDateRange` |
| GET | `/resource/layout/configuration/registerSalesGrid` |
| POST | `/resource/connexui/commands` |

#### Bank Deposits — full CRUD (discovered 2026-05-11)

These three endpoints power the "Enter Sales Transaction" → "Bank Deposits" tab in the `next.ct` edit form. Cookie auth, no CSRF. Verified end-to-end against salesId=6180801 (KY-2065, 05/10/2026).

| Method | Path | Notes |
|---|---|---|
| POST | `/resource/salestransactions/bankdeposits?_dc=<ms>` | **Read** — list deposit rows for the open transaction. Body: `{"pagingInfo":{"page":1,"start":0,"limit":75},"sortInfo":{"sortList":[{"property":"amount","direction":"ASC"}]}}`. Session context (the open transaction's salesId) is implicit from the prior `/prepare` call. |
| POST | `/resource/salestransactions/bankdeposits/save` | **Write** — create / update / delete deposit row(s). Body: `[{"depositId":-2,"amount":0.01,"memo":""}]`. **Negative `depositId` = new row** (client-assigned temp id, server returns the real positive id). Positive `depositId` = existing row (omit/keep value to delete? — TBD via testing). Returns the saved rows with assigned ids. |
| POST | `/resource/salestransactions/submit` | **Commit** — persists the whole sales transaction (all sub-grids — bank deposits, paid outs, comps, etc.). Body: `{"extraCriteriaMap":{"salesId":6180801,"viewOnly":false,"posId":2148,"salesDate":"05/10/2026"}}`. `salesId` + `posId` come from `registerSales/summary`. `salesDate` in MM/DD/YYYY. |

**Required form-prep calls before /save will work** (CT binds session to the open transaction):
1. `POST /resource/salestransactions/retrieveResources`
2. `POST /resource/salestransactions/currentmode`
3. `POST /resource/salestransactions/validateedit`
4. `POST /resource/salestransactions/prepare`
5. Now `bankdeposits/save` + `submit` are valid.

The shorter path that the agent script uses: navigate the edit URL `https://fiveguysfr77.net-chef.com/ncext/next.ct#SalesTransactions?mode=edit&salesId=<id>` via Playwright (which fires the prep chain implicitly), then replay `/save` + `/submit` with cookies. Pure-`requests` replay without the form-prep chain returns 400.

**Agent-entry script:** `scripts/enter_ct_deposits.py` reads pending entries from `data/deposits_pending.json`, opens each transaction's edit form, posts the deposit row, submits, marks the entry as processed.

#### Sales Journal
| Method | Path | Notes |
|---|---|---|
| POST | `/resource/salesjournal/resources` | Period boundaries — minDate, postPeriods array (9.3 KB). Foundational for journal queries. |
| GET | `/resource/layout/configuration/salesjournal-summarygrid-` | Grid layout |

#### Labor — Labor Summary (week-level by fiscal year)
| Method | Path | Notes |
|---|---|---|
| POST | `/resource/labor/actual/2026` | All week-ending rows for fiscal year 2026 with import/edit dates and review status (9.5 KB). |
| GET | `/resource/labor/actual/fiscalYears?page=1&start=0&limit=25` | Available years |
| GET | `/resource/layout/configuration/laborActualsGrid` |

#### Projected Overtime
| Method | Path | Notes |
|---|---|---|
| POST | `/resource/labor-summary-projected-overtime-report` | **Big payload — 75 KB.** Per-employee projected OT for the week. |
| POST | `/resource/labor-summary-projected-overtime-report/retrieveResources` |
| POST | `/resource/labor-summary-projected-overtime-report/prepare` |
| GET | `/resource/labor-summary-projected-overtime-report/employee?weekEndingDate=05/03/2026&page=1&start=0&limit=25` |
| GET | `/resource/labor-summary-projected-overtime-report/dateranges` |
| GET | `/resource/layout/configuration/laborsummaryprojectedovertime-grid` |

#### Inventory Overview
| Method | Path |
|---|---|
| POST | `/resource/inventory/physicalinventory/summary/post/period` |
| POST | `/resource/inventory/physicalinventory/summary` |
| POST | `/resource/inventory/adjustment` |
| GET | `/resource/inventory/adjustment/dateRange` |
| POST | `/resource/inventory/location/transfers` |
| GET | `/resource/inventory/location/transfers/filters` |
| GET | `/resource/inventory/location/transfer/types` |
| GET | `/resource/inventory/location/transfer/statuses` |
| GET | `/resource/inventory/location/transfer/transmission/statuses` |
| GET | `/resource/layout/corporate/inventoryPanel/default` |
| GET | `/resource/layout/configuration/physicalInventorySummaryGrid` |
| GET | `/resource/layout/configuration/recentLocationTransfersGrid` |
| GET | `/resource/layout/configuration/recentAdjustmentsGrid` |

#### Schedule Shift Audit (THE schedule data — replaces Par Brink Weekly Labor Schedule)
| Method | Path | Notes |
|---|---|---|
| POST | `/resource/nc/scheduleshiftaudit/` | Body: `{"pagingInfo":{"page":1,"start":0,"limit":75},"extraCriteriaMap":{"startDate":"04/27/2026","endDate":"05/03/2026"}}`. Returns 31 KB grid: every shift change record with `employeeName`, `businessDate`, `timeIn`, `timeOut`, `field`, `editType`, `oldValue`, `editValue`, `userId`, `firstName`, `lastName`. Schedule + audit history in one call. |
| POST | `/resource/nc/scheduleshiftaudit/retrieveResources` | Page bootstrap |
| GET | `/resource/nc/scheduleshiftaudit/currentPeriodDateRange` |
| GET | `/resource/layout/configuration/scheduleshiftaudit-maingrid` |

#### Consolidated Schedule Shift Audit (multi-location)
| Method | Path |
|---|---|
| GET | `/resource/nc/consolidatedscheduleshiftaudit/currentPeriodDateRange` |
| GET | `/resource/layout/configuration/consolidatedscheduleshiftaudit-maingrid` |

#### Menu Mix (replaces Par Brink Product Mix)
| Method | Path | Notes |
|---|---|---|
| POST | `/resource/menumix/common/resources` | Page bootstrap; returns groupBy options (CATEGORY, SUBCATEGORY, MICROCATEGORY, DAYPART, CUSTOMER, REVENUE_CENTER) |
| POST | `/resource/postperiods` | List of post periods with beginDate / postDate (12.4 KB — useful for any "by period" rollup) |
| GET | `/resource/menumix/common/hierarchies` | Hierarchy lookup |
| POST | `/resource/menumix/location/groupoptions` |
| POST | `/resource/menumix/location/secondarygroupoptions` |
| GET | `/resource/layout/configuration/menumixsummary-grid` |

#### Consolidated Menu Mix (multi-location)
| Method | Path |
|---|---|
| POST | `/resource/menumix/consolidated/groupoptions` |
| POST | `/resource/menumix/consolidated/secondarygroupoptions` |
| GET | `/resource/layout/configuration/menumixsummary-consolidatedgrid` |

#### Labor Productivity (replaces Par Brink Labor Cost By Job)
| Method | Path | Notes |
|---|---|---|
| POST | `/resource/nc/labor/productivity/summary` | 59 KB — FOH/BOH hours + productivity with ideal/scheduled/actual/variance. Body: `{"pagingInfo":{...},"extraCriteriaMap":{"summarizeBy":"","viewBy":"hours","locationId":13969,"startDate":"04/27/2026 00:00:00","endDate":...}}` |
| POST | `/resource/nc/labor/productivity/resources` | Page bootstrap |
| GET | `/resource/nc/labor/productivity/currentPeriodDateRange` |
| GET | `/resource/layout/configuration/laborproductivity-summarygrid-basic-hours` |

#### Consolidated Labor Productivity (multi-location)
| Method | Path |
|---|---|
| POST | `/resource/nc/labor/consolidatedproductivity/resources` |
| GET | `/resource/nc/labor/consolidatedproductivity/dateranges` (29 KB — full date-range index) |
| GET | `/resource/hierarchy/display` |
| GET | `/resource/layout/configuration/consolidatedlaborproductivity-summarygrid` |

#### Consolidated Payroll Control (multi-location forecast vs actual)
| Method | Path |
|---|---|
| POST | `/resource/nc/labor/payrollcontrol/consolidated/retrieveResources` |
| GET | `/resource/nc/labor/payrollcontrol/consolidated/dateranges` (40 KB) |
| GET | `/resource/layout/configuration/consolidatedpayrollcontrol-summarygrid` |

#### Employee Breaks
| Method | Path |
|---|---|
| POST | `/resource/nc/employeebreaks/resources` |
| GET | `/resource/layout/configuration/employeebreaks-summarygrid-E-M` |

#### Employee Changes (audit log)
| Method | Path | Notes |
|---|---|---|
| POST | `/resource/nc/labor/employeechanges/summary` | 7.7 KB — change log per employee |
| GET | `/resource/layout/configuration/employeechanges-summarygrid` |

#### Post Labor (lock the books)
| Method | Path |
|---|---|
| POST | `/resource/administration/posting/post/validate` |

---

### 1.5 calcId → day-of-week mapping (Performance Metrics)

`/resource/dashboard/performance/metrics` returns each KPI with `metrics: [{calcId, value, isAlert}]`. The mapping (verified 2026-05-03):

| calcId | Day |
|---|---|
| 1 | Sun (today, partial) |
| 2 | Mon |
| 3 | Tue |
| 4 | Wed |
| 5 | Thu |
| 6 | Fri |
| 7 | Sat (yesterday) |
| WTD | Mon-Sat sum (week-to-date, excludes today's Sunday) |
| PTD | Period-to-date |

Formula: `calcId = isoweekday() % 7 + 1`. Verified by sum check: WTD = sum of calcIds 2-7. See `scraper/api_query.py`.

---

## Section 2 — Public Integration API (documented)

**Base URLs**
- **Test:** `https://webservices-test.net-chef.com`
- **Production:** `https://webservices.net-chef.com`

**Auth (every request)** — header-based, NOT cookie:
```
authenticationtoken: <secure token, issued by CrunchTime>
userid: <Application User ID>
password: <Application User password>
sitename: test | production
```

Optional headers: `X-B3-TraceId`, `accept` (defaults to application/json).

**Endpoint patterns** — three families:
- `getAll<Entity>` — targeted query, requires filter params (small payload)
- `getByPage<Entity>` / `<entity>byPage` — paginated bulk retrieval (large datasets)
- `save<Entity>` — POST upserts

**Status codes:** 200 OK, 400 validation, 401 auth fail, 404 not found, 429 rate limit, 500 server, 503 maintenance, 504 timeout.

### 2.1 Public endpoints documented at developer.crunchtime.com

| Service | Endpoint | Method | Notes |
|---|---|---|---|
| Employee — get one | `/employee/v1/detail` | GET | Required: `employeeNumber`, `employeeId`. Optional: `auditLog`, `includeNull`. |
| Locations — list all | `/location/v1/getAllLocations` | GET | Filters: `activeFlag`, `corporate`, `locationCode`, `market`, `city`, `stateProvince`, `country`, `franchiseCode`, `exportCode`, `payrollExportCode`, `minutesSinceUpdate`. Sort: `sortBy`, `sortOrder`. |
| Application Users | `getAllApplicationUsersV1` | GET | User profiles with IDs/passwords for Enterprise Manager + Net-Chef + Teamworx |
| Hierarchy | `getHierarchiesV1` | GET | Region/area groupings |
| Sales Forecast — 15-min | `/salesforecast/v1/15-minutes/getSalesForecast` | GET | Required: `locationCode`, `weekEndingDate` (`dd-MMM-yy`). Optional: `includeNull`. |
| Sales Forecast — hourly by page | `/salesforecast/v1/hourly/getSalesForecastByPage` | GET | Required: `startDate`, `endDate` (`dd-MMM-yy`). Optional: `locationCode`, `pageNumber`, `includeNull`. |
| Sales Forecast — save hourly | `saveHourlySalesForecast` | POST | Push manual override |
| Sales Mix — get all | `getAllCheckMenuMixRecordsV1` | GET | Check/recipe-item-level POS data |
| Sales Mix Service | `/allsalesmixrecordsv1` | GET | Daily POS data including: Sales (type 0), Sales Tax (type 1), Paid Outs (type 3), Non-Cash Media (type 5), Comps/Discounts (type 6), **Bank Deposits (type 7)**. Bank Deposits are unique — no GL required for `/save` (uses GL with Description="Cash"). |
| Time Clock Enhanced | `getAllTimeClockEnhancedRecordsV1` | GET / POST | GET for Labor-Summary-screen-adjusted records; POST to push from external payroll/POS |
| Supplemental Wage | `getAllSupplementalWageRecordsV1` | GET / POST | Tip sharing, vacation pay, sick pay, jury duty — lump sum or hourly |
| Budget Service | (Financial Operations) | GET / POST | Budget figures by GL across periods/locations, currency or percentage |
| General Ledger | (Financial Operations) | — | GL codes + P&L groupings |
| Currency Ratio | (Financial Operations) | — | Exchange rates |

**To use the Public API**, Bobby would need partner credentials issued by CrunchTime. The internal cookie path covers our daily dashboard needs without that.

**Sources / further reading:**
- [Crunchtime Developer Hub](https://developer.crunchtime.com/)
- [Using Our APIs](https://developer.crunchtime.com/docs/using-apis)
- [Employees, Locations, & Users](https://developer.crunchtime.com/docs/employee-location)
- [Point-of-Sale / Sales](https://developer.crunchtime.com/docs/point-of-sale)
- [Labor](https://developer.crunchtime.com/docs/labor)
- [Financial Operations](https://developer.crunchtime.com/docs/setup)
- [Sales Forecasting blog post](https://www.crunchtime.com/blog/new-sales-forecasting-api)

---

## Section 3 — Test-phase rebuild plan

`scraper/api_main.py` is **not yet built**. The current production scraper (`main.py`) keeps running daily. Plan when ready:

1. **Cookie cache + session-alive probe.** First operation each run:
   - load `data/ct_cookies.json`
   - `GET /resource/recommended-actions/status` — 200 → reuse, 401/403 → re-mint via Playwright login (single Playwright surface).
2. **Per-endpoint module** (`scraper/api/perf_metrics.py`, `api/labor_hours.py`, ...). Each module has a `validate(resp)` that asserts expected fields exist — fail loud at the scraper boundary, never propagate empty payloads to `wire_dashboard.py`. Pattern from Maverick (2026-05-03).
3. **Wire only after parity test.** Run `api_main.py` alongside `main.py` for ≥7 days. Diff their outputs. When stable, swap.
4. **Don't touch the workflow yet.** The 8:05 AM ET GitHub Actions run keeps using `main.py` until parity is proven.

---

## Section 4 — Re-running discovery

Whenever the CrunchTime UI gets a vendor update or we need to find a new screen's endpoints:

```powershell
# 1. Refresh menu inventory (pulls every menuitem label for the current user/role)
python scraper/api_enumerate_menu.py

# 2. Browse data/ct_menu_inventory.json for the screen name you want

# 3. Add it to TARGETS dict in api_discover_targeted.py and rerun
python scraper/api_discover_targeted.py

# 4. Update this doc with the new endpoint(s)
```

Cookie auth has no rate limit visible to us; keep runs under 1/min as courtesy.

---

## Section 1.6 — Purchasing Module (Partially Discovered — 2026-05-07)

The Purchasing menu exists in `ct_menu_inventory.json`: Purchasing Overview, Create Vendor Order, Recent Vendor Orders, Create Purchase by Invoice, Recent Purchase by Invoices, Vendor Returns, Vendor Information, Purchase Journal, Purchases by GL, Cost Analysis. None were captured in the initial 119-endpoint sweep.

| Method | Path | Notes |
|---|---|---|
| POST | `/resource/nc/purchasebyinvoice/summary` | Returns HTTP 200 but `{"rows":[],"total":0}` for all date-filter bodies tested. Needs Playwright navigation to the Purchasing screen first to establish page context. |
| POST | `/resource/nc/purchasebyinvoice/resources` | Returns config: `{"deliveryMinDate":"05/04/2026","deliveryMaxDate":"05/10/2026","invoiceMinDate":"05/07/2016","invoiceMaxDate":"05/07/2036","isPbiReconcileRequired":false,"glLinkToCategory":"S"}`. Confirms data exists back to 2016. |

**Status:** BLOCKED. Direct API POST returns empty. Fix path: add "PurchasingOverview", "RecentPurchaseByInvoices", "PurchaseJournal" to `api_discover_targeted.py` TARGETS dict, run discovery, capture the real POST body and date-range field names that fire with real data. Update this section when done.

---

## Section 5 — Known constraints / gotchas

- **DO NOT navigate to `/ncext/index.ct` (classic UI)** — logs out the modern.ct session. (Confirmed 2026-04-20.)
- **DO NOT touch the "Period" dropdown** — it's a Phil-Lexington convention. KY-2065 uses report-specific date filters. (Confirmed 2026-04-25.)
- The user must select KY-2065 (locationId=13969) post-login. The session-cookie scope is bound to that location.
- The internal API uses POST for many "read" operations because they take a body filter (e.g. date range, paging). It's a read in semantics even when it's a POST in HTTP.
- Cash Over/Short and Bank Deposit drilldowns **may not have a dedicated screen** in this CT instance — the dashboard's "Total Cash Over/Shorts" KPI plus per-register `registerSales/summary` is the highest-resolution data we've found in the internal API. Bank Deposits as a discrete object lives in the Public API's Sales Mix Service (type 7).
- Some menuitems in `ct_menu_inventory.json` have `hasHandler: false` because the click is wired through a controller listener, not a direct handler. The discovery script handles this by trying `c.click()` → `fireEvent('click')` → `el.dom.click()` in fallback order.
