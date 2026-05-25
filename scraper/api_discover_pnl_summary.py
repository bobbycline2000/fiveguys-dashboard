#!/usr/bin/env python3
"""
Capture the P&L summary POST (the call that returns COGS%/food cost rows) for a
specific Mon-Sun post-period. Logs in, opens Profit & Loss, sets the start/end
post-period combos to last completed Mon-Sun, clicks Retrieve, and dumps every
profitandloss POST (url + body + response) to data/pnl_summary_discovery.json.
"""
import os, sys, json, asyncio
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent; DATA = ROOT/"data"
env = ROOT/".env"
if env.exists():
    for line in env.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k,v=line.split("=",1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
sys.path.insert(0, str(Path(__file__).parent))
from main import NETCHEF_BASE, do_login, select_location
from scrape_cogs import _last_week_mon_sun
from api_discover_targeted import click_menuitem
from playwright.async_api import async_playwright

CAP=[]
async def main():
    s,e=_last_week_mon_sun(date.today())
    start=f"{s.month:02d}/{s.day:02d}/{s.year}"; end=f"{e.month:02d}/{e.day:02d}/{e.year}"
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True); ctx=await b.new_context(viewport={"width":1600,"height":1000}); page=await ctx.new_page()
        async def on_resp(resp):
            if "profitandloss" not in resp.url.lower(): return
            try: body=await resp.text()
            except: body=""
            CAP.append({"method":resp.request.method,"url":resp.url,"status":resp.status,
                        "req_body":(resp.request.post_data or "")[:1500],"resp_head":body[:2000],"resp_len":len(body)})
        page.on("response", on_resp)
        await page.goto(NETCHEF_BASE, wait_until="domcontentloaded", timeout=30000)
        await do_login(page); await select_location(page); await page.wait_for_timeout(4000)
        await click_menuitem(page, "Profit & Loss"); await page.wait_for_timeout(4000)
        # set start/end post-period combos via ExtJS, then fire retrieve
        res = await page.evaluate("""(args)=>{
            const [start,end]=args; const out=[];
            const combos=Ext.ComponentQuery.query('combo, combobox');
            combos.forEach(c=>{
              const st=c.getStore&&c.getStore(); if(!st)return;
              let rec=null; st.each(r=>{const v=Object.values(r.getData()).map(String);
                if(v.includes(start)){rec=r;} });
              if(rec){c.setValue(rec); c.fireEvent('select',c,[rec]); out.push('set start '+(c.name||c.fieldLabel||c.itemId));}
              let rec2=null; st.each(r=>{const v=Object.values(r.getData()).map(String); if(v.includes(end)){rec2=r;} });
              if(rec2){/*end combo*/ if((c.name||'').toLowerCase().includes('end')||(c.fieldLabel||'').toLowerCase().includes('end')){c.setValue(rec2);c.fireEvent('select',c,[rec2]);out.push('set end');}}
            });
            // click retrieve/run
            const btns=Ext.ComponentQuery.query('button');
            const r=btns.find(x=>/retrieve|run|go|apply/i.test((x.text||'')));
            if(r){r.fireEvent('click',r); out.push('clicked '+r.text);}
            return out;
        }""", [start,end])
        print("extjs:", res)
        await page.wait_for_timeout(7000)
        await b.close()
    (DATA/"pnl_summary_discovery.json").write_text(json.dumps(CAP,indent=2))
    print(f"period {start} -> {end}; captured {len(CAP)} profitandloss calls")
    for c in CAP: print(f"  {c['method']} {c['status']} {c['url'][:90]} ({c['resp_len']}b) body={c['req_body'][:120]}")

asyncio.run(main())
