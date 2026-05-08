"""
Five Guys 2065 Secret Shopper Tracker — v2 (clean single-page-scroll layout)
- Compact column widths, fits standard screen
- Managers separated from Crew
- Only as many shop columns as actual shops in that month
"""
import json
import os
from collections import defaultdict
from datetime import date as dt
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter, column_index_from_string

RED, WHITE, OFF_WHITE = "C8102E", "FFFFFF", "F9F9F9"
DARK, DARK_GREY, MID_GREY, LIGHT_GREY = "1A1A1A", "595959", "D0D0D0", "F2F2F2"
GOLD, LIGHT_GOLD = "D4A017", "FFFBF0"
GREEN, LIGHT_GREEN = "2E7D32", "E8F5E9"
RED_LIGHT = "FDECEA"
HEADER_BG = "3B1F1F"
NAVY = "1A2A4A"
MGR_BG = "FCE7C7"  # light gold for manager rows

HERE = Path(__file__).resolve().parent
DASH_ROOT = HERE.parent
DATA_ROOT = DASH_ROOT / "data" / "raw" / "marketforce"
STORE_ID = os.environ.get("STORE_ID", "2065")
OUT = DASH_ROOT / "Shop_Tracker_2065_2026.xlsx"


def _find_latest_shops_json() -> Path:
    store_dir = DATA_ROOT / STORE_ID
    for d in sorted((x for x in store_dir.iterdir() if x.is_dir()), reverse=True):
        p = d / "shops.json"
        if p.exists():
            return p
    raise FileNotFoundError(f"No shops.json found in {store_dir}")


SHOPS_JSON = _find_latest_shops_json()
PART_JSON = DATA_ROOT / STORE_ID / "participation.json"

MANAGERS = ["Madison", "Vicki", "Kasey", "Nathan"]
MGR_DISPLAY = {
    "Madison": "Madison C.",
    "Vicki":   "Vicki L.",
    "Kasey":   "Kasey W.",
    "Nathan":  "Nathan R.",
}
CREW = [
    "Alen","Ash","Autumn","Bri","Dakayla","Divan","Francisco","Grace",
    "Jada","Jeremiah","Kable","Kayla","Kenzie","Lidy","Maylin","Mike",
    "Richard","Samuel","Zach"
]

MONTHS = {1:"January", 2:"February", 3:"March", 4:"April", 5:"May"}

def _b(c=MID_GREY):
    s = Side(border_style="thin", color=c)
    return Border(left=s, right=s, top=s, bottom=s)
def _f(c): return PatternFill("solid", start_color=c, end_color=c)
def _set(cell, value=None, bold=False, size=10, fg=DARK, bg=None,
         h="center", v="center", wrap=False, italic=False, border=True, num_fmt=None):
    if value is not None: cell.value = value
    cell.font = Font(name="Arial", bold=bold, size=size, color=fg, italic=italic)
    if bg: cell.fill = _f(bg)
    cell.alignment = Alignment(horizontal=h, vertical=v, wrap_text=wrap)
    if border: cell.border = _b()
    if num_fmt: cell.number_format = num_fmt

def score_bg(p):
    if p is None: return OFF_WHITE
    if p >= 100: return LIGHT_GREEN
    if p >= 90:  return "EFF8E8"
    if p >= 80:  return LIGHT_GOLD
    return RED_LIGHT
def score_fg(p):
    if p is None: return DARK
    if p >= 100: return GREEN
    if p >= 90:  return "4A7A0F"
    if p >= 80:  return GOLD
    return RED


def build_sheet(wb, month_num, month_name, shops, by_shop):
    ws = wb.create_sheet(month_name)
    ws.sheet_view.showGridLines = False

    n_shops = len(shops)
    # Column layout: A=#, B=Name, C..(C+n_shops-1)=shop cols, then MTD/N/$
    NAME_COL = "B"
    shop_cols = [get_column_letter(3 + i) for i in range(n_shops)]
    mtd_col   = get_column_letter(3 + n_shops)
    n_col     = get_column_letter(4 + n_shops)
    bonus_col = get_column_letter(5 + n_shops)
    last_col  = bonus_col

    # Tight widths
    ws.column_dimensions["A"].width = 4
    ws.column_dimensions[NAME_COL].width = 16
    for c in shop_cols:
        ws.column_dimensions[c].width = 7  # tight
    ws.column_dimensions[mtd_col].width = 9
    ws.column_dimensions[n_col].width = 7
    ws.column_dimensions[bonus_col].width = 10

    # Print area: fit to one page wide
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_options.horizontalCentered = True

    r = 1

    # Title
    ws.merge_cells(f"A{r}:{last_col}{r}")
    _set(ws.cell(r, 1), f"SECRET SHOPPER SCORES — {month_name.upper()} 2026",
         bold=True, size=14, fg=WHITE, bg=RED, border=False)
    ws.row_dimensions[r].height = 26
    r += 1

    # Subtitle
    ws.merge_cells(f"A{r}:{last_col}{r}")
    _set(ws.cell(r, 1),
         f"Five Guys Store 2065 · Louisville, KY · {n_shops} shop{'s' if n_shops!=1 else ''} · Source: Marketforce + CrunchTime",
         size=8, fg=DARK_GREY, bg=LIGHT_GREY, italic=True, border=False)
    ws.row_dimensions[r].height = 14
    r += 1

    # spacer
    ws.row_dimensions[r].height = 4; r += 1

    # ── Shop header rows ──
    # Row: # SHOP labels
    _set(ws.cell(r, 1), "", bg=HEADER_BG)
    _set(ws.cell(r, 2), "SHOP →", bold=True, size=9, fg=WHITE, bg=HEADER_BG, h="left")
    for i, col in enumerate(shop_cols):
        _set(ws.cell(r, column_index_from_string(col)), f"#{i+1}", bold=True, size=10, fg=WHITE, bg=RED)
    _set(ws.cell(r, column_index_from_string(mtd_col)), "AVG", bold=True, size=9, fg=WHITE, bg=HEADER_BG)
    _set(ws.cell(r, column_index_from_string(n_col)), "N", bold=True, size=9, fg=WHITE, bg=HEADER_BG)
    _set(ws.cell(r, column_index_from_string(bonus_col)), "BONUS", bold=True, size=9, fg=WHITE, bg=HEADER_BG)
    ws.row_dimensions[r].height = 18; r += 1

    # Date row
    _set(ws.cell(r, 1), "", bg=LIGHT_GREY)
    _set(ws.cell(r, 2), "Date", bold=True, size=8, fg=DARK, bg=LIGHT_GREY, h="left")
    for i, col in enumerate(shop_cols):
        d = dt.fromisoformat(shops[i]["date"]).strftime("%m/%d")
        _set(ws.cell(r, column_index_from_string(col)), d, size=8, fg=DARK, bg=LIGHT_GREY, bold=True)
    for col in [mtd_col, n_col, bonus_col]:
        _set(ws.cell(r, column_index_from_string(col)), "", bg=LIGHT_GREY)
    ws.row_dimensions[r].height = 14; r += 1

    # Meal row (L/D)
    _set(ws.cell(r, 1), "", bg=LIGHT_GREY)
    _set(ws.cell(r, 2), "Meal", bold=True, size=8, fg=DARK, bg=LIGHT_GREY, h="left")
    for i, col in enumerate(shop_cols):
        mp = shops[i]["meal_period"]
        short = "L" if mp.lower() == "lunch" else ("D" if mp.lower() == "dinner" else ("LD" if "late" in mp.lower() else mp[:2]))
        bg = LIGHT_GOLD if short == "L" else "E8EEF8"
        fg = GOLD if short == "L" else NAVY
        _set(ws.cell(r, column_index_from_string(col)), short, bold=True, size=8, fg=fg, bg=bg)
    for col in [mtd_col, n_col, bonus_col]:
        _set(ws.cell(r, column_index_from_string(col)), "", bg=LIGHT_GREY)
    ws.row_dimensions[r].height = 14; r += 1

    # Total Score % row
    score_row = r
    _set(ws.cell(r, 1), "", bg=RED_LIGHT)
    _set(ws.cell(r, 2), "Total Score", bold=True, size=9, fg=RED, bg=RED_LIGHT, h="left")
    for i, col in enumerate(shop_cols):
        pct = shops[i]["score"]
        _set(ws.cell(r, column_index_from_string(col)), pct/100,
             bold=True, size=10, fg=score_fg(pct), bg=score_bg(pct), num_fmt="0%")
    if shops:
        first, last = shop_cols[0], shop_cols[-1]
        _set(ws.cell(r, column_index_from_string(mtd_col)),
             f'=IFERROR(AVERAGE({first}{r}:{last}{r}),"")',
             bold=True, size=9, fg=DARK, bg=LIGHT_GREY, num_fmt="0%")
    for col in [n_col, bonus_col]:
        _set(ws.cell(r, column_index_from_string(col)), "", bg=RED_LIGHT)
    ws.row_dimensions[r].height = 18; r += 1

    # Sub-categories: Service, Quality, Cleanliness, Customer Sat
    cats = [("Service","service"),("Quality","quality"),("Cleanliness","cleanliness"),("Customer Sat","customer_satisfaction")]
    for label, key in cats:
        _set(ws.cell(r, 1), "", bg=OFF_WHITE)
        _set(ws.cell(r, 2), label, size=8, fg=DARK_GREY, bg=OFF_WHITE, h="left")
        for i, col in enumerate(shop_cols):
            v = shops[i].get(key)
            if v is not None:
                _set(ws.cell(r, column_index_from_string(col)), v/100,
                     size=8, fg=score_fg(v), bg=OFF_WHITE, num_fmt="0%")
            else:
                _set(ws.cell(r, column_index_from_string(col)), "", bg=OFF_WHITE)
        if shops:
            first, last = shop_cols[0], shop_cols[-1]
            _set(ws.cell(r, column_index_from_string(mtd_col)),
                 f'=IFERROR(AVERAGE({first}{r}:{last}{r}),"")',
                 size=8, fg=DARK_GREY, bg=LIGHT_GREY, num_fmt="0%")
        for col in [n_col, bonus_col]:
            _set(ws.cell(r, column_index_from_string(col)), "", bg=OFF_WHITE)
        ws.row_dimensions[r].height = 13; r += 1

    # spacer
    ws.row_dimensions[r].height = 6
    ws.merge_cells(f"A{r}:{last_col}{r}")
    ws.cell(r, 1).fill = _f(MID_GREY); r += 1

    # ── MANAGERS section ──
    ws.merge_cells(f"A{r}:{last_col}{r}")
    _set(ws.cell(r, 1), "MANAGERS",
         bold=True, size=10, fg=WHITE, bg=NAVY, h="left")
    ws.row_dimensions[r].height = 18; r += 1

    first_mgr_row = r
    for idx, emp in enumerate(MANAGERS, 1):
        display = MGR_DISPLAY.get(emp, emp)
        _set(ws.cell(r, 1), idx, size=8, fg=DARK_GREY, bg=MGR_BG)
        _set(ws.cell(r, 2), display, size=10, fg=DARK, bg=MGR_BG, h="left", bold=True)
        for i, col in enumerate(shop_cols):
            shop = shops[i]
            worked = emp in by_shop.get(shop["job_id"], [])
            val = "Y" if worked else None
            bg_cell = LIGHT_GREEN if worked else MGR_BG
            fg_cell = GREEN if worked else DARK
            _set(ws.cell(r, column_index_from_string(col)), val,
                 bold=worked, size=10, fg=fg_cell, bg=bg_cell)
        # Personal Avg
        first, last = shop_cols[0], shop_cols[-1]
        _set(ws.cell(r, column_index_from_string(mtd_col)),
             f'=IFERROR(AVERAGEIFS(${first}${score_row}:${last}${score_row},{first}{r}:{last}{r},"Y"),"")',
             bold=True, size=9, fg=DARK, bg=LIGHT_GREY, num_fmt="0%")
        _set(ws.cell(r, column_index_from_string(n_col)),
             f'=COUNTIF({first}{r}:{last}{r},"Y")',
             size=9, fg=DARK_GREY, bg=LIGHT_GREY)
        _set(ws.cell(r, column_index_from_string(bonus_col)),
             f'=SUMPRODUCT(({first}${score_row}:${last}${score_row}=1)*({first}{r}:{last}{r}="Y"))*50',
             bold=True, size=9, fg=GREEN, bg=LIGHT_GREEN, num_fmt='"$"#,##0')
        ws.row_dimensions[r].height = 17; r += 1
    last_mgr_row = r - 1

    # ── CREW section ──
    ws.row_dimensions[r].height = 6
    ws.merge_cells(f"A{r}:{last_col}{r}")
    ws.cell(r, 1).fill = _f(MID_GREY); r += 1

    ws.merge_cells(f"A{r}:{last_col}{r}")
    _set(ws.cell(r, 1), "CREW",
         bold=True, size=10, fg=WHITE, bg=HEADER_BG, h="left")
    ws.row_dimensions[r].height = 18; r += 1

    first_crew_row = r
    for idx, emp in enumerate(CREW, 1):
        bg_row = WHITE if idx % 2 == 1 else OFF_WHITE
        _set(ws.cell(r, 1), idx, size=8, fg=DARK_GREY, bg=bg_row)
        _set(ws.cell(r, 2), emp, size=10, fg=DARK, bg=bg_row, h="left")
        for i, col in enumerate(shop_cols):
            shop = shops[i]
            worked = emp in by_shop.get(shop["job_id"], [])
            val = "Y" if worked else None
            bg_cell = LIGHT_GREEN if worked else bg_row
            fg_cell = GREEN if worked else DARK
            _set(ws.cell(r, column_index_from_string(col)), val,
                 bold=worked, size=10, fg=fg_cell, bg=bg_cell)
        first, last = shop_cols[0], shop_cols[-1]
        _set(ws.cell(r, column_index_from_string(mtd_col)),
             f'=IFERROR(AVERAGEIFS(${first}${score_row}:${last}${score_row},{first}{r}:{last}{r},"Y"),"")',
             bold=True, size=9, fg=DARK, bg=LIGHT_GREY, num_fmt="0%")
        _set(ws.cell(r, column_index_from_string(n_col)),
             f'=COUNTIF({first}{r}:{last}{r},"Y")',
             size=9, fg=DARK_GREY, bg=LIGHT_GREY)
        _set(ws.cell(r, column_index_from_string(bonus_col)),
             f'=SUMPRODUCT(({first}${score_row}:${last}${score_row}=1)*({first}{r}:{last}{r}="Y"))*50',
             bold=True, size=9, fg=GREEN, bg=LIGHT_GREEN, num_fmt='"$"#,##0')
        ws.row_dimensions[r].height = 17; r += 1
    last_crew_row = r - 1

    # Total on shift row
    _set(ws.cell(r, 1), "", bg=HEADER_BG)
    _set(ws.cell(r, 2), "Total on shift", bold=True, size=8, fg=WHITE, bg=HEADER_BG, h="left")
    for col in shop_cols:
        _set(ws.cell(r, column_index_from_string(col)),
             f'=COUNTIF({col}{first_mgr_row}:{col}{last_crew_row},"Y")',
             bold=True, size=9, fg=WHITE, bg=HEADER_BG)
    _set(ws.cell(r, column_index_from_string(mtd_col)), "", bg=HEADER_BG)
    _set(ws.cell(r, column_index_from_string(n_col)),
         f'=SUM({n_col}{first_mgr_row}:{n_col}{last_crew_row})',
         bold=True, size=9, fg=WHITE, bg=HEADER_BG)
    _set(ws.cell(r, column_index_from_string(bonus_col)),
         f'=SUM({bonus_col}{first_mgr_row}:{bonus_col}{last_crew_row})',
         bold=True, size=9, fg=WHITE, bg=HEADER_BG, num_fmt='"$"#,##0')
    ws.row_dimensions[r].height = 18; r += 1

    # Footer
    ws.merge_cells(f"A{r}:{last_col}{r}")
    _set(ws.cell(r, 1),
         "Y = on shift during shop's meal window. Personal Avg = average score of shops worked. Bonus = $50 per 100% shop worked.",
         size=7, fg=DARK_GREY, bg=LIGHT_GREY, italic=True, h="left", border=False)
    ws.row_dimensions[r].height = 12


def build():
    shops_data = json.loads(SHOPS_JSON.read_text(encoding="utf-8"))
    all_shops = sorted(shops_data["shops"], key=lambda s: s["date"])
    by_month = defaultdict(list)
    for s in all_shops:
        by_month[int(s["date"][5:7])].append(s)

    by_shop = {}
    if PART_JSON.exists():
        by_shop = json.loads(PART_JSON.read_text(encoding="utf-8")).get("by_shop", {})

    wb = Workbook()
    wb.remove(wb.active)
    for m in [1,2,3,4,5]:
        shops = by_month.get(m, [])
        if not shops: continue
        build_sheet(wb, m, MONTHS[m], shops, by_shop)
    wb.save(OUT)
    print(f"Saved: {OUT}")

if __name__ == "__main__":
    build()
