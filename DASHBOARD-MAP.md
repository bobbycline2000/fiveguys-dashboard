# Dashboard Section Map — Source of Truth

**Updated:** 2026-04-27
**Goal:** Every visible card on `dashboard.html` has a documented data path, a CI step that populates it, and a failure mode. If a card isn't wired, it's listed as RED and either gets wired or removed — no half-built cards on a customer-facing dashboard.

**Reliability target:** every card must update on every 8:05 AM ET CI run, or surface a debug-log entry by 8:10 AM ET.

---

## Status Legend
- 🟢 **LIVE** — wired end-to-end, populates every day, verified working
- 🟡 **WIRED-UNTESTED** — code exists, hasn't run in CI yet (first proof tomorrow)
- 🟠 **PARTIAL** — wires today, fails on weekends/edge cases, or depends on manual upload
- 🔴 **HARDCODED** — fake data shipped as if real. Either wire it or strip it.
- ⛔ **BLOCKED** — needs Bobby (access, sample file, decision)

---

## Section-by-Section

### 1. The Controllables — Food Cost (line 691)
| Element | Source | Wiring File | Status |
|---|---|---|---|
| Big % (31.2%) | CrunchTime → Inventory → Reports → Profit and Loss | `scraper/scrape_cogs.py` (sidebar nav) → `wire_dashboard.py:320` | 🟡 untested — first CI run tomorrow |
| Goal flag (Over/On/Under) | Computed from Big % vs 27.5% | `wire_dashboard.py:323` | 🟡 |
| Top 3 Variance Items | CrunchTime API `/dashboard/top/actual/vs/theoretical` | `scrape_cogs.py` API call → `wire_dashboard.py:361` | 🟡 |
| Week / Month / Last Mo variance | Same P&L report, three date ranges | `scrape_cogs.py` 3× `_extract_cogs_pct` → `wire_dashboard.py:340` | 🟡 |
| Date range label (e.g. "04/13–04/19") | `cogs.meta.week_start/end` | `wire_dashboard.py:381` | 🟡 |

**Failure modes:** sidebar selector changes; CrunchTime auth fails; report date inputs not found.
**Action if fails:** logs a debug-log entry; next session sees it auto.

---

### 2. The Controllables — Labor (line 740)
| Element | Source | Wiring | Status |
|---|---|---|---|
| Big % (21.1%) | Par Brink Sales Summary PDF (`labor_percent`) | `parbrink_parse_sales_summary.py` → `wire_dashboard.py:251` | 🟢 |
| Labor $ Today | Par Brink Sales Summary | `wire_dashboard.py` | 🟢 |
| Actual Hrs / Sched Hrs | Par Brink Sales Summary | `wire_dashboard.py` | 🟢 |
| Avg Hrly Wage | computed (cost / hours) | `wire_dashboard.py` | 🟢 |
| Goal flag | computed vs 18.5% | `wire_dashboard.py` | 🟢 |

**Failure modes:** Par Brink email doesn't arrive; PDF format change.
**Verified working:** today's run shows $1,066, 78.5 actual hrs.

---

### 3. KPI Row (line 798)
| Element | Source | Wiring | Status |
|---|---|---|---|
| Daily Sales ($5,065) | Par Brink Sales Summary `net_sales` | `wire_dashboard.py:393` | 🟢 |
| Transactions (204) | Par Brink Sales Summary `order_count` | `wire_dashboard.py:663` | 🟢 (was hardcoded "312" before 4/26) |
| Sales / Guest ($24.83) | Par Brink Sales Summary `order_average` | `wire_dashboard.py` | 🟢 |
| Compliance (100%) | ComplianceMate scraped | `scrape_compliancemate.py` → `wire_dashboard.py` | 🟢 |
| Today/Week/Month/Quarter swap | `data-swap` attrs from `period_rollups.json` + `compliance_rollups.json` | `aggregate_compliance.py`, `period_rollups.py` | 🟢 |

**Failure modes:** Par Brink not arrived → Daily/Sales-per-Guest stale; ComplianceMate site change → Compliance stale.

---

### 4. ComplianceMate Required Checklists (line 837)
| Element | Source | Wiring | Status |
|---|---|---|---|
| Required-only checklist list | ComplianceMate Playwright scrape | `scrape_compliancemate.py` → `wire_dashboard.py:589` | 🟢 |
| Day-aware filtering (Milkshake on Tue/Fri) | Day-of-week logic in scraper | `scrape_compliancemate.py` | 🟢 |

**Failure modes:** ComplianceMate site UI change; Playwright DOM drift.

---

### 5. Secret Shop card (line 869) — ⛔ BLOCKED
| Element | Source | Wiring | Status |
|---|---|---|---|
| Rolling avg | Marketforce email reports | none | 🔴 hardcoded |
| Last shop scores | Marketforce 100% shop email PDF | none | 🔴 hardcoded |

**Blocker:** needs Outlook access + sample 100% shop email PDF from Bobby.
**Action:** until unblocked, this card displays fake data. Strip it from production view OR mark visibly as "preview" until live.

---

### 6. Steritech card (line 908) — 🔴 HARDCODED
| Element | Source | Wiring | Status |
|---|---|---|---|
| Last audit score | unknown — no portal scrape | none | 🔴 hardcoded "100 / 0 / 0" |

**Decision needed from Bobby:** manual entry (you type latest score after each audit) OR portal scrape (where do Steritech audit results live? Is there a portal?).
**Action:** until decided, strip or mark as "manual."

---

### 7. Team Notes card (line 958) — 🔴 HARDCODED
| Element | Source | Wiring | Status |
|---|---|---|---|
| Notes body | none | none | 🔴 lorem-ipsum content |

**Decision needed from Bobby:** keep (and where do messages come from?) OR drop the card entirely.

---

### 8. Today's Schedule (line 1011)
| Element | Source | Wiring | Status |
|---|---|---|---|
| AM/PM shift roster | Par Brink Weekly Labor Schedule PDF | `parbrink_parse_weekly_schedule.py` → `wire_dashboard.py:475` | 🟠 |
| Today-aware day extraction | new 4/27 — extracts all 7 days, picks today | `parbrink_parse_weekly_schedule.py` | 🟠 |

**Failure mode:** depends on Bobby manually exporting `weekly_schedule.pdf` to email each Monday. If he forgets, schedule shows last week's. **Reliability gap.**
**Fix needed:** either automate the Par Brink schedule report (configure another scheduled email), OR add a stale-detector that flags when schedule is >7 days old.

---

### 9. Hourly Labor % (line 1121)
| Element | Source | Wiring | Status |
|---|---|---|---|
| Hourly bars + alerts | Par Brink Hourly Sales And Labor PDF | `parbrink_parse_hourly_sales_labor.py` | 🟢 |

**Failure mode:** Par Brink email missing → stale hourly chart.

---

### 10. Discounts & Comps (line 687 in wire_dashboard, card location TBD)
| Element | Source | Wiring | Status |
|---|---|---|---|
| Discount line items | Par Brink Discount Summary PDF | `parbrink_parse_discounts.py` | 🟢 |

---

### 11. Header / Footer
| Element | Source | Wiring | Status |
|---|---|---|---|
| Date chip ("Sunday, April 26") | computed | `wire_dashboard.py:236` | 🟢 |
| "Updated daily" timestamp | computed at run time | `wire_dashboard.py:733` | 🟢 |
| Greeting | computed from time | `wire_dashboard.py` | 🟢 |

---

## Summary Counts

| Status | Count | Cards |
|---|---|---|
| 🟢 LIVE | 7 | Labor, Daily Sales, Transactions, Sales/Guest, Compliance KPI, ComplianceMate detail, Hourly Labor, Discounts, Header/Footer |
| 🟡 WIRED-UNTESTED | 1 | Food Cost (full card — proves out tomorrow) |
| 🟠 PARTIAL | 1 | Today's Schedule (manual weekly PDF dependency) |
| 🔴 HARDCODED | 3 | Secret Shop, Steritech, Team Notes |
| ⛔ BLOCKED | 1 | Secret Shop (overlap with hardcoded) |

---

## Reliability Rules (proposed)

1. **No hardcoded "live-looking" KPIs.** Every card either pulls live data or carries a visible "manual" / "preview" tag. Bobby's customer-facing dashboard cannot have lorem-ipsum hidden as data.
2. **Every CI step is a hard gate.** No `continue-on-error: true` on data scrapers. If `scrape_X.py` fails, CI fails loudly; debug-log catches it; next session fixes it.
3. **Stale-detector on every card.** `verify_dashboard.py` already checks date chip + sales freshness. Extend it to: schedule (≤7 days old), compliance (today's date), food cost (week_end ≤ 7 days ago).
4. **Map this file every time a card changes.** When a card is wired, hardcoded, or stripped, update DASHBOARD-MAP.md in the same commit. Drift kills credibility.
5. **Tomorrow's CI run = live test.** Every Tuesday, audit the 8:05 AM run output against this map. Any 🟡 that didn't go 🟢 gets debugged before any new feature work.

---

## Open Decisions for Bobby

1. **Secret Shop:** unblock with Outlook access + sample PDF, OR strip the card?
2. **Steritech:** manual entry workflow OR is there a portal we can scrape?
3. **Team Notes:** keep (with what source?) OR drop?
4. **Weekly Schedule PDF export:** automate via another Par Brink scheduled email, OR keep manual with a stale-warning?
