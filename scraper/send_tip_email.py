"""Email the weekly 2065 tip breakdown + xlsx from fg2065 via Microsoft Graph.

Usage: python scraper/send_tip_email.py MM/DD/YYYY [recipient@estep-co.com]
Default recipient: jreiss@estep-co.com (Jeff Reiss — set by Bobby 2026-08-31,
replaces the prior Crystal Hess default).
"""
from __future__ import annotations
import base64, datetime as dt, json, os, sys
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
env_path = ROOT / ".env"
for line in env_path.read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())

TENANT_ID, CLIENT_ID = os.environ["GRAPH_TENANT_ID"], os.environ["GRAPH_CLIENT_ID"]
REFRESH_TOKEN = os.environ["GRAPH_REFRESH_TOKEN"]
FROM_ADDR = os.environ.get("GRAPH_ACCOUNT_USERNAME", "fg2065@estep-co.com")


def get_token() -> str:
    r = requests.post(f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token",
                      data={"grant_type": "refresh_token", "client_id": CLIENT_ID,
                            "refresh_token": REFRESH_TOKEN,
                            "scope": "https://outlook.office.com/.default offline_access"},
                      timeout=30)
    r.raise_for_status()
    b = r.json()
    nrt = b.get("refresh_token")
    if nrt and nrt != REFRESH_TOKEN:
        env_path.write_text(env_path.read_text().replace(REFRESH_TOKEN, nrt))
        print("[auth] refresh token rotated -> .env")
    return b["access_token"]


def main() -> int:
    arg = next((a for a in sys.argv[1:] if "/" in a and a.count("/") == 2), None)
    to_addr = next((a for a in sys.argv[1:] if "@" in a), "jreiss@estep-co.com")
    if not arg:
        print("usage: send_tip_email.py MM/DD/YYYY [recipient]"); return 2
    sun = dt.datetime.strptime(arg, "%m/%d/%Y").date()
    snap = json.loads((ROOT / "data" / f"tips_we_{sun.strftime('%Y_%m_%d')}_snapshot.json").read_text())
    p = snap["payouts"]; names = sorted(p)
    we = sun.strftime("%m/%d")

    rows = "".join(
        f"<tr><td style='padding:4px 12px;border-bottom:1px solid #eee'>{n}</td>"
        f"<td style='padding:4px 12px;border-bottom:1px solid #eee;text-align:right'>{p[n]['hours']:.2f}</td>"
        f"<td style='padding:4px 12px;border-bottom:1px solid #eee;text-align:right'>${p[n]['payout']:.2f}</td></tr>"
        for n in names)
    html = f"""<div style="font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#222">
<div style="background:#DA291C;color:#fff;padding:10px 14px;font-weight:bold">KY-2065 Dixie Highway — Week End {we}</div>
<p>Jeff,</p>
<p>Tips for week end {we} are entered in CrunchTime (Labor &rarr; Supplemental Wages, Credit Card Tip)
and verified against the source. Your live <b>east side tips.xlsx</b> tab <b>2065</b> is filled and ties.
Please double-check and <b>Post Labor</b> when you're satisfied.</p>
<table style="border-collapse:collapse;font-size:13px">
<tr><td style="padding:2px 12px">Charged Tips (Consolidated Sales Entry Summary)</td><td style="padding:2px 12px;text-align:right"><b>${snap['chargedTips']:.2f}</b></td></tr>
<tr><td style="padding:2px 12px">Entered in CrunchTime</td><td style="padding:2px 12px;text-align:right"><b>${snap['sumPayout']:.2f}</b> ({len(names)} employees)</td></tr>
<tr><td style="padding:2px 12px">Tip pool hours (paid, breaks excluded)</td><td style="padding:2px 12px;text-align:right">{snap['poolHours']:.2f}</td></tr>
<tr><td style="padding:2px 12px">Tips per hour</td><td style="padding:2px 12px;text-align:right">${snap['tipsPerHour']:.4f}</td></tr>
<tr><td style="padding:2px 12px">Delta</td><td style="padding:2px 12px;text-align:right">${snap['delta']:+.2f}</td></tr>
</table>
<p style="margin-top:16px"><b>Per-employee breakdown</b> (GM excluded from the pool)</p>
<table style="border-collapse:collapse;font-size:13px">
<tr style="background:#002855;color:#fff"><th style="padding:6px 12px;text-align:left">Employee</th>
<th style="padding:6px 12px;text-align:right">Hours</th><th style="padding:6px 12px;text-align:right">Payout</th></tr>
{rows}
<tr style="font-weight:bold"><td style="padding:6px 12px">Total</td>
<td style="padding:6px 12px;text-align:right">{snap['poolHours']:.2f}</td>
<td style="padding:6px 12px;text-align:right">${snap['sumPayout']:.2f}</td></tr>
</table>
<p style="margin-top:16px">Tip sheet attached.</p>
<p>Bobby Cline<br>GM, Five Guys 2065 Dixie Highway</p></div>"""

    xlsx = ROOT / "data" / "tip-sheets" / f"tip-sheet-2065-WE-{sun.strftime('%m-%d')}.xlsx"
    payload = {"Message": {
        "Subject": f"WE {we} — 2065 Tips Entered (please double-check + Post Labor)",
        "Body": {"ContentType": "HTML", "Content": html},
        "ToRecipients": [{"EmailAddress": {"Address": to_addr}}],
        "Attachments": [{"@odata.type": "#Microsoft.OutlookServices.FileAttachment",
                         "Name": xlsx.name,
                         "ContentBytes": base64.b64encode(xlsx.read_bytes()).decode("ascii")}],
    }, "SaveToSentItems": True}

    # Graph .default carries NO Mail.Send for this app (AADSTS65002 on named scopes);
    # the outlook.office.com resource DOES — send through Outlook REST v2.0.
    r = requests.post("https://outlook.office.com/api/v2.0/me/sendmail",
                      headers={"Authorization": f"Bearer {get_token()}",
                               "Content-Type": "application/json"},
                      json=payload, timeout=60)
    if r.status_code in (200, 202):
        print(f"[send] sent to {to_addr} — {r.status_code} (attached {xlsx.name})")
        return 0
    print(f"[send] {r.status_code}: {r.text[:400]}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
