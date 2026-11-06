#!/usr/bin/env python3
"""Builds the Ultimate Project Manager workbook (.xlsx, macro-free).

Usage:  python3 build_project_manager.py OUTPUT.xlsx

Every dashboard value is a formula over the input tables. Sample rows are
marked DEMO DATA. Colours and fonts come from ../../design-system/design-tokens.json.
"""
import re
import sys
import datetime as dt

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import FormulaRule, DataBarRule
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.workbook.properties import CalcProperties
from openpyxl.chart import BarChart, DoughnutChart, Reference
from openpyxl.chart.marker import DataPoint
from openpyxl.utils import get_column_letter as CL

OUT = sys.argv[1] if len(sys.argv) > 1 else "Ultimate_Project_Manager.xlsx"

# ---------------------------------------------------------------- design tokens
NAVY = "17243A"; MIDNIGHT = "223653"; BLUE = "4169E1"; SOFT_BLUE = "EAF1FB"
TEAL = "24A89A"; SOFT_TEAL = "E2F4F0"; LAV = "8B7BE8"; SOFT_LAV = "F0EDFC"
BG = "F5F7FA"; WHITE = "FFFFFF"; LGRAY = "E9EDF2"; MGRAY = "9AA5B1"
DARK = "263445"; SEC = "6B7785"; BORDER = "DCE3EA"
SUCCESS = "279B70"; SUCCESS_BG = "E5F5ED"; WARN = "E9A23B"; WARN_BG = "FFF3DC"
DANGER = "DC5B64"; DANGER_BG = "FCEAEC"; INFO = "4D8FD8"; INFO_BG = "EAF2FC"


def fill(c):
    return PatternFill("solid", start_color=c, end_color=c)


SIDE = Side(style="thin", color=BORDER)
BOX = Border(left=SIDE, right=SIDE, top=SIDE, bottom=SIDE)


def fnt(size=9, bold=False, color=DARK, italic=False):
    return Font(name="Arial", size=size, bold=bold, color=color, italic=italic)


FMT_DATE = "dd-mmm-yyyy"
FMT_MONEY = "#,##0.00;[Red]-#,##0.00"
FMT_PCT = "0%"
FMT_DAYS = "0;[Red]-0"
FMT_HRS = "0.0"
FMT_TIME = "hh:mm"
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

# ---------------------------------------------------------------- sheet names
SHEETS = ["Setup", "Dashboard", "Monthly Calendar", "Weekly Calendar", "Project Overview",
          "Project Manager", "Project Budget", "Variable Tasks", "Recurring Tasks",
          "Task Schedule", "Task Filter", "Decision Matrix", "Kanban Board", "Gantt Chart",
          "Instructions"]

# ---------------------------------------------------------------- table registry
REG = {}


def reg(key, sheet, tname, hdr, nrows, headers, col0=2):
    REG[key] = dict(sheet=sheet, tname=tname, hdr=hdr, first=hdr + 1, last=hdr + nrows,
                    col0=col0, L={h: CL(col0 + i) for i, h in enumerate(headers)})


def R(key, h):
    """Absolute cross-sheet range for a table column."""
    s = REG[key]
    c = s["L"][h]
    return f"'{s['sheet']}'!${c}${s['first']}:${c}${s['last']}"


def fx(key, r, tmpl):
    """Expand {Header} to same-row cell, {^Header} to expanding range from first row to row r."""
    s = REG[key]

    def caret(m):
        c = s["L"][m.group(1)]
        return f"${c}${s['first']}:{c}{r}"

    tmpl = re.sub(r"\{\^([^}]+)\}", caret, tmpl)
    return re.sub(r"\{([^}]+)\}", lambda m: f"{s['L'][m.group(1)]}{r}", tmpl)


def pick(key, col, n, kh, fn="SMALL"):
    """n-th item of a table column ordered by a helper key column (INDEX/MATCH, no arrays)."""
    rng = R(key, col)
    kr = R(key, kh)
    return f'IFERROR(INDEX({rng},MATCH({fn}({kr},{n}),{kr},0)),"")'


# Cross-sheet anchors
TASK_FILTER = "Task Filter"
FP, FPR, FS, FC, FA, FD, FCO, FO = [f"'{TASK_FILTER}'!$D${r}" for r in range(6, 14)]
GANTT_SEL = "'Gantt Chart'!$C$4"
AGENDA = "'Monthly Calendar'!$K$4"

# Register all tables first so formulas can reference any of them.
TASK_H = ["Task ID", "Task Name", "Description", "Project ID", "Category", "Assigned To",
          "Start Date", "Due Date", "Priority", "Status", "Est. Hours", "Actual Hours",
          "Progress", "Notes", "Days Left", "Overdue", "Deadline Key", "Overdue Key",
          "Recent Key", "Filter Key", "Gantt Key", "Agenda Key", "Kanban Key"]
PROJ_H = ["Project ID", "Project Name", "Description", "Category", "Project Manager",
          "Start Date", "Due Date", "Priority", "Status", "Progress", "Budget", "Actual Cost",
          "Remaining Budget", "Days Remaining"]
BUD_H = ["Expense ID", "Project ID", "Budget Category", "Planned Budget", "Actual Expense",
         "Remaining Budget", "Budget Utilization", "Expense Date", "Vendor", "Description",
         "Budget Alert"]
REC_H = ["Recurring ID", "Task Name", "Project ID", "Category", "Assigned To", "Frequency",
         "Custom Every (days)", "Start Date", "Last Completed", "Next Occurrence",
         "Days Until Next", "Status", "Schedule Flag"]
SCH_H = ["Schedule ID", "Date", "Start Time", "End Time", "Task", "Project ID", "Priority",
         "Status", "Duration (h)", "Assigned Person", "Slot Key"]
PM_H = ["Project ID", "Project Name", "Department", "Objectives", "Key Deliverables",
        "Milestones", "Next Milestone", "Team Members", "Timeline", "Dependencies", "Risks",
        "Risk Level", "Progress", "Task Completion %", "Notes"]

reg("tasks", "Variable Tasks", "tblTasks", 5, 300, TASK_H)
reg("proj", "Project Overview", "tblProjects", 5, 50, PROJ_H)
reg("bud", "Project Budget", "tblBudget", 5, 300, BUD_H)
reg("rec", "Recurring Tasks", "tblRecurring", 5, 50, REC_H)
reg("sch", "Task Schedule", "tblSchedule", 5, 200, SCH_H)
reg("pm", "Project Manager", "tblProjectDetail", 5, 50, PM_H)

TID = R("tasks", "Task ID"); TN = R("tasks", "Task Name"); TPID = R("tasks", "Project ID")
TST = R("tasks", "Status"); TPRI = R("tasks", "Priority"); TDUE = R("tasks", "Due Date")
TSTART = R("tasks", "Start Date"); TPROG = R("tasks", "Progress"); TAS = R("tasks", "Assigned To")
TCAT = R("tasks", "Category"); TOVD = R("tasks", "Overdue")
PID = R("proj", "Project ID"); PST = R("proj", "Status"); PDUE = R("proj", "Due Date")
PPRI = R("proj", "Priority")
BPID = R("bud", "Project ID"); BPLAN = R("bud", "Planned Budget"); BACT = R("bud", "Actual Expense")
SDATE = R("sch", "Date"); SDUR = R("sch", "Duration (h)"); SPRI = R("sch", "Priority")
SSLOT = R("sch", "Slot Key"); STASK = R("sch", "Task"); SPROJ = R("sch", "Project ID")
PC = REG["proj"]["L"]  # Project Overview column letters


# ---------------------------------------------------------------- column specs
def I(h, w=14, fmt=None, wrap=False):
    return dict(h=h, kind="in", w=w, fmt=fmt, wrap=wrap)


def C(h, f, w=14, fmt=None, wrap=False):
    return dict(h=h, kind="calc", f=f, w=w, fmt=fmt, wrap=wrap)


FILTER_F = (
    'IF(AND(LEN({Task Name})>0,'
    f'OR({FP}="All",{{Project ID}}={FP}),'
    f'OR({FPR}="All",{{Priority}}={FPR}),'
    f'OR({FS}="All",{{Status}}={FS}),'
    f'OR({FC}="All",{{Category}}={FC}),'
    f'OR({FA}="All",{{Assigned To}}={FA}),'
    f'OR({FCO}="All",AND({FCO}="Completed",{{Status}}="Completed"),AND({FCO}="Not completed",{{Status}}<>"Completed")),'
    f'OR({FO}="All",{{Overdue}}={FO}),'
    f'OR({FD}="All",AND({FD}="Overdue",{{Overdue}}="Yes"),'
    f'AND({FD}="Next 7 days",ISNUMBER({{Due Date}}),{{Due Date}}>=TODAY(),{{Due Date}}<=TODAY()+7),'
    f'AND({FD}="No due date",NOT(ISNUMBER({{Due Date}})))))'
    ',ROW(),"")'
)

TASK_COLS = [
    C("Task ID", 'IF(LEN({Task Name})=0,"","TSK-"&TEXT(ROW()-5,"000"))', 11),
    I("Task Name", 30), I("Description", 34, wrap=True), I("Project ID", 12),
    I("Category", 14), I("Assigned To", 16), I("Start Date", 13, FMT_DATE),
    I("Due Date", 13, FMT_DATE), I("Priority", 11), I("Status", 13),
    I("Est. Hours", 10, FMT_HRS), I("Actual Hours", 10, FMT_HRS), I("Progress", 10, FMT_PCT),
    I("Notes", 30, wrap=True),
    C("Days Left", 'IF(ISNUMBER({Due Date}),{Due Date}-TODAY(),"")', 10, FMT_DAYS),
    C("Overdue", 'IF(ISNUMBER({Due Date}),IF(AND({Status}<>"Completed",{Due Date}<TODAY()),"Yes","No"),"")', 10),
    C("Deadline Key", 'IF(AND(ISNUMBER({Due Date}),{Status}<>"Completed"),IF({Due Date}>=TODAY(),{Due Date}+ROW()/100000,""),"")', 12),
    C("Overdue Key", 'IF(AND(ISNUMBER({Due Date}),{Status}<>"Completed"),IF({Due Date}<TODAY(),{Due Date}+ROW()/100000,""),"")', 12),
    C("Recent Key", 'IF(ISNUMBER({Start Date}),{Start Date}+ROW()/100000,"")', 12),
    C("Filter Key", FILTER_F, 10),
    C("Gantt Key", f'IF(AND(LEN({{Task Name}})>0,{{Project ID}}={GANTT_SEL}),ROW(),"")', 10),
    C("Agenda Key", f'IF(AND(ISNUMBER({{Due Date}}),{{Due Date}}={AGENDA}),ROW(),"")', 10),
    C("Kanban Key", 'IF(LEN({Status})=0,"",{Status}&"|"&COUNTIF({^Status},{Status}))', 14),
]

PROJ_COLS = [
    C("Project ID", 'IF(LEN({Project Name})=0,"","PRJ-"&TEXT(ROW()-5,"000"))', 11),
    I("Project Name", 28), I("Description", 36, wrap=True), I("Category", 15),
    I("Project Manager", 16), I("Start Date", 13, FMT_DATE), I("Due Date", 13, FMT_DATE),
    I("Priority", 11), I("Status", 13),
    C("Progress", f'IF({{Project ID}}="","",IFERROR(AVERAGEIFS({TPROG},{TPID},{{Project ID}}),""))', 11, FMT_PCT),
    C("Budget", f'IF({{Project ID}}="","",SUMIFS({BPLAN},{BPID},{{Project ID}}))', 14, FMT_MONEY),
    C("Actual Cost", f'IF({{Project ID}}="","",SUMIFS({BACT},{BPID},{{Project ID}}))', 14, FMT_MONEY),
    C("Remaining Budget", 'IF({Project ID}="","",{Budget}-{Actual Cost})', 14, FMT_MONEY),
    C("Days Remaining", 'IF(ISNUMBER({Due Date}),{Due Date}-TODAY(),"")', 11, FMT_DAYS),
]

BUD_COLS = [
    C("Expense ID", 'IF(COUNT({Planned Budget},{Actual Expense})=0,"","EXP-"&TEXT(ROW()-5,"000"))', 11),
    I("Project ID", 12), I("Budget Category", 16), I("Planned Budget", 14, FMT_MONEY),
    I("Actual Expense", 14, FMT_MONEY),
    C("Remaining Budget", 'IF(ISNUMBER({Planned Budget}),{Planned Budget}-N({Actual Expense}),"")', 14, FMT_MONEY),
    C("Budget Utilization", 'IF(AND(ISNUMBER({Planned Budget}),N({Planned Budget})>0),N({Actual Expense})/{Planned Budget},"")', 12, FMT_PCT),
    I("Expense Date", 13, FMT_DATE), I("Vendor", 20), I("Description", 34, wrap=True),
    C("Budget Alert", 'IF({Budget Utilization}="","",IF({Budget Utilization}>1,"Over budget",IF({Budget Utilization}>=0.9,"Near limit","On track")))', 14),
]

_nest = 'MAX(1,N({Custom Every (days)}))'
_nest = "{Last Completed}+" + _nest
for _cond, _val in reversed([("Daily", "{Last Completed}+1"), ("Weekly", "{Last Completed}+7"),
                             ("Biweekly", "{Last Completed}+14"), ("Monthly", "EDATE({Last Completed},1)"),
                             ("Quarterly", "EDATE({Last Completed},3)"), ("Annually", "EDATE({Last Completed},12)")]):
    _nest = f'IF({{Frequency}}="{_cond}",{_val},{_nest})'
NEXT_F = (f'IF(NOT(ISNUMBER({{Start Date}})),"",IF(NOT(ISNUMBER({{Last Completed}})),'
          f'{{Start Date}},{_nest}))')

REC_COLS = [
    C("Recurring ID", 'IF(LEN({Task Name})=0,"","REC-"&TEXT(ROW()-5,"000"))', 11),
    I("Task Name", 28), I("Project ID", 12), I("Category", 14), I("Assigned To", 16),
    I("Frequency", 12), I("Custom Every (days)", 12), I("Start Date", 13, FMT_DATE),
    I("Last Completed", 13, FMT_DATE),
    C("Next Occurrence", NEXT_F, 13, FMT_DATE),
    C("Days Until Next", 'IF(ISNUMBER({Next Occurrence}),{Next Occurrence}-TODAY(),"")', 11, FMT_DAYS),
    I("Status", 10),
    C("Schedule Flag", 'IF(LEN({Task Name})=0,"",IF({Status}="Paused","Paused",IF(NOT(ISNUMBER({Next Occurrence})),"Set start date",IF({Days Until Next}<0,"Overdue",IF({Days Until Next}<=3,"Due soon","On schedule")))))', 14),
]

SCH_COLS = [
    C("Schedule ID", 'IF(LEN({Task})=0,"","SCH-"&TEXT(ROW()-5,"000"))', 11),
    I("Date", 13, FMT_DATE), I("Start Time", 10, FMT_TIME), I("End Time", 10, FMT_TIME),
    I("Task", 34), I("Project ID", 12), I("Priority", 11), I("Status", 13),
    C("Duration (h)", 'IF(AND(ISNUMBER({Start Time}),ISNUMBER({End Time})),({End Time}-{Start Time})*24,"")', 11, FMT_HRS),
    I("Assigned Person", 16),
    C("Slot Key", 'IF(AND(ISNUMBER({Date}),ISNUMBER({Start Time})),INT({Date})*100+HOUR({Start Time}),"")', 12),
]

_oc = REG["proj"]["L"]
PM_COLS = [
    C("Project ID", lambda r: f"IF(LEN('Project Overview'!${_oc['Project Name']}{r})=0,\"\",'Project Overview'!${_oc['Project ID']}{r})", 11),
    C("Project Name", lambda r: f"IF(LEN('Project Overview'!${_oc['Project Name']}{r})=0,\"\",'Project Overview'!${_oc['Project Name']}{r})", 26),
    I("Department", 14), I("Objectives", 34, wrap=True), I("Key Deliverables", 34, wrap=True),
    I("Milestones", 30, wrap=True), I("Next Milestone", 13, FMT_DATE), I("Team Members", 24, wrap=True),
    C("Timeline", lambda r: (f"IF(LEN('Project Overview'!${_oc['Project Name']}{r})=0,\"\","
                             f"TEXT('Project Overview'!${_oc['Start Date']}{r},\"dd-mmm-yy\")&\" to \"&"
                             f"TEXT('Project Overview'!${_oc['Due Date']}{r},\"dd-mmm-yy\"))"), 22),
    I("Dependencies", 28, wrap=True), I("Risks", 30, wrap=True), I("Risk Level", 11),
    C("Progress", lambda r: f"IF(LEN('Project Overview'!${_oc['Project Name']}{r})=0,\"\",'Project Overview'!${_oc['Progress']}{r})", 10, FMT_PCT),
    C("Task Completion %", lambda r: (f"IF(LEN('Project Overview'!${_oc['Project Name']}{r})=0,\"\","
                                      f"IFERROR(COUNTIFS({TPID},'Project Overview'!${_oc['Project ID']}{r},{TST},\"Completed\")/"
                                      f"COUNTIF({TPID},'Project Overview'!${_oc['Project ID']}{r}),\"\"))"), 12, FMT_PCT),
    I("Notes", 30, wrap=True),
]

# ---------------------------------------------------------------- generic writers
def page(ws, title, sub, tab, demo=False, widths=None):
    ws.sheet_view.showGridLines = False
    ws.sheet_properties.tabColor = tab
    ws.column_dimensions["A"].width = 2
    ws["B1"] = title
    ws["B1"].font = fnt(18, True, NAVY)
    ws.row_dimensions[1].height = 30
    ws["B2"] = sub
    ws["B2"].font = fnt(9, False, SEC)
    if demo:
        ws["B3"] = "DEMO DATA: sample entries are included so every view works. Clear the blue input cells to start your own."
        ws["B3"].font = fnt(9, True, INFO)
    for col, w in (widths or {}).items():
        ws.column_dimensions[col].width = w


def section(ws, cell, text):
    ws[cell] = text
    ws[cell].font = fnt(10, True, NAVY)


def label(ws, cell, text, bold=False):
    ws[cell] = text
    ws[cell].font = fnt(9, bold, SEC if not bold else DARK)


def inp(ws, cell, value=None, fmt=None):
    c = ws[cell]
    if value is not None:
        c.value = value
    c.fill = fill(SOFT_BLUE)
    c.border = BOX
    c.font = fnt(9)
    if fmt:
        c.number_format = fmt


def legend(ws, row, col):
    items = [("Input", SOFT_BLUE), ("Calculated", LGRAY), ("Positive", SOFT_TEAL),
             ("Warning", DANGER_BG), ("Optional", SOFT_LAV), ("Standard", WHITE)]
    for i, (txt, colr) in enumerate(items):
        c = ws.cell(row, col + i, txt)
        c.fill = fill(colr)
        c.font = fnt(8, False, DARK)
        c.border = BOX
        c.alignment = Alignment(horizontal="center")


def cf(ws, rng, formula, bg=None, color=None, bold=False, stop=True):
    kw = {}
    if bg:
        kw["fill"] = fill(bg)
    if color or bold:
        kw["font"] = Font(color=color, bold=bold) if color else Font(bold=bold)
    ws.conditional_formatting.add(rng, FormulaRule(formula=[formula], stopIfTrue=stop, **kw))


def databar(ws, rng, color=TEAL):
    ws.conditional_formatting.add(rng, DataBarRule(start_type="num", start_value=0,
                                                   end_type="num", end_value=1, color=color))


def dv_list(ws, rng, source):
    d = DataValidation(type="list", formula1=source, allow_blank=True)
    d.error = "Pick a value from the list (edit lists on the Setup sheet)."
    d.errorTitle = "Not in list"
    ws.add_data_validation(d)
    d.add(rng)


def dv_date(ws, rng):
    d = DataValidation(type="date", operator="greaterThan", formula1="36526", allow_blank=True)
    d.error = "Enter a valid date, for example 15-Nov-2026."
    d.errorTitle = "Date needed"
    ws.add_data_validation(d)
    d.add(rng)


def write_table(ws, key, cols, rows=()):
    s = REG[key]
    hdr = s["hdr"]
    for j, c in enumerate(cols):
        col = s["col0"] + j
        ws.column_dimensions[CL(col)].width = c.get("w", 14)
        h = ws.cell(hdr, col, c["h"])
        h.font = fnt(9, True, WHITE)
        h.fill = fill(NAVY if c["kind"] == "in" else MIDNIGHT)
        h.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        h.border = BOX
    ws.row_dimensions[hdr].height = 32
    for r in range(s["first"], s["last"] + 1):
        i = r - s["first"]
        data = rows[i] if i < len(rows) else {}
        for j, c in enumerate(cols):
            cell = ws.cell(r, s["col0"] + j)
            if c["kind"] == "calc":
                f = c["f"]
                cell.value = "=" + (f(r) if callable(f) else fx(key, r, f))
                cell.fill = fill(LGRAY)
            else:
                v = data.get(c["h"])
                if v is not None:
                    cell.value = v
                cell.fill = fill(SOFT_BLUE)
            cell.font = fnt(9)
            cell.border = BOX
            cell.alignment = Alignment(vertical="center", wrap_text=c.get("wrap", False))
            if c.get("fmt"):
                cell.number_format = c["fmt"]
    ref = f"{CL(s['col0'])}{hdr}:{CL(s['col0'] + len(cols) - 1)}{s['last']}"
    tb = Table(displayName=s["tname"], ref=ref)
    tb.tableStyleInfo = TableStyleInfo(name="TableStyleLight1", showRowStripes=False)
    ws.add_table(tb)


def col_range(key, h):
    s = REG[key]
    c = s["L"][h]
    return f"{c}{s['first']}:{c}{s['last']}"


# ---------------------------------------------------------------- sample data
def D(y, m, dd):
    return dt.date(y, m, dd)


def t(h, m=0):
    return dt.time(h, m)


PROJECTS = [
    {"Project Name": "Website Redesign", "Description": "Rebuild the public website with the new brand guidelines",
     "Category": "Client Work", "Project Manager": "Alex Morgan", "Start Date": D(2026, 9, 1),
     "Due Date": D(2026, 12, 18), "Priority": "High", "Status": "Active"},
    {"Project Name": "Q4 Marketing Campaign", "Description": "Multi-channel holiday campaign",
     "Category": "Marketing", "Project Manager": "Priya Shah", "Start Date": D(2026, 10, 5),
     "Due Date": D(2026, 12, 31), "Priority": "High", "Status": "Active"},
    {"Project Name": "ERP Migration", "Description": "Move finance and inventory data to the new ERP",
     "Category": "Operations", "Project Manager": "Jonas Weber", "Start Date": D(2026, 7, 1),
     "Due Date": D(2026, 10, 30), "Priority": "Critical", "Status": "Active"},
    {"Project Name": "Mobile App v2", "Description": "Second release of the customer mobile app",
     "Category": "Product", "Project Manager": "Sam Lee", "Start Date": D(2026, 11, 1),
     "Due Date": D(2027, 2, 28), "Priority": "Medium", "Status": "Not Started"},
    {"Project Name": "Annual Audit Preparation", "Description": "Collect evidence and reconcile ledgers",
     "Category": "Operations", "Project Manager": "Maria Gomez", "Start Date": D(2026, 9, 15),
     "Due Date": D(2026, 11, 20), "Priority": "High", "Status": "On Hold"},
    {"Project Name": "Office Relocation", "Description": "Move the team to the downtown office",
     "Category": "Operations", "Project Manager": "Dan Okafor", "Start Date": D(2026, 3, 1),
     "Due Date": D(2026, 9, 30), "Priority": "Low", "Status": "Completed"},
]

P1, P2, P3, P4, P5, P6 = "PRJ-001", "PRJ-002", "PRJ-003", "PRJ-004", "PRJ-005", "PRJ-006"
TASKS = [
    ("Define sitemap and wireframes", P1, "Design", "Alex Morgan", D(2026, 10, 26), D(2026, 11, 6), "High", "In Progress", 16, 12, 0.6),
    ("Write homepage copy", P1, "Communication", "Priya Shah", D(2026, 10, 30), D(2026, 11, 10), "High", "To Do", 8, 0, 0),
    ("Build component library", P1, "Development", "Sam Lee", D(2026, 11, 2), D(2026, 11, 27), "Medium", "Backlog", 40, 0, 0),
    ("Stakeholder review of wireframes", P1, "Meeting", "Alex Morgan", D(2026, 11, 9), D(2026, 11, 9), "High", "To Do", 1, 0, 0),
    ("Launch readiness milestone", P1, "Milestone", "Alex Morgan", D(2026, 12, 18), D(2026, 12, 18), "Critical", "Backlog", 0, 0, 0),
    ("Weekly status report", P1, "Communication", "Alex Morgan", D(2026, 11, 2), D(2026, 11, 13), "Low", "In Progress", 2, 1, 0.5),
    ("Competitor research", P2, "Research", "Priya Shah", D(2026, 10, 5), D(2026, 10, 16), "Medium", "Completed", 12, 14, 1),
    ("Campaign creative brief", P2, "Design", "Priya Shah", D(2026, 10, 12), D(2026, 10, 23), "High", "Completed", 8, 9, 1),
    ("Media buying plan", P2, "Admin", "Priya Shah", D(2026, 10, 26), D(2026, 11, 4), "High", "In Progress", 10, 6, 0.5),
    ("Social content calendar", P2, "Communication", "Priya Shah", D(2026, 11, 2), D(2026, 11, 20), "Medium", "In Progress", 14, 3, 0.25),
    ("Landing page build", P2, "Development", "Sam Lee", D(2026, 11, 10), D(2026, 12, 4), "High", "Backlog", 24, 0, 0),
    ("Data migration mapping", P3, "Research", "Jonas Weber", D(2026, 7, 6), D(2026, 8, 14), "Critical", "Completed", 60, 72, 1),
    ("Finance module cutover", P3, "Development", "Jonas Weber", D(2026, 9, 1), D(2026, 10, 15), "Critical", "Review", 80, 84, 0.9),
    ("Inventory test cycles", P3, "Review", "Dan Okafor", D(2026, 9, 15), D(2026, 10, 28), "High", "In Progress", 40, 38, 0.7),
    ("Go-live sign-off", P3, "Milestone", "Jonas Weber", D(2026, 10, 30), D(2026, 10, 30), "Critical", "To Do", 2, 0, 0),
    ("Vendor invoice approval", P3, "Admin", "Dan Okafor", D(2026, 11, 3), D(2026, 11, 12), "High", "To Do", 3, 0, 0),
    ("Mobile app requirements", P4, "Research", "Sam Lee", D(2026, 11, 1), D(2026, 11, 13), "Medium", "To Do", 16, 0, 0),
    ("Prototype user flows", P4, "Design", "Sam Lee", D(2026, 11, 16), D(2026, 11, 30), "Medium", "Backlog", 20, 0, 0),
    ("Design review workshop", P4, "Meeting", "Sam Lee", D(2026, 11, 18), D(2026, 11, 18), "Medium", "Backlog", 2, 0, 0),
    ("Collect audit evidence", P5, "Admin", "Maria Gomez", D(2026, 9, 15), D(2026, 10, 31), "High", "In Progress", 30, 28, 0.8),
    ("Bank reconciliation", P5, "Admin", "Maria Gomez", D(2026, 10, 1), D(2026, 11, 13), "High", "To Do", 18, 0, 0),
    ("Auditor kickoff meeting", P5, "Meeting", "Maria Gomez", D(2026, 9, 16), D(2026, 9, 16), "Medium", "Completed", 1, 1, 1),
    ("Move inventory to new office", P6, "Other", "Dan Okafor", D(2026, 6, 1), D(2026, 9, 20), "Low", "Completed", 24, 22, 1),
    ("Office setup checklist", P6, "Admin", "Dan Okafor", D(2026, 8, 15), D(2026, 9, 30), "Low", "Completed", 6, 6, 1),
]
TASK_ROWS = [dict(zip(["Task Name", "Project ID", "Category", "Assigned To", "Start Date",
                       "Due Date", "Priority", "Status", "Est. Hours", "Actual Hours", "Progress"], t_),
                  Notes="DEMO DATA")
             for t_ in TASKS]
for row, t_ in zip(TASK_ROWS, TASKS):
    row["Description"] = f"{t_[0]} for {PROJECTS[int(t_[1][-1]) - 1]['Project Name']}"

BUDGET = [
    (P1, "Software", 2400, 1850, D(2026, 10, 3), "Figma and Notion", "Design and workspace licences"),
    (P1, "Services", 15000, 9500, D(2026, 10, 15), "Brightline Studio", "Design support retainer"),
    (P1, "Contingency", 2000, 0, None, "", "Reserve for scope changes"),
    (P2, "Marketing", 25000, 18200, D(2026, 10, 20), "Ad platforms", "Paid social and search"),
    (P2, "Services", 8000, 8950, D(2026, 11, 2), "Northwind Creative", "Creative production"),
    (P2, "Software", 1500, 1200, D(2026, 10, 8), "Mailforge", "Email platform"),
    (P3, "Software", 120000, 134500, D(2026, 9, 1), "ERP Vendor Ltd", "ERP licence and modules"),
    (P3, "Services", 60000, 58000, D(2026, 10, 2), "Atlas Consulting", "Implementation partner"),
    (P3, "Labour", 30000, 24000, D(2026, 10, 31), "Payroll", "Internal backfill"),
    (P3, "Contingency", 15000, 0, None, "", "Reserve"),
    (P4, "Labour", 20000, 0, None, "", "Development team allocation"),
    (P4, "Hardware", 3000, 0, None, "Techstore", "Test devices"),
    (P5, "Services", 12000, 11000, D(2026, 10, 25), "Keller Audit LLP", "External audit preparation"),
    (P5, "Travel", 1500, 640, D(2026, 10, 12), "Various", "Site visits"),
    (P6, "Travel", 4000, 3850, D(2026, 9, 18), "Swift Movers", "Moving logistics"),
    (P6, "Hardware", 6000, 5920, D(2026, 9, 25), "Desk Co", "Office furniture"),
]
BUDGET_ROWS = [dict(zip(["Project ID", "Budget Category", "Planned Budget", "Actual Expense",
                         "Expense Date", "Vendor", "Description"], b)) for b in BUDGET]

RECURRING = [
    ("Weekly team stand-up", "Meeting", "Priya Shah", "Weekly", None, D(2026, 10, 5), D(2026, 11, 2), "Active"),
    ("Monthly budget review", "Admin", "Jonas Weber", "Monthly", None, D(2026, 10, 1), D(2026, 11, 1), "Active"),
    ("Daily inbox triage", "Communication", "Alex Morgan", "Daily", None, D(2026, 11, 1), D(2026, 11, 5), "Active"),
    ("Biweekly client check-in", "Meeting", "Alex Morgan", "Biweekly", None, D(2026, 10, 14), D(2026, 10, 28), "Active"),
    ("Quarterly tax filing", "Admin", "Maria Gomez", "Quarterly", None, D(2026, 7, 15), D(2026, 10, 15), "Active"),
    ("Annual insurance renewal", "Admin", "Dan Okafor", "Annually", None, D(2025, 3, 10), D(2026, 3, 10), "Active"),
    ("Review supplier SLAs", "Review", "Sam Lee", "Custom", 10, D(2026, 10, 20), D(2026, 10, 30), "Paused"),
]
RECURRING_ROWS = [dict(zip(["Task Name", "Category", "Assigned To", "Frequency", "Custom Every (days)",
                            "Start Date", "Last Completed", "Status"], r_)) for r_ in RECURRING]
for row, r_ in zip(RECURRING_ROWS, RECURRING):
    row["Project ID"] = None

SCHEDULE = [
    (D(2026, 11, 2), t(9), t(10, 30), "Stand-up and planning", P1, "High", "Completed", "Alex Morgan"),
    (D(2026, 11, 2), t(11), t(12), "Wireframe review", P1, "High", "In Progress", "Alex Morgan"),
    (D(2026, 11, 3), t(10), t(11), "Media buying check", P2, "High", "To Do", "Priya Shah"),
    (D(2026, 11, 3), t(14), t(16), "Finance cutover rehearsal", P3, "Critical", "In Progress", "Jonas Weber"),
    (D(2026, 11, 4), t(9), t(10), "Audit evidence sweep", P5, "High", "To Do", "Maria Gomez"),
    (D(2026, 11, 4), t(13), t(15), "Mobile requirements workshop", P4, "Medium", "To Do", "Sam Lee"),
    (D(2026, 11, 5), t(9, 30), t(11), "Social calendar planning", P2, "Medium", "In Progress", "Priya Shah"),
    (D(2026, 11, 5), t(15), t(16), "Vendor invoice approval", P3, "High", "To Do", "Dan Okafor"),
    (D(2026, 11, 6), t(10), t(12), "Component library sprint", P1, "Medium", "Backlog", "Sam Lee"),
    (D(2026, 11, 6), t(13), t(14), "Status report", P1, "Low", "In Progress", "Alex Morgan"),
    (D(2026, 11, 9), t(9), t(10), "Stakeholder review", P1, "High", "To Do", "Alex Morgan"),
    (D(2026, 11, 10), t(11), t(12, 30), "Landing page kickoff", P2, "High", "Backlog", "Priya Shah"),
]
SCHEDULE_ROWS = [dict(zip(["Date", "Start Time", "End Time", "Task", "Project ID", "Priority", "Status",
                           "Assigned Person"], s_)) for s_ in SCHEDULE]

PM_ROWS = [
    {"Department": "Product", "Objectives": "Ship new brand site with 30% faster load time",
     "Key Deliverables": "Sitemap, design system, CMS build, launch", "Milestones": "Design sign-off; Beta; Launch",
     "Next Milestone": D(2026, 11, 9), "Team Members": "Alex Morgan, Sam Lee", "Dependencies": "Brand guidelines v3",
     "Risks": "Copy approvals may slip", "Risk Level": "Medium", "Notes": "DEMO DATA"},
    {"Department": "Marketing", "Objectives": "Generate 500 qualified leads in Q4",
     "Key Deliverables": "Creative set, media plan, landing pages", "Milestones": "Creative approved; Launch",
     "Next Milestone": D(2026, 11, 20), "Team Members": "Priya Shah, Sam Lee", "Dependencies": "Website Redesign landing page",
     "Risks": "Media costs above forecast", "Risk Level": "High", "Notes": "DEMO DATA"},
    {"Department": "Finance", "Objectives": "Cut over to the ERP with no ledger gaps",
     "Key Deliverables": "Data migration, module cutover, sign-off", "Milestones": "Cutover; Go-live",
     "Next Milestone": D(2026, 10, 30), "Team Members": "Jonas Weber, Dan Okafor", "Dependencies": "Vendor licence",
     "Risks": "Schedule overrun; budget over 100%", "Risk Level": "High", "Notes": "DEMO DATA"},
]


# ---------------------------------------------------------------- sheet builders
def build_setup(ws, wb):
    page(ws, "Setup", "Central configuration. Edit the blue values and lists; every dropdown in the workbook reads from here.",
         NAVY, demo=True, widths={"B": 22, "C": 24, "D": 3})
    section(ws, "B4", "PROFILE AND PREFERENCES")
    prof = [("Workspace name", "Ultimate Project Office", None),
            ("Owner", "Your name", None),
            ("Currency", "USD", None),
            ("Week starts on", "Monday", None),
            ("Working day starts", t(9), FMT_TIME),
            ("Working day ends", t(17, 30), FMT_TIME)]
    for i, (lab, val, fmt) in enumerate(prof):
        r = 5 + i
        label(ws, f"B{r}", lab, bold=True)
        inp(ws, f"C{r}", val, fmt)
    wb.defined_names["CurrencyCode"] = DefinedName("CurrencyCode", attr_text="Setup!$C$7")
    wb.defined_names["WeekStart"] = DefinedName("WeekStart", attr_text="Setup!$C$8")
    dv_list(ws, "C7", "CurrencyList")
    dv_list(ws, "C8", "WeekStartList")
    label(ws, "B12", "Amounts are shown in the currency above; formats follow your regional settings.")
    legend(ws, 14, 2)

    section(ws, "E4", "DROPDOWN SOURCE LISTS (edit the blue cells; keep each list contiguous, up to 15 items)")
    lists = [
        ("ProjectCategories", "Project categories", ["Client Work", "Marketing", "Operations", "Product", "Internal", "Personal"]),
        ("TaskCategories", "Task categories", ["Development", "Design", "Research", "Admin", "Meeting", "Review", "Milestone", "Communication", "Other"]),
        ("Priorities", "Priority levels", ["Critical", "High", "Medium", "Low"]),
        ("TaskStatuses", "Task statuses", ["Backlog", "To Do", "In Progress", "Review", "Completed"]),
        ("ProjectStatuses", "Project statuses", ["Not Started", "Active", "On Hold", "Completed", "Cancelled"]),
        ("TeamMembers", "Team members", ["Alex Morgan", "Priya Shah", "Jonas Weber", "Sam Lee", "Maria Gomez", "Dan Okafor"]),
        ("Departments", "Departments", ["Operations", "Marketing", "Finance", "Product", "Engineering", "Sales", "HR"]),
        ("PaymentCategories", "Budget categories", ["Labour", "Software", "Hardware", "Travel", "Marketing", "Services", "Contingency"]),
        ("MonthList", "Months", MONTHS),
        ("YearList", "Years", list(range(2025, 2036))),
        ("CurrencyList", "Currencies", ["USD", "EUR", "GBP", "MAD", "CAD", "AUD", "INR"]),
        ("WeekStartList", "Week start", ["Monday", "Sunday"]),
        ("FrequencyList", "Recurrence", ["Daily", "Weekly", "Biweekly", "Monthly", "Quarterly", "Annually", "Custom"]),
        ("RiskLevels", "Risk levels", ["High", "Medium", "Low"]),
        ("ActiveList", "Recurring status", ["Active", "Paused"]),
        ("DueWindowList", "Due window", ["All", "Overdue", "Next 7 days", "No due date"]),
        ("CompletionList", "Completion", ["All", "Completed", "Not completed"]),
        ("OverdueList", "Overdue", ["All", "Yes", "No"]),
    ]
    for i, (nm, lab, items) in enumerate(lists):
        col = CL(5 + i)
        ws.column_dimensions[col].width = 18
        h = ws[f"{col}5"]
        h.value = lab
        h.font = fnt(9, True, WHITE)
        h.fill = fill(NAVY)
        h.alignment = Alignment(horizontal="center", wrap_text=True)
        h.border = BOX
        for j, v in enumerate(items):
            inp(ws, f"{col}{6 + j}", v)
        for j in range(len(items), 15):
            inp(ws, f"{col}{6 + j}")
        wb.defined_names[nm] = DefinedName(nm, attr_text=f"Setup!${col}$6:${col}$20")
    ws.row_dimensions[5].height = 30
    ws.freeze_panes = "A6"


def build_dashboard(ws):
    page(ws, "All-in-One Dashboard", "Executive view. Every number updates from the Project, Task and Budget tables.",
         BLUE, demo=True)
    for col in "BCDEFGHIJKLM":
        ws.column_dimensions[col].width = 14
    ws.column_dimensions["N"].width = 3
    for col in "PQRSTUVWXY":
        ws.column_dimensions[col].width = 14

    def pos(i):
        return f"{['B', 'E', 'H', 'K'][i % 4]}{6 + 4 * (i // 4)}"

    kpis = [
        ("TOTAL PROJECTS", f'=COUNTIF({PID},"?*")', "0", "projects in portfolio"),
        ("ACTIVE PROJECTS", f'=COUNTIF({PST},"Active")', "0", "currently running"),
        ("COMPLETED PROJECTS", f'=COUNTIF({PST},"Completed")', "0", "delivered"),
        ("OVERDUE PROJECTS", f'=COUNTIFS({PDUE},"<"&TODAY(),{PST},"<>Completed",{PID},"?*")', "0", "past due, not completed"),
        ("TOTAL TASKS", f'=COUNTIF({TID},"?*")', "0", "one-time tasks"),
        ("COMPLETED TASKS", f'=COUNTIFS({TID},"?*",{TST},"Completed")', "0", "marked Completed"),
        ("PENDING TASKS", f'=COUNTIFS({TID},"?*",{TST},"<>Completed")', "0", "open tasks"),
        ("COMPLETION RATE", f'=IFERROR(COUNTIFS({TID},"?*",{TST},"Completed")/COUNTIF({TID},"?*"),0)', "0%", "completed / total tasks"),
        ("TOTAL PROJECT BUDGET", f'=SUM({BPLAN})', FMT_MONEY, "planned, all expense lines"),
        ("ACTUAL SPENDING", f'=SUM({BACT})', FMT_MONEY, "recorded expenses"),
        ("REMAINING BUDGET", f"={pos(8)}-{pos(9)}", FMT_MONEY, "budget minus spending"),
    ]
    for i, (lab, f, fmt, sub) in enumerate(kpis):
        k = i // 4
        c0 = 2 + 3 * (i % 4)
        r0 = 5 + 4 * k
        for rr, txt, fn_, col_ in ((r0, lab, fnt(8, True, SEC), SEC), (r0 + 1, f, fnt(20, True, NAVY), NAVY),
                                   (r0 + 2, sub, fnt(8, False, SEC), SEC)):
            ws.merge_cells(start_row=rr, start_column=c0, end_row=rr, end_column=c0 + 2)
            cell = ws.cell(rr, c0, txt)
            cell.font = fn_
            cell.alignment = Alignment(horizontal="left", vertical="center", indent=1)
            for cc in range(c0, c0 + 3):
                ws.cell(rr, cc).fill = fill(WHITE)
                ws.cell(rr, cc).border = Border(
                    left=SIDE if cc == c0 else None, right=SIDE if cc == c0 + 2 else None,
                    top=SIDE if rr == r0 else None, bottom=SIDE if rr == r0 + 2 else None)
        ws.cell(r0 + 1, c0).number_format = fmt
        ws.row_dimensions[r0 + 1].height = 30

    # chart data block (auto)
    section(ws, "P4", "CHART DATA (automatic; do not type here)")
    hdrs = {"P": "Project status", "Q": "Projects", "R": "Task status", "S": "Tasks",
            "T": "Month", "U": "Due", "V": "Completed", "W": "Project", "X": "Budget", "Y": "Actual"}
    for col, h in hdrs.items():
        c = ws[f"{col}5"]
        c.value = h
        c.font = fnt(8, True, WHITE)
        c.fill = fill(MIDNIGHT)
    for k in range(5):
        r = 6 + k
        ws[f"P{r}"] = f"=Setup!I{6 + k}"
        ws[f"Q{r}"] = f'=COUNTIF({PST},P{r})'
        ws[f"R{r}"] = f"=Setup!H{6 + k}"
        ws[f"S{r}"] = f'=COUNTIF({TST},R{r})'
    for k in range(6):
        r = 6 + k
        start = f"DATE(YEAR(TODAY()),MONTH(TODAY())-{5 - k},1)"
        nxt = f"DATE(YEAR(TODAY()),MONTH(TODAY())-{4 - k},1)"
        ws[f"T{r}"] = f'=TEXT({start},"mmm yy")'
        ws[f"U{r}"] = f'=COUNTIFS({TDUE},">="&{start},{TDUE},"<"&{nxt},{TID},"?*")'
        ws[f"V{r}"] = f'=COUNTIFS({TDUE},">="&{start},{TDUE},"<"&{nxt},{TST},"Completed")'
    for k in range(8):
        r = 6 + k
        src = 6 + k
        ws[f"W{r}"] = f"=IF('Project Overview'!C{src}=\"\",\"\",'Project Overview'!C{src})"
        ws[f"X{r}"] = f"=IF(W{r}=\"\",0,N('Project Overview'!{PC['Budget']}{src}))"
        ws[f"Y{r}"] = f"=IF(W{r}=\"\",0,N('Project Overview'!{PC['Actual Cost']}{src}))"
    for row in ws["P5:Y13"]:
        for c in row:
            c.font = fnt(8, False, DARK)
            if c.column_letter in "XY":
                c.number_format = FMT_MONEY

    # charts
    dn = DoughnutChart()
    dn.title = "Project status"
    dn.add_data(Reference(ws, min_col=17, min_row=5, max_row=10), titles_from_data=True)
    dn.set_categories(Reference(ws, min_col=16, min_row=6, max_row=10))
    colors = [MGRAY, BLUE, WARN, SUCCESS, DANGER]
    for idx, colr in enumerate(colors):
        pt = DataPoint(idx=idx)
        pt.graphicalProperties.solidFill = colr
        dn.series[0].dPt.append(pt)
    dn.width, dn.height = 12.5, 7.5
    dn.legend.position = "r"
    ws.add_chart(dn, "B18")

    bs = BarChart()
    bs.type = "bar"
    bs.title = "Task completion by status"
    bs.add_data(Reference(ws, min_col=19, min_row=5, max_row=10), titles_from_data=True)
    bs.set_categories(Reference(ws, min_col=18, min_row=6, max_row=10))
    bs.series[0].graphicalProperties.solidFill = BLUE
    bs.series[0].graphicalProperties.line.solidFill = BLUE
    bs.legend = None
    bs.width, bs.height = 12.5, 7.5
    ws.add_chart(bs, "G18")

    mc = BarChart()
    mc.type = "col"
    mc.title = "Monthly productivity (tasks due vs completed)"
    mc.add_data(Reference(ws, min_col=21, max_col=22, min_row=5, max_row=11), titles_from_data=True)
    mc.set_categories(Reference(ws, min_col=20, min_row=6, max_row=11))
    mc.series[0].graphicalProperties.solidFill = MGRAY
    mc.series[1].graphicalProperties.solidFill = TEAL
    mc.width, mc.height = 12.5, 7.5
    mc.legend.position = "b"
    ws.add_chart(mc, "B34")

    bc = BarChart()
    bc.type = "bar"
    bc.title = "Project budget vs actual spending"
    bc.add_data(Reference(ws, min_col=24, max_col=25, min_row=5, max_row=13), titles_from_data=True)
    bc.set_categories(Reference(ws, min_col=23, min_row=6, max_row=13))
    bc.series[0].graphicalProperties.solidFill = BLUE
    bc.series[1].graphicalProperties.solidFill = LAV
    bc.width, bc.height = 12.5, 7.5
    bc.legend.position = "b"
    ws.add_chart(bc, "G34")

    # lists
    section(ws, "B51", "UPCOMING DEADLINES")
    section(ws, "I51", "OVERDUE TASKS")
    section(ws, "B63", "RECENT ACTIVITY (latest start dates)")
    section(ws, "I63", "PROJECT PERFORMANCE")

    def head(cell_range, text):
        first = cell_range.split(":")[0]
        ws.merge_cells(cell_range) if ":" in cell_range else None
        c = ws[first]
        c.value = text
        c.font = fnt(8, True, WHITE)
        c.fill = fill(NAVY)
        c.alignment = Alignment(horizontal="left", indent=1)

    for rng, t_ in (("B52:D52", "Task"), ("E52", "Project"), ("F52", "Due"), ("G52", "Days left"),
                    ("I52:K52", "Task"), ("L52", "Assigned"), ("M52", "Days overdue"),
                    ("B64:D64", "Task"), ("E64", "Status"), ("F64", "Start"),
                    ("I64:J64", "Project"), ("K64", "Progress"), ("L64", "Budget used"), ("M64", "Health")):
        head(rng, t_)

    for n in range(1, 9):
        r = 52 + n
        ws.merge_cells(f"B{r}:D{r}")
        ws[f"B{r}"] = f'=IFERROR(INDEX({TN},MATCH(SMALL({R("tasks", "Deadline Key")},{n}),{R("tasks", "Deadline Key")},0)),"")'
        ws[f"E{r}"] = f'=IFERROR(INDEX({TPID},MATCH(SMALL({R("tasks", "Deadline Key")},{n}),{R("tasks", "Deadline Key")},0)),"")'
        ws[f"F{r}"] = f'=IFERROR(INT(SMALL({R("tasks", "Deadline Key")},{n})),"")'
        ws[f"F{r}"].number_format = FMT_DATE
        ws[f"G{r}"] = f'=IFERROR(INT(SMALL({R("tasks", "Deadline Key")},{n}))-TODAY(),"")'
        ws[f"G{r}"].number_format = FMT_DAYS
        ws.merge_cells(f"I{r}:K{r}")
        ws[f"I{r}"] = f'=IFERROR(INDEX({TN},MATCH(SMALL({R("tasks", "Overdue Key")},{n}),{R("tasks", "Overdue Key")},0)),"")'
        ws[f"L{r}"] = f'=IFERROR(INDEX({TAS},MATCH(SMALL({R("tasks", "Overdue Key")},{n}),{R("tasks", "Overdue Key")},0)),"")'
        ws[f"M{r}"] = f'=IFERROR(TODAY()-INT(SMALL({R("tasks", "Overdue Key")},{n})),"")'
        ws[f"M{r}"].number_format = "0"
        for col in "BEFGILM":
            ws[f"{col}{r}"].font = fnt(9)
            ws[f"{col}{r}"].fill = fill(WHITE)
    for n in range(1, 7):
        r = 64 + n
        ws.merge_cells(f"B{r}:D{r}")
        ws[f"B{r}"] = f'=IFERROR(INDEX({TN},MATCH(LARGE({R("tasks", "Recent Key")},{n}),{R("tasks", "Recent Key")},0)),"")'
        ws[f"E{r}"] = f'=IFERROR(INDEX({TST},MATCH(LARGE({R("tasks", "Recent Key")},{n}),{R("tasks", "Recent Key")},0)),"")'
        ws[f"F{r}"] = f'=IFERROR(INT(LARGE({R("tasks", "Recent Key")},{n})),"")'
        ws[f"F{r}"].number_format = FMT_DATE
        for col in "BEF":
            ws[f"{col}{r}"].font = fnt(9)
    for i in range(8):
        r = 65 + i
        src = 6 + i
        ws.merge_cells(f"I{r}:J{r}")
        ws[f"I{r}"] = f"=IF('Project Overview'!C{src}=\"\",\"\",'Project Overview'!C{src})"
        ws[f"K{r}"] = f"=IF(I{r}=\"\",\"\",N('Project Overview'!{PC['Progress']}{src}))"
        ws[f"K{r}"].number_format = FMT_PCT
        ws[f"L{r}"] = f"=IF(I{r}=\"\",\"\",IFERROR('Project Overview'!{PC['Actual Cost']}{src}/'Project Overview'!{PC['Budget']}{src},\"\"))"
        ws[f"L{r}"].number_format = FMT_PCT
        ws[f"M{r}"] = (f"=IF(I{r}=\"\",\"\",IF('Project Overview'!{PC['Status']}{src}=\"Completed\",\"Complete\","
                       f"IF(AND(ISNUMBER('Project Overview'!{PC['Due Date']}{src}),'Project Overview'!{PC['Due Date']}{src}<TODAY()),\"Overdue\","
                       f"IF(AND(ISNUMBER(L{r}),N(L{r})>1),\"Over budget\","
                       f"IF('Project Overview'!{PC['Status']}{src}=\"On Hold\",\"On hold\",\"On track\")))))")
        for col in "IKLM":
            ws[f"{col}{r}"].font = fnt(9)
    databar(ws, "K65:K72", TEAL)
    cf(ws, "M65:M72", 'OR($M65="Overdue",$M65="Over budget")', DANGER_BG, DANGER, True)
    cf(ws, "M65:M72", '$M65="Complete"', SUCCESS_BG, SUCCESS, True)
    cf(ws, "M65:M72", '$M65="On track"', SUCCESS_BG, SUCCESS, False)
    cf(ws, "G53:G60", 'AND(ISNUMBER($G53),$G53<=3)', WARN_BG, DARK, False)
    cf(ws, "M53:M60", 'ISNUMBER($M53)', DANGER_BG, DANGER, True)
    ws.freeze_panes = "A4"


def build_monthly(ws):
    page(ws, "Monthly Calendar", "Pick a month and year. Dates, due counts and the day agenda update automatically.",
         BLUE, demo=True, widths={"B": 12, "C": 12, "D": 12, "E": 12, "F": 12, "G": 12, "H": 12,
                                  "I": 3, "J": 28, "K": 12, "L": 14, "M": 14})
    label(ws, "B4", "Month", True)
    inp(ws, "C4", "November")
    label(ws, "E4", "Year", True)
    inp(ws, "F4", 2026)
    dv_list(ws, "C4", "MonthList")
    dv_list(ws, "F4", "YearList")
    label(ws, "J4", "Agenda for", True)
    inp(ws, "K4", D(2026, 11, 6), FMT_DATE)
    dv_date(ws, "K4")
    # stats row
    label(ws, "B5", "Tasks due this month")
    ws["D5"] = (f'=COUNTIFS({TDUE},">="&$P$4,{TDUE},"<="&EOMONTH($P$4,0),{TID},"?*")')
    label(ws, "F5", "Completed")
    ws["H5"] = (f'=COUNTIFS({TDUE},">="&$P$4,{TDUE},"<="&EOMONTH($P$4,0),{TST},"Completed")')
    label(ws, "J5", "Project deadlines this month")
    ws["L5"] = f'=COUNTIFS({PDUE},">="&$P$4,{PDUE},"<="&EOMONTH($P$4,0),{PID},"?*")'
    for c in ("D5", "H5", "L5"):
        ws[c].font = fnt(12, True, NAVY)
    # helpers
    ws["P4"] = "=DATE($F$4,IFERROR(MATCH($C$4,MonthList,0),11),1)"
    ws["Q4"] = "=DAY(EOMONTH($P$4,0))"
    ws["R4"] = "=MOD(WEEKDAY($P$4,1)-$S$4,7)"
    ws["S4"] = '=IF(WeekStart="Sunday",1,2)'
    for c in ("P4",):
        ws[c].number_format = FMT_DATE
    for c in ("P4", "Q4", "R4", "S4"):
        ws[c].font = fnt(8, False, SEC)
    ws.column_dimensions["P"].hidden = True
    ws.column_dimensions["Q"].hidden = True
    ws.column_dimensions["R"].hidden = True
    ws.column_dimensions["S"].hidden = True

    cols = "BCDEFGH"
    for c in range(7):
        cell = ws[f"{cols[c]}7"]
        cell.value = f'=CHOOSE(MOD($S$4-1+{c},7)+1,"Sun","Mon","Tue","Wed","Thu","Fri","Sat")'
        cell.font = fnt(9, True, WHITE)
        cell.fill = fill(NAVY)
        cell.alignment = Alignment(horizontal="center")
    ws.row_dimensions[7].height = 20
    for w in range(6):
        rd = 8 + 3 * w
        for c in range(7):
            X = cols[c]
            e = f"({7 * w + c}-$R$4)"
            cd = ws[f"{X}{rd}"]
            cd.value = f'=IF(AND({e}>=0,{e}<$Q$4),$P$4+{e},"")'
            cd.number_format = "d"
            cd.font = fnt(11, True, NAVY)
            cd.alignment = Alignment(horizontal="left", vertical="top", indent=1)
            cd.fill = fill(WHITE)
            cd.border = BOX
            n_due = (f'COUNTIFS({TDUE},{X}{rd},{TST},"<>Completed")+COUNTIFS({PDUE},{X}{rd},{PST},"<>Completed")')
            cdue = ws[f"{X}{rd + 1}"]
            cdue.value = f'=IF({X}{rd}="","",IF({n_due}=0,"",{n_due}&" due"))'
            cdue.font = fnt(8, True, DARK)
            cdue.fill = fill(SOFT_BLUE)
            cdue.border = BOX
            csch = ws[f"{X}{rd + 2}"]
            csch.value = f'=IF({X}{rd}="","",IF(COUNTIF({SDATE},{X}{rd})=0,"",COUNTIF({SDATE},{X}{rd})&" block(s)"))'
            csch.font = fnt(8, False, SEC)
            csch.fill = fill(SOFT_LAV)
            csch.border = BOX
        ws.row_dimensions[rd].height = 22
        cf(ws, f"B{rd}:H{rd}", f"AND(ISNUMBER(B{rd}),B{rd}=TODAY())", BLUE, WHITE, True)
        cf(ws, f"B{rd}:H{rd}", f'AND(ISNUMBER(B{rd}),B{rd}<TODAY(),COUNTIFS({TDUE},B{rd},{TST},"<>Completed")>0)',
           DANGER_BG, DANGER, True)

    # agenda
    for col, h in zip("JKLM", ["Task on this day", "Priority", "Status", "Project"]):
        c = ws[f"{col}7"]
        c.value = h
        c.font = fnt(9, True, WHITE)
        c.fill = fill(MIDNIGHT)
    for n in range(1, 11):
        r = 7 + n
        ws[f"J{r}"] = "=" + pick("tasks", "Task Name", n, "Agenda Key")
        ws[f"K{r}"] = "=" + pick("tasks", "Priority", n, "Agenda Key")
        ws[f"L{r}"] = "=" + pick("tasks", "Status", n, "Agenda Key")
        ws[f"M{r}"] = "=" + pick("tasks", "Project ID", n, "Agenda Key")
        for col in "JKLM":
            ws[f"{col}{r}"].font = fnt(9)
            ws[f"{col}{r}"].border = BOX
    cf(ws, "K8:K17", '$K8="Critical"', DANGER_BG, DANGER, True)
    cf(ws, "K8:K17", '$K8="High"', WARN_BG, DARK, True)
    cf(ws, "L8:L17", '$L8="Completed"', SUCCESS_BG, SUCCESS, True)
    label(ws, "J19", "Legend: blue date = today; red date = overdue tasks on that day; 'due' counts open tasks and project deadlines.")
    legend(ws, 21, 10)
    ws.freeze_panes = "A8"


def build_weekly(ws):
    page(ws, "Weekly Calendar", "Enter any date in the week you want. The grid, workload and completion stats update automatically.",
         BLUE, demo=True, widths={"B": 9, "C": 19, "D": 19, "E": 19, "F": 19, "G": 19, "H": 19,
                                  "I": 19, "J": 3, "K": 28, "L": 14})
    label(ws, "B4", "Week containing", True)
    inp(ws, "C4", D(2026, 11, 2), FMT_DATE)
    dv_date(ws, "C4")
    label(ws, "E4", "Week starts", True)
    ws["F4"] = '=C4-MOD(WEEKDAY(C4,1)-IF(WeekStart="Sunday",1,2),7)'
    ws["F4"].number_format = FMT_DATE
    ws["F4"].font = fnt(9, True, NAVY)
    label(ws, "H4", "Week ends", True)
    ws["I4"] = "=F4+6"
    ws["I4"].number_format = FMT_DATE
    ws["I4"].font = fnt(9, True, NAVY)
    cols = "CDEFGHI"
    ws["B7"] = "Time"
    ws["B7"].font = fnt(9, True, WHITE)
    ws["B7"].fill = fill(NAVY)
    for k, X in enumerate(cols):
        h = ws[f"{X}7"]
        h.value = f'=TEXT({X}8,"dddd")'
        h.font = fnt(9, True, WHITE)
        h.fill = fill(NAVY)
        h.alignment = Alignment(horizontal="center")
        dte = ws[f"{X}8"]
        dte.value = f"=$F$4+{k}"
        dte.number_format = "dd mmm yyyy"
        dte.font = fnt(9, True, NAVY)
        dte.fill = fill(SOFT_BLUE)
        dte.alignment = Alignment(horizontal="center")
    for i, hour in enumerate(range(7, 21)):
        r = 9 + i
        hc = ws[f"B{r}"]
        hc.value = hour
        hc.number_format = '00":00"'
        hc.font = fnt(9, True, SEC)
        hc.fill = fill(LGRAY)
        for X in cols:
            m = f"MATCH({X}$8*100+$B{r},{SSLOT},0)"
            cell = ws[f"{X}{r}"]
            cell.value = (f'=IFERROR(LEFT(INDEX({SPRI},{m}),1)&" "&INDEX({STASK},{m})&" · "&INDEX({SPROJ},{m}),"")')
            cell.font = fnt(8)
            cell.alignment = Alignment(wrap_text=True, vertical="center")
            cell.border = BOX
        ws.row_dimensions[r].height = 30
    rng = "C9:I22"
    cf(ws, rng, 'LEFT(C9,2)="C "', DANGER_BG, DANGER, True)
    cf(ws, rng, 'LEFT(C9,2)="H "', WARN_BG, DARK, True)
    cf(ws, rng, 'LEFT(C9,2)="M "', INFO_BG, DARK, True)
    cf(ws, rng, 'LEFT(C9,2)="L "', SOFT_TEAL, DARK, True)

    # workload
    labels = [(24, "Scheduled blocks"), (25, "Scheduled hours"), (26, "Tasks due"), (27, "Tasks completed")]
    for r, lab in labels:
        label(ws, f"B{r}", lab, True)
    for X in cols:
        ws[f"{X}24"] = f"=COUNTIF({SDATE},{X}$8)"
        ws[f"{X}25"] = f"=SUMIFS({SDUR},{SDATE},{X}$8)"
        ws[f"{X}25"].number_format = FMT_HRS
        ws[f"{X}26"] = f'=COUNTIFS({TDUE},{X}$8,{TID},"?*")'
        ws[f"{X}27"] = f'=COUNTIFS({TDUE},{X}$8,{TST},"Completed")'
        for r in range(24, 28):
            ws[f"{X}{r}"].fill = fill(LGRAY)
            ws[f"{X}{r}"].font = fnt(9, True, DARK)
            ws[f"{X}{r}"].alignment = Alignment(horizontal="center")
            ws[f"{X}{r}"].border = BOX
    cf(ws, "C24:I24", "C24>=4", WARN_BG, DARK, True)

    section(ws, "K7", "WEEKLY COMPLETION STATS")
    stats = [
        ("Tasks due this week", f'=COUNTIFS({TDUE},">="&$F$4,{TDUE},"<="&$I$4,{TID},"?*")', "0"),
        ("Tasks completed", f'=COUNTIFS({TDUE},">="&$F$4,{TDUE},"<="&$I$4,{TST},"Completed")', "0"),
        ("Weekly completion rate", "=IFERROR(L9/L8,0)", "0%"),
        ("Scheduled hours", f'=SUMIFS({SDUR},{SDATE},">="&$F$4,{SDATE},"<="&$I$4)', FMT_HRS),
        ("Scheduled blocks", f'=COUNTIFS({SDATE},">="&$F$4,{SDATE},"<="&$I$4)', "0"),
        ("High and critical tasks due", (f'=COUNTIFS({TDUE},">="&$F$4,{TDUE},"<="&$I$4,{TPRI},"High")'
                                          f'+COUNTIFS({TDUE},">="&$F$4,{TDUE},"<="&$I$4,{TPRI},"Critical")'), "0"),
        ("Busiest day", "=INDEX($C$8:$I$8,MATCH(MAX($C$24:$I$24),$C$24:$I$24,0))", "dddd"),
    ]
    for i, (lab, f, fmt) in enumerate(stats):
        r = 8 + i
        label(ws, f"K{r}", lab, True)
        ws[f"L{r}"] = f
        ws[f"L{r}"].number_format = fmt
        ws[f"L{r}"].fill = fill(LGRAY)
        ws[f"L{r}"].font = fnt(10, True, NAVY)
        ws[f"L{r}"].border = BOX
    label(ws, "K17", "Cell text: priority letter (C, H, M, L), task, then project ID.")
    legend(ws, 19, 11)
    ws.freeze_panes = "C9"


def build_proj_overview(ws):
    page(ws, "Project Overview", "Project portfolio. Type a name to start a project; ID, progress, budget and cost calculate.",
         TEAL, demo=True)
    write_table(ws, "proj", PROJ_COLS, PROJECTS)
    rng = f"B6:O55"
    for r in range(6, 56):
        ws[f"K{r}"].number_format = FMT_PCT
    dv_list(ws, col_range("proj", "Category"), "ProjectCategories")
    dv_list(ws, col_range("proj", "Project Manager"), "TeamMembers")
    dv_list(ws, col_range("proj", "Priority"), "Priorities")
    dv_list(ws, col_range("proj", "Status"), "ProjectStatuses")
    dv_date(ws, col_range("proj", "Start Date"))
    dv_date(ws, col_range("proj", "Due Date"))
    databar(ws, "K6:K55", TEAL)
    cf(ws, "I6:I55", '$I6="Critical"', DANGER_BG, DANGER, True)
    cf(ws, "I6:I55", '$I6="High"', WARN_BG, DARK, True)
    cf(ws, "J6:J55", '$J6="Completed"', SUCCESS_BG, SUCCESS, True)
    cf(ws, "J6:J55", '$J6="Active"', INFO_BG, INFO, True)
    cf(ws, "J6:J55", '$J6="On Hold"', WARN_BG, DARK, True)
    cf(ws, "O6:O55", 'AND(ISNUMBER($O6),$O6<0)', DANGER_BG, DANGER, True)
    cf(ws, "O6:O55", 'AND(ISNUMBER($O6),$O6>=0,$O6<=7)', WARN_BG, DARK, True)
    cf(ws, "N6:N55", 'AND(ISNUMBER($N6),$N6<0)', DANGER_BG, DANGER, True)
    cf(ws, "N6:N55", 'AND(ISNUMBER($N6),$N6>=0)', SUCCESS_BG, SUCCESS, False)
    legend(ws, 3, 12)
    ws.freeze_panes = "C6"


def build_pm(ws):
    page(ws, "Project Manager", "Detailed tracking per project. Row numbers match the Project Overview rows.",
         TEAL, demo=True)
    write_table(ws, "pm", PM_COLS, PM_ROWS)
    for r in range(6, 56):
        ws[f"O{r}"].number_format = FMT_PCT
        ws[f"N{r}"].number_format = FMT_PCT
    dv_list(ws, col_range("pm", "Department"), "Departments")
    dv_list(ws, col_range("pm", "Risk Level"), "RiskLevels")
    dv_date(ws, col_range("pm", "Next Milestone"))
    cf(ws, "M6:M55", '$M6="High"', DANGER_BG, DANGER, True)
    cf(ws, "M6:M55", '$M6="Medium"', WARN_BG, DARK, True)
    databar(ws, "N6:N55", TEAL)
    ws.freeze_panes = "C6"


def build_budget(ws):
    page(ws, "Project Budget", "Expense lines per project. Choose a Project ID; utilisation and alerts calculate automatically.",
         TEAL, demo=True)
    write_table(ws, "bud", BUD_COLS, BUDGET_ROWS)
    for r in range(6, 306):
        ws[f"H{r}"].number_format = FMT_PCT
    dv_list(ws, col_range("bud", "Project ID"), "ProjectIDList")
    dv_list(ws, col_range("bud", "Budget Category"), "PaymentCategories")
    dv_date(ws, col_range("bud", "Expense Date"))
    cf(ws, "L6:L305", '$L6="Over budget"', DANGER_BG, DANGER, True)
    cf(ws, "L6:L305", '$L6="Near limit"', WARN_BG, DARK, True)
    cf(ws, "L6:L305", '$L6="On track"', SUCCESS_BG, SUCCESS, True)
    cf(ws, "G6:G305", 'AND(ISNUMBER($G6),$G6<0)', DANGER_BG, DANGER, True)
    legend(ws, 3, 12)
    ws.freeze_panes = "C6"


def build_tasks(ws):
    page(ws, "Variable Tasks", "One-time task database. Type a name and pick the options; flags and keys calculate automatically.",
         LAV, demo=True)
    write_table(ws, "tasks", TASK_COLS, TASK_ROWS)
    for r in range(6, 306):
        ws[f"N{r}"].number_format = FMT_PCT
    dv_list(ws, col_range("tasks", "Project ID"), "ProjectIDList")
    dv_list(ws, col_range("tasks", "Category"), "TaskCategories")
    dv_list(ws, col_range("tasks", "Assigned To"), "TeamMembers")
    dv_list(ws, col_range("tasks", "Priority"), "Priorities")
    dv_list(ws, col_range("tasks", "Status"), "TaskStatuses")
    dv_date(ws, col_range("tasks", "Start Date"))
    dv_date(ws, col_range("tasks", "Due Date"))
    cf(ws, "K6:K305", '$K6="Completed"', SUCCESS_BG, SUCCESS, True)
    cf(ws, "K6:K305", '$K6="In Progress"', INFO_BG, INFO, True)
    cf(ws, "K6:K305", '$K6="Review"', SOFT_LAV, DARK, True)
    cf(ws, "J6:J305", '$J6="Critical"', DANGER_BG, DANGER, True)
    cf(ws, "J6:J305", '$J6="High"', WARN_BG, DARK, True)
    cf(ws, "Q6:Q305", '$Q6="Yes"', DANGER_BG, DANGER, True)
    cf(ws, "P6:P305", 'AND(ISNUMBER($P6),$P6<0)', DANGER_BG, DANGER, True)
    cf(ws, "P6:P305", 'AND(ISNUMBER($P6),$P6>=0,$P6<=3)', WARN_BG, DARK, True)
    databar(ws, "N6:N305", TEAL)
    # helper keys are supporting columns: group and grey them
    for col in "RSTUVWX":
        ws.column_dimensions[col].outlineLevel = 1
        ws.column_dimensions[col].hidden = True
    legend(ws, 3, 12)
    ws.freeze_panes = "C6"


def build_recurring(ws):
    page(ws, "Recurring Tasks", "Repeating work. Enter Last Completed when you finish an occurrence; the next one is calculated.",
         LAV, demo=True)
    write_table(ws, "rec", REC_COLS, RECURRING_ROWS)
    for r in range(6, 56):
        ws[f"H{r}"].number_format = "0"
    dv_list(ws, col_range("rec", "Project ID"), "ProjectIDList")
    dv_list(ws, col_range("rec", "Category"), "TaskCategories")
    dv_list(ws, col_range("rec", "Assigned To"), "TeamMembers")
    dv_list(ws, col_range("rec", "Frequency"), "FrequencyList")
    dv_list(ws, col_range("rec", "Status"), "ActiveList")
    cf(ws, "N6:N55", '$N6="Overdue"', DANGER_BG, DANGER, True)
    cf(ws, "N6:N55", '$N6="Due soon"', WARN_BG, DARK, True)
    cf(ws, "N6:N55", '$N6="On schedule"', SUCCESS_BG, SUCCESS, True)
    cf(ws, "N6:N55", '$N6="Paused"', SOFT_LAV, DARK, True)
    legend(ws, 3, 12)
    ws.freeze_panes = "C6"


def build_schedule(ws):
    page(ws, "Task Schedule", "Time-blocked schedule. Each block appears on the Weekly Calendar in its start hour.",
         LAV, demo=True)
    write_table(ws, "sch", SCH_COLS, SCHEDULE_ROWS)
    for r in range(6, 206):
        ws[f"D{r}"].number_format = FMT_TIME
        ws[f"E{r}"].number_format = FMT_TIME
    dv_list(ws, col_range("sch", "Project ID"), "ProjectIDList")
    dv_list(ws, col_range("sch", "Priority"), "Priorities")
    dv_list(ws, col_range("sch", "Status"), "TaskStatuses")
    dv_list(ws, col_range("sch", "Assigned Person"), "TeamMembers")
    dv_date(ws, col_range("sch", "Date"))
    cf(ws, "H6:H205", '$H6="Critical"', DANGER_BG, DANGER, True)
    cf(ws, "H6:H205", '$H6="High"', WARN_BG, DARK, True)
    cf(ws, "I6:I205", '$I6="Completed"', SUCCESS_BG, SUCCESS, True)
    ws.column_dimensions["L"].hidden = True
    legend(ws, 3, 12)
    ws.freeze_panes = "C6"


def build_filter(ws, wb):
    page(ws, "Task Filter", "Choose any combination of filters. Matching tasks list below and update instantly.",
         LAV, demo=True, widths={"B": 6, "C": 12, "D": 34, "E": 12, "F": 14, "G": 16, "H": 11,
                                 "I": 13, "J": 13, "K": 11, "L": 11})
    filters = [("Project", "All", "FilterProject"), ("Priority", "All", "FilterPriority"),
               ("Status", "All", "FilterStatus"), ("Category", "All", "FilterCategory"),
               ("Assigned person", "All", "FilterTeam"), ("Due window", "All", "DueWindowList"),
               ("Completion", "All", "CompletionList"), ("Overdue", "All", "OverdueList")]
    for i, (lab, val, src) in enumerate(filters):
        r = 6 + i
        label(ws, f"B{r}", lab, True)
        inp(ws, f"D{r}", val)
        dv_list(ws, f"D{r}", src)
    ws["F6"] = f'=COUNT({R("tasks", "Filter Key")})&" task(s) match the filters"'
    ws["F6"].font = fnt(10, True, NAVY)
    label(ws, "F8", "Select All in any box to ignore that filter.")

    # helper lists (hidden columns X:AB)
    ws["X5"] = "All"
    for k in range(6, 56):
        src = k
        ws[f"X{k}"] = f"=IF(LEN('Project Overview'!C{src})=0,\"\",'Project Overview'!B{src})"
    for col, nm, src_col, n_rows in (("Y", "FilterPriority", "G", 15), ("Z", "FilterStatus", "H", 15),
                                     ("AA", "FilterCategory", "F", 15), ("AB", "FilterTeam", "J", 15)):
        ws[f"{col}5"] = "All"
        for k in range(n_rows):
            ws[f"{col}{6 + k}"] = f'=IF(Setup!{src_col}{6 + k}="","",Setup!{src_col}{6 + k})'
    for nm, col, last in (("FilterProject", "X", 55), ("FilterPriority", "Y", 20), ("FilterStatus", "Z", 20),
                          ("FilterCategory", "AA", 20), ("FilterTeam", "AB", 20)):
        wb.defined_names[nm] = DefinedName(nm, attr_text=f"'Task Filter'!${col}$5:${col}${last}")
    for col in ["X", "Y", "Z", "AA", "AB"]:
        ws.column_dimensions[col].hidden = True

    hdrs = ["#", "Task ID", "Task Name", "Project", "Category", "Assigned To", "Priority", "Status",
            "Due Date", "Days Left", "Overdue"]
    src = ["Task ID", "Task Name", "Project ID", "Category", "Assigned To", "Priority", "Status",
           "Due Date", "Days Left", "Overdue"]
    for j, h in enumerate(hdrs):
        c = ws.cell(16, 2 + j, h)
        c.font = fnt(9, True, WHITE)
        c.fill = fill(NAVY)
        c.alignment = Alignment(horizontal="center")
    FK = R("tasks", "Filter Key")
    for n in range(1, 51):
        r = 16 + n
        ws[f"B{r}"] = f'=IF(COUNT({FK})>={n},{n},"")'
        for j, s_ in enumerate(src):
            col = CL(3 + j)
            ws[f"{col}{r}"] = f'=IF($B{r}="","",INDEX({R("tasks", s_)},MATCH(SMALL({FK},$B{r}),{FK},0))&"")' \
                if s_ not in ("Due Date", "Days Left") else \
                f'=IF($B{r}="","",IFERROR(INDEX({R("tasks", s_)},MATCH(SMALL({FK},$B{r}),{FK},0)),""))'
            ws[f"{col}{r}"].font = fnt(9)
            ws[f"{col}{r}"].border = BOX
        ws[f"J{r}"].number_format = FMT_DATE
        ws[f"K{r}"].number_format = FMT_DAYS
    cf(ws, "L17:L66", '$L17="Yes"', DANGER_BG, DANGER, True)
    cf(ws, "I17:I66", '$I17="Completed"', SUCCESS_BG, SUCCESS, True)
    cf(ws, "H17:H66", '$H17="Critical"', DANGER_BG, DANGER, True)
    cf(ws, "H17:H66", '$H17="High"', WARN_BG, DARK, True)
    ws.freeze_panes = "A17"


def build_decision(ws):
    page(ws, "Decision Matrix", "Score options against weighted criteria (1 = poor, 10 = excellent). The highest total wins.",
         INFO, demo=True, widths={"B": 30, "C": 12, "D": 14, "E": 14, "F": 14, "G": 3, "H": 16, "I": 16, "J": 16})
    label(ws, "B4", "Decision name", True)
    inp(ws, "C4", "Choose project management software")
    ws.merge_cells("C4:F4")
    for col, h in zip("BCDEF", ["Criterion", "Weight", "Tool Alpha", "Tool Beta", "Tool Gamma"]):
        c = ws[f"{col}6"]
        c.value = h
        c.font = fnt(9, True, WHITE)
        c.fill = fill(NAVY)
        c.alignment = Alignment(horizontal="center")
    for col, src in zip("HIJ", "DEF"):
        c = ws[f"{col}6"]
        c.value = f'="Weighted: "&{src}6'
        c.font = fnt(9, True, WHITE)
        c.fill = fill(MIDNIGHT)
        c.alignment = Alignment(horizontal="center")
    criteria = [("Total cost of ownership", 0.25, 6, 8, 5), ("Ease of use", 0.20, 9, 7, 6),
                ("Integrations", 0.20, 8, 6, 9), ("Reporting", 0.15, 7, 8, 6),
                ("Security", 0.10, 8, 8, 7), ("Support", 0.10, 6, 7, 9)]
    for i, (name_, w, a, b, c_) in enumerate(criteria):
        r = 7 + i
        inp(ws, f"B{r}", name_)
        inp(ws, f"C{r}", w, FMT_PCT)
        for col, v in zip("DEF", (a, b, c_)):
            inp(ws, f"{col}{r}", v)
            ws[f"{col}{r}"].alignment = Alignment(horizontal="center")
        for col, src in zip("HIJ", "DEF"):
            ws[f"{col}{r}"] = f'=IF(ISNUMBER({src}{r}),$C{r}*{src}{r},"")'
            ws[f"{col}{r}"].number_format = "0.00"
            ws[f"{col}{r}"].fill = fill(LGRAY)
            ws[f"{col}{r}"].border = BOX
    dvw = DataValidation(type="whole", operator="between", formula1="1", formula2="10", allow_blank=True)
    dvw.error = "Score must be a whole number from 1 to 10."
    ws.add_data_validation(dvw)
    dvw.add("D7:F12")
    dvp = DataValidation(type="decimal", operator="between", formula1="0", formula2="1", allow_blank=True)
    ws.add_data_validation(dvp)
    dvp.add("C7:C12")
    label(ws, "B13", "Total weight", True)
    ws["C13"] = "=SUM(C7:C12)"
    ws["C13"].number_format = FMT_PCT
    ws["D13"] = '=IF(ROUND(C13,4)=1,"Weights OK (100%)","Weights should total 100%")'
    ws["D13"].font = fnt(9, True, DARK)
    cf(ws, "D13", "ROUND($C$13,4)<>1", DANGER_BG, DANGER, True)
    label(ws, "B14", "Weighted total score", True)
    for col in "HIJ":
        ws[f"{col}14"] = f"=SUM({col}7:{col}12)"
        ws[f"{col}14"].number_format = "0.00"
        ws[f"{col}14"].font = fnt(11, True, NAVY)
        ws[f"{col}14"].fill = fill(SOFT_LAV)
        ws[f"{col}14"].border = BOX
    label(ws, "B16", "Recommended option", True)
    ws["C16"] = "=INDEX($D$6:$F$6,MATCH(MAX($H$14:$J$14),$H$14:$J$14,0))"
    ws["C16"].font = fnt(12, True, NAVY)
    ws["C16"].fill = fill(SOFT_TEAL)
    ws.merge_cells("C16:D16")
    label(ws, "B17", "Winning score", True)
    ws["C17"] = "=MAX($H$14:$J$14)"
    ws["C17"].number_format = "0.00"
    ws["C17"].font = fnt(10, True, NAVY)
    label(ws, "B19", "How it works: weighted score = weight x score. Totals add the weighted scores per option. "
                     "Recommended option = the option with the highest total (ties show the first).")
    label(ws, "B20", "Edit criteria names, weights (must total 100%) and scores in the blue cells.")
    legend(ws, 22, 2)


def build_kanban(ws):
    page(ws, "Kanban Board", "Cards are tasks grouped by status. Card text: priority letter, then task name.",
         INFO, demo=True, widths={"B": 26, "C": 26, "D": 26, "E": 26, "F": 26})
    TKB = R("tasks", "Kanban Key")
    for k, col in enumerate("BCDEF"):
        h = ws[f"{col}5"]
        h.value = f"=Setup!H{6 + k}"
        h.font = fnt(10, True, WHITE)
        h.fill = fill(NAVY)
        h.alignment = Alignment(horizontal="center")
        cnt = ws[f"{col}6"]
        cnt.value = f'=COUNTIF({TST},{col}$5)&" task(s)"'
        cnt.font = fnt(9, True, BLUE)
        cnt.fill = fill(SOFT_BLUE)
        cnt.alignment = Alignment(horizontal="center")
        for r in range(8, 28):
            m = f'MATCH({col}$5&"|"&(ROW()-7),{TKB},0)'
            cell = ws[f"{col}{r}"]
            cell.value = f'=IFERROR(LEFT(INDEX({TPRI},{m}),1)&" · "&INDEX({TN},{m}),"")'
            cell.font = fnt(9)
            cell.fill = fill(WHITE)
            cell.border = BOX
    ws.row_dimensions[5].height = 26
    for prefix, bg, color in (("C", DANGER_BG, DANGER), ("H", WARN_BG, DARK), ("M", INFO_BG, DARK), ("L", SUCCESS_BG, SUCCESS)):
        cf(ws, "B8:F27", f'LEFT(B8,4)="{prefix} · "', bg, color, True)
    label(ws, "B29", "Priority letters: C = Critical, H = High, M = Medium, L = Low. Change a task's Status on Variable Tasks to move its card.")
    legend(ws, 31, 2)
    ws.freeze_panes = "A6"


def build_gantt(ws):
    page(ws, "Gantt Chart", "Pick a project. Bars show each task's dates: blue in progress, teal completed, lavender review, gray not started. ◆ = milestone.",
         INFO, demo=True, widths={"B": 30, "C": 14, "D": 12, "E": 12, "F": 8, "G": 13, "H": 12, "I": 10})
    label(ws, "B4", "Project", True)
    inp(ws, "C4", P1)
    dv_list(ws, "C4", "ProjectIDList")
    label(ws, "E4", "Timeline start", True)
    inp(ws, "F4", D(2026, 9, 28), FMT_DATE)
    ws.merge_cells("F4:G4")
    heads = ["Task", "Assigned To", "Start", "Due", "Days", "Category", "Status", "Progress"]
    for j, h in enumerate(heads):
        c = ws.cell(8, 2 + j, h)
        c.font = fnt(9, True, WHITE)
        c.fill = fill(NAVY)
        c.alignment = Alignment(horizontal="center", wrap_text=True)
    GK = R("tasks", "Gantt Key")
    for k in range(26):
        col = CL(10 + k)
        ws.column_dimensions[col].width = 6.5
        c = ws[f"{col}8"]
        c.value = f"=$F$4+{7 * k}"
        c.number_format = "dd-mmm"
        c.font = fnt(7, True, WHITE)
        c.fill = fill(NAVY)
        c.alignment = Alignment(text_rotation=90, horizontal="center")
    ws.row_dimensions[8].height = 44
    for n in range(1, 26):
        r = 8 + n
        ws[f"B{r}"] = "=" + pick("tasks", "Task Name", n, "Gantt Key")
        ws[f"C{r}"] = "=" + pick("tasks", "Assigned To", n, "Gantt Key")
        ws[f"D{r}"] = "=" + pick("tasks", "Start Date", n, "Gantt Key")
        ws[f"E{r}"] = "=" + pick("tasks", "Due Date", n, "Gantt Key")
        ws[f"F{r}"] = f'=IF(AND(ISNUMBER(D{r}),ISNUMBER(E{r})),E{r}-D{r}+1,"")'
        ws[f"G{r}"] = "=" + pick("tasks", "Category", n, "Gantt Key")
        ws[f"H{r}"] = "=" + pick("tasks", "Status", n, "Gantt Key")
        ws[f"I{r}"] = "=" + pick("tasks", "Progress", n, "Gantt Key")
        ws[f"D{r}"].number_format = FMT_DATE
        ws[f"E{r}"].number_format = FMT_DATE
        ws[f"I{r}"].number_format = FMT_PCT
        for col in "BCDEFGHI":
            ws[f"{col}{r}"].font = fnt(9)
            ws[f"{col}{r}"].border = BOX
        for k in range(26):
            col = CL(10 + k)
            cell = ws[f"{col}{r}"]
            cell.value = f'=IF(OR($G{r}<>"Milestone",NOT(ISNUMBER($E{r}))),"",IF(AND($E{r}>={col}$8,$E{r}<{col}$8+7),"◆",""))'
            cell.font = fnt(9, True, NAVY)
            cell.alignment = Alignment(horizontal="center")
            cell.border = Border(left=Side(style="hair", color=BORDER), right=Side(style="hair", color=BORDER),
                                 top=Side(style="hair", color=BORDER), bottom=Side(style="hair", color=BORDER))
    tl = "J9:AI33"
    bar = "AND(ISNUMBER($D9),ISNUMBER($E9),J$8+6>=$D9,J$8<=$E9"
    cf(ws, tl, bar + ',$H9="Completed")', TEAL, WHITE, False)
    cf(ws, tl, bar + ',$H9="In Progress")', BLUE, WHITE, False)
    cf(ws, tl, bar + ',$H9="Review")', LAV, WHITE, False)
    cf(ws, tl, bar + ')', MGRAY, WHITE, False)
    cf(ws, tl, "AND(TODAY()>=J$8,TODAY()<J$8+7)", SOFT_LAV, None, False, stop=False)
    cf(ws, "J8:AI8", "AND(TODAY()>=J$8,TODAY()<J$8+7)", NAVY, WHITE, True, stop=False)
    databar(ws, "I9:I33", TEAL)
    label(ws, "B35", "Timeline shows 26 weeks from the start date. The lavender column marks the week that contains today.")
    legend(ws, 37, 2)
    ws.freeze_panes = "C9"


def build_instructions(ws):
    page(ws, "Instructions", "Getting started, how each part works, formulas, and troubleshooting.", NAVY,
         widths={"B": 110})
    blocks = [
        ("GETTING STARTED", [
            "1. Open the workbook in Excel 2019 or Microsoft 365 (recommended). It contains no macros.",
            "2. Look around with the DEMO DATA. Every dashboard, calendar and chart is already populated.",
            "3. Start on Setup: enter your workspace name, currency, week start and your team lists.",
            "4. When ready to use your own data, clear the sample entries (see RESET below).",
        ]),
        ("SETUP", [
            "Setup holds every dropdown list. Edit the blue items; dropdowns update everywhere.",
            "Each list has room for 15 items. Keep items contiguous with no blank rows in between.",
        ]),
        ("HOW TO ADD A PROJECT", [
            "Project Overview: type a Project Name (column C). The Project ID (PRJ-001 ...) is created automatically.",
            "Fill Category, Project Manager, dates, Priority and Status. Progress, Budget, Actual Cost, Remaining and Days Remaining calculate.",
            "Project Manager (same row): add objectives, deliverables, milestones, dependencies and risks.",
            "Add new projects at the bottom of the list. Do not sort Project Overview after linking tasks or budget lines, because IDs come from row position.",
        ]),
        ("HOW TO CREATE TASKS", [
            "Variable Tasks: type a Task Name, then choose Project ID, Category, Assigned To, Priority and Status. Task ID is automatic.",
            "Days Left and Overdue update from the Due Date and Status. Progress (0-100%) feeds the project progress.",
            "Recurring Tasks: enter Last Completed each time you finish an occurrence. Next Occurrence moves forward automatically.",
            "Task Schedule: time blocks (date, start, end). They appear on the Weekly Calendar in their start hour.",
            "Project Budget: one line per expense. Enter Planned Budget and Actual Expense against a Project ID.",
        ]),
        ("HOW DASHBOARDS AND CALENDARS WORK", [
            "All dashboard KPIs use COUNTIF, COUNTIFS and SUMIFS over the input tables. No numbers are typed in.",
            "Charts read the CHART DATA block (columns P to Y on the Dashboard). Do not type there.",
            "Monthly Calendar: choose a Month and Year. Due counts include open tasks and project deadlines. The agenda lists tasks due on the date in cell K4.",
            "Weekly Calendar: enter any date in C4. The week starting on your Week start setting is shown with time slots, workload and stats.",
            "Gantt Chart: choose a Project ID. Bars use each task's start and due dates.",
            "Kanban Board: cards group by status; priority letter first.",
            "Task Filter: pick filters in the blue boxes; the matching list refreshes instantly.",
        ]),
        ("FORMULA EXPLANATIONS", [
            "Days Left = Due Date minus TODAY(). Negative means overdue.",
            "Overdue = Yes when the Due Date is before today and the Status is not Completed.",
            "Budget Utilization = Actual Expense / Planned Budget. Alert: 90% or more = Near limit; over 100% = Over budget.",
            "Next Occurrence = Last Completed + step (Daily 1 day, Weekly 7, Biweekly 14, Monthly/Quarterly/Annually via EDATE, Custom = your day count).",
            "Project Progress = average Progress of tasks with that Project ID. Task Completion % = completed tasks / all tasks for the project.",
            "Decision Matrix: weighted score = weight x score. Recommended option = INDEX/MATCH on the highest total.",
            "Helper 'Key' columns on Variable Tasks (grey headers, hidden) rank rows for lists. They are safe to leave untouched.",
        ]),
        ("TROUBLESHOOTING", [
            "A dashboard shows zero: check that Project IDs on tasks and budget lines match an ID on Project Overview.",
            "A date shows as a number: select the cells and apply a date format.",
            "A dropdown is missing a value: add it to the list on Setup (the list has 15 slots).",
            "Weekly Calendar shows one task per hour: when two blocks start in the same hour, the first one shows in the grid. Use separate hours for each block.",
            "Google Sheets: formulas and dropdowns import, but data bars and some chart styles may need re-creating. See the Google Sheets note in the product guide.",
            "Calendars and Overdue flags use TODAY(), so they change daily by design.",
        ]),
        ("RESET SAMPLE DATA", [
            "Select only the blue columns in each table (Project Overview: C to D, F to I; Variable Tasks: C to D, F to H, J to L, O; and so on) and press Delete.",
            "Grey columns are formulas. Leave them in place; they empty automatically when their inputs are empty.",
            "Clear the blue input cells on Setup too, then re-enter your team, categories and currency.",
        ]),
    ]
    r = 4
    for head, lines in blocks:
        c = ws.cell(r, 2, head)
        c.font = fnt(10, True, WHITE)
        c.fill = fill(NAVY)
        r += 1
        for line in lines:
            c = ws.cell(r, 2, line)
            c.font = fnt(9)
            c.alignment = Alignment(wrap_text=True, vertical="top")
            r += 1
        r += 1
    legend(ws, r + 1, 2)


# ---------------------------------------------------------------- main
def main():
    wb = Workbook()
    wb.remove(wb.active)
    sheets = {name: wb.create_sheet(name) for name in SHEETS}

    # Named list ranges for Project IDs (formula column on Project Overview)
    wb.defined_names["ProjectIDList"] = DefinedName(
        "ProjectIDList", attr_text=f"'Project Overview'!$B$6:$B$55")

    build_setup(sheets["Setup"], wb)
    build_dashboard(sheets["Dashboard"])
    build_monthly(sheets["Monthly Calendar"])
    build_weekly(sheets["Weekly Calendar"])
    build_proj_overview(sheets["Project Overview"])
    build_pm(sheets["Project Manager"])
    build_budget(sheets["Project Budget"])
    build_tasks(sheets["Variable Tasks"])
    build_recurring(sheets["Recurring Tasks"])
    build_schedule(sheets["Task Schedule"])
    build_filter(sheets["Task Filter"], wb)
    build_decision(sheets["Decision Matrix"])
    build_kanban(sheets["Kanban Board"])
    build_gantt(sheets["Gantt Chart"])
    build_instructions(sheets["Instructions"])

    wb.calculation = CalcProperties(fullCalcOnLoad=True)
    wb.active = 0
    wb.save(OUT)
    print("saved", OUT)


if __name__ == "__main__":
    main()
