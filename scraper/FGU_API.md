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

### ⚠️ Token is SHORT-LIVED (~30 min) — refresh needed for pure-requests
The Bearer JWT expired mid-discovery-session (`401 {"code":"401003001","message":"Expired token"}`). The Angular app silently refreshes it from `localStorage['refresh_token']` on activity. Implication for `scrape_fgu.py`: a token captured from Chrome is only good for ~30 min. For a repeatable pull, either (a) capture fresh at run time from a live Chrome tab, or (b) implement the refresh-token exchange (Schoox `/api/v2/auth/refresh`-style — not yet captured). Today's pull runs inside the capture window.

## Discovery backlog (not yet mapped)
- **Team-wide per-learner due dates in ONE call.** Today you must loop `/team-dashboard/learners/<id>/compliance/courses` per learner (34 calls) to get each person's due-date-tracked courses. Fine for a nightly job. A bulk endpoint may exist — look for it if the per-learner loop is too slow.
- **NOTE on this store's data:** most KY-2065 crew have **0 compliance (due-date-tracked) courses** — their training is "complete when able," not deadline-enforced. The reliable per-person signal is `coursesCompletionRate`; hard due dates are sparse. Anchor the brief's "overdue in 7 days" flag on **hire_date + onboarding window** (from new-hire detection) rather than assuming Schoox due dates exist for everyone.
- The refresh-token exchange (for true lights-out). Assign/enroll a course (WRITE) — not attempted; needs Bobby's go.

## Gotchas
- Cookie auth is NOT enough — always the Bearer token.
- `limit` param is ignored (server caps at 20) — page through with `page=N` + `.more`.
- `trainingFilters[]` is a repeated query param, URL-encoded as `trainingFilters%5B%5D=`. The `orgStructure,1291469,orgUnit` triple is what scopes to store 2065.
- SPA is Angular; the page renders after the API calls resolve — capture network, don't scrape DOM.
