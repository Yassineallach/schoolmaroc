#!/usr/bin/env python3
"""Builds Weekly Planner Pro (.xlsx, macro-free, 8 tabs).

Usage: python3 build_weekly_planner.py OUTPUT.xlsx
Colours and fonts follow ../../design-system/design-tokens.json.
"""
import sys
import datetime as dt

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import FormulaRule, DataBarRule
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.workbook.properties import CalcProperties
from openpyxl.utils import get_column_letter as CL

OUT = sys.argv[1] if len(sys.argv) > 1 else "Weekly_Planner_Pro.xlsx"

NAVY = "17243A"; MIDNIGHT = "223653"; BLUE = "4169E1"; SOFT_BLUE = "EAF1FB"
TEAL = "24A89A"; SOFT_TEAL = "E2F4F0"; LAV = "8B7BE8"; SOFT_LAV = "F0EDFC"
BG = "F5F7FA"; WHITE = "FFFFFF"; LGRAY = "E9EDF2"; MGRAY = "9AA5B1"
DARK = "263445"; SEC = "6B7785"; BORDER = "DCE3EA"
SUCCESS = "279B70"; SUCCESS_BG = "E5F5ED"; WARN = "E9A23B"; WARN_BG = "FFF3DC"
DANGER = "DC5B64"; DANGER_BG = "FCEAEC"; INFO = "4D8FD8"; INFO_BG = "EAF2FC"

SIDE = Side(style="thin", color=BORDER)
BOX = Border(left=SIDE, right=SIDE, top=SIDE, bottom=SIDE)
FMT_DATE = "dd-mmm-yyyy"


def fill(c):
    return PatternFill("solid", start_color=c, end_color=c)


def fnt(size=9, bold=False, color=DARK):
    return Font(name="Arial", size=size, bold=bold, color=color)


def D(y, m, d):
    return dt.date(y, m, d)


def band(ws, row, c1, c2, text, bg=NAVY, color=WHITE, size=16):
    for c in range(c1, c2 + 1):
        ws.cell(row, c).fill = fill(bg)
    cell = ws.cell(row, c1, text)
    cell.font = fnt(size, True, color)
    cell.alignment = Alignment(vertical="center", indent=1)
    ws.row_dimensions[row].height = 30 if size >= 14 else 22


def page(ws, title, sub, tab, band_to, demo=False):
    ws.sheet_view.showGridLines = False
    ws.sheet_properties.tabColor = tab
    ws.column_dimensions["A"].width = 2
    band(ws, 1, 2, band_to, title)
    for c in range(2, band_to + 1):
        ws.cell(2, c).fill = fill(SOFT_BLUE)
    ws["B2"] = sub
    ws["B2"].font = fnt(9, False, MIDNIGHT)
    if demo:
        ws["B3"] = "DEMO DATA: sample entries are included. Clear the blue cells to start your own."
        ws["B3"].font = fnt(9, True, INFO)


def inp(ws, cell, value=None, fmt=None, align=None):
    c = ws[cell]
    if value is not None:
        c.value = value
    c.fill = fill(SOFT_BLUE)
    c.border = BOX
    c.font = fnt(9)
    c.alignment = Alignment(vertical="center", wrap_text=True, horizontal=align)
    if fmt:
        c.number_format = fmt


def calc(ws, cell, formula, fmt=None, bold=False, align="center", bg=LGRAY):
    c = ws[cell]
    c.value = formula
    c.fill = fill(bg)
    c.border = BOX
    c.font = fnt(9, bold, DARK)
    c.alignment = Alignment(vertical="center", horizontal=align)
    if fmt:
        c.number_format = fmt


def label(ws, cell, text, bold=True):
    ws[cell] = text
    ws[cell].font = fnt(9, bold, DARK if bold else SEC)
    ws[cell].alignment = Alignment(vertical="center")


def merge_inp(ws, rng, value=None, fmt=None, height=None, align=None):
    first = rng.split(":")[0]
    ws.merge_cells(rng)
    for row in ws[rng]:
        for c in row:
            c.fill = fill(SOFT_BLUE)
            c.border = BOX
    inp(ws, first, value, fmt, align)
    if height:
        ws.row_dimensions[ws[first].row].height = height


def merge_calc(ws, rng, formula, fmt=None, bold=False, align="center"):
    first = rng.split(":")[0]
    ws.merge_cells(rng)
    for row in ws[rng]:
        for c in row:
            c.fill = fill(LGRAY)
            c.border = BOX
    calc(ws, first, formula, fmt, bold, align)


def dv_list(ws, rng, source):
    d = DataValidation(type="list", formula1=source, allow_blank=True)
    d.error = "Pick a value from the list (edit lists on Setup)."
    ws.add_data_validation(d)
    d.add(rng)


def cf(ws, rng, formula, bg, color=None, bold=False):
    kw = {"fill": fill(bg)}
    if color or bold:
        kw["font"] = Font(color=color, bold=bold) if color else Font(bold=bold)
    ws.conditional_formatting.add(rng, FormulaRule(formula=[formula], stopIfTrue=True, **kw))


def legend(ws, row, col):
    items = [("Input", SOFT_BLUE), ("Calculated", LGRAY), ("Positive", SOFT_TEAL),
             ("Warning", DANGER_BG), ("Optional", SOFT_LAV), ("Standard", WHITE)]
    for i, (txt, colr) in enumerate(items):
        c = ws.cell(row, col + i, txt)
        c.fill = fill(colr)
        c.font = fnt(8, False, DARK)
        c.border = BOX
        c.alignment = Alignment(horizontal="center")


# ------------------------------------------------------------------ Setup
SETUP_HABITS = ["Read 20 minutes", "Walk 30 minutes", "Drink 8 glasses of water",
                "No phone before 9am", "Journal"]


def build_setup(ws, wb):
    page(ws, "Setup", "Personal information, planning preferences and the lists every weekly sheet uses.",
         NAVY, 9, demo=True)
    ws.column_dimensions["B"].width = 26
    ws.column_dimensions["C"].width = 24
    ws.column_dimensions["D"].width = 3
    for col, w in zip("EFGHIJ", (14, 18, 26, 14, 10, 14)):
        ws.column_dimensions[col].width = w
    band(ws, 4, 2, 3, "PERSONAL AND PLANNING", MIDNIGHT, WHITE, 10)
    rows = [
        ("Your name", "Jordan Lee", None),
        ("First week starts (a Monday)", D(2026, 11, 2), FMT_DATE),
        ("Working day starts", dt.time(7, 0), "hh:mm"),
        ("Working day ends", dt.time(18, 0), "hh:mm"),
        ("Daily water goal (glasses)", 8, "0"),
        ("Daily exercise goal (minutes)", 30, "0"),
    ]
    for i, (lab, val, fmt) in enumerate(rows):
        r = 5 + i
        label(ws, f"B{r}", lab)
        inp(ws, f"C{r}", val, fmt)
    wb.defined_names["FirstWeek"] = DefinedName("FirstWeek", attr_text="Setup!$C$6")
    wb.defined_names["WaterGoal"] = DefinedName("WaterGoal", attr_text="Setup!$C$9")
    wb.defined_names["ExerciseGoal"] = DefinedName("ExerciseGoal", attr_text="Setup!$C$10")
    label(ws, "B12", "Set the first Monday once; every week sheet and the monthly calendar follow it.", False)
    band(ws, 14, 2, 3, "HOW TO USE", MIDNIGHT, WHITE, 10)
    notes = ["1. Fill in the Setup block above.",
             "2. Open Week 1 and type the main goal, three priorities and the daily tasks.",
             "3. Move to the next week tab when the week starts. Each tab is reusable.",
             "4. Use Monthly Calendar to add important dates and deadlines for the month."]
    for i, n in enumerate(notes):
        label(ws, f"B{15 + i}", n, False)
    legend(ws, 20, 2)

    lists = [
        ("Priorities", "Priority", ["High", "Medium", "Low"]),
        ("Categories", "Category", ["Work", "Personal", "Health", "Family", "Admin", "Learning"]),
        ("HabitList", "Habits", SETUP_HABITS),
        ("HabitStatus", "Habit status", ["Done", "Missed"]),
        ("YesNo", "Done?", ["Yes", "No"]),
        ("MonthList", "Months", ["January", "February", "March", "April", "May", "June", "July",
                                 "August", "September", "October", "November", "December"]),
    ]
    band(ws, 4, 5, 10, "DROPDOWN LISTS (edit the blue cells)", MIDNIGHT, WHITE, 10)
    for i, (nm, head, items) in enumerate(lists):
        col = CL(5 + i)
        h = ws[f"{col}5"]
        h.value = head
        h.font = fnt(9, True, WHITE)
        h.fill = fill(NAVY)
        h.alignment = Alignment(horizontal="center")
        for j in range(15):
            inp(ws, f"{col}{6 + j}", items[j] if j < len(items) else None)
        wb.defined_names[nm] = DefinedName(nm, attr_text=f"Setup!${col}$6:${col}$20")
    ws.freeze_panes = "A4"


# ------------------------------------------------------------------ Weekly sheets
TASKS_PER_DAY = 5
BLOCK = TASKS_PER_DAY + 3          # day header, top priority row, column labels, task rows
BLOCK_START = 14
HABIT_HDR = 72
HABIT_ROW0 = 73
WATER_ROW = 79
EXER_ROW = 80
PROD_ROW = 81
REFLECT_BAND = 83


def week_date(n, k):
    return f"(FirstWeek+{7 * (n - 1) + k})"


def build_week(ws, n, sample):
    page(ws, f"Week {n}", "Plan the week: goal, priorities, daily checklists, habits, water, exercise and reflection.",
         BLUE, 9, demo=sample)
    ws.column_dimensions["A"].width = 2
    ws.column_dimensions["B"].width = 30
    for col in "CDEFGHI":
        ws.column_dimensions[col].width = 14
    ws.column_dimensions["J"].width = 12

    # overview
    label(ws, "B4", "Week number")
    calc(ws, "C4", n, "0", True, "left")
    ws.merge_cells("C4:D4")
    label(ws, "B5", "Start date")
    merge_calc(ws, "C5:D5", f"=FirstWeek+{7 * (n - 1)}", FMT_DATE, True, "left")
    label(ws, "B6", "End date")
    merge_calc(ws, "C6:D6", f"=FirstWeek+{7 * (n - 1) + 6}", FMT_DATE, True, "left")
    label(ws, "B7", "Main goal of the week")
    merge_inp(ws, "C7:I7", "Sample: finish the Q4 report draft" if sample else None, height=24)
    for i, r in enumerate((8, 9, 10)):
        label(ws, f"B{r}", f"Priority {i + 1}")
        merge_inp(ws, f"C{r}:I{r}", ("Sample priority " + str(i + 1)) if sample and i == 0 else None)
    label(ws, "B11", "Weekly progress (tasks done)")
    done_terms = []
    total_terms = []
    for k in range(7):
        s = BLOCK_START + BLOCK * k
        done_terms.append(f'COUNTIF(E{s + 3}:E{s + 2 + TASKS_PER_DAY},"Yes")')
        total_terms.append(f"COUNTA(B{s + 3}:B{s + 2 + TASKS_PER_DAY})")
    done = "+".join(done_terms)
    total = "+".join(total_terms)
    calc(ws, "C11", f"=IFERROR(({done})/({total}),0)", "0%", True)
    ws.merge_cells("C11:D11")
    for col_lab, row, f, fmt in (
        ("Tasks done", 4, f"={done}", "0"),
        ("Tasks planned", 5, f"={total}", "0"),
        ("Habit completion", 6, f"=IFERROR(AVERAGE(J{HABIT_ROW0}:J{HABIT_ROW0 + 4}),0)", "0%"),
        ("Productivity average", 11, f"=IFERROR(AVERAGE(C{PROD_ROW}:I{PROD_ROW}),0)", "0%"),
    ):
        ws.merge_cells(f"F{row}:H{row}")
        ws[f"F{row}"] = col_lab
        ws[f"F{row}"].font = fnt(9, True, DARK)
        ws[f"F{row}"].fill = fill(SOFT_LAV)
        ws[f"F{row}"].alignment = Alignment(indent=1, vertical="center")
        calc(ws, f"I{row}", f, fmt, True, "center", SOFT_LAV)
    # daily blocks
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    sample_tasks = {0: ["Draft report outline", "Call supplier", "Team stand-up", "Gym session"],
                    1: ["Write report section 1", "Review budget", "Pay invoices"],
                    2: ["Client meeting prep"]}
    for k in range(7):
        s = BLOCK_START + BLOCK * k
        for col in "BCDEFGHI":
            ws[f"{col}{s}"].fill = fill(MIDNIGHT)
        ws[f"B{s}"] = f'=TEXT(FirstWeek+{7 * (n - 1) + k},"dddd dd-mmm-yyyy")'
        ws[f"B{s}"].font = fnt(10, True, WHITE)
        ws.merge_cells(f"C{s}:E{s}")
        ws[f"C{s}"] = "Top priority"
        ws[f"C{s}"].font = fnt(8, True, WHITE)
        ws.merge_cells(f"F{s}:I{s}")
        ws[f"F{s}"] = "Appointments and schedule"
        ws[f"F{s}"].font = fnt(8, True, WHITE)
        ws.row_dimensions[s].height = 22
        # top priority / appointment inputs on the row below header
        r1 = s + 1
        merge_inp(ws, f"C{r1}:E{r1}", "Sample top priority" if (sample and k == 0) else None)
        merge_inp(ws, f"F{r1}:I{r1}", "Dentist 10:30" if (sample and k == 0) else None)
        ws[f"B{r1}"] = "Top priority and appointments"
        ws[f"B{r1}"].font = fnt(8, False, SEC)
        for col, lab in zip("BCDEF", ["Task", "Priority", "Time", "Done?", "Notes"]):
            ws[f"{col}{s + 2}"] = lab
            ws[f"{col}{s + 2}"].font = fnt(8, True, SEC)
        ws.merge_cells(f"F{s + 2}:I{s + 2}")
        for j in range(TASKS_PER_DAY):
            r = s + 3 + j
            label(ws, f"B{r}", None, False)
            inp(ws, f"B{r}", (sample_tasks.get(k, []) + [None] * 5)[j] if sample else None)
            inp(ws, f"C{r}", None, None, "center")
            inp(ws, f"D{r}", None, "hh:mm", "center")
            done_demo = sample and ((k == 0 and j < 2) or (k == 1 and j == 0))
            inp(ws, f"E{r}", "Yes" if done_demo else None, None, "center")
            merge_inp(ws, f"F{r}:I{r}", None)
            ws.row_dimensions[r].height = 18
        # header labels for task columns on first task row
    # the checklist columns: label row above first block
    for k in range(7):
        s = BLOCK_START + BLOCK * k
        for j in range(TASKS_PER_DAY):
            r = s + 3 + j
            dv_list(ws, f"C{r}", "Priorities")
            dv_list(ws, f"E{r}", "YesNo")
    # sub-labels for task columns on each block (row s+1 right side is used by top priority)
    # trackers
    band(ws, HABIT_HDR - 1, 2, 10, "TRACKERS", BLUE, WHITE, 10)
    label(ws, f"B{HABIT_HDR}", "Habit")
    for k, col in enumerate("CDEFGHI"):
        ws[f"{col}{HABIT_HDR}"] = f'=TEXT(FirstWeek+{7 * (n - 1) + k},"ddd dd")'
        ws[f"{col}{HABIT_HDR}"].font = fnt(9, True, WHITE)
        ws[f"{col}{HABIT_HDR}"].fill = fill(NAVY)
        ws[f"{col}{HABIT_HDR}"].alignment = Alignment(horizontal="center")
    ws[f"J{HABIT_HDR}"] = "Done %"
    ws[f"J{HABIT_HDR}"].font = fnt(9, True, WHITE)
    ws[f"J{HABIT_HDR}"].fill = fill(NAVY)
    ws[f"B{HABIT_HDR}"].font = fnt(9, True, WHITE)
    ws[f"B{HABIT_HDR}"].fill = fill(NAVY)
    for i in range(5):
        r = HABIT_ROW0 + i
        calc(ws, f"B{r}", f"=Setup!G{6 + i}", None, False, "left", SOFT_TEAL if False else LGRAY)
        for k, col in enumerate("CDEFGHI"):
            inp(ws, f"{col}{r}", "Done" if (sample and k < 3 and i < 2) else None, None, "center")
        calc(ws, f"J{r}", f'=IFERROR(COUNTIF(C{r}:I{r},"Done")/7,0)', "0%", True)
        dv_list(ws, f"C{r}:I{r}", "HabitStatus")
    cf(ws, f"J{HABIT_ROW0}:J{HABIT_ROW0 + 4}", f"J{HABIT_ROW0}>=0.5", SUCCESS_BG, SUCCESS, True)
    cf(ws, f"J{HABIT_ROW0}:J{HABIT_ROW0 + 4}", f"J{HABIT_ROW0}<0.5", WARN_BG, DARK, False)

    label(ws, f"B{WATER_ROW}", "Water (glasses)")
    label(ws, f"B{EXER_ROW}", "Exercise (minutes)")
    label(ws, f"B{PROD_ROW}", "Productivity (% of tasks done)")
    for k, col in enumerate("CDEFGHI"):
        s = BLOCK_START + BLOCK * k
        inp(ws, f"{col}{WATER_ROW}", 6 if (sample and k < 3) else None, "0", "center")
        inp(ws, f"{col}{EXER_ROW}", 30 if (sample and k in (0, 2)) else None, "0", "center")
        calc(ws, f"{col}{PROD_ROW}",
             f'=IFERROR(COUNTIF(E{s + 3}:E{s + 2 + TASKS_PER_DAY},"Yes")/COUNTA(B{s + 3}:B{s + 2 + TASKS_PER_DAY}),0)',
             "0%", True)
    calc(ws, f"J{WATER_ROW}", f"=SUM(C{WATER_ROW}:I{WATER_ROW})", "0", True)
    calc(ws, f"J{EXER_ROW}", f"=SUM(C{EXER_ROW}:I{EXER_ROW})", "0", True)
    calc(ws, f"J{PROD_ROW}", f"=IFERROR(AVERAGE(C{PROD_ROW}:I{PROD_ROW}),0)", "0%", True)
    cf(ws, f"C{WATER_ROW}:I{WATER_ROW}", f"AND(ISNUMBER(C{WATER_ROW}),C{WATER_ROW}>=WaterGoal)", SUCCESS_BG, SUCCESS, True)
    cf(ws, f"C{EXER_ROW}:I{EXER_ROW}", f"AND(ISNUMBER(C{EXER_ROW}),C{EXER_ROW}>=ExerciseGoal)", SUCCESS_BG, SUCCESS, True)
    label(ws, f"K{WATER_ROW}", "Goal: Setup", False)
    ws.conditional_formatting.add(f"C{PROD_ROW}:I{PROD_ROW}",
                                  DataBarRule(start_type="num", start_value=0, end_type="num", end_value=1, color=TEAL))

    # reflection
    band(ws, REFLECT_BAND, 2, 10, "WEEKLY REFLECTION", BLUE, WHITE, 10)
    prompts = [("Wins this week", "Sample: report draft done on time" if sample else None),
               ("Challenges", None), ("Lessons learned", None), ("Focus for next week", None)]
    for i, (lab, val) in enumerate(prompts):
        r = REFLECT_BAND + 1 + i
        label(ws, f"B{r}", lab)
        merge_inp(ws, f"C{r}:J{r}", val, height=36)
    ws.freeze_panes = "A4"
    legend(ws, REFLECT_BAND + 5, 2)


# ------------------------------------------------------------------ Monthly
def build_monthly(ws, wb):
    page(ws, "Monthly Calendar", "Pick a month. See important dates, deadlines, weekly goals and this month's priorities.",
         INFO, 13, demo=True)
    widths = {"B": 14, "C": 14, "D": 14, "E": 14, "F": 14, "G": 14, "H": 14, "I": 3,
              "J": 14, "K": 28, "L": 14, "M": 28}
    for col, w in widths.items():
        ws.column_dimensions[col].width = w
    label(ws, "B4", "Month")
    inp(ws, "C4", "November")
    label(ws, "E4", "Year")
    inp(ws, "F4", 2026, "0")
    dv_list(ws, "C4", "MonthList")
    ws["P4"] = "=DATE($F$4,IFERROR(MATCH($C$4,MonthList,0),11),1)"
    ws["Q4"] = "=DAY(EOMONTH($P$4,0))"
    ws["R4"] = "=MOD(WEEKDAY($P$4,1)-2,7)"
    for c in ("P4", "Q4", "R4"):
        ws[c].font = fnt(8, False, SEC)
    ws["P4"].number_format = FMT_DATE
    for c in "PQR":
        ws.column_dimensions[c].hidden = True
    cols = "BCDEFGH"
    for c in range(7):
        h = ws[f"{cols[c]}6"]
        h.value = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][c]
        h.font = fnt(9, True, WHITE)
        h.fill = fill(NAVY)
        h.alignment = Alignment(horizontal="center")
    EV = "$J$8:$J$27"
    DL = "$L$8:$L$27"
    for w in range(6):
        rd = 7 + 3 * w
        for c in range(7):
            X = cols[c]
            e = f"({7 * w + c}-$R$4)"
            ws[f"{X}{rd}"] = f'=IF(AND({e}>=0,{e}<$Q$4),$P$4+{e},"")'
            ws[f"{X}{rd}"].number_format = "d"
            ws[f"{X}{rd}"].font = fnt(11, True, NAVY)
            ws[f"{X}{rd}"].fill = fill(WHITE)
            ws[f"{X}{rd}"].border = BOX
            ws[f"{X}{rd}"].alignment = Alignment(horizontal="left", vertical="top", indent=1)
            ws[f"{X}{rd + 1}"] = (f'=IF({X}{rd}="","",IF(COUNTIF({EV},{X}{rd})+COUNTIF({DL},{X}{rd})=0,"",'
                                  f'COUNTIF({EV},{X}{rd})&" event · "&COUNTIF({DL},{X}{rd})&" due"))')
            ws[f"{X}{rd + 1}"].font = fnt(8, True, DARK)
            ws[f"{X}{rd + 1}"].fill = fill(SOFT_BLUE if False else SOFT_LAV)
            ws[f"{X}{rd + 1}"].border = BOX
            ws[f"{X}{rd + 2}"].fill = fill(WHITE)
            ws[f"{X}{rd + 2}"].border = BOX
        ws.row_dimensions[rd].height = 22
        cf(ws, f"B{rd}:H{rd}", f"AND(ISNUMBER(B{rd}),B{rd}=TODAY())", BLUE, WHITE, True)
    # important dates & deadlines (inputs)
    band(ws, 5, 10, 13, "IMPORTANT DATES", MIDNIGHT, WHITE, 10)
    for col, h in zip("JKLM", ["Date", "Important date or event", "Date", "Task deadline"]):
        ws[f"{col}6"] = h
        ws[f"{col}6"].font = fnt(9, True, WHITE)
        ws[f"{col}6"].fill = fill(NAVY)
    samples_ev = [(D(2026, 11, 5), "Parent-teacher evening"), (D(2026, 11, 14), "Team offsite"),
                  (D(2026, 11, 26), "Thanksgiving")]
    samples_dl = [(D(2026, 11, 6), "Submit timesheet"), (D(2026, 11, 13), "Q4 report draft"),
                  (D(2026, 11, 20), "Pay rent")]
    for i in range(20):
        r = 8 + i
        inp(ws, f"J{r}", samples_ev[i][0] if i < len(samples_ev) else None, FMT_DATE)
        inp(ws, f"K{r}", samples_ev[i][1] if i < len(samples_ev) else None)
        inp(ws, f"L{r}", samples_dl[i][0] if i < len(samples_dl) else None, FMT_DATE)
        inp(ws, f"M{r}", samples_dl[i][1] if i < len(samples_dl) else None)
    band(ws, 30, 10, 13, "WEEKLY GOALS (from the Week tabs)", MIDNIGHT, WHITE, 10)
    for i in range(6):
        r = 31 + i
        label(ws, f"J{r}", f"Week {i + 1}")
        ws.merge_cells(f"K{r}:M{r}")
        calc(ws, f"K{r}", f"=IF('Week {i + 1}'!C7=\"\",\"\",'Week {i + 1}'!C7)", None, False, "left")
    band(ws, 38, 10, 13, "MONTHLY PRIORITIES", MIDNIGHT, WHITE, 10)
    for i in range(3):
        r = 39 + i
        label(ws, f"J{r}", f"Priority {i + 1}")
        ws.merge_cells(f"K{r}:M{r}")
        inp(ws, f"K{r}", "Sample monthly priority" if i == 0 else None)
        for col in "LM":
            ws[f"{col}{r}"].fill = fill(SOFT_BLUE)
    legend(ws, 26, 2)
    ws.freeze_panes = "A7"


def main():
    wb = Workbook()
    wb.remove(wb.active)
    setup = wb.create_sheet("Setup")
    weeks = [wb.create_sheet(f"Week {i}") for i in range(1, 7)]
    monthly = wb.create_sheet("Monthly Calendar")

    build_setup(setup, wb)
    for i, ws in enumerate(weeks, start=1):
        build_week(ws, i, sample=(i == 1))
    build_monthly(monthly, wb)

    for ws in wb.worksheets:
        ws.page_setup.orientation = "portrait"
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True
    wb.calculation = CalcProperties(fullCalcOnLoad=True)
    wb.active = 0
    wb.save(OUT)
    print("saved", OUT)


if __name__ == "__main__":
    main()
