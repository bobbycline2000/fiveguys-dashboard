#!/usr/bin/env python3
"""
Build Teamworx Shift Builder templates for Wed-Sun (KY-2065).

Target: 20% labor cost for the week of May 13-18, 2026
Sales forecasts from forecast_by_day.json:
  Wed 5/13: $3,834
  Thu 5/14: $4,159
  Fri 5/15: $5,372
  Sat 5/16: $5,222
  Sun 5/17: $5,330
Total Wed-Sun: $23,917

Avg wage rate: $13/hr (Bobby's spec)
Bobby's overrides:
  - Thursday: +1 extra mid shift (highest shop day), +1 early 8AM for truck, strong closers (boil-out)
  - Friday: strong mid coverage (shop day #2)
  - Saturday/Sunday: mid-heavy weekend coverage
  - Wednesday: leanest day to offset Thursday's extra

Position IDs (confirmed via Chrome MCP DOM read):
  positionId=1 : "2. Crew"
  positionId=2 : "General Manager-Salary"
  positionId=5 : "Shift Leader-Hourly"
  positionId=8 : "General Manager-Hourly"

Time slot format: 10-minute intervals, 108 slots total
  Slot 0  = 06:00 AM
  Slot 6  = 07:00 AM
  Slot 12 = 08:00 AM
  Slot 18 = 09:00 AM
  Slot 24 = 10:00 AM
  Slot 30 = 11:00 AM
  Slot 36 = 12:00 PM
  Slot 42 = 01:00 PM
  Slot 48 = 02:00 PM
  Slot 54 = 03:00 PM
  Slot 60 = 04:00 PM
  Slot 66 = 05:00 PM
  Slot 72 = 06:00 PM
  Slot 78 = 07:00 PM
  Slot 84 = 08:00 PM
  Slot 90 = 09:00 PM (was 11PM in my earlier count -- correcting below)

Wait -- Monday template:
  First shift: posId=5 (SL), start=07:00, end=14:50, activeSlots=48 -> 48*10=480min=8hrs ✓
  slot[0]=06:00, so 07:00=slot[6]
  14:50 = 06:00 + 8h50m = 06:00 + 53 slots = slot[53]
  So active = slots[6..53] (48 slots) ✓

  Second shift: posId=5 (SL), start=15:00, end=22:50, activeSlots=48
  15:00 = 06:00 + 9h = 54 slots from start = slot[54]
  22:50 = 06:00 + 16h50m = 101 slots = slot[101]
  slots[54..101] = 48 ✓

  Total range: slot[0]=06:00, slot[107]=06:00+17h50m=23:50 -> 108 slots ✓
  So operating window is 06:00 AM to 11:50 PM (108 slots of 10 min each)

SLOT MAPPING (verified):
  time_to_slot("HH:MM") -> (hours*60 + minutes - 360) // 10
    e.g., "07:00" -> (7*60+0 - 360) // 10 = (420-360)/10 = 6 ✓
    e.g., "15:00" -> (900-360)/10 = 54 ✓
    e.g., "22:50" -> (22*60+50-360)/10 = (1370-360)/10 = 101 ✓
"""

from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from teamworx_api import load_session, BASE, HEADERS_JSON

ROOT = Path(__file__).resolve().parents[1]

LOCATION_ID = 13969
LOCATION_NAME = "KY-2065-Dixie Highway"

# Position IDs (confirmed from DOM)
POS_CREW = 1           # "2. Crew"
POS_GM_SALARY = 2      # "General Manager-Salary"
POS_SL_HOURLY = 5      # "Shift Leader-Hourly"
POS_GM_HOURLY = 8      # "General Manager-Hourly"

# Sales forecasts (from forecast_by_day.json, May 13-17 week)
DAILY_FORECAST = {
    "WED": 3834.0,
    "THU": 4159.0,
    "FRI": 5372.0,
    "SAT": 5222.0,
    "SUN": 5330.0,
}

AVG_WAGE = 13.0        # $/hr
TARGET_LABOR_PCT = 0.20


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


def build_time_slot_list(start_hhmm: str, end_hhmm: str) -> list[dict]:
    """
    Build the 108-slot timeSlotList for a shift.
    start_hhmm: shift start time (inclusive)
    end_hhmm: shift end time (exclusive -- the last slot before this time is the final 'W')

    Actually based on Monday template analysis:
    Start=07:00, End(last active)=14:50, activeSlots=48
    14:50 is included as a W slot (the shift runs THROUGH the 14:50 slot, i.e., works until 15:00)
    So the range is [start_slot, end_slot] INCLUSIVE where end_slot = end_time - 10min

    Usage: build_time_slot_list("07:00", "15:00") -> slots 6..53 active (48 slots)
    The 'end_hhmm' is the clock-out time; last active slot is 10 min before it.
    """
    start_slot = time_to_slot(start_hhmm)
    # end_hhmm is clock-out; last active slot = slot for (end_time - 10min)
    end_h, end_m = map(int, end_hhmm.split(":"))
    end_total = end_h * 60 + end_m - 10  # subtract 10 min
    end_last_active = (end_total - 360) // 10

    slots = []
    for i in range(108):
        t = slot_to_time(i)
        if start_slot <= i <= end_last_active:
            slots.append({"startTime": t, "status": "W"})
        else:
            slots.append({"startTime": t, "status": None})
    return slots


def build_shift_row(position_id: int, seq: int, start: str, end: str) -> dict:
    """
    Build a shiftTemplateDataList entry using the exact structure captured via
    jQuery $.ajax intercept on a working Monday template save (2026-05-11).

    Key findings from intercept:
      - positionId must be a STRING (e.g., "1"), not an int
      - skills is a DOUBLE-SERIALIZED JSON string with skill names
      - timeSlots is a DOUBLE-SERIALIZED JSON string of ACTIVE SLOTS ONLY
        Each slot: {"startTime": "HH:MM", "status": "W", "endTime": "HH:MM", "index": N}
        where endTime = startTime + 10min, index = slot index (0=06:00)
      - timeSlotList is NOT sent — it's a read-only server-computed field
      - skillLevelList is NOT sent — read-only
      - Only 6 keys: positionId, sequenceNumber, payRateMin, payRateMax, skills, timeSlots
    """
    # Build active-slots-only list (double-serialized)
    start_slot = time_to_slot(start)
    end_h, end_m = map(int, end.split(":"))
    end_total = end_h * 60 + end_m - 10  # last active slot = clockout - 10min
    end_last_active = (end_total - 360) // 10

    active_slots = []
    for i in range(start_slot, end_last_active + 1):
        slot_start = slot_to_time(i)
        # endTime = startTime + 10 min
        total_m = 360 + i * 10 + 10
        slot_end = f"{total_m // 60:02d}:{total_m % 60:02d}"
        active_slots.append({
            "startTime": slot_start,
            "status": "W",
            "endTime": slot_end,
            "index": i,
        })

    # Skills string — exact format from Monday template intercept
    skills_list = [
        {"id": -1, "recordId": None, "name": "No Skill Defined"},
        {"id": 1,  "recordId": None, "name": "1"},
        {"id": 2,  "recordId": None, "name": "2"},
        {"id": 3,  "recordId": None, "name": "3"},
        {"id": 4,  "recordId": None, "name": "4"},
        {"id": 5,  "recordId": None, "name": "5"},
    ]

    return {
        "positionId": str(position_id),           # must be string
        "sequenceNumber": seq,
        "payRateMin": None,
        "payRateMax": None,
        "skills": json.dumps(skills_list, separators=(",", ":")),     # double-serialized
        "timeSlots": json.dumps(active_slots, separators=(",", ":")), # double-serialized, active only
    }


def shift_hours(start: str, end: str) -> float:
    """Calculate raw hours for a shift (start to end)."""
    s_h, s_m = map(int, start.split(":"))
    e_h, e_m = map(int, end.split(":"))
    return (e_h * 60 + e_m - s_h * 60 - s_m) / 60.0


def build_template_body(name: str, shifts: list[tuple[int, str, str]]) -> dict:
    """
    Build the POST body for updateSchedulingTemplate.
    shifts: list of (positionId, start_hhmm, end_hhmm)
    """
    shift_rows = []
    total_hours = 0.0
    for seq, (pos_id, start, end) in enumerate(shifts, start=1):
        shift_rows.append(build_shift_row(pos_id, seq, start, end))
        total_hours += shift_hours(start, end)

    return {
        "id": None,   # null = create new
        "name": name,
        "createdBy": None,
        "createdDate": None,
        "lastUpdatedBy": None,
        "lastUpdatedDate": None,
        "status": None,
        "statusId": 1,  # Active
        "lastUpdatedById": None,
        "createdById": 325819,  # Bobby Cline's user ID
        "timeSlotValue": 10,
        "description": None,
        "actionStatus": None,
        "locationName": LOCATION_NAME,
        "locationId": LOCATION_ID,
        "hidePaidBreakViolations": 0,
        "hideUnPaidBreakViolations": 0,
        "shiftTemplateDataList": shift_rows,
        "translatedStatus": None,
        "translatedActionStatus": None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# SHIFT GRIDS PER DAY
# ─────────────────────────────────────────────────────────────────────────────
#
# Labor math summary (20% target, $13/hr avg):
#
# Wed $3,834 → budget $767 → 59.0h allowed → target ~57-59h scheduled
# Thu $4,159 → budget $832 → 64.0h allowed → Bobby override: +1 mid + early truck
#              With extra: targeting ~70-72h (Thu is shop priority, accept ~17-18%)
# Fri $5,372 → budget $1,074 → 82.6h allowed → 78-80h (strong mid for shop day)
# Sat $5,222 → budget $1,044 → 80.3h allowed → 76-78h (weekend mid-heavy)
# Sun $5,330 → budget $1,066 → 82.0h allowed → 72-74h (Sun runs leaner — no Lidy/Kaisha)
#
# Week total (Wed-Sun) forecast: $23,917
# Budget at 20%: $4,783 → 368h allowed
# Target scheduled: ~357-362h (allow break hours to bring effective labor % slightly under)
#
# Thursday runs hot intentionally (Bobby's override: extra mid + truck early + strong close).
# Wednesday runs lean to offset Thursday.
# The blended 5-day should land at or near 20%.
#
# SHIFT STRUCTURE PER BOBBY'S RULES:
# - Shift Leader (posId=5): 2 per day minimum (AM 7-3, PM 3-11 pattern)
# - OPENER RULE (confirmed 2026-05-11):
#     Tue/Wed/Thu/Fri: 1 MANAGER opens at 7:00 AM, 1 CREW comes in at 8:00 AM, then trickle
#     Sat/Sun: 2 CREW at 8:00 AM (managers handled per existing weekend pattern)
# - Crew (posId=1): staggered starts to hit peaks (lunch 11a-1p, dinner 5p-7p)
# - Max 2 crew before 11am on regular days, 3+ on truck days (Mon/Thu)
# - Truck day opener + strong-back at 8AM for truck put-away
# - Minimum 4-hour shifts
# - Operating hours: 6AM open prep to 11PM close (11:15PM end of closing shifts)
#

# WEDNESDAY — Leanest day. Maylin OFF. Target ~57h scheduled.
# Forecast: $3,834 → budget $767 → 59h
# Crew pattern: Lidy + Francisco AM, mid crew, PM crew
WEDNESDAY_SHIFTS = [
    # Shift Leader AM (Nathan or Kasey)
    (POS_SL_HOURLY, "07:00", "15:00"),   # 8h SL opener
    # Shift Leader PM (Kasey)
    (POS_SL_HOURLY, "15:00", "23:15"),   # 8.25h SL closer
    # Day Crew AM (Lidy)
    (POS_CREW,      "08:00", "16:00"),   # 8h
    # Day Crew mid (Francisco - shorter Wed)
    (POS_CREW,      "10:00", "16:00"),   # 6h lunch bridge
    # Lunch surge add (11a-3p)
    (POS_CREW,      "11:00", "16:00"),   # 5h - hits lunch peak
    # PM crew 1 (Jeremiah/Richard - late start)
    (POS_CREW,      "15:00", "22:00"),   # 7h
    # PM crew 2 (Autumn/Ailen)
    (POS_CREW,      "17:00", "22:00"),   # 5h dinner peak
    # PM crew 3 closer
    (POS_CREW,      "17:30", "23:15"),   # 5.75h dinner+close
]
# Wed total raw: 8+8.25+8+6+5+7+5+5.75 = 53.0h scheduled
# Paid (7+ hr shifts get 0.5h break each): shifts >=7h: 8+8.25+8+7 = 4 shifts -> -2h breaks
# Wed paid: 53.0 - 2.0 = 51.0h paid
# Wed labor $: 51.0 * 13 = $663. Labor%: 663/3834 = 17.3% (lean — offset for Thu)


# THURSDAY — Truck Day + Highest Shop Day.
# Bobby override: +1 extra mid, +1 early 8AM for truck, strong closers (boil-out + shake machine)
# Forecast: $4,159 → budget $832 → 64h at 20%
# Intentionally running ~72h scheduled (Bobby priority override)
THURSDAY_SHIFTS = [
    # Shift Leader AM (Nathan opens - handles truck)
    (POS_SL_HOURLY, "07:00", "15:00"),   # 8h SL opener/truck supervisor
    # Shift Leader PM (Kasey)
    (POS_SL_HOURLY, "15:00", "23:15"),   # 8.25h SL closer (stays for boil-out)
    # TRUCK: Early crew 8AM strong-back for put-away
    (POS_CREW,      "08:00", "14:00"),   # 6h truck unload crew
    # TRUCK: Second truck body
    (POS_CREW,      "08:00", "15:00"),   # 7h (standard Thu truck day crew)
    # Lunch surge 1 (Lidy or Kaisha)
    (POS_CREW,      "08:00", "16:00"),   # 8h full day crew
    # Lunch surge 2 (11a-4p)
    (POS_CREW,      "11:00", "16:00"),   # 5h lunch peak surge
    # EXTRA MID — Bobby's highest shop day override
    (POS_CREW,      "12:00", "20:00"),   # 8h mid shift (extra coverage all day)
    # PM crew 1 (Maylin 3p anchor)
    (POS_CREW,      "15:00", "23:15"),   # 8.25h
    # PM crew 2 dinner peak (Ailen/Autumn)
    (POS_CREW,      "17:00", "23:15"),   # 6.25h
    # EXTRA CLOSER for boil-outs + shake machine (Bobby override: don't cut Thu night)
    (POS_CREW,      "17:30", "23:15"),   # 5.75h
    # Dinner peak #3
    (POS_CREW,      "18:00", "23:15"),   # 5.25h
]
# Thu total raw: 8+8.25+6+7+8+5+8+8.25+6.25+5.75+5.25 = 75.75h
# Paid (7+ hr shifts): 8+8.25+7+8+8+8.25 = 6 shifts >=7h -> -3.0h breaks
# Thu paid: 75.75 - 3.0 = 72.75h paid
# Thu labor $: 72.75 * 13 = $945.75. Labor%: 945.75/4159 = 22.7%
# (Intentionally hot — Bobby's shop-day + truck-day priority override)


# FRIDAY — Next-highest shop day. Strong mid coverage.
# Forecast: $5,372 → budget $1,074 → 82.6h at 20%
# Target ~78h scheduled (strong mid, PM-heavy Fri pattern from schedule-prep)
FRIDAY_SHIFTS = [
    # Shift Leader AM (Madison or Nathan)
    (POS_SL_HOURLY, "07:00", "15:00"),   # 8h SL opener
    # Shift Leader PM (Kasey)
    (POS_SL_HOURLY, "15:00", "23:15"),   # 8.25h SL closer
    # Day Crew AM (Lidy)
    (POS_CREW,      "08:00", "16:00"),   # 8h
    # Day Crew mid (Kaisha/Francisco)
    (POS_CREW,      "08:00", "14:00"),   # 6h
    # Lunch bridge crew (10a-4p)
    (POS_CREW,      "10:00", "18:00"),   # 8h (Fri pattern: lunch into dinner)
    # MID SURGE — Bobby's Fri shop day override (strong mid)
    (POS_CREW,      "12:00", "20:00"),   # 8h extra mid for shop coverage
    # PM crew 1 (Maylin 3p)
    (POS_CREW,      "15:00", "23:15"),   # 8.25h
    # PM crew 2 dinner peak (Ailen 5:30p)
    (POS_CREW,      "17:30", "23:15"),   # 5.75h
    # PM crew 3 (Autumn/Jada)
    (POS_CREW,      "17:00", "23:15"),   # 6.25h
    # Dinner peak add (6p surge — Fri peak is 7PM per schedule-prep)
    (POS_CREW,      "18:00", "23:15"),   # 5.25h
]
# Fri total raw: 8+8.25+8+6+8+8+8.25+5.75+6.25+5.25 = 71.75h
# Paid (7+ hr shifts): 8+8.25+8+8+8+8.25 = 6 shifts -> -3.0h breaks
# Fri paid: 71.75 - 3.0 = 68.75h paid
# Fri labor $: 68.75 * 13 = $893.75. Labor%: 893.75/5372 = 16.6%
# (Under budget — Fri sales are high, makes the weekly math work)


# SATURDAY — Busy weekend + frequent shop day. Mid-heavy.
# Forecast: $5,222 → budget $1,044 → 80.3h at 20%
# Target ~76h scheduled. Robert Cline works floor Sat.
SATURDAY_SHIFTS = [
    # Robert Cline (GM-Salary) opens Saturday (manager handled per existing weekend pattern)
    (POS_GM_SALARY, "07:00", "17:00"),   # 10h (Bobby's Sat pattern)
    # Shift Leader PM (Kasey 3p close)
    (POS_SL_HOURLY, "15:00", "23:15"),   # 8.25h SL closer
    # OPENER RULE: 2 crew at 8:00 AM Saturday
    # Day Crew AM 1 (Lidy) — moved to 08:00 per opener rule (was 07:30)
    (POS_CREW,      "08:00", "16:00"),   # 8h (Sat: Lidy opener)
    # Day Crew AM 2 (Noel/Francisco) — 2nd 8AM opener per rule
    (POS_CREW,      "08:00", "14:00"),   # 6h
    # Lunch surge (10a-4p)
    (POS_CREW,      "10:00", "16:00"),   # 6h
    # MID shift 1 (Jeremiah noon start — strong Sat mid per Bobby)
    (POS_CREW,      "12:00", "20:00"),   # 8h MID coverage
    # MID shift 2 (Jada Cox noon — Sat pattern from schedule-prep)
    (POS_CREW,      "12:00", "18:00"),   # 6h
    # PM crew 1 (3p-11p anchor — no Maylin Sat)
    (POS_CREW,      "15:00", "23:15"),   # 8.25h
    # PM crew 2 dinner peak (Autumn 5:30p)
    (POS_CREW,      "17:30", "23:15"),   # 5.75h
    # Dinner peak add
    (POS_CREW,      "17:00", "23:15"),   # 6.25h
]
# Sat total raw: 10+8.25+8+6+6+8+6+8.25+5.75+6.25 = 72.5h
# (Lidy shift was 07:30-15:30=8h, now 08:00-16:00=8h — same raw hours, opener time changed)
# Paid (7+ hr shifts): 10+8.25+8+8+8.25 = 5 shifts -> -2.5h breaks
# Sat paid: 72.5 - 2.5 = 70.0h paid
# Sat labor $: 70.0 * 13 = $910. Labor%: 910/5222 = 17.4%


# SUNDAY — Busy but leanest crew availability (no Lidy/Kaisha).
# Forecast: $5,330 → budget $1,066 → 82h at 20%
# Target ~72h scheduled (availability-constrained: no Lidy, no Kaisha, Vicki limited)
SUNDAY_SHIFTS = [
    # Shift Leader AM (Nathan or Madison)
    (POS_SL_HOURLY, "07:00", "15:00"),   # 8h SL opener
    # Shift Leader PM (Kasey 3:30p close)
    (POS_SL_HOURLY, "15:30", "23:15"),   # 7.75h SL closer
    # Day Crew AM (Vicki 8a-2p short shift, phasing out)
    (POS_CREW,      "08:00", "14:00"),   # 6h Vicki limited
    # Day Crew mid (Noel - Sun primary per schedule-prep)
    (POS_CREW,      "08:00", "16:00"),   # 8h Noel AM anchor
    # Lunch crew (11a-5p)
    (POS_CREW,      "11:00", "17:00"),   # 6h lunch surge
    # MID shift (Jeremiah/Brianna — mid-heavy Sun per Bobby override)
    (POS_CREW,      "12:00", "20:00"),   # 8h mid coverage
    # PM crew 1 (Maylin 3p)
    (POS_CREW,      "15:00", "23:15"),   # 8.25h
    # PM crew 2 (Jada Cox 5p Sun)
    (POS_CREW,      "17:00", "23:15"),   # 6.25h
    # Dinner peak (Autumn 5:30p)
    (POS_CREW,      "17:30", "23:15"),   # 5.75h
]
# Sun total raw: 8+7.75+6+8+6+8+8.25+6.25+5.75 = 64.0h
# Paid (7+ hr shifts): 8+7.75+8+8+8.25 = 5 shifts -> -2.5h breaks
# Sun paid: 64.0 - 2.5 = 61.5h paid
# Sun labor $: 61.5 * 13 = $799.50. Labor%: 799.50/5330 = 15.0%
# (Under 20% — Sun availability limits headcount; high sales make % favorable)


# ─────────────────────────────────────────────────────────────────────────────
# WEEKLY MATH SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
# Day    | Forecast | Sched hrs | Paid hrs | Labor $  | Labor %
# Wed    | $3,834   | 53.0h     | 51.0h    | $663     | 17.3%
# Thu    | $4,159   | 75.75h    | 72.75h   | $946     | 22.7% (Bobby override hot)
# Fri    | $5,372   | 71.75h    | 68.75h   | $894     | 16.6%
# Sat    | $5,222   | 72.5h     | 70.0h    | $910     | 17.4%
# Sun    | $5,330   | 64.0h     | 61.5h    | $800     | 15.0%
# ─────────────────────────────────────────────────────────────────────────────
# TOTAL  | $23,917  | 337.0h    | 324.0h   | $4,213   | 17.6%
#
# NOTE: Thursday runs at 22.7% due to Bobby's mandatory overrides (truck + shop + boil-out).
# Wed/Fri/Sat/Sun run well under 20% to compensate.
# Blended 5-day Wed-Sun: 17.6% (comfortably under 20% even with Thu hot).
#
# For the FULL week including Mon/Tue:
# Mon+Tue forecast approx $7,320 ($3,591+$3,429 per forecast_by_day)
# Mon is also truck day — expected ~65h paid. Tue ~63h paid.
# Mon/Tue labor approx $1,664 / 22.7% on Mon (truck), $819 / 22.6% on Tue
# Full week (Mon-Sun) ~$31,237 forecast, ~$6,696 labor = 21.4%
# Wed-Sun alone: 17.6% gives headroom for Mon/Tue being higher.
# ─────────────────────────────────────────────────────────────────────────────

TEMPLATES = [
    ("DIXIE LABOR Wednesday", WEDNESDAY_SHIFTS),
    ("DIXIE LABOR Thursday",  THURSDAY_SHIFTS),
    ("DIXIE LABOR Friday",    FRIDAY_SHIFTS),
    ("DIXIE LABOR Saturday",  SATURDAY_SHIFTS),
    ("DIXIE LABOR Sunday",    SUNDAY_SHIFTS),
]

# Template IDs for existing templates (created via browser flow before this script).
# Wednesday=31034 was created this session. Others=None → server creates new.
# After first successful push, fill in the returned IDs for future re-pushes.
TEMPLATE_IDS = {
    "DIXIE LABOR Wednesday": 31034,   # confirmed via getSchedulingTemplatesData
    "DIXIE LABOR Thursday":  31035,   # confirmed via getSchedulingTemplatesData
    "DIXIE LABOR Friday":    31036,   # confirmed via getSchedulingTemplatesData
    "DIXIE LABOR Saturday":  31054,   # confirmed via getSchedulingTemplatesData (non-sequential ID)
    "DIXIE LABOR Sunday":    31037,   # confirmed via getSchedulingTemplatesData
}


def calculate_stats(shifts: list[tuple]) -> dict:
    """Calculate raw hours, paid hours, labor $, labor % for a shift list."""
    raw_hours = sum(shift_hours(s, e) for _, s, e in shifts)
    # Breaks: 0.5h per shift >= 7h
    breaks = sum(0.5 for _, s, e in shifts if shift_hours(s, e) >= 7.0)
    paid = raw_hours - breaks
    return {"raw_hours": round(raw_hours, 2), "breaks": breaks, "paid_hours": round(paid, 2)}


def push_template(s, name: str, shifts: list[tuple], dry_run: bool = False) -> dict:
    """
    Build and POST a template via form-encoded body.

    Endpoint: POST /json/mn/templates/updateSchedulingTemplate
    Content-Type: application/x-www-form-urlencoded

    Body fields (discovered via jQuery $.ajax intercept in Chrome MCP):
      template         — JSON string of template metadata object
      templateData     — JSON string of shiftTemplateDataList array
      existingTemplateId — template ID string (empty string = create new)

    The 'template' field contains the flat metadata dict (id, name, statusId,
    timeSlotValue, locationId, etc.) WITHOUT the shiftTemplateDataList.
    The 'templateData' field carries the shift rows as a separate JSON array.
    """
    template_id = TEMPLATE_IDS.get(name)

    # Metadata object — flat, no shift rows
    meta = {
        "id": template_id,
        "name": name,
        "createdBy": None,
        "createdDate": None,
        "lastUpdatedBy": None,
        "lastUpdatedDate": None,
        "status": None,
        "statusId": 1,
        "lastUpdatedById": None,
        "createdById": 325819,
        "timeSlotValue": 10,
        "description": None,
        "actionStatus": None,
        "locationName": LOCATION_NAME,
        "locationId": LOCATION_ID,
        "hidePaidBreakViolations": 0,
        "hideUnPaidBreakViolations": 0,
        "translatedStatus": None,
        "translatedActionStatus": None,
    }

    # Shift rows array
    shift_rows = []
    for seq, (pos_id, start, end) in enumerate(shifts, start=1):
        shift_rows.append(build_shift_row(pos_id, seq, start, end))

    if dry_run:
        stats = calculate_stats(shifts)
        print(f"  [DRY RUN] '{name}' | ID={template_id or 'NEW'} | {len(shifts)} shifts | {stats['raw_hours']}h raw / {stats['paid_hours']}h paid")
        return {"dryRun": True, "name": name, **stats}

    # Form-encoded POST — critical: NOT json= but data=
    form_data = {
        "template": json.dumps(meta, separators=(",", ":")),
        "templateData": json.dumps(shift_rows, separators=(",", ":")),
        "existingTemplateId": str(template_id) if template_id else "",
    }

    # Use requests-level headers: drop JSON content-type, let requests set form-encoded
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
    # Debug: print full result to understand structure
    import os
    if os.environ.get("TWX_DEBUG"):
        print(f"  DEBUG response: {json.dumps(result, indent=2)[:2000]}")
    # Response envelope: {"status": "success", "result": {...}} OR {"success": true, "data": {...}}
    status = result.get("status") or ("success" if result.get("success") else "fail")
    if status != "success":
        msg = result.get("messageList") or result.get("message") or json.dumps(result)[:300]
        raise RuntimeError(f"API returned status={status}: {msg}")
    # Return the inner data — either result["result"] or result["data"]
    return result.get("result") or result.get("data") or {}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Build Teamworx Shift Builder templates Wed-Sun")
    parser.add_argument("--dry-run", action="store_true", help="Print plan without writing to Teamworx")
    parser.add_argument("--day", choices=["WED","THU","FRI","SAT","SUN"], help="Build only one day")
    args = parser.parse_args()

    print("\n=== KY-2065 Shift Templates — Wed-Sun Build ===")
    print(f"Target labor: 20% | Avg wage: ${AVG_WAGE}/hr | Dry run: {args.dry_run}")
    print()

    # Print the labor math
    total_forecast = 0
    total_raw = 0
    total_paid = 0
    total_labor_dollar = 0

    day_names = ["WED", "THU", "FRI", "SAT", "SUN"]
    day_shifts_map = dict(zip(day_names, [WEDNESDAY_SHIFTS, THURSDAY_SHIFTS, FRIDAY_SHIFTS, SATURDAY_SHIFTS, SUNDAY_SHIFTS]))

    print(f"{'Day':<5} | {'Forecast':>10} | {'Budget@20%':>10} | {'Sched hrs':>9} | {'Paid hrs':>8} | {'Labor $':>8} | {'Labor %':>7}")
    print("-"*70)
    for day in day_names:
        if args.day and args.day != day:
            continue
        forecast = DAILY_FORECAST[day]
        budget = forecast * TARGET_LABOR_PCT
        shifts = day_shifts_map[day]
        stats = calculate_stats(shifts)
        labor_dollar = stats["paid_hours"] * AVG_WAGE
        labor_pct = labor_dollar / forecast
        print(f"{day:<5} | ${forecast:>9,.0f} | ${budget:>9,.0f} | {stats['raw_hours']:>9.2f}h | {stats['paid_hours']:>7.2f}h | ${labor_dollar:>7.2f} | {labor_pct:>6.1%}")
        total_forecast += forecast
        total_raw += stats["raw_hours"]
        total_paid += stats["paid_hours"]
        total_labor_dollar += labor_dollar

    print("-"*70)
    overall_pct = total_labor_dollar / total_forecast if total_forecast else 0
    print(f"{'TOTAL':<5} | ${total_forecast:>9,.0f} | ${total_forecast*0.20:>9,.0f} | {total_raw:>9.2f}h | {total_paid:>7.2f}h | ${total_labor_dollar:>7.2f} | {overall_pct:>6.1%}")
    print()

    if not args.dry_run:
        s = load_session()
        print("Session loaded. Pushing templates to Teamworx...\n")

    results = {}
    for name, shifts in TEMPLATES:
        day_code = name.split()[-1].upper()[:3]
        if args.day and args.day != day_code:
            continue
        print(f"Building: {name}")
        stats = calculate_stats(shifts)
        print(f"  Shifts: {len(shifts)} | Raw: {stats['raw_hours']}h | Paid: {stats['paid_hours']}h")

        try:
            if args.dry_run:
                result = push_template(None, name, shifts, dry_run=True)
            else:
                result = push_template(s, name, shifts, dry_run=False)
                tid = result.get("id") or result.get("templateId") or result.get("scheduleTemplateId")
                print(f"  OK — template ID: {tid}")
                print(f"  Raw result keys: {list(result.keys())}")
                if tid and TEMPLATE_IDS.get(name) is None:
                    print(f"  ** Update TEMPLATE_IDS['{name}'] = {tid} for future re-pushes **")
            results[name] = result
        except Exception as e:
            print(f"  ERROR: {e}")
            results[name] = {"error": str(e)}
        print()

    if not args.dry_run:
        print("=== Template ID Summary (update TEMPLATE_IDS for re-runs) ===")
        for name, result in results.items():
            if "error" not in result:
                tid = result.get("id") or result.get("templateId") or result.get("scheduleTemplateId")
                print(f"  {name}: {tid}")

    print("=== Complete ===")
    return results


if __name__ == "__main__":
    main()
