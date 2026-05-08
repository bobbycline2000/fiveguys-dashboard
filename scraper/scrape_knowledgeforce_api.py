#!/usr/bin/env python3
"""
KnowledgeForce Secret Shop Scraper — pure requests (no Playwright)
==================================================================
Replaces scrape_knowledgeforce.py. Same output schema.

Auth flow (reverse-engineered 2026-05-07):
  1. GET https://www.knowledgeforce.com/  (form has _csrf hidden input)
  2. POST same URL with Login[username], Login[password], _csrf
  3. Reuse session cookies for /reporting/api/* JSON calls

Endpoints:
  GET /reporting/api/filters/903?dataset=[]              — period tree
  GET /reporting/api/widget/175639?isDash=1&reportId=923&dataset=<json>
                                                          — Individual Shops

Usage:
  python scraper/scrape_knowledgeforce_api.py --store 2065

Output:
  data/raw/marketforce/<store>/<today>/shops.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse as up
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = ROOT / "data" / "raw" / "marketforce"
ET = timezone(timedelta(hours=-4))

BASE = "https://www.knowledgeforce.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 KnowledgeForceAPIClient/1.0"


def log(msg: str) -> None:
    print(f"[kf-api] {msg}", flush=True)


def login(s: requests.Session, user: str, pw: str) -> bool:
    r = s.get(BASE + "/", timeout=30)
    r.raise_for_status()
    m = re.search(r'name="_csrf"[^>]*value="([^"]+)"', r.text)
    if not m:
        log("no _csrf token found on landing page")
        return False
    csrf = m.group(1)
    payload = {
        "_csrf": csrf,
        "Login[username]": user,
        "Login[password]": pw,
    }
    r = s.post(BASE + "/", data=payload, timeout=30, allow_redirects=True)
    r.raise_for_status()
    if "/login" in r.url.lower() or 'name="Login[username]"' in r.text[:5000]:
        log(f"login failed — final URL {r.url}")
        return False
    log(f"login OK — landed on {r.url}")
    return True


def fetch_period_ids(s: requests.Session) -> list[int]:
    """Get all period2 IDs from the filter form HTML.
    Filter API returns {"html": "...rendered filter form..."} — checkbox values
    are formatted as `period2-||-<id>`. Extract every <id>."""
    r = s.get(BASE + "/reporting/api/filters/903?dataset=%5B%5D", timeout=30)
    r.raise_for_status()
    html = r.json().get("html", "")
    ids = sorted({int(x) for x in re.findall(r'value="period2-\|\|-(\d+)"', html)})
    return ids


def fetch_shops(s: requests.Session) -> list[dict]:
    period_ids = fetch_period_ids(s)
    log(f"period IDs: {len(period_ids)}")
    if not period_ids:
        log("no period IDs in filter HTML — cannot widen scope")
        return []

    # First call: all-periods at once to know total. {"period2":[ids]} flat shape.
    enc_all = up.quote(json.dumps({"period2": period_ids}))
    r = s.get(f"{BASE}/reporting/api/widget/175639?isDash=1&reportId=923&dataset={enc_all}",
              timeout=60)
    if not r.ok:
        log(f"widget HTTP {r.status_code}")
        return []
    all_rows = _parse_dataset_var(r.json().get("html", ""))
    log(f"all-periods query: {len(all_rows)} shops")

    # Per-period requery so each row's href carries its OWN period2 (the all-periods
    # query embeds the whole period list into every href, losing per-shop accuracy).
    # Only requery periods that actually had shops in the all-periods pass.
    job_to_period: dict[str, int] = {}
    periods_with_shops = sorted({int(p) for p in period_ids})  # query all 71; cheap (~10s total)
    seen_jobs: set[str] = set()
    refined: list[dict] = []
    for pid in periods_with_shops:
        enc = up.quote(json.dumps({"period2": [pid]}))
        r = s.get(f"{BASE}/reporting/api/widget/175639?isDash=1&reportId=923&dataset={enc}",
                  timeout=30)
        if not r.ok:
            continue
        rows = _parse_dataset_var(r.json().get("html", ""))
        for row in rows:
            jid = row["job_id"]
            if jid in seen_jobs:
                continue
            seen_jobs.add(jid)
            row["period2"] = pid  # override with this period's ID
            refined.append(row)
    log(f"per-period requery: {len(refined)} shops with accurate period2")

    # Use refined if it covers all_rows, else fall back to all_rows
    if len(refined) >= len(all_rows) * 0.9:
        return refined
    log("per-period coverage incomplete — falling back to all-rows result")
    return all_rows


def _parse_dataset_var(html: str) -> list[dict]:
    """Widget response is `{"type":"render","html":"..."}` and the rows live
    inside the embedded JS as `var dataSet = [[...row...], ...];`.
    Each row is [job_link_html, loc_id, location, date, meal_period, score]."""
    m = re.search(r"var dataSet\s*=\s*(\[\[.*?\]\]);", html, re.S)
    if not m:
        return []
    try:
        rows = json.loads(m.group(1))
    except Exception as e:
        log(f"dataSet JSON parse failed: {e}")
        return []
    out = []
    for row in rows:
        if not isinstance(row, list) or len(row) < 6:
            continue
        # row[0] is "<a href=\"/reporting/assignment/view?dataset={...}\">JOB_ID</a>"
        cell0 = str(row[0])
        job_id_m = re.search(r">(\d+)<", cell0)
        job_id = job_id_m.group(1) if job_id_m else cell0
        href_m = re.search(r'href\s*=\s*"([^"]+)"', cell0)
        href = href_m.group(1).replace("\\/", "/") if href_m else ""
        ds_obj = {}
        ds_m = re.search(r"dataset=([^&\"]+)", href)
        if ds_m:
            try:
                ds_obj = json.loads(up.unquote(ds_m.group(1)))
            except Exception:
                pass
        try:
            score = float(str(row[5]).replace("%", ""))
        except (TypeError, ValueError):
            score = None
        out.append({
            "job_id":      job_id,
            "location_id": str(row[1]),
            "location":    str(row[2]),
            "date_raw":    str(row[3]),
            "meal_period": str(row[4]),
            "score":       score,
            "jid":         ds_obj.get("jid"),
            "period2":     (ds_obj.get("period2") or [None])[0],
            "scheme":      (ds_obj.get("scheme") or [None])[0],
            "href":        href,
        })
    return out


def parse_us_date(s: str) -> date | None:
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def compute_averages(shops: list[dict]) -> dict:
    today = datetime.now(tz=ET).date()
    cuts = {"week": today - timedelta(days=7),
            "month": today - timedelta(days=30),
            "quarter": today - timedelta(days=90)}
    out = {}
    for k, cut in cuts.items():
        scored = [s for s in shops if s.get("score") is not None and s.get("_date") and s["_date"] >= cut]
        if scored:
            out[k] = {"score": round(sum(s["score"] for s in scored) / len(scored), 2), "n": len(scored)}
        else:
            out[k] = {"score": None, "n": 0}
    return out


def load_historical(store_id: str) -> list[dict]:
    store_dir = DATA_ROOT / store_id
    if not store_dir.exists():
        return []
    for d in sorted((x for x in store_dir.iterdir() if x.is_dir()), reverse=True):
        f = d / "shops.json"
        if f.exists():
            try:
                return json.loads(f.read_text(encoding="utf-8")).get("shops", [])
            except Exception:
                continue
    return []


def build_payload(store_id: str, rows: list[dict]) -> dict:
    scraped = {}
    for r in rows:
        d = parse_us_date(r["date_raw"])
        scraped[r["job_id"]] = {
            "job_id":      r["job_id"],
            "date":        d.strftime("%Y-%m-%d") if d else r["date_raw"],
            "meal_period": r["meal_period"],
            "score":       r.get("score"),
            "period2":     r.get("period2"),
            "service":               r.get("service"),
            "quality":               r.get("quality"),
            "cleanliness":           r.get("cleanliness"),
            "customer_satisfaction": r.get("customer_satisfaction"),
            "_date":       d,
        }
    merged = {}
    for h in load_historical(store_id):
        jid = h.get("job_id")
        if not jid:
            continue
        d = parse_us_date(h.get("date", ""))
        if d is None:
            try:
                d = date.fromisoformat(h.get("date", ""))
            except Exception:
                d = None
        e = dict(h); e["_date"] = d
        merged[jid] = e
    # Merge scraped data — preserve historical SQC fields when the API returns null
    # (the API client skips per-shop detail pages; SQC comes from the Playwright path or
    # Marketforce email PDFs stored in prior runs).
    SQC_FIELDS = ("service", "quality", "cleanliness", "customer_satisfaction")
    for jid, new in scraped.items():
        if jid in merged:
            old = merged[jid]
            for field in SQC_FIELDS:
                if new.get(field) is None and old.get(field) is not None:
                    new[field] = old[field]
            # Also preserve visit_window from historical
            if new.get("visit_window") is None and old.get("visit_window") is not None:
                new["visit_window"] = old["visit_window"]
                new["visit_window_source"] = old.get("visit_window_source")
        merged[jid] = new
    shops = sorted(merged.values(), key=lambda s: s.get("_date") or date.min, reverse=True)
    averages = compute_averages(shops)
    latest = None
    if shops:
        l = shops[0]
        latest = {k: l.get(k) for k in ("job_id","date","meal_period","score","period2",
                                        "service","quality","cleanliness","customer_satisfaction")}
    for s in shops:
        s.pop("_date", None)
    now = datetime.now(tz=ET)
    return {
        "meta": {"generated": now.strftime("%Y-%m-%d %H:%M"),
                 "location": store_id,
                 "status": "ok" if shops else "empty",
                 "shops_total": len(shops)},
        "latest": latest,
        "averages": averages,
        "shops": shops,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--store", default=os.environ.get("STORE_ID", "2065"))
    ap.add_argument("--out-suffix", default="", help="appended to output dir for side-by-side test runs")
    args = ap.parse_args()

    user = os.environ.get("KNOWLEDGEFORCE_USERNAME", "")
    pw = os.environ.get("KNOWLEDGEFORCE_PASSWORD", "")
    if not user or not pw:
        log("KNOWLEDGEFORCE_USERNAME / PASSWORD env vars required")
        return 3

    s = requests.Session()
    s.headers.update({"User-Agent": UA})

    if not login(s, user, pw):
        return 3

    rows = fetch_shops(s)
    if not rows:
        log("zero shops returned")
        return 2

    payload = build_payload(args.store, rows)
    today_str = datetime.now(tz=ET).date().isoformat()
    out_dir = DATA_ROOT / args.store / (today_str + args.out_suffix)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "shops.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    log(f"wrote {out_path}")
    if payload.get("latest"):
        l = payload["latest"]
        log(f"latest: job {l['job_id']} {l['date']} {l['meal_period']} {l['score']}% | "
            f"Q-avg {payload['averages']['quarter']['score']}% (n={payload['averages']['quarter']['n']})")
    return 0


if __name__ == "__main__":
    # Auto-load .env if creds not in env
    if not os.environ.get("KNOWLEDGEFORCE_USERNAME"):
        env_path = ROOT / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("KNOWLEDGEFORCE_") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip())
    sys.exit(main())
