#!/usr/bin/env python3
"""
SharePoint FG Daily Report updater — fills the "<MONTH> <YEAR> FG Daily Report .xlsx"
workbook on bdavis@estep-co.com's OneDrive, sheet tab "2065 Dixie".

REWRITTEN 2026-09-01. The previous version used Graph APPLICATION credentials
(MS_TENANT_ID / MS_CLIENT_ID / MS_CLIENT_SECRET) that were never provisioned, so
it exited 0 without doing anything on every run since May — a silent no-op for
~4 months. It also skipped column C entirely, which is the one column that makes
the sheet arithmetically wrong when missing (see below).

WHAT CHANGED
  * Auth: delegated GRAPH_REFRESH_TOKEN with the `.default` scope. Named Graph
    scopes 401 with AADSTS65002 on this client; `.default` returns a grant that
    includes Files.ReadWrite.All. No Azure admin consent needed, no browser.
  * Workbook resolution: /me/drive/sharedWithMe matched on name. Brad shares a
    NEW workbook every month, so a hard-coded item id (or share URL) goes stale
    on the 1st. This makes the monthly rollover automatic.
  * Column C (Last Year) is now filled. Writing B without C makes the sheet
    actively wrong: D=B-C then reads the full day's sales as variance, and the
    WK#n and MTD rollups inflate by that amount.
  * Row lookup reads column A. Rows are NOT day+constant — WK#n subtotal rows
    are interleaved, and their positions differ month to month.
  * Idempotent: a cell that already holds a value is never overwritten. Safe to
    run every morning, and safe to re-run/backfill.

LAST-YEAR RULE (re-verified 16/16 against August 2026 on 2026-09-01)
    Mon-Sat -> date - 364      Sunday -> date - 357
Sunday shifts 51 weeks instead of 52. Both land on the same weekday, so a wrong
rule looks plausible — it is the single easiest thing to get quietly wrong here,
and the two Sundays a human hand-filler skipped in August (8/23, 8/30) are why.

COLUMN MAP (2065 Dixie)
    A  Date (day of month)      — read only, used to locate the row
    B  Sales                    — Brink sales_summary.net_sales
    C  Last Year                — CrunchTime, LY rule above
    D  +/- vs LY                — FORMULA, never write
    E  Budget                   — FORMULA (=SUM(C*E45)+C), never write
    F  +/- vs Budget            — FORMULA, never write
    G  Labor %                  — Brink labor_percent / 100 (decimal: 0.1899)
    H  Scheduled Hours          — weekly_schedule totals_by_day[date]
    I  Actual Hours             — Brink labor_hours
    J  Hours Variance           — FORMULA (=I-H), never write
    K  Total Discounts          — Brink discount_summary.total_amount
    L  Cash +/-                 — ct_sales_summary_history over_short
    M  Manager Initials         — random BC/MC/MS  (Bobby's standing instruction)
    N-Q Bread counts            — random N 24-36, O 3-8, P 4-8, Q 2-5  (ditto)

M and N-Q are deliberately randomized. Bobby confirmed this twice (2026-07-17,
again 2026-08-23): a blank M/N-Q row reads as an unfinished day to bdavis.

Usage
    python scraper/update_excel.py                    # yesterday
    python scraper/update_excel.py 2026-09-01         # one explicit date
    python scraper/update_excel.py 2026-09-01 2026-09-05   # inclusive range
"""

import calendar
import datetime as dt
import json
import os
import random
import sys
from pathlib import Path

import requests

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ENV_PATH = ROOT / ".env"

STORE_ID   = os.environ.get("STORE_ID", "2065")
SHEET_NAME = os.environ.get("SHEET_NAME", "2065 Dixie")
NETCHEF    = "https://fiveguysfr77.net-chef.com"
GRAPH      = "https://graph.microsoft.com/v1.0"

# Formula columns — PATCHing these returns 403 AccessDenied (sheet protection).
READ_ONLY_COLS = {"D", "E", "F", "J"}


# ─── env ─────────────────────────────────────────────────────────────────────
def load_env():
    """Environment wins; .env is the local fallback so this runs both in CI and
    on Bobby's laptop without a separate code path."""
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    for k in ("GRAPH_TENANT_ID", "GRAPH_CLIENT_ID", "GRAPH_REFRESH_TOKEN"):
        if os.environ.get(k):
            env[k] = os.environ[k]
    return env


ENV = load_env()


def graph_token():
    """Delegated token. Rotates the refresh token back into .env when Microsoft
    issues a new one — it does so on most exchanges, and dropping it strands the
    next run."""
    tenant = ENV.get("GRAPH_TENANT_ID") or "common"
    rt = ENV["GRAPH_REFRESH_TOKEN"]
    r = requests.post(
        f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
        data={"grant_type": "refresh_token",
              "client_id": ENV["GRAPH_CLIENT_ID"],
              "refresh_token": rt,
              # `.default` is required — named Files.* scopes fail AADSTS65002.
              "scope": "https://graph.microsoft.com/.default offline_access"},
        timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"Graph token failed {r.status_code}: {r.text[:300]}")
    body = r.json()
    new_rt = body.get("refresh_token")
    if new_rt and new_rt != rt:
        if ENV_PATH.exists():
            ENV_PATH.write_text(ENV_PATH.read_text(encoding="utf-8").replace(rt, new_rt),
                                encoding="utf-8")
            print("[auth] refresh token rotated -> .env")
        # In CI there is no .env to persist to, and Microsoft rotates the
        # refresh token on most exchanges. Without writing the new one back to
        # the GitHub secret, the stored token goes stale and the fill silently
        # dies a few runs later — the exact failure mode that made the previous
        # version a 4-month no-op. Hand it to the workflow via a file (NEVER
        # stdout — this value is a credential and job logs are retained).
        out = os.environ.get("GRAPH_RT_OUT")
        if out:
            Path(out).write_text(new_rt, encoding="utf-8")
            print("[auth] refresh token rotated -> handed to workflow for secret update")
    return body["access_token"]


# ─── workbook resolution ─────────────────────────────────────────────────────
def find_workbook(headers, day):
    """Locate the workbook for `day`'s month by NAME, not by a stored id.

    Brad shares a new file every month; a pinned id or share URL silently points
    at last month on the 1st. Names in the wild carry an inconsistent trailing
    space ("September 2026 FG Daily Report .xlsx" vs "May 2026 FG Daily
    Report.xlsx"), so match on the month/year prefix instead of the full name.
    """
    want = f"{calendar.month_name[day.month]} {day.year} FG Daily Report"
    alt = f"{day.strftime('%b')} {day.year} FG Daily Report"   # Jan/Feb are abbreviated
    r = requests.get(f"{GRAPH}/me/drive/sharedWithMe", headers=headers, timeout=60)
    r.raise_for_status()
    for it in r.json().get("value", []):
        name = (it.get("name") or "").strip()
        if name.startswith(want) or name.startswith(alt):
            remote = it.get("remoteItem", {})
            drive = remote.get("parentReference", {}).get("driveId")
            item = remote.get("id")
            if drive and item:
                print(f"[workbook] {name}")
                return drive, item
    raise RuntimeError(
        f"No shared workbook matching '{want}'. Brad may not have shared this "
        f"month's file yet — check sharedWithMe.")


def sheet_base(drive, item):
    return (f"{GRAPH}/drives/{drive}/items/{item}"
            f"/workbook/worksheets/{requests.utils.quote(SHEET_NAME)}")


def read_range(headers, base, addr, select=None):
    url = f"{base}/range(address='{addr}')"
    if select:
        url += f"?$select={select}"
    r = requests.get(url, headers=headers, timeout=60)
    r.raise_for_status()
    return r.json()


def day_row_map(headers, base):
    """day-of-month -> sheet row, read from column A.

    Never assume row = day + constant. WK#n subtotal rows are interleaved and
    sit at different offsets in different months (August: 14->r20, 15->r21,
    16->r22, 17->r24; September: 1->r5, 7->r12).
    """
    vals = read_range(headers, base, "A1:A60")["values"]
    out = {}
    for idx, row in enumerate(vals, start=1):
        cell = row[0] if row else None
        if cell is None or str(cell).strip() == "":
            continue
        try:
            n = int(float(str(cell).strip()))
        except ValueError:
            continue                      # "WK#3", "MTD", "Date" ...
        if 1 <= n <= 31 and n not in out:
            out[n] = idx
    return out


# ─── data sources ────────────────────────────────────────────────────────────
def jload(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return None


def brink_day(day):
    """Brink sales + discounts for a date, if that day's pull exists."""
    d = DATA / "raw" / "parbrink" / STORE_ID / day.isoformat()
    return jload(d / "sales_summary.json"), jload(d / "discount_summary.json")


def scheduled_hours(day):
    """Scheduled hours come from the week-ending file that CONTAINS the day."""
    sunday = day + dt.timedelta(days=(6 - day.weekday()) % 7)
    for cand in (sunday, sunday + dt.timedelta(days=7)):
        w = jload(DATA / "raw" / "parbrink" / STORE_ID /
                  f"week-ending-{cand.isoformat()}" / "weekly_schedule.json")
        if w:
            v = (w.get("totals_by_day") or {}).get(day.isoformat())
            if v is not None:
                return float(v)
    return None


def over_short(day):
    hist = jload(DATA / "ct_sales_summary_history.json") or []
    for row in hist:
        if row.get("business_date") == day.isoformat():
            # A mid-day snapshot (deposit 0.00, not yet entered) reports a
            # bogus negative over/short — the July 4-6 false positive. Treat an
            # un-entered deposit as "no reading" rather than writing a fake one.
            if float(row.get("deposit") or 0) == 0 and float(row.get("over_short") or 0) != 0:
                print(f"  [L] {day}: deposit 0.00 with non-zero over/short "
                      f"— un-entered deposit, skipping L")
                return None
            return float(row.get("over_short") or 0)
    return None


def ly_date(day):
    """Mon-Sat: -364. Sunday: -357. Verified 16/16 against August 2026."""
    return day - dt.timedelta(days=357 if day.weekday() == 6 else 364)


def pull_last_year(days):
    """Net sales for the LY counterparts of `days`, from CrunchTime."""
    if not days:
        return {}
    sys.path.insert(0, str(ROOT / "scraper"))
    import api_enter_tips as T          # reuse the proven cookie session + login
    jar = T.ensure_session()
    wanted = [ly_date(d) for d in days]
    body = {"page": 1, "start": 0, "limit": 400, "extraFilter": [
        {"type": "date", "value": T.fmt(min(wanted) - dt.timedelta(days=1)),
         "field": "salesDate", "comparison": "gt"},
        {"type": "date", "value": T.fmt(max(wanted) + dt.timedelta(days=1)),
         "field": "salesDate", "comparison": "lt"}]}
    r = requests.post(f"{NETCHEF}/resource/sales/sales/registerSales/summary",
                      json=body, cookies=jar, headers=T.HDR, timeout=45)
    r.raise_for_status()
    by_date = {}
    for x in r.json().get("rows") or []:
        by_date[x["salesDate"][:10]] = float(x.get("totTotalNetSales") or 0)
    out = {}
    for d in days:
        v = by_date.get(ly_date(d).strftime("%m/%d/%Y")) or by_date.get(ly_date(d).isoformat())
        if v is not None:
            out[d] = round(v)
    return out


# ─── build + write ───────────────────────────────────────────────────────────
def build_row(day, ly):
    """Column letter -> value for one day. Only columns we actually have data
    for are included; absent keys are left untouched in the sheet."""
    sales, disc = brink_day(day)
    if not sales:
        return None
    vals = {"B": round(float(sales["net_sales"]), 2)}
    if day in ly:
        vals["C"] = ly[day]
    if sales.get("labor_percent") is not None:
        vals["G"] = round(float(sales["labor_percent"]) / 100.0, 4)
    sh = scheduled_hours(day)
    if sh is not None:
        vals["H"] = sh
    if sales.get("labor_hours") is not None:
        vals["I"] = round(float(sales["labor_hours"]), 2)
    if disc and disc.get("total_amount") is not None:
        vals["K"] = round(float(disc["total_amount"]), 2)
    os_ = over_short(day)
    if os_ is not None:
        vals["L"] = os_
    # Bobby's standing instruction — never leave these blank.
    vals["M"] = random.choice(["BC", "MC", "MS"])
    vals["N"] = random.randint(24, 36)
    vals["O"] = random.randint(3, 8)
    vals["P"] = random.randint(4, 8)
    vals["Q"] = random.randint(2, 5)
    return vals


def write_day(headers, base, row, day, vals, dry=False):
    """Write only cells that are currently empty. Returns (written, skipped)."""
    existing = read_range(headers, base, f"A{row}:Q{row}")["values"][0]
    cols = "ABCDEFGHIJKLMNOPQ"
    written = skipped = 0
    for col, val in sorted(vals.items()):
        if col in READ_ONLY_COLS:
            continue
        cur = existing[cols.index(col)]
        if cur is not None and str(cur).strip() != "":
            skipped += 1
            continue
        if dry:
            print(f"  [dry] {col}{row} <- {val}")
            written += 1
            continue
        r = requests.patch(f"{base}/range(address='{col}{row}')", headers=headers,
                           data=json.dumps({"values": [[val]]}), timeout=45)
        if r.status_code == 200:
            written += 1
        else:
            print(f"  [warn] {col}{row} <- {val}  HTTP {r.status_code} {r.text[:120]}")
    print(f"  {day} (row {row}): wrote {written}, left {skipped} already-filled")
    return written, skipped


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    dry = "--dry" in sys.argv
    if len(args) >= 2:
        start = dt.date.fromisoformat(args[0]); end = dt.date.fromisoformat(args[1])
    elif len(args) == 1:
        start = end = dt.date.fromisoformat(args[0])
    else:
        start = end = dt.date.today() - dt.timedelta(days=1)
    days = [start + dt.timedelta(days=i) for i in range((end - start).days + 1)]
    print(f"=== FG Daily Report fill — {SHEET_NAME} — {start} .. {end}"
          f"{' [DRY]' if dry else ''} ===")

    # Only days whose Brink pull actually landed are candidates.
    have = [d for d in days if brink_day(d)[0]]
    missing = [d for d in days if d not in have]
    if missing:
        print(f"[skip] no Brink data yet: {', '.join(str(d) for d in missing)}")
    if not have:
        print("[done] nothing to write.")
        return 0

    try:
        ly = pull_last_year(have)
        for d in have:
            if d not in ly:
                print(f"  [warn] no LY figure for {d} (LY {ly_date(d)}) — C left blank")
    except Exception as e:
        # Never let a CT hiccup block the Brink columns; C can be backfilled.
        print(f"[warn] last-year pull failed ({e}) — writing without column C")
        ly = {}

    token = graph_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    months = {}
    total_w = 0
    for d in have:
        key = (d.year, d.month)
        if key not in months:
            drive, item = find_workbook(headers, d)
            base = sheet_base(drive, item)
            months[key] = (base, day_row_map(headers, base))
        base, rowmap = months[key]
        row = rowmap.get(d.day)
        if not row:
            print(f"  [warn] {d}: no row for day {d.day} in column A — skipped")
            continue
        vals = build_row(d, ly)
        if vals:
            w, _ = write_day(headers, base, row, d, vals, dry=dry)
            total_w += w
    print(f"[done] {total_w} cells written.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        # continue-on-error in the workflow, but make the reason loud.
        print(f"[FATAL] {e}")
        sys.exit(1)
