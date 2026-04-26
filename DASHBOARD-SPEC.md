# Five Guys Dashboard — Master Spec

> **Last verified:** 2026-04-26 13:56 ET (Bobby asked for the complete map — every section × every time period, what feeds it, current status, what's needed to close gaps.)

This is the source-of-truth doc for what the dashboard is and what makes each piece work. If you ever want to know "is X working?" — find the row, read the status, read the closer.

---

## Architecture (one paragraph)

The live page is a single static HTML file at `dashboard.html`, hosted free on GitHub Pages at `https://bobbycline2000.github.io/fiveguys-dashboard/dashboard.html`. A daily GitHub Actions cron (`.github/workflows/daily_dashboard.yml`, fires 8:05 AM ET, sometimes runs late due to GHA cron flakiness) does this in order: (1) pulls overnight Par Brink emails from Bobby's Gmail, (2) parses each PDF to JSON in `data/raw/parbrink/2065/<date>/`, (3) runs `scraper/wire_dashboard.py` to inject the JSON into `dashboard.html`'s `data-swap` attributes, (4) runs `scraper/verify_dashboard.py` to confirm the date chip + key values updated, (5) commits the new `dashboard.html` to `main`, GitHub Pages auto-redeploys. CrunchTime stays in the picture for food cost / variance only (weekly, not daily). ComplianceMate is scraped via Playwright on the same daily run. Secret shops come from Marketforce email reports (not yet wired).

---

## Section-by-section status

Status legend: 🟢 = working today · 🟡 = partial / hardcoded / placeholder · 🔴 = broken or empty · ⏳ = waiting on data source decision

### Sidebar / Navigation
| Item | Today | Status | What it needs |
|---|---|---|---|
| Overview (the main page) | the only built page | 🟢 | — |
| Employee List | downloads `employee_directory.xlsx` | 🔴 file doesn't exist yet | **Bobby:** give me the roster (name, role, phone, hire date if you have it). I'll drop it in as `.xlsx` and the link works immediately. Static file, doesn't refresh. |
| Locations | empty button | 🔴 not built | Decision: 1-store summary card (when you go DM)? 11-store roll-up? Defer until DM role is real. |
| Settings | empty button | 🔴 not built | Probably never needed unless we add per-user prefs. Can hide. |

### Topbar
| Item | Today | Status | What it needs |
|---|---|---|---|
| Date chip | "Saturday, April 25 2026" | 🟢 | Auto-set from `data/latest.json.report_date` by the wire step. |
| Period toggle (Today / Week / Month / Quarter) | client-side JS swaps `data-today` / `data-week` / `data-month` / `data-quarter` attributes on every cell tagged `data-swap` | 🟡 Today + Week populated, Month + Quarter show `—` placeholder | **Gap 3.** Need monthly + quarterly aggregator. Sources: Par Brink "Sales By Day" (weekly batch) for last 4 weeks → roll into Month. CrunchTime weekly P&L for Quarter. Build `scraper/aggregate_periods.py` that writes `data/period_rollups.json`, wire into `wire_dashboard.py`. |
| Refresh button | cosmetic, no behavior | 🟡 | Decision: hook to a manual workflow_dispatch button or remove. |
| "Updated daily" pill | static text | 🟢 | — |

### The Controllables — Food Cost
| Field | Today | Status | What it needs |
|---|---|---|---|
| Big % (e.g. 31.2%) | hardcoded | 🟡 | CrunchTime "Consolidated Actual Theoretical Costs" report. Weekly only. Need a CrunchTime export step (not Par Brink — wrong tool). |
| Goal % (27.5%) | hardcoded | 🟢 (it's a constant) | Confirm 27.5% is the right corporate goal. |
| Top 3 Variance Items + dollars | hardcoded "Ground Beef +$110, Hot Dog +$84, Bun Burger +$47" | 🟡 | Same CrunchTime weekly report. Top-N from variance column. |
| Period boxes (Week / Month / QTD %) | hardcoded | 🟡 | Same source, rolled across last 1 / 4 / 13 weeks. |

### The Controllables — Labor
| Field | Today | Status | What it needs |
|---|---|---|---|
| Big Labor % | wired from Par Brink Hourly Sales And Labor totals (e.g. 19.4%) | 🟢 (parser shipped 4/26, awaiting Mon 8:05 AM CI proof) | — |
| Goal (18.5%) | hardcoded constant | 🟢 (corrected this week from 17.5 → 18.5) | — |
| Labor $ Today | wired from Par Brink Hourly totals (e.g. $1,073) | 🟢 | — |
| Actual Hrs | wired from Par Brink Hourly totals (e.g. 102.6) | 🟢 | — |
| Sched Hrs | wired from Par Brink Weekly Labor Schedule | 🟡 only when sched JSON exists; otherwise "—" | Build `parbrink_parse_weekly_schedule.py` (item #5 in queue). |
| Avg Hrly Wage | computed labor_$ / labor_hrs (e.g. $10.46) | 🟢 | — |
| WTD %, WTD Labor $, WTD Hours | hardcoded | 🟡 | Par Brink "Sales And Labor Summary By Location" (weekly batch, lands ~2:30 AM Tue). Already on the report list — just need parser + wire. |
| Labor % by Hour bars (11A–10P) | wired from Par Brink Hourly per-hour rows | 🟢 (parser shipped 4/26, awaiting Mon 8:05 AM CI proof) | — |

### Secondary KPIs row (the 4 cards under Controllables)
| Card | Today | Week | Month | Quarter | Source | Status |
|---|---|---|---|---|---|---|
| Daily Sales ($5,541) | 🟢 wired from Par Brink | 🟢 wired | 🟡 `—` | 🟡 `—` | Par Brink Sales Summary (daily) + Sales By Day (weekly batch) | Today/Week working. Month/Quarter is Gap 3. |
| Transactions (207) | 🟢 wired (from `parbrink_parse_sales_summary.py`, parser added 4/26 — first CI proof Mon 4/27) | 🟡 `—` | 🟡 `—` | 🟡 `—` | Same as Daily Sales | Today: parser shipped, awaiting Mon 8:05 AM CI. Week+: Gap 3. |
| Sales / Guest ($5.46) | 🟢 wired | 🟢 wired | 🟡 `—` | 🟡 `—` | Computed from Sales Summary (Net / Guests) | Same as Daily Sales. |
| Compliance (100%, 9/9) | 🟢 wired from ComplianceMate scraper | 🟡 today only | 🟡 today only | 🟡 today only | ComplianceMate Playwright scrape (`scraper/compliancemate_scrape.py`) | Filter to required-only checklists working. Week+/Month+/Quarter+ rolling avg not built. |

### ComplianceMate detail card
| Item | Today | Status | What it needs |
|---|---|---|---|
| List of required checklists w/ pass % | 🟢 9 items, daily refresh, only required-only filter applied | 🟢 (closed Gap 2 on 4/26) | — |
| Overall pill (On Track / Behind) | 🟢 | 🟢 | — |
| Period view (W/M/Q rollups of pass %) | not built | 🔴 | Decision: store ComplianceMate snapshot daily into `data/raw/compliancemate/<date>.json`, then a rollup script computes 7/30/90-day averages. ~1 day of work. |

### Right column — Secret Shop / Steritech / Team Notes
| Card | Today | Status | What it needs |
|---|---|---|---|
| **Secret Shop** | hardcoded score, last visit date | 🔴 | Marketforce shop reports email → Bobby's Outlook (not Gmail). Per memory: names email comes ONLY for 100% shops (payout trigger). Need: pull score + date from each Marketforce report PDF. Build `marketforce_parse_shop.py` + Outlook pickup. Per spec: dashboard needs KPIs + W/M/Q averages. |
| **Steritech** | hardcoded "100 / 0 / 0" (score / critical / non-critical) | 🟡 (per the 4/23 simplify pass — set as last-known-good) | Steritech runs ~quarterly. Decision: leave hardcoded with a "last visit YYYY-MM-DD" caption Bobby updates manually after each visit, OR scrape from Steritech portal if he has access. |
| **Team Notes** | placeholder text | 🔴 | Decision: do you want this card at all? It's a manual freeform field. If yes, edit `data/team_notes.md` and wire into the card. If no, drop the card. |

### Today's Schedule
| Field | Today | Status | What it needs |
|---|---|---|---|
| Roster of names + shift times for today | hardcoded sample | 🔴 | Par Brink "Weekly Labor Schedule" PDF (in the weekly batch, lands Tue ~2:30 AM). Parser pulls today's row from the weekly schedule. Build `parbrink_parse_weekly_schedule.py`. |

### Hourly Labor %
| Field | Today | Status | What it needs |
|---|---|---|---|
| Bar chart 11A–10P showing labor % each hour | hardcoded sample bars | 🔴 | Par Brink "Hourly Sales And Labor By Section" PDF. Same parser as Labor "Labor % by Hour bars" above — one parser feeds both. |

### Discounts & Comps
| Field | Today | Status | What it needs |
|---|---|---|---|
| Table of comp/discount line items + counts + $ | 🟢 wired from Par Brink Discount Summary | 🟢 (closed Gap 1 on 4/26 — `parbrink_parse_discounts.py` shipped, awaiting Mon 8:05 AM CI proof) | Today: working pending CI. Week+/Month+: Par Brink "Discount Summary" is also in the weekly batch — wire the rolled-up version for Week tab. |

---

## What you (Bobby) need to provide me

To close the gaps that aren't blocked on building parsers:

1. **Employee roster** — name, role, phone, optional hire date. Send as a list in chat or drop a CSV/xlsx. **Closes:** Employee List sidebar link.
2. **Confirm Food Cost goal is 27.5%** (or correct it). **Closes:** the goal display in Food Cost card.
3. **Steritech approach** — manual update after each visit, or do you want me to look at scraping their portal? **Closes:** Steritech card.
4. **Team Notes** — keep it (manual updates) or drop the card? **Closes:** that card.
5. **Locations page** — defer until you take the DM role, or build now as a static "all 11 stores" list? **Closes:** Locations sidebar.
6. **Marketforce login + sample shop email** — for me to see the actual report shape and build the parser. **Closes:** Secret Shop card.
7. **CrunchTime food-cost report export decision** — do you want to add a CrunchTime daily export step to the GHA pipeline, or pull weekly only via a separate Monday job? **Closes:** Food Cost card (the real numbers).

---

## Build queue (priority order)

If you give me a green light, I'd build in this order — biggest visible impact first, smallest dependency-on-Bobby first:

1. **Verify Mon 4/27 CI run** — Sales Summary + Discount Summary parsers prove out end-to-end. (No build needed, just check.)
2. **Par Brink Hourly Sales And Labor parser** — closes the Labor "today" row + drives the hourly bar chart. (~1 session.)
3. **Par Brink Sales By Day weekly parser + aggregator** — closes Month tab for Sales / Transactions / Sales-per-Guest. (~1 session.)
4. **Par Brink Sales And Labor Summary By Location weekly parser** — closes the WTD labor stats. (~½ session.)
5. **Par Brink Weekly Labor Schedule parser** — closes Today's Schedule card. (~1 session.)
6. **CrunchTime food-cost export step** — closes Food Cost card. (~1–2 sessions, harder because CrunchTime is a Playwright scrape.)
7. **Marketforce Secret Shop pickup + parser** — closes Secret Shop card + KPI rollups. (~1–2 sessions; depends on you giving me access + a sample email.)
8. **Quarter aggregator** — closes Quarter tab. (~½ session, depends on having Month working first.)
9. **ComplianceMate rolling rollups** — Week/Month/Quarter for compliance %. (~½ session.)

---

## How I should be reporting status to you

Going forward: at the end of every dashboard work session, I update **this file's section-by-section table**. If a 🟡 becomes 🟢, I flip it here. If a 🔴 stays 🔴 because we hit a blocker, I write the blocker into the row's "What it needs" column. That way you have one place to look — not a handoff narrative — to know where the dashboard actually is.

This file is the contract. If a section is 🟢 here, it should work. If you see something in the live dashboard that doesn't match a 🟢 in here, I owe you a fix.
