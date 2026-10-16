"""CI primary ComplianceMate pull (URL-replay, no browser).

Writes data/raw/compliancemate/<store>/<date>/compliance.json in the schema
wire_dashboard.py / aggregate_compliance.py read:
  {meta:{date,generated,location,status}, overall_pct, lists:[{name,pct,raw}]}
Date = yesterday (ET) unless --date given. Exits 1 if no lists came back so the
workflow can fall back to the legacy Playwright scraper.
Root cause it fixes: scrape_compliancemate.py (Playwright) has returned
login_ok_no_data since ~2026-09-27; the API path still returns the full roster.
"""
import argparse, json, os, sys
from datetime import datetime, timedelta
from pathlib import Path
import requests

sys.path.insert(0, str(Path(__file__).parent))
import compliancemate_api as cm

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="2065")
    ap.add_argument("--date", default="yesterday")
    a = ap.parse_args()
    cm._load_env()
    cfg = cm.STORES[a.store]
    d = cm._resolve_date(a.date)
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 cm-api-client/1.0"})
    cm.login(s, os.environ["COMPLIANCEMATE_USERNAME"], os.environ["COMPLIANCEMATE_PASSWORD"])
    out = cm.get_list_completions(s, cfg["group_id"], cfg["location_id"], d,
                                  report_type="all_list_completions")
    lists = [{"name": l["name"], "pct": l["required_pct"],
              "raw": f"{l['name']}\n{l['required_pct']}% | {l['all_pct']}%"} for l in out["lists"]]
    if not lists:
        print(f"[CM-API] no lists for {d}")
        return 1
    overall = out["overall_required_pct"] or round(sum(l["pct"] for l in lists) / len(lists))
    dest = ROOT / "data" / "raw" / "compliancemate" / a.store / d
    dest.mkdir(parents=True, exist_ok=True)
    payload = {"meta": {"date": d, "generated": datetime.now().strftime("%m/%d/%Y at %I:%M %p"),
                        "location": a.store, "status": "ok", "source": "api"},
               "overall_pct": overall, "lists": lists}
    (dest / "compliance.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[CM-API] OK {d}: {len(lists)} lists, overall {overall}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
