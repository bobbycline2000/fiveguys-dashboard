# Design: ComplianceMate Individual Checklist Display

**Date:** 2026-04-20  
**Status:** Approved  
**Scope:** Fix scraper to pull individual checklist percentages; update dashboard display

---

## Problem

The ComplianceMate scraper currently captures only the location-level aggregate score (e.g., "58%"). The 22 individual checklists are hidden behind an accordion row that must be clicked to expand. The dashboard shows no per-checklist breakdown.

---

## Goal

Show ~19 individual checklist completion percentages on the dashboard as color-coded progress bars, grouped by category.

---

## Checklists Included / Excluded

**Excluded** (opening and closing):
- Pre Open
- Closing Checklist
- Closing

**Included** (~19 lists):
- Time & Temp: 11AM, 1PM, 3PM, 5PM, 7PM, 9PM
- Shift Checks: AM Pre-Shift Check, PM Pre-Shift Check, Shift Change, MMCCA
- Milkshake: Milkshake Pump Cleaning Check, Tuesday Milkshake Cleaning Check, Friday Milkshake Cleaning Check
- Inspections: Weekly Store Inspection, Delivery Check, Temperature Sample, Calibration Test, Operational Spot Check, Battery Swap Checklist

---

## Part 1: Scraper Fix (`scraper/scrape_compliancemate.py`)

### What changes
After the List Completion report loads, the scraper must expand the location accordion row to reveal individual checklist rows.

### Steps
1. Load the report page and apply filters (already working)
2. Wait for `#accordion .card` to appear (already working)
3. **New:** Find and click the `2065 - Louisville, KY` accordion card to expand it
4. **New:** Wait for the expanded sub-rows to appear (individual checklist rows)
5. **New:** Extract each row: checklist name + completion percentage
6. Filter out excluded checklists (Pre Open, Closing Checklist, Closing)
7. Save to `data/compliancemate.json`

### Output format (updated)
```json
{
  "meta": { "date": "2026-04-20", "location": "2065", "status": "ok" },
  "overall_pct": 58,
  "lists": [
    { "name": "11AM: Time and Temp", "pct": 100 },
    { "name": "AM Pre-Shift Check", "pct": 40 },
    { "name": "Milkshake Pump Cleaning Check", "pct": 100 }
  ]
}
```

### Fallback behavior
If accordion expansion fails (no data for that day, site structure changed), fall back to current behavior: save only the overall percentage. Dashboard handles this gracefully by showing the overall % with a note that detail is unavailable.

---

## Part 2: Dashboard Display

### Layout
A new or updated ComplianceMate section in the dashboard with:
- **Header:** "Checklist Compliance" + date + overall % (top-right, large)
- **4 groups** separated by labeled dividers:
  1. ⏱ Time & Temp (6 items, 2-column grid)
  2. 👔 Shift Checks (4 items, 2-column grid)
  3. 🥛 Milkshake (3 items, 2-column grid)
  4. 📋 Inspections (6 items, 2-column grid)
- **Color legend** at the bottom

### Color coding
| Color | Threshold | Meaning |
|-------|-----------|---------|
| Green `#6fcf6f` | ≥ 80% | Good |
| Yellow `#f5a623` | 50–79% | Needs attention |
| Red `#e05555` | < 50% | Action required |
| Gray `#444` | N/A | Not scheduled today |

### N/A handling
Checklists with no data for the day (e.g., Tuesday Milkshake Cleaning on a Monday) display as "N/A" with a gray bar.

### Data source
Dashboard reads from `data/compliancemate.json`. If `lists` is empty or missing, show only the overall % with a message: "Detail unavailable — scraper could not expand checklist data."

---

## Files Changed

| File | Change |
|------|--------|
| `scraper/scrape_compliancemate.py` | Add accordion click + per-checklist extraction |
| `scraper/main.py` | Update HTML generation template for ComplianceMate section (progress bars) |
| `data/compliancemate.json` | Schema updated to include `overall_pct` + `lists` array |

---

## Out of Scope

- Trend over time (week-over-week compliance scores)
- Alerts or notifications when a checklist is red
- Food cost section (separate future task)
- ComplianceMate login credential changes
