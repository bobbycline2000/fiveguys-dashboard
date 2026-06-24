#!/usr/bin/env python3
"""
Lights-out Monday tip entry — HEADLESS BROWSER path (the one that actually persists).

WHY THIS EXISTS (root cause found 2026-06-24):
  CrunchTime's /resource/labor-details/supplemental-wages/save only persists rows
  into a session WIP that exists ONLY while the Labor Detail page is loaded in
  editMode in a real browser. A pure-requests cron (api_enter_tips.py) POSTs /save
  + /prepare + /validate, all return 200/"success", but NOTHING persists — the WIP
  was never opened by a live page. This ghost recurred 5/10, 6/8, 6/24.

  The fix is to do headlessly EXACTLY what works by hand:
    1. log in (reuse api_discover.do_login)
    2. open  next.ct#LaborDetails?weekEndingDate=<Sun>&editMode=true   (page-load
       fires /labor-details/prepare → opens the WIP)
    3. if "previous unsaved data" alert → Continue
    4. in-page idempotent upsert loop against /supplemental-wages/save
       (update existing rows in place by composite id; append only missing;
        zero any stale non-target rows — never creates duplicates)
    5. click the disk-save icon (.md-icon-save) → "Labor Adjustments Alert" → Continue
       (this is the real commit)
    6. reopen in View mode (editMode=false), read the rendered grid, assert
       count == #employees and total == sum_payout within rounding.

  READS (Charged Tips + per-employee hours + payout math) are reused from
  api_enter_tips.py via cookie-auth requests — those work fine cold. Only the
  WRITE needs the browser.

Usage:
  python scraper/enter_tips_browser.py                 # auto prior Mon-Sun, LIVE
  python scraper/enter_tips_browser.py 06/21/2026       # explicit week ending, LIVE
  python scraper/enter_tips_browser.py 06/21/2026 dry   # compute + snapshot only, no write
"""
import asyncio
import datetime as dt
import json
import sys
from pathlib import Path

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# Reuse the proven login + all the read/compute logic.
sys.path.insert(0, str(Path(__file__).parent))
import api_enter_tips as T          # ensure_session, pull_charged_tips, pull_time_detail, compute_payouts, fmt, prior_week_mon_sun, build_tip_sheet_xlsx
import api_discover as D            # do_login, USERNAME, PASSWORD

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
NETCHEF = "https://fiveguysfr77.net-chef.com"
SW_ID = 12292  # Credit Card Tip


# ── in-page JS (literal braces — NOT an f-string) ───────────────────────────
# Reads EXISTING rows from the loaded Ext grid store (reliable; the
# /supplemental-wages fetch returns the empty edit-session WIP, not committed
# rows). Returns {error:...} if the store can't be found — caller ABORTS rather
# than blind-appending (never create duplicates on a read failure).
JS_UPSERT = r"""
async (P) => {
  const {mon, sun, sw, targets} = P;
  const H = {"Content-Type":"application/json","X-Requested-With":"XMLHttpRequest","Accept":"application/json"};
  if (typeof Ext === 'undefined') return {error: 'Ext not loaded'};
  // locate the supplemental-wages grid store and read full row objects
  const grids = Ext.ComponentQuery.query('labordetails-supplementalwagesgrid, grid, gridpanel');
  let store = null;
  for (const g of grids) {
    const s = g.getStore && g.getStore();
    if (!s || !s.each) continue;
    if (g.xtype === 'labordetails-supplementalwagesgrid') { store = s; break; }
    let hit = false; s.each(r => { const d = (r.getData ? r.getData() : r.data) || {}; if ('swLumpSumVal' in d) hit = true; });
    if (hit) { store = s; break; }
  }
  if (!store) return {error: 'supplemental-wages grid store not found'};
  const existing = [];
  store.each(r => { const d = (r.getData ? r.getData() : r.data) || {}; if (d.swId === sw) existing.push(d); });
  const byEmp = {};
  existing.forEach(r => { (byEmp[r.employeeId] = byEmp[r.employeeId] || []).push(r); });

  const saveUrl = `/resource/labor-details/supplemental-wages/save?operatingDate=${encodeURIComponent(mon)}&weekEndingDate=${encodeURIComponent(sun)}`;
  const post = async (body) => {
    const r = await fetch(saveUrl, {method:"POST",credentials:"include",headers:H,body:JSON.stringify(body)});
    const t = await r.text();
    return r.status === 200 && (t.trim() === "" || (() => { try { return JSON.parse(t).success !== false; } catch(e){ return false; } })());
  };
  const mkNew = (eid,pos,lump) => ({
    id:-1, employeeId:eid, employeeNumber:"", employeeName:"", employeeFullName:"",
    employeePositionId:pos, employeePositionName:"", terminationDate:null, terminated:false,
    swId:sw, swDescription:"", swLumpSumVal:Math.round(lump*100)/100, viewOnly:false,
    mondayHoursAdjusted:0,tuesdayHoursAdjusted:0,wednesdayHoursAdjusted:0,thursdayHoursAdjusted:0,
    fridayHoursAdjusted:0,saturdayHoursAdjusted:0,sundayHoursAdjusted:0,
    mondayDailyLumpSum:0,tuesdayDailyLumpSum:0,wednesdayDailyLumpSum:0,thursdayDailyLumpSum:0,
    fridayDailyLumpSum:0,saturdayDailyLumpSum:0,sundayDailyLumpSum:0,
    detailsList:[], altLocationFlag:true, deletedPositionFlag:false, reviewed:true, reviewUser:""
  });

  let appended=0, updated=0, zeroed=0; const failed=[];
  const targetIds = new Set(targets.map(t => String(t.employeeId)));
  for (const t of targets) {
    const ex = byEmp[t.employeeId] || byEmp[String(t.employeeId)] || [];
    if (ex.length) {
      for (let i=0; i<ex.length; i++) {
        const want = (i===0) ? t.payout : 0;
        if (Math.abs((parseFloat(ex[i].swLumpSumVal)||0) - want) < 0.001) continue;
        const ok = await post([Object.assign({}, ex[i], {swLumpSumVal: Math.round(want*100)/100})]);
        if (ok) { (i===0) ? updated++ : zeroed++; } else failed.push(t.name + " (update)");
        await new Promise(s => setTimeout(s, 180));
      }
    } else {
      const ok = await post([mkNew(t.employeeId, t.positionCode, t.payout)]);
      if (ok) appended++; else failed.push(t.name + " (new)");
      await new Promise(s => setTimeout(s, 180));
    }
  }
  // zero stale non-target rows so nobody outside the pool gets paid
  for (const eid in byEmp) {
    if (targetIds.has(String(eid))) continue;
    for (const r of byEmp[eid]) {
      if (Math.abs(parseFloat(r.swLumpSumVal)||0) < 0.001) continue;
      const ok = await post([Object.assign({}, r, {swLumpSumVal:0})]);
      if (ok) zeroed++; else failed.push("stale-" + eid);
      await new Promise(s => setTimeout(s, 180));
    }
  }
  return {existing: existing.length, appended, updated, zeroed, failed};
}
"""

JS_CLICK_SAVE = r"""
() => {
  const e = document.querySelector('.md-icon-save');
  if (!e) return "no-save-icon";
  const r = e.getBoundingClientRect();
  ['mouseover','mousedown','mouseup','click'].forEach(t =>
    e.dispatchEvent(new MouseEvent(t, {bubbles:true,cancelable:true,view:window,clientX:r.x+r.width/2,clientY:r.y+r.height/2})));
  return "clicked-save";
}
"""

JS_VERIFY = r"""
(P) => {
  const {sw} = P;
  if (typeof Ext === 'undefined') return {error: 'Ext not loaded'};
  const grids = Ext.ComponentQuery.query('labordetails-supplementalwagesgrid, grid, gridpanel');
  let store = null;
  for (const g of grids) {
    const s = g.getStore && g.getStore();
    if (!s || !s.each) continue;
    if (g.xtype === 'labordetails-supplementalwagesgrid') { store = s; break; }
    let hit = false; s.each(r => { const d = (r.getData ? r.getData() : r.data) || {}; if ('swLumpSumVal' in d) hit = true; });
    if (hit) { store = s; break; }
  }
  if (!store) return {error: 'verify: grid store not found'};
  let total = 0; const seen = {};
  store.each(r => {
    const d = (r.getData ? r.getData() : r.data) || {};
    if (d.swId !== sw) return;
    const amt = parseFloat(d.swLumpSumVal) || 0;
    if (amt > 0) { total += amt; seen[d.employeeId] = (seen[d.employeeId]||0)+1; }
  });
  const dups = Object.entries(seen).filter(([k,v]) => v > 1);
  return {paidRows: Object.values(seen).reduce((a,b)=>a+b,0), unique: Object.keys(seen).length,
          total: Math.round(total*100)/100, dups};
}
"""


async def click_visible_text(page, text, timeout=4000):
    """Click the first visible element whose trimmed text == `text`. Returns True if clicked."""
    try:
        res = await page.evaluate(
            """(label) => {
                const H = window.innerHeight, W = window.innerWidth;
                const els = [...document.querySelectorAll('a,button,span,div')].filter(el => {
                    const t = (el.innerText||el.textContent||'').trim();
                    const r = el.getBoundingClientRect();
                    return t === label && r.width>0 && r.height>0 && r.width<400 && r.top>0 && r.top<H && r.left>0 && r.left<W;
                });
                if (!els.length) return false;
                const c = els[els.length-1];
                const r = c.getBoundingClientRect();
                ['mouseover','mousedown','mouseup','click'].forEach(tp =>
                    c.dispatchEvent(new MouseEvent(tp,{bubbles:true,cancelable:true,view:window,clientX:r.x+r.width/2,clientY:r.y+r.height/2})));
                return true;
            }""", text)
        return bool(res)
    except Exception as e:
        print(f"  click_visible_text({text!r}) error: {e}")
        return False


async def _authed(page):
    """True only when an authenticated API probe returns 200 JSON. Ext being
    defined is NOT proof of login — Ext loads on the login page too."""
    try:
        return await page.evaluate("""async () => {
            try {
                const r = await fetch('/resource/recommended-actions/status', {credentials:'include'});
                return r.status === 200 && /json/i.test(r.headers.get('content-type') || '');
            } catch (e) { return false; }
        }""")
    except Exception:
        return False


async def robust_login(page):
    """Sign in for real. CrunchTime needs the credentials filled AND the Sign In
    button clicked; Enter alone doesn't submit. Gate on an authenticated API probe,
    not on Ext presence (Ext is loaded on the login page too — the false-positive
    that left the headless context unauthenticated)."""
    await page.goto(D.NETCHEF_BASE, wait_until="domcontentloaded", timeout=30_000)
    await page.wait_for_timeout(2000)
    for attempt in range(10):
        if await _authed(page):
            print(f"[browser] authenticated (probe OK) after {attempt} attempts")
            await page.wait_for_timeout(1500)
            return True
        try:
            if await page.locator('input[type="password"]').count():
                await page.fill('input[type="text"]', D.USERNAME)
                await page.fill('input[type="password"]', D.PASSWORD)
        except Exception:
            pass
        await D._click_sign_in(page)
        try:
            await page.keyboard.press("Enter")
        except Exception:
            pass
        await page.wait_for_timeout(3500)
    raise RuntimeError("login failed — authenticated probe never succeeded")


async def wait_for_sw_grid(page, timeout_ms=20000):
    """Wait until the supplemental-wages Ext grid store exists (rows may be 0)."""
    step = 0
    while step < timeout_ms:
        ready = await page.evaluate("""() => {
            if (typeof Ext === 'undefined') return false;
            const gs = Ext.ComponentQuery.query('labordetails-supplementalwagesgrid');
            return gs.length > 0 && !!gs[0].getStore;
        }""")
        if ready:
            return True
        await page.wait_for_timeout(1000)
        step += 1000
    return False


async def enter_via_browser(mon, sun, targets, expected_total):
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1680, "height": 950})
        page = await ctx.new_page()
        try:
            await robust_login(page)

            # Route to the week in edit mode WITHIN the live SPA (same effect as
            # clicking the Labor Summary "Edit" link). Two hard-won constraints:
            #   - NEVER page.goto(index.ct...) — it logs the session out (4/20 finding).
            #   - A full page.goto to next.ct#LaborDetails does NOT route in headless;
            #     the SPA router only fires on an in-document hashchange. So we land on
            #     the next.ct shell (where login leaves us) and set location.hash, which
            #     triggers the LaborDetails controller → /prepare → opens the WIP.
            sundate = T.fmt(sun)
            cur = page.url or ""
            if "next.ct" not in cur:
                await page.goto(f"{NETCHEF}/ncext/next.ct", wait_until="domcontentloaded", timeout=30_000)
                await page.wait_for_timeout(4000)
            await page.evaluate("(h) => { window.location.hash = h; }",
                                f"LaborDetails?weekEndingDate={sundate}&editMode=true")
            print(f"[browser] SPA-routed to LaborDetails editMode for WE {sundate}")
            await page.wait_for_timeout(6000)

            # "Net-Chef detected previous Labor Detail data that was not saved" → Continue
            if await click_visible_text(page, "Continue"):
                print("[browser] dismissed unsaved-data alert (Continue)")
                await page.wait_for_timeout(3000)

            # Make sure the Supplemental Wages grid is loaded before reading it.
            await click_visible_text(page, "Supplemental Wages")
            await page.wait_for_timeout(2500)
            if not await wait_for_sw_grid(page):
                await page.screenshot(path=str(DATA / "api_discover_tipdebug_grid.png"))
                raise RuntimeError("supplemental-wages grid never loaded")

            # Idempotent upsert loop (runs inside the live edit session).
            res = await page.evaluate(JS_UPSERT, {
                "mon": T.fmt(mon), "sun": T.fmt(sun), "sw": SW_ID, "targets": targets})
            if res.get("error"):
                raise RuntimeError(f"upsert read failed: {res['error']} — ABORTED (no write, no dup risk)")
            print(f"[browser] upsert: existing={res['existing']} appended={res['appended']} "
                  f"updated={res['updated']} zeroed={res['zeroed']} failed={res['failed']}")
            await page.wait_for_timeout(1500)

            # Commit: disk-save → Labor Adjustments Alert → Continue
            clicked = await page.evaluate(JS_CLICK_SAVE)
            print(f"[browser] save icon: {clicked}")
            await page.wait_for_timeout(2500)
            if await click_visible_text(page, "Continue"):
                print("[browser] committed (Labor Adjustments Alert → Continue)")
            await page.wait_for_timeout(5000)

            # VERIFY in a fresh read-only view.
            vurl = f"{NETCHEF}/ncext/next.ct#LaborDetails?weekEndingDate={T.fmt(sun)}&editMode=false"
            await page.goto(vurl, wait_until="domcontentloaded", timeout=30_000)
            await page.wait_for_timeout(5000)
            await click_visible_text(page, "Supplemental Wages")
            await page.wait_for_timeout(2500)
            await wait_for_sw_grid(page)
            v = await page.evaluate(JS_VERIFY, {"sw": SW_ID})
            if v.get("error"):
                raise RuntimeError(f"verify read failed: {v['error']}")
            print(f"[verify] paidRows={v['paidRows']} unique={v['unique']} "
                  f"total=${v['total']:.2f} (expected ${expected_total:.2f}) dups={v['dups']}")

            ok = (v["unique"] == len(targets)
                  and not v["dups"]
                  and abs(v["total"] - expected_total) <= 0.05)
            await page.screenshot(path=str(DATA / f"tips_verify_{sun.strftime('%Y_%m_%d')}.png"))
            return ok, v, res
        finally:
            await browser.close()


def main():
    args = sys.argv[1:]
    dry = "dry" in args
    explicit = next((a for a in args if "/" in a), None)
    if explicit:
        sun = dt.datetime.strptime(explicit, "%m/%d/%Y").date()
        mon = sun - dt.timedelta(days=6)
    else:
        mon, sun = T.prior_week_mon_sun()
    print(f"=== KY-2065 tip entry (BROWSER) — WE {T.fmt(sun)} (Mon {T.fmt(mon)} → Sun {T.fmt(sun)}) ===")
    print(f"  mode: {'DRY (no write)' if dry else 'LIVE'}")

    # ── READS (cookie-auth requests; these work cold) ──
    jar = T.ensure_session()
    if not T.labor_reviewed(jar, sun):
        print(f"[prereq] WARNING: WE {T.fmt(sun)} labor not Reviewed — proceeding; validate hours look right.")
    charged, _ = T.pull_charged_tips(jar, mon, sun)
    print(f"[tips] Charged Tips Mon-Sun: ${charged:.2f}")
    employees = T.pull_time_detail(jar, mon, sun)
    payouts, pool_hrs, rate, sum_payout = T.compute_payouts(employees, charged)
    print(f"[pool] {len(payouts)} employees, {pool_hrs:.2f} hrs, ${rate:.4f}/hr, "
          f"sum ${sum_payout:.2f} (delta ${sum_payout - charged:+.2f})")

    # snapshot + xlsx (same artifacts as the requests path)
    snap = DATA / f"tips_we_{sun.strftime('%Y_%m_%d')}_snapshot.json"
    snap.write_text(json.dumps({
        "weekEnding": T.fmt(sun), "weekStart": T.fmt(mon), "chargedTips": charged,
        "poolHours": pool_hrs, "tipsPerHour": rate, "sumPayout": sum_payout,
        "delta": round(sum_payout - charged, 2), "payouts": payouts,
    }, indent=2, default=str))
    print(f"[snapshot] {snap}")
    try:
        T.build_tip_sheet_xlsx(sun, charged, payouts, pool_hrs, rate,
                               DATA / "tip-sheets" / f"tip-sheet-2065-WE-{sun.strftime('%m-%d')}.xlsx")
    except Exception as e:
        print(f"[xlsx] skip: {e}")

    targets = [{"name": n, "employeeId": payouts[n]["employeeId"],
                "positionCode": payouts[n]["positionCode"], "payout": payouts[n]["payout"]}
               for n in sorted(payouts)]

    if dry:
        for t in targets:
            print(f"   {t['name']:<35} emp {t['employeeId']:>9} pos {t['positionCode']} ${t['payout']:>8.2f}")
        print("[dry] no write performed.")
        return 0

    ok, v, res = asyncio.run(enter_via_browser(mon, sun, targets, sum_payout))

    # log
    log = ROOT.parent.parent / "_memory" / "tip-entry-log.md"
    if log.exists():
        line = (f"| {T.fmt(sun)} | ${charged:.2f} | {pool_hrs:.2f} | ${rate:.4f} | "
                f"${v['total']:.2f} | {v['unique']} | enter_tips_browser.py (headless) | "
                f"{'VERIFIED' if ok else 'VERIFY FAILED'}: {v['unique']}/{len(targets)} rows, "
                f"dups={v['dups']}, lights-out browser path. |\n")
        with log.open("a", encoding="utf-8") as f:
            f.write(line)

    if not ok:
        print("[FATAL] verification failed — review before posting.")
        return 1
    print(f"[OK] WE {T.fmt(sun)}: {v['unique']} rows, ${v['total']:.2f}, 0 dups — persisted & verified.")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main())
