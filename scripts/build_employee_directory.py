"""Build employee directory Excel file from the handwritten list."""
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

EMPLOYEES = [
    ("Alen",      "(407) 334-3088", "Active"),
    ("Ash",       "(502) 554-4833", "Active"),
    ("Autumn",    "(502) 656-2133", "Active"),
    ("Bri",       "(502) 202-4126", "Active"),
    ("Divan",     "(502) 821-9406", "Active"),
    ("Francisco", "(407) 456-1445", "Active"),
    ("Grace",     "(502) 527-1477", "Active"),
    ("Jada",      "(502) 821-5962", "Active"),
    ("Jeremiah",  "(502) 498-9401", "Active"),
    ("Kable",     "(502) 606-3088", "Active"),
    ("Kasey",     "(502) 884-2273", "Active"),
    ("Kayla",     "(502) 531-8704", "Active"),
    ("Kenzie",    "(502) 650-2273", "Active"),
    ("Lidy",      "(502) 381-0680", "Active"),
    ("Madison",   "(502) 438-7200", "Active"),
    ("Maylin",    "(502) 803-1973", "Active"),
    ("Mike",      "(502) 281-8177", "Active"),
    ("Nathan",    "(502) 693-8371", "Active"),
    ("Richard",   "(270) 874-0655", "Active"),
    ("Samuel",    "(502) 724-2384", "Active"),
    ("Vicki",     "(502) 701-9597", "Active"),
]


def build(path: str) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Employees"

    headers = ["Name", "Phone Number", "Status"]
    ws.append(headers)

    header_font = Font(bold=True, color="FFFFFF", size=12)
    header_fill = PatternFill(start_color="C8102E", end_color="C8102E", fill_type="solid")
    header_align = Alignment(horizontal="left", vertical="center")
    thin = Side(border_style="thin", color="CCCCCC")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    for col_idx, _ in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = border

    for row in EMPLOYEES:
        ws.append(row)

    last_row = ws.max_row
    for r in range(2, last_row + 1):
        for c in range(1, len(headers) + 1):
            cell = ws.cell(row=r, column=c)
            cell.alignment = Alignment(horizontal="left", vertical="center")
            cell.border = border
        if ws.cell(row=r, column=3).value and "Crossed out" in ws.cell(row=r, column=3).value:
            grey = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
            for c in range(1, len(headers) + 1):
                ws.cell(row=r, column=c).fill = grey
                ws.cell(row=r, column=c).font = Font(italic=True, color="777777")

    widths = {1: 16, 2: 20, 3: 38}
    for col, w in widths.items():
        ws.column_dimensions[get_column_letter(col)].width = w

    ws.row_dimensions[1].height = 22
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{last_row}"

    wb.save(path)
    print(f"Wrote {path} with {len(EMPLOYEES)} rows")


if __name__ == "__main__":
    build("employee_directory.xlsx")
