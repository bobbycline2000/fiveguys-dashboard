"""Build employee directory Excel file from the handwritten list."""
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

EMPLOYEES = [
    # Rebuilt 2026-11-21 from CrunchTime punches (everyone who clocked in during
    # the last 5 weeks — scraper/build_active_roster.py) + AllianceHCM new-hire
    # phones. Status: Shift Leader / Crew / Starting (hired, not on the clock yet).
    ("Alexandra Campbell",         "(502) 926-9757", "Shift Leader"),
    ("Anthony Pirtle",             "(502) 938-5182", "Shift Leader"),
    ("Cortez Brown",               "(502) 599-4837", "Shift Leader"),
    ("Madelynn Smith",             "(502) 938-3999", "Shift Leader"),
    ("Madison Cureton",            "(502) 938-9208", "Shift Leader"),
    ("Rusul Kadhim",               "(502) 656-9660", "Shift Leader"),
    ("Vicki Lucey",                "(502) 701-9597", "Shift Leader"),
    ("Ailen Gonzalez Cardero",     "(407) 334-3088", "Crew"),
    ("Daiden Gray",                "(502) 910-0842", "Crew"),
    ("Emanuela Kamara",            "(502) 527-4717", "Crew"),
    ("Francisco Llorente Mejias",  "(407) 456-1445", "Crew"),
    ("Javeh Goodman",              "(502) 216-4460", "Crew"),
    ("Katherine Valentin",         "(502) 249-4632", "Crew"),
    ("Lidy Henry",                 "(502) 381-0680", "Crew"),
    ("Maylin Hernandez Rodriguez", "(PHONE PENDING)", "Crew"),
    ("Mykenize Milledge",          "(502) 650-2273", "Crew"),
    ("Robert Muncy Jr",            "(PHONE PENDING)", "Crew"),
    ("Rodolfo Trujillo",           "(786) 494-9911", "Crew"),
    ("Samuel Muradas",             "(305) 458-0475", "Crew"),
    ("Zack Whitten",               "(502) 422-9088", "Crew"),
    ("Hannah Dorilas",             "(PHONE PENDING)", "Starting"),
    ("Laura Logan",                "(PHONE PENDING)", "Starting"),
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


def build_pdf(path: str) -> None:
    doc = SimpleDocTemplate(
        path,
        pagesize=LETTER,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title="Employee Directory — Five Guys 2065",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "title", parent=styles["Heading1"],
        fontName="Helvetica-Bold", fontSize=16, textColor=colors.HexColor("#C8102E"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "subtitle", parent=styles["Normal"],
        fontName="Helvetica", fontSize=10, textColor=colors.HexColor("#666666"),
        spaceAfter=14,
    )

    story = [
        Paragraph("Employee Directory", title_style),
        Paragraph("Five Guys — Store 2065, Dixie Highway, Louisville KY", subtitle_style),
    ]

    data = [["Name", "Phone Number", "Role"]]
    for name, phone, status in EMPLOYEES:
        data.append([name, phone, status])

    table = Table(data, colWidths=[2.6 * inch, 1.8 * inch, 1.4 * inch], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#C8102E")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F7F7")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.25 * inch))
    story.append(Paragraph(
        f"{len(EMPLOYEES)} employees",
        ParagraphStyle("footer", parent=styles["Normal"], fontSize=9,
                       textColor=colors.HexColor("#888888"), alignment=2),
    ))

    doc.build(story)
    print(f"Wrote {path} with {len(EMPLOYEES)} rows")


if __name__ == "__main__":
    build("employee_directory.xlsx")
    build_pdf("employee_directory.pdf")
