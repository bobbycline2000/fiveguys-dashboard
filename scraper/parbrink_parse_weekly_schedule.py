"""
Parse a Par Brink "Weekly Labor Schedule" PDF for a store and emit JSON the
dashboard's Today's Schedule card consumes.

Reads (in priority order):
  1. data/raw/parbrink/{store}/{date}/weekly_schedule.pdf       ← per-store export
  2. data/raw/parbrink/{store}/{date}/Weekly Labor Schedule.pdf ← multi-store batch (per-store split TODO)

Writes: data/raw/parbrink/{store}/{date}/weekly_schedule.json

Schema matches the file wire_dashboard.py already loads:
{
  "meta": {...},
  "totals_by_day": {"YYYY-MM-DD": hours, ..., "week_total": hours},
  "today": {
    "date": "YYYY-MM-DD",
    "day_of_week": "Saturday",
    "scheduled_hours": 90.5,
    "shifts": [{"name": "First L.", "role": "Crew", "start": "08:00 AM", "end": "04:00 PM"}, ...]
  }
}

Anchor: today = report_date in the PDF header (e.g. "Saturday, April 25, 2026").
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAY_FULL_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def find_pdf(store_id: str) -> Path | None:
    base = ROOT / "data" / "raw" / "parbrink" / store_id
    if not base.exists():
        return None
    for d in sorted([x for x in base.iterdir() if x.is_dir()], reverse=True):
        for cand_name in ("weekly_schedule.pdf", "Weekly Labor Schedule.pdf"):
            cand = d / cand_name
            if cand.exists():
                return cand
    return None


def extract_pages(pdf_path: Path) -> list[str]:
    from pypdf import PdfReader
    reader = PdfReader(str(pdf_path))
    out = []
    for page in reader.pages:
        try:
            out.append(page.extract_text(extraction_mode="layout") or "")
        except TypeError:
            out.append(page.extract_text() or "")
    return out


def parse_report_date(text: str) -> datetime | None:
    m = re.search(r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+'
                  r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+'
                  r'(\d{1,2}),\s+(\d{4})', text)
    if not m:
        return None
    return datetime.strptime(f"{m.group(2)} {m.group(3)} {m.group(4)}", "%B %d %Y")


def parse_week_dates(text: str) -> list[datetime]:
    """Return the 7 weekday dates (Mon..Sun) from the date header row."""
    dates = re.findall(r'(\d{1,2})/(\d{1,2})/(\d{4})', text)
    parsed = []
    seen = set()
    for mm, dd, yy in dates:
        try:
            d = datetime(int(yy), int(mm), int(dd))
        except ValueError:
            continue
        key = d.isoformat()
        if key in seen:
            continue
        seen.add(key)
        parsed.append(d)
        if len(parsed) >= 7:
            break
    return parsed


def find_day_columns(lines: list[str]) -> dict[str, int]:
    """Find x-positions of each day-name in the header row. Falls back to {}."""
    for line in lines:
        if 'Monday' in line and 'Sunday' in line:
            cols = {}
            for day in DAY_NAMES:
                p = line.find(day)
                if p >= 0:
                    cols[day] = p
            if len(cols) == 7:
                return cols
    return {}


def nearest_day(x: int, cols: dict[str, int]) -> str | None:
    if not cols:
        return None
    return min(cols.keys(), key=lambda d: abs(cols[d] - x))


def find_all(needle: str, hay: str) -> list[int]:
    out = []
    start = 0
    while True:
        i = hay.find(needle, start)
        if i < 0:
            return out
        out.append(i)
        start = i + 1


_TIME_RE = re.compile(r'\d{1,2}:\d{2}\s*(?:AM|PM)')


def time_after(line: str, anchor: int) -> str | None:
    seg = line[anchor:anchor + 60]
    m = _TIME_RE.search(seg)
    return m.group(0).replace(" ", "") if m else None


def is_role_token(s: str) -> bool:
    s = s.strip()
    return s in ("Crew",) or "Shift Lead" in s or "General Manager" in s


def parse_shifts_from_page(text: str, today_idx: int | None) -> tuple[list[dict], dict[str, float]]:
    """Walk the page, return (today_shifts, totals_by_day).
    today_idx: 0=Mon..6=Sun. If None, today shifts come back empty.
    """
    lines = text.split("\n")
    cols = find_day_columns(lines)
    if not cols:
        return [], {}

    day_to_idx = {d: i for i, d in enumerate(DAY_NAMES)}
    today_day = DAY_NAMES[today_idx] if today_idx is not None else None

    today_shifts: list[dict] = []
    totals_by_day: dict[str, float] = {}

    # We sweep the page line by line. Most rows look like:
    #   line N:   <name (left margin)>      Start: HH:MM ...  Start: HH:MM ...   End: ... ...   <total>
    # but in layout mode each shift cell occupies 3 stacked lines (Start: / End: / Role).
    # Simplest stable approach: walk the lines, and whenever we see a line that contains
    # "Start: HH:MM" entries, look 1-2 lines forward for matching "End: HH:MM" entries
    # at the same columns and a role line below.
    # The employee name is the leftmost token on the line that contains the End: row.
    name_pattern = re.compile(r'^\s*([A-Z][A-Za-z][A-Za-z\-\'\. ]+?,\s*[A-Z][A-Za-z\-\'\. ]+?)\s{2,}')
    last_total_row = None

    # Track which "row" we're in by grouping every 3 consecutive non-blank lines that
    # contain Start:/End:/Role. A row resets when we see a new name on an End: line.

    i = 0
    while i < len(lines):
        line = lines[i]
        # Detect a totals summary row: starts with "Total" then 7 numbers
        ts = re.match(r'\s*Total\s+([\d.\s]+)', line)
        if ts:
            nums = re.findall(r'\d+\.\d{2}', ts.group(1))
            if len(nums) >= 7:
                last_total_row = [float(n) for n in nums[:8]]
            i += 1
            continue

        starts = find_all("Start:", line)
        if not starts:
            i += 1
            continue

        # The corresponding End: line is the next line that contains "End:" anchors.
        end_line_idx = None
        for j in range(i + 1, min(i + 4, len(lines))):
            if "End:" in lines[j]:
                end_line_idx = j
                break
        if end_line_idx is None:
            i += 1
            continue

        end_line = lines[end_line_idx]
        ends = find_all("End:", end_line)
        # Role line is typically the next line after End:
        role_line = lines[end_line_idx + 1] if end_line_idx + 1 < len(lines) else ""

        # Extract employee name. Layout cases:
        #   (a) name on End: line:    "Last, First    End: ..."
        #   (b) name split across Start/End lines:
        #         "Last,         Start: ..."
        #         "First         End:   ..."
        #   (c) name split across prior-line/End line:
        #         "Last,"
        #         "                 Start: ..."
        #         "First            End: ..."
        name = None
        end_prefix = end_line[:ends[0]].rstrip() if ends else ""
        start_prefix = line[:starts[0]].rstrip() if starts else ""

        # (a) full "Last, First" already on End: line
        nm = re.search(r'([A-Z][A-Za-z\-\'\. ]+,\s*[A-Z][A-Za-z\-\'\. ]+)\s*$', end_prefix)
        if nm:
            name = nm.group(1).strip()

        # (b) "Last," on the Start line + "First" on the End line
        if not name:
            sm = re.search(r'([A-Z][A-Za-z\-\'\. ]+,\s*$)', start_prefix)
            if sm and end_prefix.strip():
                name = (sm.group(1).strip() + " " + end_prefix.strip()).strip()

        # (c) "Last," on the line ABOVE the Start line + "First" on End line
        if not name and i > 0 and lines[i - 1].strip():
            prev = lines[i - 1].strip()
            pm = re.search(r'([A-Z][A-Za-z\-\'\. ]+,\s*$)', prev)
            if pm and end_prefix.strip():
                name = (prev + " " + end_prefix.strip()).strip()

        # If we still don't have a name, skip this row
        if not name:
            i = end_line_idx + 1
            continue

        # Pair each Start: with the End: at the closest column
        for sx in starts:
            # Find nearest End:
            if not ends:
                continue
            ex = min(ends, key=lambda e: abs(e - sx))
            day = nearest_day(sx, cols)
            if day is None:
                continue
            start_time = time_after(line, sx)
            end_time = time_after(end_line, ex)
            # Role from role_line at nearest column to sx
            role = "Crew"
            if role_line.strip():
                tokens = re.findall(r'(General Manager - Salary|Shift Lead - Hourly|Shift Lead|General Manager|Crew)', role_line)
                if tokens:
                    # Use position-aligned token if possible
                    pos_tokens = []
                    for tok in tokens:
                        p = role_line.find(tok)
                        if p >= 0:
                            pos_tokens.append((p, tok))
                            role_line = role_line[:p] + (" " * len(tok)) + role_line[p + len(tok):]
                    if pos_tokens:
                        role = min(pos_tokens, key=lambda t: abs(t[0] - sx))[1]

            if today_day and day == today_day and start_time and end_time:
                short_name = format_short_name(name)
                today_shifts.append({
                    "name": short_name,
                    "role": role,
                    "start": format_time(start_time),
                    "end": format_time(end_time),
                })

        # Skip past the role line we consumed
        i = end_line_idx + 2

    if last_total_row and len(last_total_row) >= 7:
        # Map to dates
        # We don't have dates here — caller will inject from week_dates
        totals_by_day = {f"_idx_{k}": v for k, v in enumerate(last_total_row[:8])}

    return today_shifts, totals_by_day


def format_short_name(full: str) -> str:
    """'Cline, Robert' → 'Robert C.'   'Hernandez Rodriguez, Maylin' → 'Maylin H.'"""
    parts = [p.strip() for p in full.split(",", 1)]
    if len(parts) != 2:
        return full
    last, first = parts
    first_first = first.split()[0]
    last_first = last.split()[0]
    return f"{first_first} {last_first[0]}."


def format_time(t: str) -> str:
    """'8:00AM' → '08:00 AM'"""
    m = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM)', t)
    if not m:
        return t
    return f"{int(m.group(1)):02d}:{m.group(2)} {m.group(3)}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True)
    ap.add_argument("--pdf", help="Override PDF path")
    args = ap.parse_args()

    pdf = Path(args.pdf) if args.pdf else find_pdf(args.store)
    if pdf is None or not pdf.exists():
        print(f"No Weekly Labor Schedule PDF found for store {args.store}", file=sys.stderr)
        return 1

    pages = extract_pages(pdf)
    full_text = "\n".join(pages)

    report_dt = parse_report_date(full_text)
    if not report_dt:
        print("Could not parse report date from PDF header", file=sys.stderr)
        return 1

    # Anchor week directly on report_dt — Mon..Sun. Don't trust text date-order:
    # the first date that appears in the PDF is the generation timestamp, not Monday.
    today_idx = report_dt.weekday()  # Mon=0..Sun=6
    monday = report_dt - timedelta(days=today_idx)
    week_dates = [monday + timedelta(days=i) for i in range(7)]

    all_today_shifts: list[dict] = []
    totals_by_day_raw: dict[str, float] = {}
    for page_text in pages:
        shifts, totals = parse_shifts_from_page(page_text, today_idx)
        all_today_shifts.extend(shifts)
        if totals and not totals_by_day_raw:
            totals_by_day_raw = totals

    totals_by_day: dict[str, float] = {}
    if totals_by_day_raw and len(week_dates) >= 7:
        for k, v in totals_by_day_raw.items():
            try:
                idx = int(k.split("_")[-1])
            except ValueError:
                continue
            if idx < 7:
                totals_by_day[week_dates[idx].date().isoformat()] = v
            elif idx == 7:
                totals_by_day["week_total"] = v

    scheduled_hours = sum(s for d, s in totals_by_day.items() if d != "week_total" and d.endswith(report_dt.strftime("%Y-%m-%d")))
    if not scheduled_hours and totals_by_day:
        scheduled_hours = totals_by_day.get(report_dt.date().isoformat(), 0.0)

    out = {
        "meta": {
            "source": "parbrink_parse_weekly_schedule.py",
            "store_id": args.store,
            "report_date": report_dt.date().isoformat(),
            "generated": datetime.now().isoformat(timespec="seconds"),
            "source_pdf": str(pdf.relative_to(ROOT)).replace("\\", "/") if pdf.is_relative_to(ROOT) else str(pdf),
        },
        "totals_by_day": totals_by_day,
        "today": {
            "date": report_dt.date().isoformat(),
            "day_of_week": report_dt.strftime("%A"),
            "scheduled_hours": round(scheduled_hours, 2),
            "shifts": all_today_shifts,
        },
    }

    out_path = pdf.parent / "weekly_schedule.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"  Report date: {report_dt.date().isoformat()} ({report_dt.strftime('%A')})")
    print(f"  Today scheduled hours: {scheduled_hours}")
    print(f"  Today shifts: {len(all_today_shifts)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
