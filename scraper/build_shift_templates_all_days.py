#!/usr/bin/env python3
"""
Build Teamworx Shift Builder templates for ALL 7 days Mon-Sun (KY-2065).

Supersedes build_shift_templates_wed_sun.py (which covers only Wed-Sun).
Mon/Tue grids were pulled from live browser via Chrome MCP window.template.shiftTemplateDataList
on 2026-05-11. Wed-Sun grids ported from build_shift_templates_wed_sun.py.

Target: 20% blended labor cost for the week.
Avg wage rate: $13/hr (Bobby's spec).

Position IDs (confirmed via Chrome MCP DOM read):
  positionId=1 : "2. Crew"
  positionId=2 : "General Manager-Salary"
  positionId=5 : "Shift Leader-Hourly"
  positionId=8 : "General Manager-Hourly"

Time slot format: 10-minute intervals, 108 slots total
  Slot 0  = 06:00 AM
  Slot 6  = 07:00 AM
  Slot 12 = 08:00 AM
  ...
  Slot 102 = 23:00 PM
  Slot 107 = 23:50 PM
  time_to_slot("HH:MM") -> (h*60 + m - 360) // 10

CLOSER RULE (Bobby's directive, 2026-05-11):
  Mon / Tue / Wed  →  3 closers staying until 11:00 PM (shifts end 23:00 or 23:15)
  Thu / Fri / Sat / Sun  →  4 closers staying until 11:00 PM

OPENER RULE (Bobby's directive, 2026-05-11):
  Tue / Wed / Thu / Fri  →  1 MGR/SL opens at 7:00 AM + 1 Crew at 8:00 AM
  Sat / Sun              →  2 Crew at 8:00 AM (managers per existing weekend pattern)
"""

from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from teamworx_api import load_session, BASE, HEADERS_JSON

ROOT = Path(__file__).resolve().parents[1]

LOCATION_ID   = 13969
LOCATION_NAME = "KY-2065-Dixie Highway"

# Position IDs (confirmed from DOM)
POS_CREW      = 1   # "2. Crew"
POS_GM_SALARY = 2   # "General Manager-Salary"
POS_SL_HOURLY = 5   # "Shift Leader-Hourly"
POS_GM_HOURLY = 8   # "General Manager-Hourly"

# Sales forecasts (from forecast_by_day.json, week of May 13-18, 2026)
DAILY_FORECAST = {
    "MON": 3591.0,
    "TUE": 3429.0,
    "WED": 3834.0,
    "THU": 4159.0,
    "FRI": 5372.0,
    "SAT": 5222.0,
    "SUN": 5330.0,
}

AVG_WAGE          = 13.0   # $/hr
TARGET_LABOR_PCT  = 0.20


# ─────────────────────────────────────────────────────────────────────────────
# TIME / SLOT HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def time_to_slot(hhmm: str) -> int:
    """Convert 'HH:MM' to slot index (0=06:00, 107=23:50)."""
    h, m = map(int, hhmm.split(":"))
    slot = (h * 60 + m - 360) // 10
    if slot < 0 or slot > 107:
        raise ValueError(f"Time {hhmm} out of range 06:00-23:50")
    return slot


def slot_to_time(idx: int) -> str:
    """Convert slot index to 'HH:MM'."""
    total_min = 360 + idx * 10
    h = total_min // 60
    m = total_min % 60
    return f"{h:02d}:{m:02d}"


def build_shift_row(position_id: int, seq: int, start: str, end: str) -> dict:
    """
    Build a shiftTemplateDataList entry using the exact structure captured via
    jQuery $.ajax intercept on a working Monday template save (2026-05-11).

    positionId must be a STRING.
    timeSlots is a DOUBLE-SERIALIZED JSON string of ACTIVE SLOTS ONLY.
    Each slot: {"startTime": "HH:MM", "status": "W", "endTime": "HH:MM", "index": N}
    where endTime = startTime + 10min, index = slot index (0=06:00).

    The 'end' parameter is the clock-out time; last active slot = 10 min before it.
    """
    start_slot = time_to_slot(start)
    end_h, end_m = map(int, end.split(":"))
    end_total       = end_h * 60 + end_m - 10   # last active slot = clockout - 10min
    end_last_active = (end_total - 360) // 10

    active_slots = []
    for i in range(start_slot, end_last_active + 1):
        slot_start = slot_to_time(i)
        total_m    = 360 + i * 10 + 10
        slot_end   = f"{total_m // 60:02d}:{total_m % 60:02d}"
        active_slots.append({
            "startTime": slot_start,
            "status":    "W",
            "endTime":   slot_end,
            "index":     i,
        })

    skills_list = [
        {"id": -1, "recordId": None, "name": "No Skill Defined"},
        {"id":  1, "recordId": None, "name": "1"},
        {"id":  2, "recordId": None, "name": "2"},
        {"id":  3, "recordId": None, "name": "3"},
        {"id":  4, "recordId": None, "name": "4"},
        {"id":  5, "recordId": None, "name": "5"},
    ]

    return {
        "positionId":      str(position_id),
        "sequenceNumber":  seq,
        "payRateMin":      None,
        "payRateMax":      None,
        "skills":          json.dumps(skills_list,   separators=(",", ":")),
        "timeSlots":       json.dumps(active_slots,  separators=(",", ":")),
    }


def shift_hours(start: str, end: str) -> float:
    """Scheduled hours for a shift (start to end clock-out)."""
    s_h, s_m = map(int, start.split(":"))
    e_h, e_m = map(int, end.split(":"))
    return (e_h * 60 + e_m - s_h * 60 - s_m) / 60.0


def calculate_stats(shifts: list[tuple]) -> dict:
    """Calculate raw hours, paid hours (0.5h break per shift >= 7h), labor $ and %."""
    raw_hours = sum(shift_hours(s, e) for _, s, e in shifts)
    breaks    = sum(0.5 for _, s, e in shifts if shift_hours(s, e) >= 7.0)
    paid      = raw_hours - breaks
    return {
        "raw_hours":  round(raw_hours, 2),
        "breaks":     breaks,
        "paid_hours": round(paid, 2),
    }


def count_closers(shifts: list[tuple]) -> int:
    """Count shifts ending at 23:00 or 23:15 (the standard closing window)."""
    return sum(1 for _, _, e in shifts if e in ("23:00", "23:15"))


# ─────────────────────────────────────────────────────────────────────────────
# SHIFT GRIDS
# ─────────────────────────────────────────────────────────────────────────────
#
# Closer rule:   Mon/Tue/Wed → 3 closers at 23:00-23:15
#                Thu/Fri/Sat/Sun → 4 closers at 23:00-23:15
#
# Mon/Tue grids: pulled from live Teamworx browser via window.template
#                on 2026-05-11 and represented here faithfully.
# Wed-Sun grids: ported from build_shift_templates_wed_sun.py (opener-rule pass).
# Wed only:      seq6 extended from 22:00 → 23:15 to reach 3 closers
#                (was 2 closers: SL-23:15 + crew-23:15; seq6 was ending 22:00).


# ── MONDAY — Truck day. Closer rule: 3 at 23:00. ────────────────────────────
# Pulled from live template (ID=29661) via Chrome MCP, 2026-05-11.
# Current closer count: 3 (seq7/seq8/seq9 all end 23:00). Compliant.
# Forecast: $3,591 → budget $718 → ~55h at 20%
MONDAY_SHIFTS = [
    # Shift Leader AM (7a opener)
    (POS_SL_HOURLY, "07:00", "15:00"),   # 8.00h — SL opener, handles truck
    # Shift Leader PM (3p closer)
    (POS_SL_HOURLY, "15:00", "23:00"),   # 8.00h — SL closer #1
    # TRUCK: crew 8a (strong back for put-away)
    (POS_CREW,      "08:00", "13:10"),   # 5.17h — truck AM crew 1
    # TRUCK: crew 8a (second body)
    (POS_CREW,      "08:00", "13:50"),   # 5.83h — truck AM crew 2
    # Mid crew (9:20a bridge into lunch)
    (POS_CREW,      "09:20", "15:00"),   # 5.67h — lunch bridge
    # Lunch surge (12p-4p)
    (POS_CREW,      "12:00", "16:00"),   # 4.00h — lunch peak
    # PM crew 1 (closer #2 at 23:00)
    (POS_CREW,      "16:00", "23:00"),   # 7.00h — closer
    # PM crew 2 (closer #3 at 23:00) — staggered start
    (POS_CREW,      "16:10", "23:00"),   # 6.83h — closer
    # Dinner peak add (6p closer)
    (POS_CREW,      "18:00", "23:00"),   # 5.00h — closer (3rd crew closer, all 3 at 23:00)
    # Mid-PM (3:20p — coverage bridge)
    (POS_CREW,      "15:20", "22:00"),   # 6.67h
    # Dinner short (6p-10p)
    (POS_CREW,      "18:00", "22:00"),   # 4.00h
]
# Mon closer count: seq2(SL 23:00), seq7(crew 23:00), seq8(crew 23:00), seq9(crew 23:00) = 4 at 23:00
# Wait — original had 3 closers at 23:00. Keep representation faithful:
# seq7=16:00-23:00, seq8=16:10-23:00, seq9=18:00-23:00 → 3 crew closers + seq2 SL = 4 total
# SL closer counts → total 4 closers. Rule says 3. Mon is ABOVE minimum → compliant.
#
# Mon raw: 8+8+5.17+5.83+5.67+4+7+6.83+5+6.67+4 = 66.17h
# Paid (>=7h): 8+8+7 = 3 shifts → -1.5h breaks
# Mon paid: 66.17 - 1.5 = 64.67h
# Mon labor $: 64.67*13 = $840.71. Labor%: 840.71/3591 = 23.4%
# (Mon is truck day — intentionally runs hot like Thu. $3,591 sales is the low day.)


# ── TUESDAY — Steady mid-week. Closer rule: 3 at 23:00. ─────────────────────
# Pulled from live template (ID=30994) via Chrome MCP, 2026-05-11.
# Current closer count: 4 (seq2/SL + seq9/seq10/seq12 all end 23:00). Above minimum → compliant.
# Forecast: $3,429 → budget $686 → ~53h at 20%
TUESDAY_SHIFTS = [
    # Shift Leader AM (7a opener per Tue opener rule)
    (POS_SL_HOURLY, "07:00", "15:00"),   # 8.00h — SL AM opener
    # Shift Leader PM (3p-11p closer #1)
    (POS_SL_HOURLY, "15:00", "23:00"),   # 8.00h — SL closer
    # Day Crew AM (8a opener per Tue opener rule — 1 crew at 8a)
    (POS_CREW,      "08:00", "16:00"),   # 8.00h — opener crew
    # Mid crew (9a-2p)
    (POS_CREW,      "09:00", "14:00"),   # 5.00h
    # Lunch crew 1 (11a-3p)
    (POS_CREW,      "11:00", "15:00"),   # 4.00h
    # Lunch crew 2 (11a-3p)
    (POS_CREW,      "11:00", "15:00"),   # 4.00h
    # Lunch bridge into PM (12p-5p)
    (POS_CREW,      "12:00", "17:00"),   # 5.00h
    # Early PM (4:30p-9p)
    (POS_CREW,      "16:30", "21:00"),   # 4.50h
    # PM crew 1 (5p-11p closer #2)
    (POS_CREW,      "17:00", "23:00"),   # 6.00h — closer
    # PM crew 2 (5:30p-11p closer #3)
    (POS_CREW,      "17:30", "23:00"),   # 5.50h — closer
    # Dinner peak (6p-10p)
    (POS_CREW,      "18:00", "22:00"),   # 4.00h
    # Late add (7p-11p closer #4)
    (POS_CREW,      "19:00", "23:00"),   # 4.00h — closer
]
# Tue closer count: seq2(SL 23:00), seq9(17:00-23:00), seq10(17:30-23:00), seq12(19:00-23:00) = 4 closers
# Above the 3-closer minimum → compliant, no changes.
#
# Tue raw: 8+8+8+5+4+4+5+4.5+6+5.5+4+4 = 66.0h
# Paid (>=7h): 8+8+8 = 3 shifts → -1.5h breaks
# Tue paid: 66.0 - 1.5 = 64.5h
# Tue labor $: 64.5*13 = $838.50. Labor%: 838.50/3429 = 24.5%
# (Tue runs hot on lower-sales day — template was set before closer rule; acceptable trade-off
#  if Bobby wants to preserve the existing crew structure. Flag in report.)


# ── WEDNESDAY — Leanest day. Closer rule: 3 at 23:15. ───────────────────────
# CHANGE from prior version: seq6 extended from 22:00 → 23:15 (+1.25h)
# to bring closer count from 2 → 3 (SL-23:15 + crew-23:15 + this closer).
# Forecast: $3,834 → budget $767 → ~59h at 20%
WEDNESDAY_SHIFTS = [
    # Shift Leader AM (Nathan or Kasey — Tue/Wed/Thu/Fri opener rule: 1 MGR at 7a)
    (POS_SL_HOURLY, "07:00", "15:00"),   # 8.00h — SL opener
    # Shift Leader PM (closer #1)
    (POS_SL_HOURLY, "15:00", "23:15"),   # 8.25h — SL closer
    # Day Crew AM (Lidy — opener rule: 1 crew at 8a)
    (POS_CREW,      "08:00", "16:00"),   # 8.00h
    # Day Crew mid (Francisco — shorter Wed)
    (POS_CREW,      "10:00", "16:00"),   # 6.00h — lunch bridge
    # Lunch surge (11a-4p)
    (POS_CREW,      "11:00", "16:00"),   # 5.00h — hits lunch peak
    # PM crew 1 (was 15:00-22:00 — EXTENDED to 23:15 to reach 3 closers; closer #2)
    (POS_CREW,      "15:00", "23:15"),   # 8.25h — closer (was 22:00)
    # PM crew 2 (dinner peak add)
    (POS_CREW,      "17:00", "22:00"),   # 5.00h
    # PM crew 3 (closer #3)
    (POS_CREW,      "17:30", "23:15"),   # 5.75h — closer
]
# Wed closer count: seq2(SL 23:15), seq6(crew 23:15), seq8(crew 23:15) = 3 closers. Compliant.
#
# Wed raw: 8+8.25+8+6+5+8.25+5+5.75 = 54.25h  (was 53.0h; +1.25h from seq6 extension)
# Paid (>=7h): 8+8.25+8+8.25 = 4 shifts → -2.0h breaks
# Wed paid: 54.25 - 2.0 = 52.25h
# Wed labor $: 52.25*13 = $679.25. Labor%: 679.25/3834 = 17.7%  (was 17.3%, still lean)


# ── THURSDAY — Truck day + highest shop day. Closer rule: 4 at 23:15. ───────
# Already has 5 closers (seq2/8/9/10/11 all end 23:15). Compliant.
# Forecast: $4,159 → budget $832 → ~64h at 20%
# Bobby override: runs intentionally hot (~22-23%) for shop/truck/boil-out coverage.
THURSDAY_SHIFTS = [
    # Shift Leader AM (Nathan opens — handles truck; Tue/Wed/Thu/Fri opener rule: 1 MGR at 7a)
    (POS_SL_HOURLY, "07:00", "15:00"),   # 8.00h — SL opener/truck supervisor
    # Shift Leader PM (Kasey — closer #1)
    (POS_SL_HOURLY, "15:00", "23:15"),   # 8.25h — SL closer
    # TRUCK: Early crew 8AM strong-back for put-away (opener rule: 1 crew at 8a)
    (POS_CREW,      "08:00", "14:00"),   # 6.00h — truck unload crew 1
    # TRUCK: Second truck body
    (POS_CREW,      "08:00", "15:00"),   # 7.00h — truck unload crew 2
    # Full day crew (Lidy or Kaisha)
    (POS_CREW,      "08:00", "16:00"),   # 8.00h
    # Lunch surge (11a-4p)
    (POS_CREW,      "11:00", "16:00"),   # 5.00h — lunch peak surge
    # EXTRA MID — Bobby's highest shop day override
    (POS_CREW,      "12:00", "20:00"),   # 8.00h — mid shift (extra coverage all day)
    # PM crew 1 (Maylin 3p anchor — closer #2)
    (POS_CREW,      "15:00", "23:15"),   # 8.25h — closer
    # PM crew 2 dinner peak (Ailen/Autumn — closer #3)
    (POS_CREW,      "17:00", "23:15"),   # 6.25h — closer
    # EXTRA CLOSER — boil-outs + shake machine (Bobby override: don't cut Thu night; closer #4)
    (POS_CREW,      "17:30", "23:15"),   # 5.75h — closer
    # Dinner peak #3 (closer #5)
    (POS_CREW,      "18:00", "23:15"),   # 5.25h — closer
]
# Thu closer count: seq2(SL), seq8, seq9, seq10, seq11 = 5 closers. Exceeds 4 → compliant.
#
# Thu raw: 8+8.25+6+7+8+5+8+8.25+6.25+5.75+5.25 = 75.75h
# Paid (>=7h): 8+8.25+7+8+8+8.25 = 6 shifts → -3.0h breaks
# Thu paid: 72.75h.  Labor $: $946.  Labor%: 22.7%  (Bobby override)


# ── FRIDAY — Next-highest shop day. Closer rule: 4 at 23:15. ────────────────
# Already has 5 closers. Compliant. Unchanged.
# Forecast: $5,372 → budget $1,074 → ~82h at 20%
FRIDAY_SHIFTS = [
    # Shift Leader AM (opener rule: 1 MGR at 7a)
    (POS_SL_HOURLY, "07:00", "15:00"),   # 8.00h — SL opener
    # Shift Leader PM (closer #1)
    (POS_SL_HOURLY, "15:00", "23:15"),   # 8.25h — SL closer
    # Day Crew AM (Lidy — opener rule: 1 crew at 8a)
    (POS_CREW,      "08:00", "16:00"),   # 8.00h
    # Day Crew mid (Kaisha/Francisco)
    (POS_CREW,      "08:00", "14:00"),   # 6.00h
    # Lunch bridge into dinner (10a-6p)
    (POS_CREW,      "10:00", "18:00"),   # 8.00h
    # MID SURGE — Bobby's Fri shop day override
    (POS_CREW,      "12:00", "20:00"),   # 8.00h — extra mid for shop coverage
    # PM crew 1 (Maylin 3p — closer #2)
    (POS_CREW,      "15:00", "23:15"),   # 8.25h — closer
    # PM crew 2 dinner peak (Ailen 5:30p — closer #3)
    (POS_CREW,      "17:30", "23:15"),   # 5.75h — closer
    # PM crew 3 (Autumn/Jada — closer #4)
    (POS_CREW,      "17:00", "23:15"),   # 6.25h — closer
    # Dinner peak add (6p surge — Fri peak is 7PM — closer #5)
    (POS_CREW,      "18:00", "23:15"),   # 5.25h — closer
]
# Fri closer count: seq2(SL), seq7, seq8, seq9, seq10 = 5 closers. Exceeds 4 → compliant.
#
# Fri raw: 8+8.25+8+6+8+8+8.25+5.75+6.25+5.25 = 71.75h
# Paid (>=7h): 8+8.25+8+8+8+8.25 = 6 shifts → -3.0h breaks
# Fri paid: 68.75h.  Labor $: $894.  Labor%: 16.6%


# ── SATURDAY — Busy weekend. Closer rule: 4 at 23:15. ───────────────────────
# Already has 4 closers. Compliant. Unchanged.
# Forecast: $5,222 → budget $1,044 → ~80h at 20%
# Opener rule for Sat: 2 CREW at 8:00 AM (not 1 MGR+1 crew).
SATURDAY_SHIFTS = [
    # Robert Cline (GM-Salary) opens Sat (not opener-rule constrained on Sat)
    (POS_GM_SALARY, "07:00", "17:00"),   # 10.00h — Bobby's Sat pattern
    # Shift Leader PM (Kasey 3p close — closer #1)
    (POS_SL_HOURLY, "15:00", "23:15"),   # 8.25h — SL closer
    # Day Crew AM 1 (Lidy — Sat opener rule: crew at 8:00 AM)
    (POS_CREW,      "08:00", "16:00"),   # 8.00h — Sat 8a opener #1
    # Day Crew AM 2 (Noel/Francisco — 2nd 8AM opener per Sat rule)
    (POS_CREW,      "08:00", "14:00"),   # 6.00h — Sat 8a opener #2
    # Lunch surge (10a-4p)
    (POS_CREW,      "10:00", "16:00"),   # 6.00h
    # MID shift 1 (Jeremiah noon — strong Sat mid)
    (POS_CREW,      "12:00", "20:00"),   # 8.00h — mid coverage
    # MID shift 2 (Jada Cox noon)
    (POS_CREW,      "12:00", "18:00"),   # 6.00h
    # PM crew 1 (3p-11p anchor — closer #2)
    (POS_CREW,      "15:00", "23:15"),   # 8.25h — closer
    # PM crew 2 dinner peak (Autumn 5:30p — closer #3)
    (POS_CREW,      "17:30", "23:15"),   # 5.75h — closer
    # Dinner peak add (closer #4)
    (POS_CREW,      "17:00", "23:15"),   # 6.25h — closer
]
# Sat closer count: seq2(SL), seq8, seq9, seq10 = 4 closers. Compliant.
#
# Sat raw: 10+8.25+8+6+6+8+6+8.25+5.75+6.25 = 72.5h
# Paid (>=7h): 10+8.25+8+8+8.25 = 5 shifts → -2.5h breaks
# Sat paid: 70.0h.  Labor $: $910.  Labor%: 17.4%


# ── SUNDAY — Busy, availability-constrained. Closer rule: 4 at 23:15. ───────
# Already has 4 closers. Compliant. Unchanged.
# Forecast: $5,330 → budget $1,066 → ~82h at 20%
SUNDAY_SHIFTS = [
    # Shift Leader AM (Nathan or Madison — Sun opener rule: 2 CREW at 8a, MGR separate)
    (POS_SL_HOURLY, "07:00", "15:00"),   # 8.00h — SL opener
    # Shift Leader PM (Kasey 3:30p close — closer #1)
    (POS_SL_HOURLY, "15:30", "23:15"),   # 7.75h — SL closer
    # Day Crew AM (Vicki 8a-2p short shift — Sun opener rule: 2 crew at 8a)
    (POS_CREW,      "08:00", "14:00"),   # 6.00h — Vicki limited
    # Day Crew mid (Noel — Sun primary)
    (POS_CREW,      "08:00", "16:00"),   # 8.00h — Noel AM anchor
    # Lunch crew (11a-5p)
    (POS_CREW,      "11:00", "17:00"),   # 6.00h — lunch surge
    # MID shift (Jeremiah/Brianna — mid-heavy Sun per Bobby override)
    (POS_CREW,      "12:00", "20:00"),   # 8.00h — mid coverage
    # PM crew 1 (Maylin 3p — closer #2)
    (POS_CREW,      "15:00", "23:15"),   # 8.25h — closer
    # PM crew 2 (Jada Cox 5p Sun — closer #3)
    (POS_CREW,      "17:00", "23:15"),   # 6.25h — closer
    # Dinner peak (Autumn 5:30p — closer #4)
    (POS_CREW,      "17:30", "23:15"),   # 5.75h — closer
]
# Sun closer count: seq2(SL), seq7, seq8, seq9 = 4 closers. Compliant.
#
# Sun raw: 8+7.75+6+8+6+8+8.25+6.25+5.75 = 64.0h
# Paid (>=7h): 8+7.75+8+8+8.25 = 5 shifts → -2.5h breaks
# Sun paid: 61.5h.  Labor $: $800.  Labor%: 15.0%


# ─────────────────────────────────────────────────────────────────────────────
# WEEKLY MATH SUMMARY (at $13/hr avg wage)
# ─────────────────────────────────────────────────────────────────────────────
# Day  | Forecast | Sched hrs | Paid hrs | Labor $  | Labor % | Closers | Rule
# Mon  | $3,591   | 66.17h    | 64.67h   | $841     | 23.4%   |  4      | >= 3  ✓
# Tue  | $3,429   | 66.00h    | 64.50h   | $839     | 24.5%   |  4      | >= 3  ✓
# Wed  | $3,834   | 54.25h    | 52.25h   | $679     | 17.7%   |  3      | >= 3  ✓  (fixed +1.25h)
# Thu  | $4,159   | 75.75h    | 72.75h   | $946     | 22.7%   |  5      | >= 4  ✓  (Bobby override hot)
# Fri  | $5,372   | 71.75h    | 68.75h   | $894     | 16.6%   |  5      | >= 4  ✓
# Sat  | $5,222   | 72.50h    | 70.00h   | $910     | 17.4%   |  4      | >= 4  ✓
# Sun  | $5,330   | 64.00h    | 61.50h   | $800     | 15.0%   |  4      | >= 4  ✓
# ─────────────────────────────────────────────────────────────────────────────
# TOTAL| $30,937  | 470.42h   | 454.42h  | $5,909   | 19.1%   |  ALL OK
#
# Mon/Tue run hot (23-25%) on low-sales days — they're truck days / light-traffic days
# with fixed crew minimums. Offset by Wed (17.7%), Fri (16.6%), Sun (15.0%).
# Thu hot is Bobby's intentional override (truck + shop + boil-out).
# Blended 7-day: 19.1% — under the 20% target.
# ─────────────────────────────────────────────────────────────────────────────


TEMPLATES = [
    ("DIXIE LABOR Monday",    MONDAY_SHIFTS),
    ("DIXIE LABOR Tuesday",   TUESDAY_SHIFTS),
    ("DIXIE LABOR Wednesday", WEDNESDAY_SHIFTS),
    ("DIXIE LABOR Thursday",  THURSDAY_SHIFTS),
    ("DIXIE LABOR Friday",    FRIDAY_SHIFTS),
    ("DIXIE LABOR Saturday",  SATURDAY_SHIFTS),
    ("DIXIE LABOR Sunday",    SUNDAY_SHIFTS),
]

# Template IDs for all 7 days (all confirmed via getSchedulingTemplatesData)
TEMPLATE_IDS = {
    "DIXIE LABOR Monday":    29661,
    "DIXIE LABOR Tuesday":   30994,
    "DIXIE LABOR Wednesday": 31034,
    "DIXIE LABOR Thursday":  31035,
    "DIXIE LABOR Friday":    31036,
    "DIXIE LABOR Saturday":  31054,
    "DIXIE LABOR Sunday":    31037,
}

DAY_CODE = {
    "DIXIE LABOR Monday":    "MON",
    "DIXIE LABOR Tuesday":   "TUE",
    "DIXIE LABOR Wednesday": "WED",
    "DIXIE LABOR Thursday":  "THU",
    "DIXIE LABOR Friday":    "FRI",
    "DIXIE LABOR Saturday":  "SAT",
    "DIXIE LABOR Sunday":    "SUN",
}

CLOSER_RULE = {
    "MON": 3, "TUE": 3, "WED": 3,
    "THU": 4, "FRI": 4, "SAT": 4, "SUN": 4,
}


# ─────────────────────────────────────────────────────────────────────────────
# PUSH
# ─────────────────────────────────────────────────────────────────────────────

def push_template(s, name: str, shifts: list[tuple], dry_run: bool = False) -> dict:
    """
    Build and POST a template via form-encoded body.

    Endpoint: POST /json/mn/templates/updateSchedulingTemplate
    Content-Type: application/x-www-form-urlencoded

    Body fields:
      template         — JSON string of template metadata object
      templateData     — JSON string of shiftTemplateDataList array
      existingTemplateId — string ID ("" = create new)
    """
    template_id = TEMPLATE_IDS.get(name)

    meta = {
        "id":                        template_id,
        "name":                      name,
        "createdBy":                 None,
        "createdDate":               None,
        "lastUpdatedBy":             None,
        "lastUpdatedDate":           None,
        "status":                    None,
        "statusId":                  1,
        "lastUpdatedById":           None,
        "createdById":               325819,
        "timeSlotValue":             10,
        "description":               None,
        "actionStatus":              None,
        "locationName":              LOCATION_NAME,
        "locationId":                LOCATION_ID,
        "hidePaidBreakViolations":   0,
        "hideUnPaidBreakViolations": 0,
        "translatedStatus":          None,
        "translatedActionStatus":    None,
    }

    shift_rows = [
        build_shift_row(pos_id, seq, start, end)
        for seq, (pos_id, start, end) in enumerate(shifts, start=1)
    ]

    stats   = calculate_stats(shifts)
    closers = count_closers(shifts)
    day     = DAY_CODE.get(name, "???")
    rule    = CLOSER_RULE.get(day, "?")

    if dry_run:
        print(f"  [DRY RUN] '{name}' | ID={template_id} | {len(shifts)} shifts | "
              f"{stats['raw_hours']}h raw / {stats['paid_hours']}h paid | "
              f"closers={closers} (rule>={rule})")
        return {"dryRun": True, "name": name, **stats, "closers": closers}

    form_data = {
        "template":          json.dumps(meta,       separators=(",", ":")),
        "templateData":      json.dumps(shift_rows, separators=(",", ":")),
        "existingTemplateId": str(template_id) if template_id else "",
    }
    headers = {k: v for k, v in s.headers.items() if k.lower() != "content-type"}
    r = s.post(
        f"{BASE}/json/mn/templates/updateSchedulingTemplate",
        data=form_data,
        headers=headers,
        timeout=30,
    )
    if r.status_code in (401, 403):
        raise RuntimeError(f"Auth error {r.status_code} — re-mint cookies via scrape_teamworx_roster.py")
    r.raise_for_status()
    try:
        result = r.json()
    except Exception:
        raise RuntimeError(f"Non-JSON response (status {r.status_code}): {r.text[:500]}")
    import os
    if os.environ.get("TWX_DEBUG"):
        print(f"  DEBUG response: {json.dumps(result, indent=2)[:2000]}")
    status = result.get("status") or ("success" if result.get("success") else "fail")
    if status != "success":
        msg = result.get("messageList") or result.get("message") or json.dumps(result)[:300]
        raise RuntimeError(f"API returned status={status}: {msg}")
    return result.get("result") or result.get("data") or {}


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Build Teamworx Shift Builder templates for all 7 days (Mon-Sun) at KY-2065"
    )
    parser.add_argument("--dry-run", action="store_true", help="Print plan without writing to Teamworx")
    parser.add_argument(
        "--day",
        choices=["MON","TUE","WED","THU","FRI","SAT","SUN"],
        help="Build only one day",
    )
    args = parser.parse_args()

    print("\n=== KY-2065 Shift Templates — All 7 Days ===")
    print(f"Target labor: 20% blended | Avg wage: ${AVG_WAGE}/hr | Dry run: {args.dry_run}")
    print()

    day_order = ["MON","TUE","WED","THU","FRI","SAT","SUN"]
    name_map  = {DAY_CODE[n]: n for n in DAY_CODE}
    shift_map = {DAY_CODE[n]: s for n, s in TEMPLATES}

    hdr = f"{'Day':<5} | {'Forecast':>10} | {'Budget@20%':>10} | {'Sched':>7} | {'Paid':>7} | {'Labor$':>8} | {'Labor%':>7} | {'Closers':>8} | {'Rule':>6} | {'OK?':>4}"
    print(hdr)
    print("-" * len(hdr))

    total_forecast = total_raw = total_paid = total_labor = 0.0
    all_ok = True

    for day in day_order:
        if args.day and args.day != day:
            continue
        name     = name_map[day]
        shifts   = shift_map[day]
        forecast = DAILY_FORECAST[day]
        budget   = forecast * TARGET_LABOR_PCT
        stats    = calculate_stats(shifts)
        labor_d  = stats["paid_hours"] * AVG_WAGE
        labor_p  = labor_d / forecast
        closers  = count_closers(shifts)
        rule_min = CLOSER_RULE[day]
        ok       = "YES" if closers >= rule_min else "NO "
        if closers < rule_min:
            all_ok = False
        print(f"{day:<5} | ${forecast:>9,.0f} | ${budget:>9,.0f} | {stats['raw_hours']:>6.2f}h | {stats['paid_hours']:>6.2f}h | ${labor_d:>7.2f} | {labor_p:>6.1%} | {closers:>5}/{rule_min} | {'HOT' if labor_p > 0.20 else 'ok':>6} | {ok}")
        total_forecast += forecast
        total_raw      += stats["raw_hours"]
        total_paid     += stats["paid_hours"]
        total_labor    += labor_d

    print("-" * len(hdr))
    total_pct = total_labor / total_forecast if total_forecast else 0
    print(f"{'TOTAL':<5} | ${total_forecast:>9,.0f} | ${total_forecast*0.20:>9,.0f} | {total_raw:>6.2f}h | {total_paid:>6.2f}h | ${total_labor:>7.2f} | {total_pct:>6.1%} | {'ALL OK' if all_ok else 'REVIEW'}")
    print()

    if not all_ok:
        print("WARNING: One or more days below closer minimum — review before pushing.")
        return

    if not args.dry_run:
        s = load_session()
        print("Session loaded. Pushing templates to Teamworx...\n")

    for name, shifts in TEMPLATES:
        day = DAY_CODE[name]
        if args.day and args.day != day:
            continue
        print(f"Building: {name}")
        stats   = calculate_stats(shifts)
        closers = count_closers(shifts)
        print(f"  Shifts: {len(shifts)} | Raw: {stats['raw_hours']}h | Paid: {stats['paid_hours']}h | Closers: {closers}")
        try:
            if args.dry_run:
                push_template(None, name, shifts, dry_run=True)
            else:
                result = push_template(s, name, shifts, dry_run=False)
                print(f"  OK — pushed to Teamworx (ID={TEMPLATE_IDS[name]})")
        except Exception as e:
            print(f"  ERROR: {e}")
        print()

    print("=== Complete ===")


if __name__ == "__main__":
    main()
