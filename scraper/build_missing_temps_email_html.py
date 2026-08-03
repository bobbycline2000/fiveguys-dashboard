#!/usr/bin/env python3
"""Render the attributed missing-temps report as a Five Guys branded HTML email body."""
import json, sys
from pathlib import Path

src = Path(sys.argv[1]) if len(sys.argv) > 1 else (
    Path(__file__).resolve().parent.parent / "data" / "missing_temps_checklists_4wk_attributed.json")
out = Path(sys.argv[2]) if len(sys.argv) > 2 else (
    Path(__file__).resolve().parent.parent / "data" / "missing_temps_email.html")
d = json.loads(src.read_text())

CAT = {"AM_TEMP": "AM temp", "PM_TEMP": "PM temp",
       "SHIFT_CHANGE_TEMP": "Shift-change temp", "CHECKLIST": "Checklist"}
w = d["window"]
rows = ""
for it in d["missing_items"]:
    pct = "—" if it["status"] == "MISSED" else f'{it["required_pct"]}%'
    color = "#DA291C" if it["status"] == "MISSED" else "#B8860B"
    rows += (f'<tr><td>{it["day_of_week"][:3]} {it["date"][5:]}</td>'
             f'<td>{CAT.get(it["category"], it["category"])}</td>'
             f'<td>{it["task_name"]}</td>'
             f'<td style="color:{color};font-weight:bold">{it["status"]}</td>'
             f'<td>{pct}</td><td><b>{it["manager"]}</b></td></tr>')

mgr_rows = "".join(
    f'<tr><td><b>{m}</b></td><td style="text-align:center">{c}</td></tr>'
    for m, c in d["by_manager"].items())
clean = ", ".join(x[5:] for x in d["days_fully_compliant"])

html = f"""<div style="font-family:Arial,Helvetica,sans-serif;max-width:760px;margin:0 auto;color:#14213D">
<div style="background:#DA291C;color:#fff;padding:16px 20px;border-radius:6px 6px 0 0">
<h1 style="margin:0;font-size:20px">Missing Time &amp; Temps &amp; Checklists</h1>
<div style="font-size:13px;opacity:.9">Store 2065 &nbsp;·&nbsp; {w['start']} → {w['end']} (4 weeks)</div></div>
<div style="border:1px solid #ccc;border-top:none;padding:18px 20px;border-radius:0 0 6px 6px">
<p style="font-size:15px"><b>{d['total_missing']} missed/incomplete items</b> over 28 days &nbsp;·&nbsp;
<b>{len(d['days_fully_compliant'])} fully clean days</b></p>

<div style="background:#fafaf6;border-left:3px solid #DA291C;padding:10px 14px;margin:14px 0">
<b style="color:#DA291C">The one real pattern:</b> Closing Checklist is the weak point —
missed or half-done <b>12 of 28 nights</b>. Everything else is scattered. Fix the nightly close first.</div>

<h3 style="border-bottom:2px solid #14213D;padding-bottom:4px">Accountability — misses on their shift</h3>
<table style="width:100%;border-collapse:collapse;font-size:14px" cellpadding="6">
<tr style="background:#f0f0ec"><th align="left">Manager</th><th>Misses</th></tr>{mgr_rows}</table>
<p style="font-size:12px;color:#555">Attributed from Teamworx: AM temps → AM manager · PM temps + Closing → closing manager · shift-change temps → shift-change manager (overlap days list all managers on).</p>

<h3 style="border-bottom:2px solid #14213D;padding-bottom:4px">Every missed item</h3>
<table style="width:100%;border-collapse:collapse;font-size:13px" cellpadding="5" border="0">
<tr style="background:#f0f0ec"><th align="left">Date</th><th align="left">Type</th><th align="left">Task</th><th align="left">Status</th><th align="left">Req%</th><th align="left">Manager on shift</th></tr>
{rows}</table>

<p style="font-size:13px;margin-top:14px"><b>Fully clean days:</b> {clean}</p>
<p style="font-size:12px;color:#777">Caveats: 7/11 is today (still in progress, not final). ComplianceMate reports done/not-done only — it cannot distinguish "late" from "missed." Now runs daily in the morning brief.</p>
</div></div>"""

out.write_text(html, encoding="utf-8")
print(str(out))
