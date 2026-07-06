#!/usr/bin/env python3
"""
Build district.html — the multi-unit dashboard — as a mirror of dashboard.html.

Instead of maintaining a second layout, this script takes the freshly wired
dashboard.html (2065's page, post wire_dashboard.py) and injects:
  1. A store-selector dropdown tab in the topbar (8 locations)
  2. CSS for the dropdown + "wired, awaiting access" blocked-card overlays
  3. JS that, when a non-2065 store is selected, fetches
     data/district/<store_id>/summary.json + schedule_analysis.json at runtime
     and overlays that store's numbers onto the same layout. Selecting 2065
     restores the native baked page.

Because district.html is regenerated from dashboard.html every daily run,
any future design change to the 2065 dashboard propagates automatically.

Run AFTER wire_dashboard.py. Exits 1 if any structural anchor is missing so
CI catches drift the same way verify_dashboard.py does.
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC  = ROOT / "dashboard.html"
OUT  = ROOT / "district.html"
CFG  = ROOT / "config" / "stores.json"

HOME_ID = "2065"
CITY = {
    "384": "New Albany, IN", "475": "Louisville, KY", "1704": "Louisville, KY",
    "1731": "Louisville, KY", "1788": "Louisville, KY", "1954": "Jeffersonville, IN",
    "2065": "Louisville, KY", "2079": "Elizabethtown, KY",
}

def build_store_list():
    reg = json.loads(CFG.read_text(encoding="utf-8"))
    stores = [{
        "id": HOME_ID, "label": "FG-2065 Dixie Highway", "name": "Dixie Highway",
        "city": CITY[HOME_ID], "target": 18.5, "home": True,
    }]
    for st in sorted(reg["stores"], key=lambda s: int(s["store_id"])):
        stores.append({
            "id": st["store_id"],
            "label": st.get("short", f"FG-{st['store_id']} {st['store_name']}"),
            "name": st["store_name"],
            "city": CITY.get(st["store_id"], ""),
            "target": st.get("labor_target_pct", 20.0),
        })
    return stores

CSS = """
/* ── Multi-unit store selector + blocked-card overlays ── */
.mu-select { position: relative; flex-shrink: 0; }
.mu-btn {
  display: flex; align-items: center; gap: 8px;
  background: var(--black); border: 1px solid var(--white-30); color: #fff;
  padding: 7px 12px; border-radius: 7px; cursor: pointer;
  font-family: 'Inter', sans-serif; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.2px;
}
.mu-btn:hover { border-color: rgba(255,255,255,0.5); }
.mu-btn svg { width: 13px; height: 13px; stroke-width: 2; }
.mu-caret { color: var(--white-60); font-size: 0.6rem; transition: transform 0.15s; }
.mu-select.open .mu-caret { transform: rotate(180deg); }
.mu-menu {
  display: none; position: absolute; top: 115%; left: 0; z-index: 90; min-width: 240px;
  background: #141414; border: 1px solid var(--white-12); border-radius: 10px;
  padding: 6px; box-shadow: 0 14px 34px rgba(0,0,0,0.55);
}
.mu-select.open .mu-menu { display: block; }
.mu-menu-item {
  display: flex; gap: 10px; align-items: center; width: 100%;
  padding: 8px 10px; background: transparent; border: none; border-radius: 7px;
  color: var(--white-90); cursor: pointer; text-align: left; font-family: 'Inter', sans-serif;
}
.mu-menu-item:hover { background: rgba(255,255,255,0.07); }
.mu-menu-item.active { background: var(--red); color: #fff; }
.mu-num { font-family: 'Barlow Condensed', sans-serif; font-weight: 800; font-size: 0.95rem; min-width: 40px; color: #fff; }
.mu-menu-item b { display: block; font-size: 0.75rem; font-weight: 600; }
.mu-menu-item small { display: block; color: var(--white-60); font-size: 0.62rem; }
.mu-menu-item.active small { color: rgba(255,255,255,0.75); }
@media (max-width: 640px) { .topbar .mu-select { display: block !important; } }

.mu-blocked { position: relative; min-height: 150px; }
.mu-blocked > *:not(.mu-note) { opacity: 0.14; filter: blur(1.5px); pointer-events: none; }
.card.collapsible.mu-blocked::after { display: none; }
.mu-note {
  position: absolute; inset: 0; z-index: 6; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 5px; text-align: center; padding: 18px;
}
.mu-note-title { font-family: 'Barlow Condensed', sans-serif; font-weight: 800; font-size: 1rem; letter-spacing: 0.5px; text-transform: uppercase; color: #fff; }
.mu-note-msg { font-size: 0.68rem; color: var(--white-60); max-width: 280px; line-height: 1.4; }
.mu-note-pill {
  font-size: 0.55rem; font-weight: 800; letter-spacing: 1.5px; padding: 3px 10px; border-radius: 20px;
  background: var(--yellow-dim); color: var(--yellow); border: 1px solid rgba(245,168,0,0.3); margin-top: 3px;
}
.mu-hide { display: none !important; }
"""

DROPDOWN_TMPL = """
      <div class="mu-select" id="muSelect">
        <button class="mu-btn" id="muBtn"><i data-lucide="store"></i><span id="muSelName">FG-2065 Dixie Highway</span><span class="mu-caret">&#9662;</span></button>
        <div class="mu-menu" id="muMenu">
{items}
        </div>
      </div>
"""

JS = """
<script>
/* ── Multi-unit store switcher (injected by build_district_dashboard.py) ── */
(function(){
  const MU_STORES = __MU_STORES__;
  const HOME = '__HOME__';
  const sel = document.getElementById('muSelect'), btn = document.getElementById('muBtn'),
        nameEl = document.getElementById('muSelName'), menu = document.getElementById('muMenu');
  btn.addEventListener('click', e => { e.stopPropagation(); sel.classList.toggle('open'); });
  document.addEventListener('click', () => sel.classList.remove('open'));
  menu.querySelectorAll('.mu-menu-item').forEach(b =>
    b.addEventListener('click', () => { sel.classList.remove('open'); muSelect(b.dataset.store); }));

  const q  = s => document.querySelector(s);
  const qa = s => Array.from(document.querySelectorAll(s));
  function set(el, html){ if(!el) return; if(el.dataset.muOrig === undefined) el.dataset.muOrig = el.innerHTML; el.innerHTML = html; }
  function hide(el){ if(el) el.classList.add('mu-hide'); }
  function block(card, title, msg, pill){
    if(!card || card.querySelector(':scope > .mu-note')) return;
    if(card.classList.contains('collapsed')){ card.dataset.muWasCollapsed = '1'; card.classList.remove('collapsed'); }
    card.classList.add('mu-blocked');
    const n = document.createElement('div'); n.className = 'mu-note';
    n.innerHTML = '<div class="mu-note-title">' + title + '</div><div class="mu-note-msg">' + msg + '</div><div class="mu-note-pill">' + (pill || 'WIRED &mdash; AWAITING ACCESS') + '</div>';
    card.appendChild(n);
  }
  function restore(){
    qa('[data-mu-orig]').forEach(el => { el.innerHTML = el.dataset.muOrig; delete el.dataset.muOrig; });
    qa('.mu-hide').forEach(el => el.classList.remove('mu-hide'));
    qa('.mu-blocked').forEach(c => {
      c.classList.remove('mu-blocked');
      const n = c.querySelector(':scope > .mu-note'); if(n) n.remove();
      if(c.dataset.muWasCollapsed){ c.classList.add('collapsed'); delete c.dataset.muWasCollapsed; }
    });
  }
  const V = (sum, k) => (sum && sum.kpis && sum.kpis[k] && sum.kpis[k].value) || '&mdash;';

  async function muSelect(id){
    try{ localStorage.setItem('mu-store', id); }catch(e){}
    const st = MU_STORES.find(s => s.id === id) || MU_STORES[0];
    nameEl.textContent = st.label;
    qa('.mu-menu-item').forEach(b => b.classList.toggle('active', b.dataset.store === st.id));
    restore();
    if (st.id === HOME) return; /* 2065 = the native wired page */

    let sum = null, sched = null;
    try{ const r = await fetch('data/district/' + st.id + '/summary.json?cb=' + Date.now()); if(r.ok) sum = await r.json(); }catch(e){}
    try{ const r = await fetch('data/district/' + st.id + '/schedule_analysis.json?cb=' + Date.now()); if(r.ok) sched = await r.json(); }catch(e){}

    /* header */
    set(q('.page-title'), st.label);
    set(q('.page-sub'), st.city + ' &nbsp;&middot;&nbsp; Multi-unit view &middot; CrunchTime week-to-date');
    set(q('.last-updated'), 'Last updated <b>' + ((sum && sum.generated) || '&mdash;') + '</b><br>Source: CrunchTime WTD');
    set(q('.store-chip .store-name'), 'Store ' + st.id);
    set(q('.store-chip .store-loc'), st.city);
    hide(q('#periodToggle'));

    /* controllables — food cost */
    set(q('.ctrl-card.food-cost .ctrl-value'), V(sum, 'food_pct'));
    hide(q('.ctrl-card.food-cost .ctrl-flag'));
    qa('.ctrl-card.food-cost .var-name').forEach(el => set(el, '&mdash;'));
    qa('.ctrl-card.food-cost .var-pct').forEach(el => set(el, ''));
    qa('.ctrl-card.food-cost .period-val').forEach(el => set(el, '&mdash;'));
    qa('.ctrl-card.food-cost .goal-tag').forEach(el => set(el, 'CrunchTime &mdash; pending'));

    /* controllables — labor */
    set(q('.ctrl-card.labor .ctrl-value'), V(sum, 'labor_pct'));
    const lraw = sum && sum.kpis && sum.kpis.labor_pct && sum.kpis.labor_pct.raw;
    const lFlag = q('.ctrl-card.labor .ctrl-flag');
    if (lFlag){ if (typeof lraw === 'number') set(lFlag, (lraw > st.target ? 'Over' : 'Under') + ' Goal (WTD)'); else hide(lFlag); }
    set(q('.ctrl-card.labor .ctrl-goal'), 'Goal: <b>' + st.target.toFixed(1) + '%</b>');
    qa('.ctrl-card.labor .ctrl-stat-val').forEach(el => set(el, '&mdash;'));
    qa('.ctrl-card.labor .period-val').forEach(el => set(el, '&mdash;'));
    qa('.ctrl-card.labor .goal-tag').forEach(el => set(el, 'Goal ' + st.target.toFixed(1) + '%'));
    hide(q('.ctrl-card.labor .ctrl-bar-row'));
    hide(q('.ctrl-card.labor .ctrl-hours-lbl'));

    /* secondary KPI cards: sales, cash O/S (repurposed), sales/guest, compliance */
    const cards = qa('.kpi-row .kpi-card');
    const kpi = (c, val, lbl, sub) => { if(!c) return;
      set(c.querySelector('.kpi-val'), val); set(c.querySelector('.kpi-lbl'), lbl);
      set(c.querySelector('.kpi-sub'), sub); set(c.querySelector('.kpi-delta'), '&nbsp;'); };
    kpi(cards[0], V(sum, 'net_sales'),   'Net Sales (WTD)',        'CrunchTime &middot; week-to-date');
    kpi(cards[1], V(sum, 'cash_os'),     'Cash Over/Short (WTD)',  'CrunchTime &middot; week-to-date');
    kpi(cards[2], V(sum, 'sales_guest'), 'Sales / Guest (WTD)',    'CrunchTime &middot; week-to-date');
    kpi(cards[3], '&mdash;',             'Compliance',             'ComplianceMate &mdash; access pending');

    /* sections wired but awaiting per-store access */
    block(q('[data-card-id="compliancemate"]'), 'ComplianceMate',
      'Store ' + st.id + ' checklists are wired to data/district/' + st.id + ' &mdash; waiting on ComplianceMate access for this location.');
    block(q('[data-card-id="secret-shop"]'), 'Secret Shop',
      'KnowledgeForce shop scores for store ' + st.id + ' are wired &mdash; waiting on account access.');
    block(q('[data-card-id="steritech"]'), 'Steritech',
      'Last-audit feed not yet connected for store ' + st.id + '.');
    block(q('[data-card-id="team-notes"]'), 'Team Notes',
      'Notes are 2065-only today. Multi-unit notes land when the daily brief covers all stores.', '2065 ONLY FOR NOW');
    block(q('[data-card-id="discounts"]'), 'Discounts &amp; Comps',
      'Par Brink reports for store ' + st.id + ' are not wired yet &mdash; 2065 gets these via email PDF pickup.');
    block(q('[data-card-id="fgu-training"]'), 'Five Guys University',
      'Training roster is pulled per-store from Schoox &mdash; store ' + st.id + ' roster not wired yet.');
    hide(q('.alerts-strip'));

    /* schedule card — real Teamworx analysis when available for this store */
    const sc = q('[data-card-id="schedule"]');
    if (sched && sched.week && (sched.per_day || []).length){
      set(sc.querySelector('.card-title'), 'Upcoming Week Schedule');
      set(sc.querySelector('.card-sub'), 'Teamworx schedule analysis &middot; week of ' + (sched.week_start || ''));
      const pill = sc.querySelector('.pill'); if(pill) set(pill, 'Labor ' + (sched.week.labor_pct || 0).toFixed(1) + '%');
      hide(sc.querySelector('.schedule-tabs')); hide(q('#shift-pm'));
      const rows = sched.per_day.map(d =>
        '<tr><td><div class="emp-name">' + (d.day || d.date || '') + '</div></td>' +
        '<td>' + (d.sched_hours != null ? d.sched_hours.toFixed(1) : '&mdash;') + '</td>' +
        '<td>$' + Math.round(d.fcst_sales || 0).toLocaleString() + '</td>' +
        '<td class="' + ((d.labor_pct || 0) > st.target ? 'var-over' : 'var-under') + '">' +
        (d.labor_pct != null ? d.labor_pct.toFixed(1) + '%' : '&mdash;') + '</td></tr>').join('');
      set(q('#shift-am'),
        '<table class="sched-table"><thead><tr><th>Day</th><th>Sched Hrs</th><th>Fcst Sales</th><th>Labor %</th></tr></thead>' +
        '<tbody>' + rows + '</tbody>' +
        '<tfoot><tr class="total-row"><td>Week</td><td>' + (sched.week.sched_hours || 0).toFixed(1) + ' hrs</td>' +
        '<td>$' + Math.round(sched.week.fcst_sales || 0).toLocaleString() + '</td>' +
        '<td>' + (sched.week.labor_pct || 0).toFixed(1) + '%</td></tr></tfoot></table>' +
        ((sched.issues || []).length ? '<div style="margin-top:10px;font-size:.7rem;color:var(--yellow)">' + sched.issues.map(i => '&#9888; ' + i).join('<br>') + '</div>' : ''));
    } else if (sched){
      set(sc.querySelector('.card-title'), 'Upcoming Week Schedule');
      set(sc.querySelector('.card-sub'), 'Teamworx schedule analysis');
      hide(sc.querySelector('.schedule-tabs')); hide(q('#shift-pm'));
      set(q('#shift-am'), '<div style="padding:14px 0;color:var(--white-60);font-size:.75rem;">No upcoming-week schedule posted in Teamworx yet for store ' + st.id + '.</div>');
    } else {
      block(sc, "Schedule", 'Teamworx location ID for store ' + st.id + ' not discovered yet &mdash; schedule analysis lights up once it is added to config/stores.json.');
    }

    /* footer */
    const fspans = qa('.footer-bar > span');
    if (fspans[0]) set(fspans[0], 'Five Guys Operations &mdash; ' + st.label + ' &mdash; Multi-Unit View');
  }

  /* boot: restore last-selected store */
  let saved = null; try{ saved = localStorage.getItem('mu-store'); }catch(e){}
  if (saved && saved !== HOME && MU_STORES.some(s => s.id === saved)) muSelect(saved);
  else qa('.mu-menu-item').forEach(b => b.classList.toggle('active', b.dataset.store === HOME));
  lucide.createIcons();
})();
</script>
"""

def main():
    html = SRC.read_text(encoding="utf-8")
    stores = build_store_list()
    missed = []

    def swap(old, new, label, count=1):
        nonlocal html
        if old not in html:
            missed.append(label)
            return
        html = html.replace(old, new, count)

    # Identity: this is the multi-unit page, not the 2065 PWA
    swap("<title>Five Guys — Store 2065 Operations</title>",
         "<title>Five Guys — Multi-Unit Operations</title>", "title")
    swap('<link rel="manifest" href="manifest.json" />', "", "manifest-link")
    swap('<meta name="apple-mobile-web-app-title" content="FG 2065" />',
         '<meta name="apple-mobile-web-app-title" content="FG Multi-Unit" />', "apple-title")
    swap('<div class="brand-name">Five Guys 2065</div>',
         '<div class="brand-name">Five Guys Multi-Unit</div>', "mobile-brand")
    swap('<div class="brand-sub">Operations Hub</div>',
         '<div class="brand-sub">Multi-Unit Hub</div>', "mobile-brand-sub")
    swap('<div class="logo-sub">Operations Hub</div>',
         '<div class="logo-sub">Multi-Unit Hub</div>', "sidebar-logo-sub")
    swap('<div class="crumb">Operations &nbsp;&rsaquo;&nbsp; <b>Overview</b></div>',
         '<div class="crumb">Operations &nbsp;&rsaquo;&nbsp; <b>Multi-Unit</b></div>', "crumb")

    # CSS
    swap("</style>", CSS + "\n</style>", "style-close")

    # Dropdown tab — first control in the topbar-right cluster
    items = "\n".join(
        f'          <button class="mu-menu-item" data-store="{s["id"]}">'
        f'<span class="mu-num">{s["id"]}</span><span><b>{s["name"]}</b><small>{s["city"]}</small></span></button>'
        for s in stores)
    swap('<div class="topbar-right">',
         '<div class="topbar-right">' + DROPDOWN_TMPL.format(items=items), "topbar-right")

    # Store switcher JS
    js = JS.replace("__MU_STORES__", json.dumps(
            [{k: s[k] for k in ("id", "label", "name", "city", "target")} for s in stores]))
    js = js.replace("__HOME__", HOME_ID)
    swap("</body>", js + "\n</body>", "body-close")

    if missed:
        print(f"FAIL: build_district_dashboard.py missed anchors: {missed}", file=sys.stderr)
        sys.exit(1)

    OUT.write_text(html, encoding="utf-8")
    print(f"district.html rebuilt from dashboard.html — {len(stores)} stores: "
          + ", ".join(s["id"] for s in stores))

if __name__ == "__main__":
    main()
