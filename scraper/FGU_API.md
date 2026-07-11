# Five Guys University (Schoox) — Reverse-Engineered API

**FGU is Schoox.** Base app: `https://app.schoox.com/academy/fiveguys/...`
Discovered 2026-07-05 via Chrome MCP network capture while Bobby was logged in.

## Account facts
- **academyId: `1177`** (the `fiveguys` academy)
- **Bobby's userId: `1143201372`** — has `team` + `academy-admin` + `training-admin` workspaces (manager access).
- **Store 2065 org unit: `orgUnit id 1291469`, name `KY2065`** — this is the filter that scopes every team query to Bobby's store. Confirmed via `/org-structure/default-selections`.
- Team size seen: **34 learners**, 75.2% completion rate, 50% overdue rate (as of discovery).

## Auth — Bearer JWT in localStorage (NOT cookies)
- The API is `https://app.schoox.com/api/v2/...`, JSON, but **cookie auth alone returns `401 Unauthenticated`**.
- Real auth: `Authorization: Bearer <token>` where the token is `localStorage.getItem('token')` on any logged-in Schoox tab. A companion `localStorage['refresh_token']` also exists.
- The token is a session JWT — **capture it fresh from Bobby's logged-in Chrome tab** (same pattern as the Outlook MSAL grab / Indeed session grab). Do NOT read the raw value into agent context (secret hygiene) — use it in-page (`fetch` with the header set inside a `javascript_tool` eval) or write it to a session file for a pure-`requests` replay.
- Token lifetime unknown; assume session-scoped. If a call returns 401, re-capture.
- Send `Accept: application/json`.

## Endpoints (all GET, academyId=1177)

### Roster + per-employee completion — THE main pull
`GET /api/v2/academies/1177/team-dashboard/learners?trainingFilterSet=teamDashboardLearners&trainingFilters[]=orgStructure,1291469,orgUnit&trainingFilters[]=sorting,alphabetically,asc`
- Paginated **20/page**. `page=N` for more; response `.more` (bool) says if another page exists. (34 learners = page1:20 + page2:14.) `&limit=100` is accepted but the server still caps at 20 — page through instead.
- Response: `{ page, limit, more, _links:{self,next}, _embedded:{ learners:[...] } }`
- Each learner: `{ id, name, surname, profileUrl, photo, totalCourses, coursesCompletionRate (0-100), coursesComplianceRate, totalLearningPaths, totalEvents, totalSkills, totalGoals, totalPerformanceReviews }`
- **`coursesCompletionRate` is the number Bobby cares about per person.** `name`+`surname` join to the employee directory via first name → `data/employee_name_map.json`.

### Aggregate stats for the store
`GET /api/v2/academies/1177/team-dashboard/learners/statistics?refresh=0&trainingFilterSet=teamDashboardLearners&trainingFilters[]=orgStructure,1291469,orgUnit&trainingFilters[]=sorting,alphabetically,asc`
- Returns: `{ totalLearners, coursesComplianceRate, coursesCompletionRate, coursesOverdueRate, calculatedAt, cached }`. Cheap one-call KPI for a dashboard Training card.

### Org structure (find the store's orgUnit id)
`GET /api/v2/academies/1177/org-structure/default-selections?featureId=teams-dashboard`
- `{ jobs, units:[{id,name}], aboves, types }` → `units[0] = {id:1291469, name:"KY2065"}`.

### Course catalog + overall course stats (per-course view, all learners)
- `GET /api/v2/academies/1177/team-dashboard/training/courses?trainingFilterSet=teamDashboardTrainingCourses&fields=id,title,estimatedTime,public,status,creationDate&embed=image,steps&size=10&trainingFilters[]=categoryType,academy&trainingFilters[]=status,active&trainingFilters[]=sorting,alphabetically,asc`
- `GET /api/v2/academies/1177/team-dashboard/training/courses/overall-statistics?...` (same filters) — aggregate completion per course.

### Individual profile
`GET /api/v2/academies/1177/user/<userId>/profile?embed=languages,customFields,workExperience,education,orgStructureAndJobs,academyScore,credits,awardBadges,...`
- Full learner profile. (Note: `/user/` singular here, vs `/users/` plural elsewhere.)

### Logged-in user context
- `GET /api/v2/auth/me?fields=...&embed=permissions,...`
- `GET /api/v2/academies?domain=fiveguys&...` → academy metadata + `academyId`.

### Per-learner drill-down (manager view) — the menu + detail endpoints
Clicking a learner in the Team Dashboard opens `/team-dashboard/learners/<userId>/summary`. Endpoints seen:
- `GET /team-dashboard/learners/<userId>/menu` → tabs: **Summary, Training, Compliance, Development**.
- `GET /team-dashboard/learners/<userId>/summary/{training-insights,compliance-insights,type-completions,completion-graph,training-insights}` → text-summary widgets (e.g. `{name,tooltip,data:[{text:"0% completion rate of all training"}]}`).
- `GET /team-dashboard/learners/<userId>/compliance/courses?trainingFilterSet=teamDashboardLearnerComplianceCourses&fields=id,title,status&embed=courseUser,courseExtraInfo,steps&size=20&trainingFilters[]=sorting,alphabetically,asc` → **the compliance (due-date-tracked) courses for that learner.** `embed=courseUser` carries the enrollment progress; `courseExtraInfo` carries due-date info. Returns `_embedded.courses[]`. ⚠️ Do NOT add `embed=progress,dueDate,enrollment` — that combo returns 500. Use `embed=courseUser,courseExtraInfo`.
- **`getFullInfo` (classic PHP):** `GET /academies/panel/organize/actions.php?page=getFullInfo&academyId=1177&userId=<userId>&featureId=teams-dashboard` → `data.sections[]` incl. `external_ids:["CTE2065348215"]` — **the CrunchTime employee ID (`CTE<store><n>`), a clean join key to CrunchTime/directory** — and the assigned job (`"2. Crew"`).

### Due-date signals (self / logged-in user) — `/training/items`
The home dashboard's due-date widgets (these are for the LOGGED-IN user, not team members):
- Upcoming due: `GET /training/items?trainingFilterSet=myTrainingUpcomingDueOverview&embed=dueDate,progress,enrollment&trainingFilters[]=sorting,dueDate,asc` → items sorted by soonest due date. **This is the "will be overdue soon" preventive signal.**
- Past due: `...myTrainingPastDueOverview...` → already overdue.
- Per-objective progress: `GET /training/progress-per-objective/{onboarding,compliance_training,career_path,job_strength}` → onboarding-specific completion.

### ⚠️ Token is SHORT-LIVED (~30 min) — refresh flow (discovered 2026-07-05, WIRED into the daily pipeline 2026-07-11)
The Bearer JWT expires (`401 {"code":"401003001","message":"Expired token"}`). The Angular app refreshes it from `localStorage['refresh_token']`. The refresh endpoint:
- **`POST /api/v2/auth/token/refresh`** — JSON body **`{"token": "<refresh_token>"}`** (⚠️ the field is literally named `token`, but it holds the REFRESH token, not the access token). Cookie-auth, no other headers required.
- Response `200`: `{tokenType, accessToken, refreshToken, expiresIn}` — a fresh `accessToken` AND a **rotated `refreshToken`** (old one is consumed). `expiresIn` is the access-token lifetime in seconds.
- Wrong field name → `422 {validationErrors:{token:["The token field is required."]}}`.
- **Dead-token response is `401` with no validationErrors** — confirmed 2026-07-11 when testing the 2026-07-05-captured refresh token (6 days old): straight `401 Unauthorized`, no rotation possible. Refresh tokens are single-use/short-lived — do not assume a captured one is still good after any real gap; test before building on it.

**Implication:** a captured refresh token → indefinite fresh access tokens IF you persist the rotated refreshToken each call (self-heal, like the SCG Gmail token). **Intended use is the READ-ONLY completion pull only** (dashboard + brief). This is NOT to be used to log into or act as other people's accounts — that's account takeover + falsified training records; declined 2026-07-05.

**WIRED 2026-07-11:** `scraper/fgu_refresh_token.py` implements the exchange — reads `FGU_REFRESH_TOKEN` env (a GitHub Secret in the daily workflow), writes `data/fgu_session.json` for `scrape_fgu.py`, and stages the rotated refresh token at `secrets/fgu_refresh_token.txt` (gitignored) for the workflow's self-heal step (`gh secret set FGU_REFRESH_TOKEN < secrets/fgu_refresh_token.txt`). **The secret has never been seeded** — until a human captures a fresh refresh_token from a logged-in Chrome tab and runs `gh secret set FGU_REFRESH_TOKEN`, this whole daily block is a no-op (workflow sets `FGU_SKIP=1` and skips gracefully). Do NOT seed a persistent stored master credential any other way — this is the one sanctioned exchange path.

## Roster reconciliation — `scraper/reconcile_fgu_roster.py` (NEW 2026-07-11)
Bobby's "FGU accounts are not current" complaint decomposes into two mismatch classes, both computed by this script from `data/fgu_training.json` + `scripts/build_employee_directory.py` (EMPLOYEES = active crew phone directory) + `data/employee_name_map.json`:
- **`fgu_not_in_directory`** — a Schoox learner whose name doesn't match any active directory entry (by full-name-via-name-map, then first-name fallback, then a hardcoded nickname list). Candidate "termed but still in Schoox" — but this is a REVIEW list, not confirmed: the phone directory is built incrementally and can lag reality or simply omit people (it excludes management — `Robert Cline`/Bobby is hardcoded excluded via `KNOWN_MANAGEMENT_EXCLUDE`).
- **`directory_missing_from_fgu`** — an active directory entry with no matching Schoox learner (`reason: no_account`) or matched but stuck at 0% (`reason: zero_percent`). This is the more actionable list — these are confirmed-active people whose training either was never set up or never opened.
- Matching gotcha discovered 2026-07-11: many directory entries are BARE FIRST NAMES not yet in `employee_name_map.json` (e.g. "Angela", "Megan", "Rusul", "Serina" — no map entry, but Schoox has "Angela Ashby" etc.). A full-name-only match wrongly reports these as `no_account`. Fix: first-name fallback match against the FGU learner's separate `name` field (not just `full_name`) BEFORE giving up.
- Also discovered: `Kenzie` (directory) is almost certainly `Mykenize Milledge` (FGU) — a nickname gap in `employee_name_map.json`, not a real roster mismatch. Tracked in `SUSPECTED_NICKNAME_PAIRS` in the script pending Bobby's confirmation + a proper map entry.
- Output: `data/fgu_reconciliation.json`.

## Alert routing — `scraper/fgu_alerts.py` (NEW 2026-07-11)
Appends (not overwrites) into `data/team_notes.json` under 3 fixed `from` tags (`FGU Overdue Rate`, `FGU New Hire Onboarding`, `FGU Roster Check`), replacing only its own tags on each run so it coexists with other scripts writing to the same file (e.g. `steritech_alert_check.py`). Fires on: overdue rate rising vs. `data/fgu_overdue_history.json`'s last entry; a new hire (`data/employee_hire_dates.json`) within 7 days of / past their 30-day onboarding deadline at <100%; and any roster mismatch from `reconcile_fgu_roster.py`'s output. The dashboard Training card also shows the same reconciliation counts directly (see `dashboard-watchdog`/wire_dashboard.py FGU section) — belt and suspenders.

## Discovery backlog (not yet mapped)
- **Team-wide per-learner due dates in ONE call.** Today you must loop `/team-dashboard/learners/<id>/compliance/courses` per learner (34 calls) to get each person's due-date-tracked courses. Fine for a nightly job. A bulk endpoint may exist — look for it if the per-learner loop is too slow.
- **NOTE on this store's data:** most KY-2065 crew have **0 compliance (due-date-tracked) courses** — their training is "complete when able," not deadline-enforced. The reliable per-person signal is `coursesCompletionRate`; hard due dates are sparse. Anchor the brief's "overdue in 7 days" flag on **hire_date + onboarding window** (from new-hire detection) rather than assuming Schoox due dates exist for everyone.
- Assign/enroll a course (WRITE) — not attempted; needs Bobby's go.
- **Seed `FGU_REFRESH_TOKEN`** — the #1 next action; see refresh-flow section above.

## Gotchas
- Cookie auth is NOT enough — always the Bearer token.
- `limit` param is ignored (server caps at 20) — page through with `page=N` + `.more`.
- `trainingFilters[]` is a repeated query param, URL-encoded as `trainingFilters%5B%5D=`. The `orgStructure,1291469,orgUnit` triple is what scopes to store 2065.
- SPA is Angular; the page renders after the API calls resolve — capture network, don't scrape DOM.
