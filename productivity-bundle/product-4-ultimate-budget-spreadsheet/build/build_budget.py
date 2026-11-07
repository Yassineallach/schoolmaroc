#!/usr/bin/env python3
"""Builds the Ultimate Budget Spreadsheet (.xlsx, macro-free, 28 tabs).

Usage: python3 build_budget.py OUTPUT.xlsx
Colours and fonts follow ../../design-system/design-tokens.json.
Money colours: income = teal, expenses = red, savings = blue, goals = lavender.
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
from openpyxl.chart import BarChart, LineChart, DoughnutChart, Reference
from openpyxl.chart.marker import DataPoint
from openpyxl.chart.label import DataLabelList
from openpyxl.utils import get_column_letter as CL

OUT = sys.argv[1] if len(sys.argv) > 1 else "Ultimate_Budget_Spreadsheet.xlsx"

NAVY = "17243A"; MIDNIGHT = "223653"; BLUE = "4169E1"; SOFT_BLUE = "EAF1FB"
TEAL = "24A89A"; SOFT_TEAL = "E2F4F0"; LAV = "8B7BE8"; SOFT_LAV = "F0EDFC"
BG = "F5F7FA"; WHITE = "FFFFFF"; LGRAY = "E9EDF2"; MGRAY = "9AA5B1"
DARK = "263445"; SEC = "6B7785"; BORDER = "DCE3EA"
SUCCESS = "279B70"; SUCCESS_BG = "E5F5ED"; WARN = "E9A23B"; WARN_BG = "FFF3DC"
DANGER = "DC5B64"; DANGER_BG = "FCEAEC"; INFO = "4D8FD8"; INFO_BG = "EAF2FC"

SIDE = Side(style="thin", color=BORDER)
BOX = Border(left=SIDE, right=SIDE, top=SIDE, bottom=SIDE)
FMT_DATE = "dd-mmm-yyyy"
FMT_MONEY = "#,##0.00;[Red]-#,##0.00"
FMT_PCT = "0.0%"
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
TODAY_DEMO = dt.date(2026, 11, 7)


def fill(c):
    return PatternFill("solid", start_color=c, end_color=c)


def fnt(size=9, bold=False, color=DARK, italic=False):
    return Font(name="Arial", size=size, bold=bold, color=color, italic=italic)


def D(y, m, d):
    return dt.date(y, m, d)


# ------------------------------------------------------------------ registry
REG = {}


def reg(key, sheet, hdr, nrows, headers, col0=2):
    REG[key] = dict(sheet=sheet, hdr=hdr, first=hdr + 1, last=hdr + nrows, col0=col0,
                    L={h: CL(col0 + i) for i, h in enumerate(headers)})


def R(key, h):
    s = REG[key]
    c = s["L"][h]
    return f"'{s['sheet']}'!${c}${s['first']}:${c}${s['last']}"


TX_H = ["Transaction ID", "Date", "Description", "Type", "Category", "Account", "Payment Method",
        "Amount", "Month", "Group", "Class", "Month Key", "Notes"]
PAY_H = ["Payment", "Amount", "Due Date", "Status", "Payment Method", "Category", "Account",
         "Paid On", "Days Until Due", "Alert"]
REC_H = ["Recurring Item", "Type", "Amount", "Frequency", "Category", "Account", "Start Date",
         "End Date", "Next Payment", "Status", "Months Step", "Days Step"]
PAYCHECK_H = ["Pay Date", "Gross Pay", "Deductions", "Net Pay", "Bills Allocated",
              "Savings Allocated", "Remaining", "Deduction Rate"]
DEBT_H = ["Debt", "Type", "Starting Balance", "Current Balance", "APR", "Minimum Payment",
          "Extra Payment", "Total Monthly Payment", "Months to Payoff", "Payoff Date",
          "Snowball Rank", "Avalanche Rank"]
FUND_H = ["Fund", "Target", "Current Balance", "Monthly Contribution", "Remaining", "Target Date",
          "Months Left", "Needed per Month", "Completion", "Status"]
BANK_H = ["Account", "Type", "Institution", "Opening Balance", "Total Income", "Total Expenses",
          "Current Balance"]

reg("tx", "Variable Transactions", 5, 400, TX_H)
reg("pay", "Payments", 5, 50, PAY_H)
reg("rec", "Recurring Transactions", 5, 40, REC_H)
reg("pc", "Paycheck Dashboard", 6, 24, PAYCHECK_H)
reg("debt", "Debt Calculator", 6, 8, DEBT_H)
reg("fund", "Sinking Funds", 6, 10, FUND_H)
reg("bank", "Bank Accounts", 5, 5, BANK_H)

TX_DATE = R("tx", "Date"); TX_TYPE = R("tx", "Type"); TX_CAT = R("tx", "Category")
TX_ACCT = R("tx", "Account"); TX_AMT = R("tx", "Amount"); TX_MONTH = R("tx", "Month")
TX_GROUP = R("tx", "Group"); TX_CLASS = R("tx", "Class"); TX_KEY = R("tx", "Month Key")
TX_DESC = R("tx", "Description")
DEBT_BAL = R("debt", "Current Balance"); DEBT_TYPE = R("debt", "Type")


# ------------------------------------------------------------------ style helpers
def page(ws, title, sub, tab, band_to, demo=False):
    ws.sheet_view.showGridLines = False
    ws.sheet_properties.tabColor = tab
    ws.column_dimensions["A"].width = 2
    for c in range(2, band_to + 1):
        ws.cell(1, c).fill = fill(NAVY)
        ws.cell(2, c).fill = fill(SOFT_BLUE)
    ws.cell(1, 2, title).font = fnt(16, True, WHITE)
    ws.cell(1, 2).alignment = Alignment(vertical="center", indent=1)
    ws.row_dimensions[1].height = 34
    ws["B2"] = sub
    ws["B2"].font = fnt(9, False, MIDNIGHT)
    ws.row_dimensions[2].height = 20
    if demo:
        ws["B3"] = "DEMO DATA: sample entries are included so every view works. Clear the blue cells to start your own."
        ws["B3"].font = fnt(9, True, INFO)


def band(ws, row, c1, c2, text, bg=MIDNIGHT, size=10):
    for c in range(c1, c2 + 1):
        ws.cell(row, c).fill = fill(bg)
    cell = ws.cell(row, c1, text)
    cell.font = fnt(size, True, WHITE)
    cell.alignment = Alignment(vertical="center", indent=1)
    ws.row_dimensions[row].height = 20


def label(ws, cell, text, bold=True):
    ws[cell] = text
    ws[cell].font = fnt(9, bold, DARK if bold else SEC)
    ws[cell].alignment = Alignment(vertical="center")


def inp(ws, cell, value=None, fmt=None, align=None):
    c = ws[cell]
    if value is not None:
        c.value = value
    c.fill = fill(SOFT_BLUE)
    c.border = BOX
    c.font = fnt(9)
    c.alignment = Alignment(vertical="center", horizontal=align)
    if fmt:
        c.number_format = fmt


def calc(ws, cell, formula, fmt=None, bold=False, align=None, bg=LGRAY, color=DARK):
    c = ws[cell]
    c.value = formula
    c.fill = fill(bg)
    c.border = BOX
    c.font = fnt(9, bold, color)
    c.alignment = Alignment(vertical="center", horizontal=align)
    if fmt:
        c.number_format = fmt


def cf(ws, rng, formula, bg, color=None, bold=False):
    kw = {"fill": fill(bg)}
    if color or bold:
        kw["font"] = Font(color=color, bold=bold) if color else Font(bold=bold)
    ws.conditional_formatting.add(rng, FormulaRule(formula=[formula], stopIfTrue=True, **kw))


def dv_list(ws, rng, source):
    d = DataValidation(type="list", formula1=source, allow_blank=True)
    d.error = "Pick a value from the list (edit lists on Easy Setup)."
    ws.add_data_validation(d)
    d.add(rng)


def dv_date(ws, rng):
    d = DataValidation(type="date", operator="greaterThan", formula1="36526", allow_blank=True)
    d.error = "Enter a date, for example 15-Nov-2026."
    ws.add_data_validation(d)
    d.add(rng)


def legend(ws, row, col):
    items = [("Input", SOFT_BLUE), ("Calculated", LGRAY), ("Income", SOFT_TEAL),
             ("Expense / warning", DANGER_BG), ("Savings", SOFT_BLUE), ("Goal", SOFT_LAV)]
    for i, (txt, colr) in enumerate(items):
        c = ws.cell(row, col + i, txt)
        c.fill = fill(colr)
        c.font = fnt(8, False, DARK)
        c.border = BOX
        c.alignment = Alignment(horizontal="center")


def set_widths(ws, widths):
    for col, w in widths.items():
        ws.column_dimensions[col].width = w


def sign_fmt(ws, rng):
    ws.conditional_formatting.add(rng, FormulaRule(formula=[f"AND(ISNUMBER({rng.split(':')[0]}),{rng.split(':')[0]}<0)"],
                                                   fill=fill(DANGER_BG), font=Font(color=DANGER, bold=True)))


def write_table(ws, key, cols, rows=(), height=18):
    """cols: list of dict(h, kind 'in'|'calc', f template or callable(r), w, fmt, align)."""
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
    ws.row_dimensions[hdr].height = 30
    for r in range(s["first"], s["last"] + 1):
        i = r - s["first"]
        data = rows[i] if i < len(rows) else {}
        for j, c in enumerate(cols):
            cell = ws.cell(r, s["col0"] + j)
            if c["kind"] == "calc":
                f = c["f"]
                cell.value = "=" + (f(r) if callable(f) else fxt(key, r, f))
                cell.fill = fill(LGRAY)
            else:
                v = data.get(c["h"])
                if v is not None:
                    cell.value = v
                cell.fill = fill(SOFT_BLUE)
            cell.font = fnt(9)
            cell.border = BOX
            cell.alignment = Alignment(vertical="center", horizontal=c.get("align"))
            if c.get("fmt"):
                cell.number_format = c["fmt"]
        ws.row_dimensions[r].height = height


def fxt(key, r, tmpl):
    s = REG[key]
    tmpl = re.sub(r"\{\^([^}]+)\}", lambda m: f"${s['L'][m.group(1)]}${s['first']}:{s['L'][m.group(1)]}{r}", tmpl)
    return re.sub(r"\{([^}]+)\}", lambda m: f"{s['L'][m.group(1)]}{r}", tmpl)


def add_table(ws, key, tname):
    s = REG[key]
    ref = f"{CL(s['col0'])}{s['hdr']}:{CL(s['col0'] + len(s['L']) - 1)}{s['last']}"
    tb = Table(displayName=tname, ref=ref)
    tb.tableStyleInfo = TableStyleInfo(name="TableStyleLight1", showRowStripes=False)
    ws.add_table(tb)


def col(key, h):
    s = REG[key]
    c = s["L"][h]
    return f"{c}{s['first']}:{c}{s['last']}"


# ------------------------------------------------------------------ setup lists
EXPENSE_CATS = [  # name, group, class
    ("Rent or mortgage", "Fixed", "Needs"),
    ("Utilities", "Fixed", "Needs"),
    ("Insurance", "Fixed", "Needs"),
    ("Phone and internet", "Fixed", "Needs"),
    ("Subscriptions", "Fixed", "Wants"),
    ("Groceries", "Variable", "Needs"),
    ("Transport", "Variable", "Needs"),
    ("Health", "Variable", "Needs"),
    ("Dining out", "Variable", "Wants"),
    ("Entertainment", "Variable", "Wants"),
    ("Shopping", "Variable", "Wants"),
    ("Debt payment", "Debt", "Savings and debt"),
    ("Savings transfer", "Savings", "Savings and debt"),
]
INCOME_CATS = ["Salary", "Freelance", "Bonus", "Interest", "Other income"]
PAY_METHODS = ["Debit card", "Credit card", "Bank transfer", "Cash"]
ACCOUNTS = ["Checking", "Savings", "Credit card"]
FREQS = ["Weekly", "Biweekly", "Monthly", "Quarterly", "Annually"]
PAY_STATUS = ["Unpaid", "Paid"]
TYPES = ["Income", "Expense"]
ACCT_TYPES = ["Checking", "Savings", "Credit", "Investment", "Cash"]
DEBT_TYPES = ["Credit card", "Loan", "Other"]
ALLOC = ["Spent", "No spend"]

# ------------------------------------------------------------------ 1 Easy Setup
def build_setup(ws, wb):
    page(ws, "Easy Setup", "Start here. Currency, budget, categories, payment methods and accounts. Every dropdown reads from this sheet.",
         NAVY, 14, demo=True)
    set_widths(ws, {"B": 30, "C": 16, "D": 3, "E": 22, "F": 14, "G": 20, "H": 3, "I": 18, "J": 3,
                    "K": 18, "L": 3, "M": 18, "N": 3, "O": 14, "P": 3, "Q": 12, "R": 12})
    band(ws, 4, 2, 3, "BUDGET PREFERENCES")
    prefs = [("Currency code", "USD", None, "CurrencyCode"),
             ("Budget year", 2026, "0", "BudgetYear"),
             ("Monthly spending budget", 3800, FMT_MONEY, "MonthlyBudget"),
             ("Savings target (share of income)", 0.20, FMT_PCT, "SavingsTarget"),
             ("Average daily spend (for no-spend challenge)", 40, FMT_MONEY, "DailyAvg")]
    for i, (lab, val, fmt, nm) in enumerate(prefs):
        r = 5 + i
        label(ws, f"B{r}", lab)
        inp(ws, f"C{r}", val, fmt)
        wb.defined_names[nm] = DefinedName(nm, attr_text=f"'Easy Setup'!$C${r}")
    dv_list(ws, "C5", '"USD,EUR,GBP,MAD,CAD,AUD,INR"')
    label(ws, "B11", "Spending budget excludes savings transfers. Savings are tracked separately.", False)
    legend(ws, 13, 2)

    band(ws, 4, 5, 7, "EXPENSE CATEGORIES")
    for j, h in enumerate(["Category", "Group", "50/30/20 class"]):
        c = ws.cell(5, 5 + j, h)
        c.font = fnt(9, True, WHITE)
        c.fill = fill(NAVY)
        c.alignment = Alignment(horizontal="center")
    for i in range(15):
        r = 6 + i
        if i < len(EXPENSE_CATS):
            n, g, k = EXPENSE_CATS[i]
        else:
            n = g = k = None
        inp(ws, f"E{r}", n)
        inp(ws, f"F{r}", g)
        inp(ws, f"G{r}", k)
    dv_list(ws, "F6:F20", '"Fixed,Variable,Debt,Savings"')
    dv_list(ws, "G6:G20", '"Needs,Wants,Savings and debt"')
    wb.defined_names["CatList"] = DefinedName("CatList", attr_text="'Easy Setup'!$E$6:$E$20")
    wb.defined_names["CatGroup"] = DefinedName("CatGroup", attr_text="'Easy Setup'!$F$6:$F$20")
    wb.defined_names["CatClass"] = DefinedName("CatClass", attr_text="'Easy Setup'!$G$6:$G$20")

    band(ws, 4, 9, 9, "INCOME")
    ws["I5"] = "Income category"
    ws["I5"].font = fnt(9, True, WHITE)
    ws["I5"].fill = fill(NAVY)
    for i in range(10):
        inp(ws, f"I{6 + i}", INCOME_CATS[i] if i < len(INCOME_CATS) else None)
    wb.defined_names["IncomeList"] = DefinedName("IncomeList", attr_text="'Easy Setup'!$I$6:$I$15")

    band(ws, 4, 11, 11, "PAYMENT METHODS")
    ws["K5"] = "Method"
    ws["K5"].font = fnt(9, True, WHITE)
    ws["K5"].fill = fill(NAVY)
    for i in range(8):
        inp(ws, f"K{6 + i}", PAY_METHODS[i] if i < len(PAY_METHODS) else None)
    wb.defined_names["MethodList"] = DefinedName("MethodList", attr_text="'Easy Setup'!$K$6:$K$13")

    band(ws, 4, 13, 13, "ACCOUNTS")
    ws["M5"] = "Account"
    ws["M5"].font = fnt(9, True, WHITE)
    ws["M5"].fill = fill(NAVY)
    for i in range(8):
        inp(ws, f"M{6 + i}", ACCOUNTS[i] if i < len(ACCOUNTS) else None)
    wb.defined_names["AccountList"] = DefinedName("AccountList", attr_text="'Easy Setup'!$M$6:$M$13")

    band(ws, 4, 15, 15, "FREQUENCY")
    ws["O5"] = "Frequency"
    ws["O5"].font = fnt(9, True, WHITE)
    ws["O5"].fill = fill(NAVY)
    for i in range(6):
        inp(ws, f"O{6 + i}", FREQS[i] if i < len(FREQS) else None)
    wb.defined_names["FreqList"] = DefinedName("FreqList", attr_text="'Easy Setup'!$O$6:$O$11")

    band(ws, 4, 17, 18, "LISTS")
    for col_, h, items, nm in (("Q", "Type", TYPES, "TypeList"), ("R", "Payment status", PAY_STATUS, "PayStatusList")):
        ws[f"{col_}5"] = h
        ws[f"{col_}5"].font = fnt(9, True, WHITE)
        ws[f"{col_}5"].fill = fill(NAVY)
        for i in range(3):
            inp(ws, f"{col_}{6 + i}", items[i] if i < len(items) else None)
        wb.defined_names[nm] = DefinedName(nm, attr_text=f"'Easy Setup'!${col_}$6:${col_}$8")
    ws["R5"].value = "Payment status"
    ws.column_dimensions["Q"].width = 12
    ws["B17"] = "CALL-OUTS"
    ws["B17"].font = fnt(10, True, NAVY)
    notes = [
        "1. Enter every income and expense in Variable Transactions. Dashboards and monthly sheets update from there.",
        "2. Group drives the monthly sheets: Fixed, Variable, Debt, Savings.",
        "3. Class drives the 50/30/20 check: Needs (50%), Wants (30%), Savings and debt (20%).",
        "4. Change the budget year to view a different year's monthly sheets (sample data is 2026).",
    ]
    for i, n in enumerate(notes):
        label(ws, f"B{18 + i}", n, False)
    ws.freeze_panes = "A4"


# ------------------------------------------------------------------ 2 Bank Accounts
def build_bank(ws, wb):
    page(ws, "Bank Accounts", "One row per account. Balances update from every transaction assigned to the account.",
         MIDNIGHT, 9, demo=True)
    set_widths(ws, {"B": 18, "C": 16, "D": 22, "E": 16, "F": 16, "G": 16, "H": 16, "I": 3})
    hdr = REG["bank"]["hdr"]
    for j, h in enumerate(BANK_H):
        c = ws.cell(hdr, 2 + j, h)
        c.font = fnt(9, True, WHITE)
        c.fill = fill(NAVY if j < 4 else MIDNIGHT)
        c.alignment = Alignment(horizontal="center", wrap_text=True)
        c.border = BOX
    ws.row_dimensions[hdr].height = 30
    inst = ["Demo Bank", "Demo Bank", "Demo Card Co"]
    opening = [2400, 6800, 0]
    types = ["Checking", "Savings", "Credit"]
    for i in range(5):
        r = hdr + 1 + i
        if i < 3:
            calc(ws, f"B{r}", f"=IF('Easy Setup'!M{6 + i}=\"\",\"\",'Easy Setup'!M{6 + i})", align="left")
            inp(ws, f"C{r}", types[i], None, "center")
            inp(ws, f"D{r}", inst[i])
            inp(ws, f"E{r}", opening[i], FMT_MONEY)
        else:
            inp(ws, f"B{r}"); inp(ws, f"C{r}"); inp(ws, f"D{r}"); inp(ws, f"E{r}")
        calc(ws, f"F{r}", f'=IF(B{r}="","",SUMIFS({TX_AMT},{TX_ACCT},B{r},{TX_TYPE},"Income"))', FMT_MONEY)
        calc(ws, f"G{r}", f'=IF(B{r}="","",SUMIFS({TX_AMT},{TX_ACCT},B{r},{TX_TYPE},"Expense"))', FMT_MONEY)
        calc(ws, f"H{r}", f'=IF(B{r}="","",E{r}+F{r}-G{r}+IF(C{r}="Savings",SUMIFS({TX_AMT},{TX_GROUP},"Savings"),0))', FMT_MONEY, True)
    r = hdr + 6
    label(ws, f"B{r}", "TOTAL")
    for col_ in "EFGH":
        calc(ws, f"{col_}{r}", f"=SUM({col_}{hdr + 1}:{col_}{hdr + 5})", FMT_MONEY, True)
    sign_fmt(ws, f"H{hdr + 1}:H{hdr + 5}")
    dv_list(ws, f"C{hdr + 1}:C{hdr + 5}", '"Checking,Savings,Credit,Investment,Cash"')
    wb.defined_names["BankBalances"] = DefinedName("BankBalances", attr_text=f"'Bank Accounts'!$H${hdr + 1}:$H${hdr + 5}")
    label(ws, f"B{hdr + 8}", "Savings transfers leave Checking and are added to the Savings account. Credit accounts show the balance owed as a negative number. Account names come from Easy Setup.", False)
    legend(ws, hdr + 10, 2)


# ------------------------------------------------------------------ 3 Recurring
def build_recurring(ws):
    page(ws, "Recurring Transactions", "Bills, subscriptions and regular income. Shows the next payment date from today.",
         MIDNIGHT, 13, demo=True)
    rows = [
        ("Rent", "Expense", 1400, "Monthly", "Rent or mortgage", "Checking", D(2026, 1, 1), None),
        ("Salary", "Income", 4800, "Monthly", "Salary", "Checking", D(2026, 1, 1), None),
        ("Streaming", "Expense", 16, "Monthly", "Subscriptions", "Credit card", D(2026, 3, 5), None),
        ("Gym membership", "Expense", 40, "Monthly", "Health", "Checking", D(2026, 2, 10), None),
        ("Car insurance", "Expense", 360, "Quarterly", "Insurance", "Checking", D(2026, 2, 12), None),
        ("Domain and hosting", "Expense", 120, "Annually", "Subscriptions", "Credit card", D(2025, 9, 20), None),
        ("Savings transfer", "Expense", 600, "Monthly", "Savings transfer", "Savings", D(2026, 1, 2), None),
    ]
    rows_d = [dict(zip(["Recurring Item", "Type", "Amount", "Frequency", "Category", "Account", "Start Date", "End Date"], r_)) for r_ in rows]
    FR = REG["rec"]
    rs = {}
    rs["Months Step"] = lambda r: f'IF(E{r}="Monthly",1,IF(E{r}="Quarterly",3,IF(E{r}="Annually",12,0)))'
    write_table(ws, "rec", [
        dict(h="Recurring Item", kind="in", w=26),
        dict(h="Type", kind="in", w=11, align="center"),
        dict(h="Amount", kind="in", w=13, fmt=FMT_MONEY),
        dict(h="Frequency", kind="in", w=12, align="center"),
        dict(h="Category", kind="in", w=18),
        dict(h="Account", kind="in", w=14),
        dict(h="Start Date", kind="in", w=13, fmt=FMT_DATE),
        dict(h="End Date", kind="in", w=13, fmt=FMT_DATE),
        dict(h="Next Payment", kind="calc", w=14, fmt=FMT_DATE,
             f=lambda r: (f'IF(NOT(ISNUMBER(H{r})),"",IF(H{r}>TODAY(),H{r},IF(L{r}>0,'
                          f'IF(EDATE(H{r},L{r}*INT(DATEDIF(H{r},TODAY(),"m")/L{r}))<TODAY(),'
                          f'EDATE(H{r},L{r}*(INT(DATEDIF(H{r},TODAY(),"m")/L{r})+1)),'
                          f'EDATE(H{r},L{r}*INT(DATEDIF(H{r},TODAY(),"m")/L{r}))),'
                          f'IF(M{r}>0,H{r}+M{r}*INT((TODAY()-H{r})/M{r})+IF(H{r}+M{r}*INT((TODAY()-H{r})/M{r})<TODAY(),M{r},0),""))))')),
        dict(h="Status", kind="calc", w=11, align="center",
             f=lambda r: f'IF(J{r}="","",IF(AND(ISNUMBER(I{r}),J{r}>I{r}),"Ended","Active"))'),
        dict(h="Months Step", kind="calc", w=10, align="center", f=lambda r: rs["Months Step"](r)),
        dict(h="Days Step", kind="calc", w=10, align="center",
             f=lambda r: f'IF(E{r}="Weekly",7,IF(E{r}="Biweekly",14,0))'),
    ], rows_d)
    rr = REG["rec"]
    last = rr["last"]
    dv_list(ws, f"C6:C{last}", "TypeList")
    dv_list(ws, f"E6:E{last}", "FreqList")
    dv_list(ws, f"F6:F{last}", "CatList")
    dv_list(ws, f"G6:G{last}", "AccountList")
    dv_date(ws, f"H6:I{last}")


# ------------------------------------------------------------------ 4 Payments
def build_payments(ws):
    page(ws, "Payments", "Bills and payments due. Status and alerts update from today's date.", MIDNIGHT, 11, demo=True)
    rows = [
        ("Credit card statement", 412.80, D(2026, 11, 15), "Unpaid", "Bank transfer", "Debt payment", "Checking", None),
        ("Car loan", 350, D(2026, 11, 15), "Unpaid", "Bank transfer", "Debt payment", "Checking", None),
        ("Electricity", 96.40, D(2026, 11, 4), "Paid", "Debit card", "Utilities", "Checking", D(2026, 11, 3)),
        ("Internet", 62, D(2026, 11, 12), "Unpaid", "Debit card", "Phone and internet", "Checking", None),
        ("Water", 48.25, D(2026, 10, 28), "Unpaid", "Bank transfer", "Utilities", "Checking", None),
        ("Gym", 40, D(2026, 11, 10), "Unpaid", "Debit card", "Health", "Checking", None),
    ]
    rows_d = [dict(zip(["Payment", "Amount", "Due Date", "Status", "Payment Method", "Category", "Account", "Paid On"], r_)) for r_ in rows]
    write_table(ws, "pay", [
        dict(h="Payment", kind="in", w=26),
        dict(h="Amount", kind="in", w=12, fmt=FMT_MONEY),
        dict(h="Due Date", kind="in", w=13, fmt=FMT_DATE),
        dict(h="Status", kind="in", w=11, align="center"),
        dict(h="Payment Method", kind="in", w=16),
        dict(h="Category", kind="in", w=18),
        dict(h="Account", kind="in", w=14),
        dict(h="Paid On", kind="in", w=13, fmt=FMT_DATE),
        dict(h="Days Until Due", kind="calc", w=12, align="center",
             f=lambda r: f'IF(ISNUMBER(D{r}),D{r}-TODAY(),"")'),
        dict(h="Alert", kind="calc", w=16, align="center",
             f=lambda r: f'IF(LEN(B{r})=0,"",IF(E{r}="Paid","Paid",IF(D{r}<TODAY(),"Overdue",IF(D{r}-TODAY()<=7,"Due within 7 days","Upcoming"))))'),
    ], rows_d)
    dv_list(ws, "E6:E55", "PayStatusList")
    dv_list(ws, "F6:F55", "MethodList")
    dv_list(ws, "G6:G55", "CatList")
    dv_list(ws, "H6:H55", "AccountList")
    dv_date(ws, "D6:D55")
    dv_date(ws, "I6:I55")
    cf(ws, "K6:K55", '$K6="Overdue"', DANGER_BG, DANGER, True)
    cf(ws, "K6:K55", '$K6="Due within 7 days"', WARN_BG, DARK, True)
    cf(ws, "K6:K55", '$K6="Paid"', SUCCESS_BG, SUCCESS, True)
    label(ws, "B58", "Total unpaid")
    calc(ws, "C58", '=SUMIFS(C6:C55,E6:E55,"Unpaid")', FMT_MONEY, True)
    label(ws, "B59", "Overdue count")
    calc(ws, "C59", '=COUNTIF(K6:K55,"Overdue")', "0", True)
    ws.freeze_panes = "C6"


# ------------------------------------------------------------------ 5 Variable transactions
def build_tx(ws):
    page(ws, "Variable Transactions", "Every income and expense. Type, category and account drive all dashboards.",
         MIDNIGHT, 13, demo=True)
    txs = []

    def add(d, desc, typ, cat, acct, method, amt, note=""):
        txs.append(dict(Date=d, Description=desc, Type=typ, Category=cat, Account=acct,
                        **{"Payment Method": method}, Amount=amt, Notes=note))

    for m in range(1, 12):
        last = 6 if m == 11 else 28
        def ok(day):
            return day <= last
        add(D(2026, m, 1), "Salary", "Income", "Salary", "Checking", "Bank transfer", 4800)
        if ok(1):
            add(D(2026, m, 1), "Rent", "Expense", "Rent or mortgage", "Checking", "Bank transfer", 1400)
        if ok(2):
            add(D(2026, m, 2), "Transfer to savings", "Expense", "Savings transfer", "Checking", "Bank transfer", 600)
        if ok(5):
            add(D(2026, m, 5), "Electricity and water", "Expense", "Utilities", "Checking", "Debit card", 150 + (m * 3) % 40)
        if ok(8):
            add(D(2026, m, 8), "Weekly groceries", "Expense", "Groceries", "Checking", "Debit card", 218 + (m * 7) % 35)
        if ok(9):
            add(D(2026, m, 9), "Fuel and transit", "Expense", "Transport", "Checking", "Debit card", 84 + (m * 5) % 22)
        if ok(10):
            add(D(2026, m, 10), "Car insurance share", "Expense", "Insurance", "Checking", "Bank transfer", 120)
        if ok(12):
            add(D(2026, m, 12), "Phone and internet", "Expense", "Phone and internet", "Checking", "Debit card", 85)
        if ok(14):
            add(D(2026, m, 14), "Streaming services", "Expense", "Subscriptions", "Credit card", "Credit card", 45)
        if ok(15):
            add(D(2026, m, 15), "Car loan payment", "Expense", "Debt payment", "Checking", "Bank transfer", 350)
        if ok(17):
            add(D(2026, m, 17), "Dinner out", "Expense", "Dining out", "Credit card", "Credit card", 62 + (m * 4) % 30)
        if ok(20):
            add(D(2026, m, 20), "Cinema and books", "Expense", "Entertainment", "Credit card", "Credit card", 40 + (m * 2) % 15)
        if ok(22):
            add(D(2026, m, 22), "Weekly groceries", "Expense", "Groceries", "Checking", "Debit card", 196 + (m * 9) % 40)
        if ok(25):
            add(D(2026, m, 25), "Clothing and household", "Expense", "Shopping", "Credit card", "Credit card", 110 + (m * 6) % 50)
        if ok(18) and m % 3 == 0:
            add(D(2026, m, 18), "Pharmacy", "Expense", "Health", "Checking", "Debit card", 58)
        if ok(28):
            add(D(2026, m, 28), "Credit card payment", "Expense", "Debt payment", "Checking", "Bank transfer", 300)
    add(D(2026, 3, 20), "Freelance project", "Income", "Freelance", "Checking", "Bank transfer", 900)
    add(D(2026, 7, 14), "Freelance project", "Income", "Freelance", "Checking", "Bank transfer", 1200)
    add(D(2026, 10, 9), "Freelance project", "Income", "Freelance", "Checking", "Bank transfer", 600)
    add(D(2026, 10, 24), "Furniture sale", "Expense", "Shopping", "Credit card", "Credit card", 480, "Over budget month")
    add(D(2026, 6, 30), "Bank interest", "Income", "Interest", "Savings", "Bank transfer", 38)

    txs.sort(key=lambda t: t["Date"])
    for t in txs:
        t["Description"] = t["Description"]

    s = REG["tx"]
    cols = [
        dict(h="Transaction ID", kind="calc", w=13, align="center",
             f=lambda r: f'IF(ISNUMBER(C{r}),"TX-"&TEXT(ROW()-5,"0000"),"")'),
        dict(h="Date", kind="in", w=13, fmt=FMT_DATE),
        dict(h="Description", kind="in", w=26),
        dict(h="Type", kind="in", w=10, align="center"),
        dict(h="Category", kind="in", w=18),
        dict(h="Account", kind="in", w=14),
        dict(h="Payment Method", kind="in", w=15),
        dict(h="Amount", kind="in", w=13, fmt=FMT_MONEY),
        dict(h="Month", kind="calc", w=11, fmt="mmm yyyy", align="center",
             f=lambda r: f'IF(ISNUMBER(C{r}),DATE(YEAR(C{r}),MONTH(C{r}),1),"")'),
        dict(h="Group", kind="calc", w=11, align="center",
             f=lambda r: f'IF(E{r}="Income","Income",IF(LEN(F{r})=0,"",IFERROR(INDEX(CatGroup,MATCH(F{r},CatList,0)),"")))'),
        dict(h="Class", kind="calc", w=16, align="center",
             f=lambda r: f'IF(E{r}="Income","Income",IF(LEN(F{r})=0,"",IFERROR(INDEX(CatClass,MATCH(F{r},CatList,0)),"")))'),
        dict(h="Month Key", kind="calc", w=12, align="center",
             f=lambda r: f'IF(ISNUMBER(J{r}),J{r}*1000+COUNTIF({{^Month}},J{r}),"")'),
        dict(h="Notes", kind="in", w=24),
    ]
    rows = [dict(zip(["Date", "Description", "Type", "Category", "Account", "Payment Method", "Amount", "Notes"],
                     [t["Date"], t["Description"], t["Type"], t["Category"], t["Account"], t["Payment Method"], t["Amount"], t["Notes"]]))
            for t in txs]
    write_table(ws, "tx", cols, rows)
    # fix the expanding-range reference for Month Key (column J = Month)
    for r in range(s["first"], s["last"] + 1):
        ws[f"M{r}"].value = f'=IF(ISNUMBER(J{r}),J{r}*1000+COUNTIF($J${s["first"]}:J{r},J{r}),"")'
    dv_list(ws, "E6:E405", "TypeList")
    dv_list(ws, "F6:F405", "CatList")
    dv_list(ws, "G6:G405", "AccountList")
    dv_list(ws, "H6:H405", "MethodList")
    dv_date(ws, "C6:C405")
    cf(ws, "E6:E405", '$E6="Income"', SOFT_TEAL, SUCCESS, True)
    cf(ws, "E6:E405", '$E6="Expense"', DANGER_BG, DANGER, True)
    cf(ws, "K6:K405", '$K6="Savings"', SOFT_BLUE, INFO, True)
    cf(ws, "K6:K405", '$K6="Debt"', SOFT_LAV, DARK, True)
    ws.freeze_panes = "D6"
    ws.column_dimensions["N"].hidden = False
    for c_ in ("M",):
        ws.column_dimensions[c_].hidden = True
    legend(ws, 3, 10)


# ------------------------------------------------------------------ 6 All-in-one dashboard
MONTH_ROWS = (7, 18)  # Annual Totals month rows


def build_dashboard(ws):
    page(ws, "All-in-One Dashboard", "Income, spending, savings and debt at a glance. Everything calculates from the transaction ledger.",
         BLUE, 13, demo=True)
    for c_ in "BCDEFGHIJKLM":
        ws.column_dimensions[c_].width = 14
    for c_ in "PQRSTUVWX":
        ws.column_dimensions[c_].width = 13
    kpis = [
        ("TOTAL INCOME", f'=SUMIFS({TX_AMT},{TX_TYPE},"Income")', FMT_MONEY, "all recorded income", TEAL),
        ("TOTAL EXPENSES", f'=SUMIFS({TX_AMT},{TX_TYPE},"Expense",{TX_GROUP},"<>Savings")', FMT_MONEY, "spending, excludes savings", DANGER),
        ("NET CASH FLOW", None, FMT_MONEY, "income minus spending and savings", TEAL),
        ("TOTAL SAVINGS", f'=SUMIFS({TX_AMT},{TX_TYPE},"Expense",{TX_GROUP},"Savings")', FMT_MONEY, "transfers to savings", BLUE),
        ("SAVINGS RATE", None, FMT_PCT, "savings divided by income", BLUE),
        ("MONTHLY BUDGET", "=MonthlyBudget", FMT_MONEY, "set on Easy Setup", LAV),
        ("BUDGET REMAINING (THIS MONTH)", None, FMT_MONEY, "budget minus this month's spending", LAV),
        ("TOTAL DEBT", f"=SUM({DEBT_BAL})", FMT_MONEY, "current balances, Debt Calculator", DANGER),
    ]

    def pos(i):
        return f"{['B', 'E', 'H', 'K'][i % 4]}{6 + 4 * (i // 4)}"

    # net cash flow = income - spending - savings
    kpis[2] = (kpis[2][0], f"={pos(0)}-{pos(1)}-{pos(3)}", FMT_MONEY, kpis[2][3], kpis[2][4])
    kpis[4] = (kpis[4][0], f"=IFERROR({pos(3)}/{pos(0)},0)", FMT_PCT, kpis[4][3], kpis[4][4])
    this_m = "DATE(BudgetYear,MONTH(TODAY()),1)"
    spend_this = (f'SUMIFS({TX_AMT},{TX_TYPE},"Expense",{TX_GROUP},"<>Savings",{TX_MONTH},{this_m})')
    kpis[6] = (kpis[6][0], f"=MonthlyBudget-{spend_this}", FMT_MONEY, kpis[6][3], kpis[6][4])
    for i, (lab, f, fmt, sub, colr) in enumerate(kpis):
        k = i // 4
        c0 = 2 + 3 * (i % 4)
        r0 = 5 + 4 * k
        for rr, txt, font_, bgc in ((r0, lab, fnt(8, True, WHITE), colr),
                                    (r0 + 1, f, fnt(18, True, NAVY), WHITE),
                                    (r0 + 2, sub, fnt(8, False, SEC), WHITE)):
            ws.merge_cells(start_row=rr, start_column=c0, end_row=rr, end_column=c0 + 2)
            cell = ws.cell(rr, c0, txt)
            cell.font = font_
            cell.alignment = Alignment(vertical="center", indent=1)
            for cc in range(c0, c0 + 3):
                ws.cell(rr, cc).fill = fill(bgc)
                ws.cell(rr, cc).border = Border(
                    left=SIDE if cc == c0 else None, right=SIDE if cc == c0 + 2 else None,
                    top=SIDE if rr == r0 else None, bottom=SIDE if rr == r0 + 2 else None)
        ws.cell(r0 + 1, c0).number_format = fmt
        ws.row_dimensions[r0 + 1].height = 28
        ws.row_dimensions[r0].height = 18
    band(ws, 17, 2, 13, "CHARTS", BLUE)

    # chart data (automatic) P..X
    band(ws, 4, 16, 24, "CHART DATA (automatic)", MIDNIGHT, 8)
    ws["P5"] = "Month"; ws["Q5"] = "Income"; ws["R5"] = "Spending"; ws["S5"] = "Savings"
    ws["T5"] = "Net"; ws["U5"] = "Budget"
    for c_ in "PQRSTU":
        ws[f"{c_}5"].font = fnt(8, True, WHITE)
        ws[f"{c_}5"].fill = fill(MIDNIGHT)
    for m in range(12):
        r = 6 + m
        src = MONTH_ROWS[0] + m
        ws[f"P{r}"] = f"='Annual Totals'!B{src}"
        ws[f"Q{r}"] = f"='Annual Totals'!C{src}"
        ws[f"R{r}"] = f"='Annual Totals'!D{src}"
        ws[f"S{r}"] = f"='Annual Totals'!E{src}"
        ws[f"T{r}"] = f"='Annual Totals'!F{src}"
        ws[f"U{r}"] = f"='Annual Totals'!H{src}"
    for r in range(6, 18):
        for c_ in "QRSTU":
            ws[f"{c_}{r}"].number_format = FMT_MONEY
            ws[f"{c_}{r}"].font = fnt(8)
    ws["P18"] = "Category"; ws["Q18"] = "YTD spend"
    for c_ in "PQ":
        ws[f"{c_}18"].font = fnt(8, True, WHITE)
        ws[f"{c_}18"].fill = fill(MIDNIGHT)
    for i in range(13):
        r = 19 + i
        ws[f"P{r}"] = f"='Expense Distribution'!B{6 + i}"
        ws[f"Q{r}"] = f"='Expense Distribution'!C{6 + i}"
        ws[f"Q{r}"].number_format = FMT_MONEY
        ws[f"P{r}"].font = fnt(8)
        ws[f"Q{r}"].font = fnt(8)
    ws["P33"] = "Goal"; ws["Q33"] = "Saved"; ws["R33"] = "Target"
    for c_ in "PQR":
        ws[f"{c_}33"].font = fnt(8, True, WHITE)
        ws[f"{c_}33"].fill = fill(MIDNIGHT)
    for i in range(4):
        r = 34 + i
        ws[f"P{r}"] = f"='Sinking Funds'!B{7 + i}"
        ws[f"Q{r}"] = f"='Sinking Funds'!D{7 + i}"
        ws[f"R{r}"] = f"='Sinking Funds'!C{7 + i}"
        for c_ in "PQR":
            ws[f"{c_}{r}"].font = fnt(8)
        ws[f"Q{r}"].number_format = FMT_MONEY
        ws[f"R{r}"].number_format = FMT_MONEY

    def style_chart(ch, title, w=16, h=7.4):
        ch.title = title
        ch.width, ch.height = w, h
        ch.legend.position = "b"
        return ch

    c1 = style_chart(BarChart(), "Income vs spending by month")
    c1.type = "col"
    c1.add_data(Reference(ws, min_col=17, max_col=18, min_row=5, max_row=17), titles_from_data=True)
    c1.set_categories(Reference(ws, min_col=16, min_row=6, max_row=17))
    c1.series[0].graphicalProperties.solidFill = TEAL
    c1.series[1].graphicalProperties.solidFill = "DC5B64"
    ws.add_chart(c1, "B18")

    c2 = style_chart(DoughnutChart(), "Expense distribution (year to date)")
    c2.add_data(Reference(ws, min_col=17, min_row=18, max_row=31), titles_from_data=True)
    c2.set_categories(Reference(ws, min_col=16, min_row=19, max_row=31))
    palette = [BLUE, TEAL, LAV, WARN, INFO, MGRAY, DANGER, MIDNIGHT, "6FCFC1", "B9AEF2", "F2C27B", "9AB8E8", "E9A3AA"]
    for i, colr in enumerate(palette):
        pt = DataPoint(idx=i)
        pt.graphicalProperties.solidFill = colr
        c2.series[0].dPt.append(pt)
    c2.dataLabels = DataLabelList()
    c2.dataLabels.showPercent = True
    c2.dataLabels.showVal = False
    c2.dataLabels.showCatName = False
    c2.dataLabels.showSerName = False
    c2.dataLabels.showLegendKey = False
    ws.add_chart(c2, "H18")

    c3 = style_chart(LineChart(), "Monthly cash flow (net)")
    c3.add_data(Reference(ws, min_col=20, min_row=5, max_row=17), titles_from_data=True)
    c3.set_categories(Reference(ws, min_col=16, min_row=6, max_row=17))
    c3.series[0].graphicalProperties.line.solidFill = BLUE
    c3.series[0].graphicalProperties.line.width = 28000
    ws.add_chart(c3, "B34")

    c4 = style_chart(BarChart(), "Savings progress by goal")
    c4.type = "bar"
    c4.add_data(Reference(ws, min_col=17, max_col=18, min_row=33, max_row=37), titles_from_data=True)
    c4.set_categories(Reference(ws, min_col=16, min_row=34, max_row=37))
    c4.series[0].graphicalProperties.solidFill = BLUE
    c4.series[1].graphicalProperties.solidFill = LAV
    ws.add_chart(c4, "H34")

    c5 = style_chart(BarChart(), "Budget vs actual spending by month")
    c5.type = "col"
    c5.add_data(Reference(ws, min_col=18, min_row=5, max_row=17), titles_from_data=True)
    c5.add_data(Reference(ws, min_col=21, min_row=5, max_row=17), titles_from_data=True)
    c5.set_categories(Reference(ws, min_col=16, min_row=6, max_row=17))
    c5.series[0].graphicalProperties.solidFill = DANGER
    c5.series[1].graphicalProperties.solidFill = MGRAY
    ws.add_chart(c5, "B50")

    c6 = style_chart(BarChart(), "Category breakdown (year to date)")
    c6.type = "bar"
    c6.add_data(Reference(ws, min_col=17, min_row=18, max_row=31), titles_from_data=True)
    c6.set_categories(Reference(ws, min_col=16, min_row=19, max_row=31))
    c6.series[0].graphicalProperties.solidFill = LAV
    c6.legend = None
    ws.add_chart(c6, "H50")
    band(ws, 67, 2, 13, "MONTH SNAPSHOT", BLUE)
    label(ws, "B68", "Spending this month")
    calc(ws, "E68", f"={spend_this}", FMT_MONEY, True)
    label(ws, "H68", "Savings this month")
    calc(ws, "K68", f'=SUMIFS({TX_AMT},{TX_TYPE},"Expense",{TX_GROUP},"Savings",{TX_MONTH},{this_m})', FMT_MONEY, True)
    label(ws, "B69", "Income this month")
    calc(ws, "E69", f'=SUMIFS({TX_AMT},{TX_TYPE},"Income",{TX_MONTH},{this_m})', FMT_MONEY, True)
    ws.freeze_panes = "A4"


# ------------------------------------------------------------------ 7 Annual totals
def build_annual(ws):
    page(ws, "Annual Totals", "Month-by-month totals for the budget year, with savings rate and budget variance.",
         BLUE, 9, demo=True)
    set_widths(ws, {"B": 12, "C": 15, "D": 15, "E": 15, "F": 16, "G": 13, "H": 15, "I": 16})
    heads = ["Month", "Income", "Spending", "Savings", "Net cash flow", "Savings rate", "Budget", "Budget variance"]
    for j, h in enumerate(heads):
        c = ws.cell(6, 2 + j, h)
        c.font = fnt(9, True, WHITE)
        c.fill = fill(NAVY)
        c.alignment = Alignment(horizontal="center", wrap_text=True)
    ws.row_dimensions[6].height = 30
    for m in range(12):
        r = 7 + m
        mstart = f"DATE(BudgetYear,{m + 1},1)"
        calc(ws, f"B{r}", f'=TEXT({mstart},"mmm")', None, True, "left")
        calc(ws, f"C{r}", f'=SUMIFS({TX_AMT},{TX_TYPE},"Income",{TX_MONTH},{mstart})', FMT_MONEY, False, None, SOFT_TEAL)
        calc(ws, f"D{r}", f'=SUMIFS({TX_AMT},{TX_TYPE},"Expense",{TX_GROUP},"<>Savings",{TX_MONTH},{mstart})', FMT_MONEY)
        calc(ws, f"E{r}", f'=SUMIFS({TX_AMT},{TX_TYPE},"Expense",{TX_GROUP},"Savings",{TX_MONTH},{mstart})', FMT_MONEY, False, None, SOFT_BLUE)
        calc(ws, f"F{r}", f"=C{r}-D{r}-E{r}", FMT_MONEY, True)
        calc(ws, f"G{r}", f"=IFERROR(E{r}/C{r},0)", FMT_PCT)
        calc(ws, f"H{r}", "=MonthlyBudget", FMT_MONEY, False, None, SOFT_LAV)
        calc(ws, f"I{r}", f"=H{r}-D{r}", FMT_MONEY, True)
    r = 19
    label(ws, f"B{r}", "YEAR")
    for col_ in "CDEFHI":
        calc(ws, f"{col_}{r}", f"=SUM({col_}7:{col_}18)", FMT_MONEY, True, None, SOFT_LAV)
    calc(ws, f"G{r}", f"=IFERROR(E{r}/C{r},0)", FMT_PCT, True, None, SOFT_LAV)
    sign_fmt(ws, "F7:F19")
    sign_fmt(ws, "I7:I19")
    band(ws, 21, 2, 9, "ANNUAL COMPARISON", BLUE)
    comp = [
        ("Average monthly income", "=IFERROR(AVERAGEIF(C7:C18,\">0\"),0)", FMT_MONEY),
        ("Average monthly spending", "=IFERROR(AVERAGEIF(D7:D18,\">0\"),0)", FMT_MONEY),
        ("Best month (net cash flow)", "=INDEX(B7:B18,MATCH(MAX(F7:F18),F7:F18,0))", None),
        ("Hardest month (net cash flow)", "=INDEX(B7:B18,MATCH(MIN(F7:F18),F7:F18,0))", None),
        ("Months over budget", '=COUNTIF(I7:I18,"<0")', "0"),
        ("Savings target met (months)", '=COUNTIFS(G7:G18,">="&SavingsTarget)', "0"),
    ]
    for i, (lab, f, fmt) in enumerate(comp):
        r = 22 + i
        label(ws, f"B{r}", lab)
        ws.merge_cells(f"B{r}:D{r}")
        calc(ws, f"E{r}", f, fmt, True, "right")
        ws.merge_cells(f"E{r}:F{r}")
    label(ws, "B30", "Months with no entries show zero. Savings rate = savings divided by income.", False)
    legend(ws, 32, 2)
    ws.freeze_panes = "A7"


# ------------------------------------------------------------------ 8 Automated calendar
def build_cal(ws):
    page(ws, "Automated Calendar", "Income dates, bills, recurring payments and savings contributions on one calendar.",
         BLUE, 13, demo=True)
    set_widths(ws, {"B": 17, "C": 17, "D": 17, "E": 17, "F": 17, "G": 17, "H": 17, "I": 3,
                    "J": 26, "K": 14, "L": 20})
    label(ws, "B4", "Month")
    inp(ws, "C4", "November")
    label(ws, "E4", "Year")
    calc(ws, "F4", "=BudgetYear", "0", True, "center")
    dv_list(ws, "C4", "MonthList_bud") if False else None
    ws["P4"] = f'=DATE($F$4,IFERROR(MATCH($C$4,{{"January","February","March","April","May","June","July","August","September","October","November","December"}},0),11),1)'
    ws["Q4"] = "=DAY(EOMONTH($P$4,0))"
    ws["R4"] = "=MOD(WEEKDAY($P$4,1)-2,7)"
    for c_ in ("P", "Q", "R"):
        ws.column_dimensions[c_].hidden = True
    ws["P4"].number_format = FMT_DATE
    dv_list(ws, "C4", '"' + ",".join(MONTHS) + '"')
    cols = "BCDEFGH"
    for c_ in range(7):
        h = ws[f"{cols[c_]}6"]
        h.value = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][c_]
        h.font = fnt(9, True, WHITE)
        h.fill = fill(NAVY)
        h.alignment = Alignment(horizontal="center")
    TD = TX_DATE; TT = TX_TYPE; TG = TX_GROUP
    PD = R("pay", "Due Date"); PS = R("pay", "Status")
    RN = R("rec", "Next Payment")
    for w in range(6):
        rd = 7 + 2 * w
        for c_ in range(7):
            X = cols[c_]
            e = f"({7 * w + c_}-$R$4)"
            ws[f"{X}{rd}"] = f'=IF(AND({e}>=0,{e}<$Q$4),$P$4+{e},"")'
            ws[f"{X}{rd}"].number_format = "d"
            ws[f"{X}{rd}"].font = fnt(11, True, NAVY)
            ws[f"{X}{rd}"].fill = fill(WHITE)
            ws[f"{X}{rd}"].border = BOX
            ws[f"{X}{rd}"].alignment = Alignment(horizontal="left", vertical="top", indent=1)
            inc = f'COUNTIFS({TD},{X}{rd},{TT},"Income")'
            bills = f'COUNTIFS({PD},{X}{rd},{PS},"Unpaid")+COUNTIF({RN},{X}{rd})'
            sav = f'COUNTIFS({TD},{X}{rd},{TG},"Savings")'
            ws[f"{X}{rd + 1}"] = (f'=IF({X}{rd}="","",IF(({inc})+({bills})+({sav})=0,"",'
                                  f'"+"&({inc})&" in · "&({bills})&" bills · "&({sav})&" save"))')
            ws[f"{X}{rd + 1}"].font = fnt(8, True, DARK)
            ws[f"{X}{rd + 1}"].fill = fill(SOFT_BLUE)
            ws[f"{X}{rd + 1}"].border = BOX
            ws[f"{X}{rd + 1}"].alignment = Alignment(wrap_text=True, vertical="center")
        ws.row_dimensions[rd].height = 20
        ws.row_dimensions[rd + 1].height = 30
        cf(ws, f"B{rd}:H{rd}", f"AND(ISNUMBER(B{rd}),B{rd}=TODAY())", BLUE, WHITE, True)
    band(ws, 6, 10, 12, "THIS MONTH'S ITEMS", MIDNIGHT, 9)
    for c_, h in zip("JKL", ["Item", "Date", "Amount"]):
        ws[f"{c_}7"] = h
        ws[f"{c_}7"].font = fnt(9, True, WHITE)
        ws[f"{c_}7"].fill = fill(NAVY)
    label(ws, "J8", "Income this month")
    calc(ws, "L8", f'=SUMIFS({TX_AMT},{TT},"Income",{TX_MONTH},$P$4)', FMT_MONEY, True)
    label(ws, "J9", "Unpaid bills this month")
    calc(ws, "L9", f'=SUMIFS({R("pay", "Amount")},{PD},">="&$P$4,{PD},"<="&EOMONTH($P$4,0),{PS},"Unpaid")', FMT_MONEY, True)
    label(ws, "J10", "Savings this month")
    calc(ws, "L10", f'=SUMIFS({TX_AMT},{TG},"Savings",{TX_MONTH},$P$4)', FMT_MONEY, True)
    label(ws, "J11", "Recurring items due this month")
    calc(ws, "L11", f'=COUNTIFS({RN},">="&$P$4,{RN},"<="&EOMONTH($P$4,0))', "0", True)
    legend(ws, 21, 2)
    label(ws, "B23", "Cell text: + income entries, bills (unpaid payments and recurring items due), savings transfers.", False)
    ws.freeze_panes = "A6"


# ------------------------------------------------------------------ 9 Paycheck dashboard
def build_paycheck(ws):
    page(ws, "Paycheck Dashboard", "Each paycheck: gross, deductions, net, and where the net money goes.",
         BLUE, 11, demo=True)
    rows = [dict(zip(["Pay Date", "Gross Pay", "Deductions", "Bills Allocated", "Savings Allocated"], r_))
            for r_ in [
                (D(2026, 9, 18), 2400, 620, 1350, 300),
                (D(2026, 10, 2), 2400, 620, 1350, 300),
                (D(2026, 10, 16), 2400, 620, 1380, 300),
                (D(2026, 10, 30), 2400, 620, 1380, 350),
                (D(2026, 11, 13), 2400, 620, 1380, 350),
            ]]
    write_table(ws, "pc", [
        dict(h="Pay Date", kind="in", w=14, fmt=FMT_DATE),
        dict(h="Gross Pay", kind="in", w=14, fmt=FMT_MONEY),
        dict(h="Deductions", kind="in", w=14, fmt=FMT_MONEY),
        dict(h="Net Pay", kind="calc", w=14, fmt=FMT_MONEY, f=lambda r: f'IF(ISNUMBER(C{r}),C{r}-N(D{r}),"")'),
        dict(h="Bills Allocated", kind="in", w=15, fmt=FMT_MONEY),
        dict(h="Savings Allocated", kind="in", w=16, fmt=FMT_MONEY),
        dict(h="Remaining", kind="calc", w=14, fmt=FMT_MONEY,
             f=lambda r: f'IF(ISNUMBER(E{r}),E{r}-N(F{r})-N(G{r}),"")'),
        dict(h="Deduction Rate", kind="calc", w=14, fmt=FMT_PCT,
             f=lambda r: f'IF(AND(ISNUMBER(C{r}),N(C{r})>0),N(D{r})/C{r},"")'),
    ], rows)
    sign_fmt(ws, "H7:H30")
    band(ws, 4, 10, 12, "SUMMARY")
    summ = [
        ("Average net pay per check", "=IFERROR(AVERAGE(E7:E30),0)", FMT_MONEY),
        ("Average deduction rate", "=IFERROR(AVERAGE(I7:I30),0)", FMT_PCT),
        ("Total remaining after bills and savings", "=SUM(H7:H30)", FMT_MONEY),
    ]
    for i, (lab, f, fmt) in enumerate(summ):
        r = 5 + 2 * i
        ws.merge_cells(f"J{r}:K{r}")
        ws[f"J{r}"] = lab
        ws[f"J{r}"].font = fnt(9, True, SEC)
        ws.merge_cells(f"J{r + 1}:K{r + 1}")
        calc(ws, f"J{r + 1}", f, fmt, True, "left", SOFT_TEAL if i != 1 else SOFT_BLUE)
    label(ws, "J12", "Bills and savings are the amounts you planned from each paycheck.", False)
    legend(ws, 14, 10)
    ws.freeze_panes = "A7"


# ------------------------------------------------------------------ 10-21 Monthly sheets
def build_month(ws, m):
    name = MONTHS[m - 1]
    page(ws, f"{name} budget", "Income, fixed and variable spending, savings, debt and the category totals for this month.",
         TEAL, 11, demo=True)
    set_widths(ws, {"B": 30, "C": 16, "D": 3, "E": 14, "F": 14, "G": 14, "H": 14, "I": 3,
                    "J": 26, "K": 12, "L": 15, "M": 13})
    label(ws, "B4", "Month starts")
    calc(ws, "C4", f"=DATE(BudgetYear,{m},1)", FMT_DATE, True, "center")
    ws.column_dimensions["O"].hidden = True
    kpi = [
        (6, "Monthly income", f'=SUMIFS({TX_AMT},{TX_TYPE},"Income",{TX_MONTH},$C$4)', FMT_MONEY, SOFT_TEAL),
        (7, "Fixed expenses", f'=SUMIFS({TX_AMT},{TX_TYPE},"Expense",{TX_GROUP},"Fixed",{TX_MONTH},$C$4)', FMT_MONEY, None),
        (8, "Variable expenses", f'=SUMIFS({TX_AMT},{TX_TYPE},"Expense",{TX_GROUP},"Variable",{TX_MONTH},$C$4)', FMT_MONEY, None),
        (9, "Debt payments", f'=SUMIFS({TX_AMT},{TX_TYPE},"Expense",{TX_GROUP},"Debt",{TX_MONTH},$C$4)', FMT_MONEY, None),
        (10, "Savings transfers", f'=SUMIFS({TX_AMT},{TX_TYPE},"Expense",{TX_GROUP},"Savings",{TX_MONTH},$C$4)', FMT_MONEY, SOFT_BLUE),
        (11, "Monthly budget", "=MonthlyBudget", FMT_MONEY, SOFT_LAV),
        (12, "Actual spending", "=C7+C8+C9", FMT_MONEY, None),
        (13, "Remaining budget", "=C11-C12", FMT_MONEY, None),
        (14, "Savings rate", "=IFERROR(C10/C6,0)", FMT_PCT, None),
        (15, "Net cash flow", "=C6-C12-C10", FMT_MONEY, None),
    ]
    band(ws, 5, 2, 3, "MONTH SUMMARY")
    for r, lab, f, fmt, bg in kpi:
        label(ws, f"B{r}", lab, r in (12, 13, 15))
        calc(ws, f"C{r}", f, fmt, r in (12, 13, 15), "right", bg or LGRAY)
    calc(ws, "B16", '=IF(C6=0,"No income recorded for this month yet",IF(C13<0,"Over budget by "&TEXT(-C13,"#,##0.00"),"Within budget by "&TEXT(C13,"#,##0.00")))',
         None, True, "left", SOFT_LAV)
    ws.merge_cells("B16:C16")
    sign_fmt(ws, "C13:C13")
    sign_fmt(ws, "C15:C15")

    band(ws, 5, 5, 9, "CATEGORY TOTALS")
    for j, h in enumerate(["Category", "Group", "Actual", "Share of spending"]):
        c = ws.cell(6, 5 + j, h)
        c.font = fnt(9, True, WHITE)
        c.fill = fill(NAVY)
        c.alignment = Alignment(horizontal="center", wrap_text=True)
    ws.merge_cells("E5:I5")
    for i in range(13):
        r = 7 + i
        calc(ws, f"E{r}", f"=IF('Easy Setup'!E{6 + i}=\"\",\"\",'Easy Setup'!E{6 + i})", None, False, "left")
        calc(ws, f"F{r}", f"=IF(E{r}=\"\",\"\",'Easy Setup'!F{6 + i})", None, False, "center")
        calc(ws, f"G{r}", f'=IF(E{r}="","",SUMIFS({TX_AMT},{TX_TYPE},"Expense",{TX_CAT},E{r},{TX_MONTH},$C$4))', FMT_MONEY)
        calc(ws, f"H{r}", f'=IF(E{r}="","",IFERROR(G{r}/SUMIFS({TX_AMT},{TX_TYPE},"Expense",{TX_MONTH},$C$4),0))', FMT_PCT)
    cf(ws, "G7:G19", "G7>0", SOFT_BLUE, None, False)
    r = 20
    calc(ws, f"E{r}", "Total", None, True, "left", SOFT_LAV)
    calc(ws, f"G{r}", "=SUM(G7:G19)", FMT_MONEY, True, None, SOFT_LAV)
    calc(ws, f"H{r}", "=IFERROR(SUM(H7:H19),0)", FMT_PCT, True, None, SOFT_LAV)

    band(ws, 23, 2, 9, "TRANSACTIONS THIS MONTH")
    for j, h in enumerate(["Date", "Description", "Type", "Category", "Account", "Amount"]):
        c = ws.cell(24, 2 + j, h)
        c.font = fnt(9, True, WHITE)
        c.fill = fill(NAVY)
        c.alignment = Alignment(horizontal="center")
    ws["I24"] = "Row"
    ws["I24"].font = fnt(8, False, SEC)
    src_map = [TX_DATE, TX_DESC, TX_TYPE, TX_CAT, TX_ACCT, TX_AMT]
    for n in range(1, 31):
        r = 24 + n
        ws[f"I{r}"] = f'=IFERROR(MATCH($C$4*1000+{n},{TX_KEY},0),"")'
        ws[f"I{r}"].font = fnt(7, False, MGRAY)
        for j, src in enumerate(src_map):
            cell = ws.cell(r, 2 + j)
            cell.value = f'=IF($I{r}="","",INDEX({src},$I{r}))'
            cell.font = fnt(9)
            cell.border = BOX
            cell.fill = fill(WHITE)
            cell.alignment = Alignment(horizontal="center" if j in (0, 2) else None)
            if j == 0:
                cell.number_format = FMT_DATE
            if j == 5:
                cell.number_format = FMT_MONEY
    cf(ws, "D25:D54", '$D25="Income"', SOFT_TEAL, SUCCESS, True)
    cf(ws, "D25:D54", '$D25="Expense"', DANGER_BG, DANGER, True)
    ws.column_dimensions["I"].width = 6
    label(ws, "B56", "Showing up to 30 transactions. Add more in Variable Transactions; the month totals above include all of them.", False)
    legend(ws, 58, 2)
    ws.freeze_panes = "A6"


# ------------------------------------------------------------------ 22 50/30/20
def build_5030(ws):
    page(ws, "50/30/20 Dashboard", "Needs at 50%, wants at 30%, savings and debt repayment at 20% of income, year to date.",
         LAV, 8, demo=True)
    set_widths(ws, {"B": 30, "C": 16, "D": 16, "E": 16, "F": 16, "G": 16, "H": 16})
    label(ws, "B4", "Income year to date")
    calc(ws, "C4", f'=SUMIFS({TX_AMT},{TX_TYPE},"Income")', FMT_MONEY, True, "right", SOFT_TEAL)
    heads = ["Bucket", "Target share", "Target amount", "Actual", "Difference", "Status"]
    for j, h in enumerate(heads):
        c = ws.cell(6, 2 + j, h)
        c.font = fnt(9, True, WHITE)
        c.fill = fill(NAVY)
        c.alignment = Alignment(horizontal="center", wrap_text=True)
    ws.row_dimensions[6].height = 30
    buckets = [("Needs", 0.50, "Needs"), ("Wants", 0.30, "Wants"), ("Savings and debt repayment", 0.20, "Savings and debt")]
    for i, (lab, share, cls) in enumerate(buckets):
        r = 7 + i
        calc(ws, f"B{r}", lab, None, True, "left")
        calc(ws, f"C{r}", share, FMT_PCT, False, "center", SOFT_LAV)
        calc(ws, f"D{r}", f"=C{r}*$C$4", FMT_MONEY)
        calc(ws, f"E{r}", f'=SUMIFS({TX_AMT},{TX_TYPE},"Expense",{TX_CLASS},"{cls}")', FMT_MONEY, True)
        calc(ws, f"F{r}", f"=D{r}-E{r}", FMT_MONEY)
        if cls == "Savings and debt":
            calc(ws, f"G{r}", f'=IF(E{r}>=D{r},"On target","Below target")', None, True, "center")
        else:
            calc(ws, f"G{r}", f'=IF(E{r}<=D{r},"Within target","Over target")', None, True, "center")
    cf(ws, "G7:G9", 'OR(G7="Over target",G7="Below target")', WARN_BG, DARK, True)
    cf(ws, "G7:G9", 'OR(G7="Within target",G7="On target")', SUCCESS_BG, SUCCESS, True)
    label(ws, "B11", "Total (should equal income for a full allocation)")
    calc(ws, "E11", "=SUM(E7:E9)", FMT_MONEY, True, "right", SOFT_LAV)
    calc(ws, "F11", "=C4-E11", FMT_MONEY, True, "right", SOFT_LAV)
    label(ws, "B13", "How to read it: a positive difference means room left in that bucket. Negative means over target.", False)
    label(ws, "B14", "Each category's class is set on Easy Setup (Needs, Wants, Savings and debt).", False)
    legend(ws, 16, 2)
    ws.freeze_panes = "A7"


# ------------------------------------------------------------------ 23 Expense distribution
def build_distribution(ws):
    page(ws, "Expense Distribution", "Where the money goes: spending by category, year to date, with share and monthly average.",
         LAV, 8, demo=True)
    set_widths(ws, {"B": 24, "C": 16, "D": 14, "E": 16, "F": 10, "G": 3, "H": 14})
    heads = ["Category", "Year to date", "Share", "Monthly average", "Rank"]
    for j, h in enumerate(heads):
        c = ws.cell(5, 2 + j, h)
        c.font = fnt(9, True, WHITE)
        c.fill = fill(NAVY)
        c.alignment = Alignment(horizontal="center", wrap_text=True)
    ws.row_dimensions[5].height = 30
    for i in range(13):
        r = 6 + i
        calc(ws, f"B{r}", f"=IF('Easy Setup'!E{6 + i}=\"\",\"\",'Easy Setup'!E{6 + i})", None, False, "left")
        calc(ws, f"C{r}", f'=IF(B{r}="","",SUMIFS({TX_AMT},{TX_TYPE},"Expense",{TX_CAT},B{r}))', FMT_MONEY, True)
        calc(ws, f"D{r}", f'=IF(B{r}="","",IFERROR(C{r}/$C$19,0))', FMT_PCT)
        calc(ws, f"E{r}", f'=IF(B{r}="","",C{r}/MAX(1,MONTH(TODAY())))', FMT_MONEY)
        calc(ws, f"F{r}", f'=IF(OR(B{r}="",C{r}=0),"",COUNTIF($C$6:$C$18,">"&C{r})+1)', "0", False, "center")
    label(ws, "B19", "Total", True)
    calc(ws, "C19", "=SUM(C6:C18)", FMT_MONEY, True, "right", SOFT_LAV)
    calc(ws, "D19", "=SUM(D6:D18)", FMT_PCT, True, "right", SOFT_LAV)
    calc(ws, "E19", "=SUM(E6:E18)", FMT_MONEY, True, "right", SOFT_LAV)
    ws.conditional_formatting.add("D6:D18", DataBarRule(start_type="num", start_value=0, end_type="num",
                                                       end_value=1, color=LAV))
    bc = BarChart()
    bc.type = "bar"
    bc.title = "All expense categories (year to date)"
    bc.add_data(Reference(ws, min_col=3, min_row=5, max_row=18), titles_from_data=True)
    bc.set_categories(Reference(ws, min_col=2, min_row=6, max_row=18))
    bc.series[0].graphicalProperties.solidFill = LAV
    bc.legend = None
    bc.width, bc.height = 16, 9
    ws.add_chart(bc, "H5")
    pc = DoughnutChart()
    pc.title = "Share of spending"
    pc.add_data(Reference(ws, min_col=3, min_row=5, max_row=18), titles_from_data=True)
    pc.set_categories(Reference(ws, min_col=2, min_row=6, max_row=18))
    pc.width, pc.height = 16, 9
    pc.legend.position = "r"
    ws.add_chart(pc, "H24")
    label(ws, "B21", "Monthly average divides the year-to-date total by the number of months elapsed in the current calendar year.", False)
    ws.freeze_panes = "A6"


# ------------------------------------------------------------------ 24 Sinking funds
def build_funds(ws):
    page(ws, "Sinking Funds", "Savings goals with a target date. See how far you are and what each month needs.",
         LAV, 11, demo=True)
    rows = [
        ("Emergency fund", 10000, 4200, 400, D(2027, 6, 30)),
        ("Car replacement", 6000, 1500, 250, D(2027, 3, 31)),
        ("Holiday", 1500, 900, 150, D(2026, 12, 15)),
        ("Home repairs", 3000, 600, 120, D(2027, 12, 31)),
    ]
    rows_d = [dict(zip(["Fund", "Target", "Current Balance", "Monthly Contribution", "Target Date"], r_)) for r_ in rows]
    write_table(ws, "fund", [
        dict(h="Fund", kind="in", w=24),
        dict(h="Target", kind="in", w=14, fmt=FMT_MONEY),
        dict(h="Current Balance", kind="in", w=15, fmt=FMT_MONEY),
        dict(h="Monthly Contribution", kind="in", w=16, fmt=FMT_MONEY),
        dict(h="Remaining", kind="calc", w=14, fmt=FMT_MONEY, f=lambda r: f'IF(ISNUMBER(C{r}),MAX(0,C{r}-N(D{r})),"")'),
        dict(h="Target Date", kind="in", w=14, fmt=FMT_DATE),
        dict(h="Months Left", kind="calc", w=11, align="center",
             f=lambda r: f'IF(ISNUMBER(G{r}),MAX(0,DATEDIF(TODAY(),G{r},"m")),"")'),
        dict(h="Needed per Month", kind="calc", w=15, fmt=FMT_MONEY,
             f=lambda r: f'IF(AND(ISNUMBER(F{r}),N(H{r})>0),F{r}/H{r},"")'),
        dict(h="Completion", kind="calc", w=12, fmt=FMT_PCT,
             f=lambda r: f'IF(AND(ISNUMBER(C{r}),N(C{r})>0),MIN(1,N(D{r})/N(C{r})),0)'),
        dict(h="Status", kind="calc", w=20, align="center",
             f=lambda r: (f'IF(LEN(B{r})=0,"",IF(N(F{r})<=0,"Fully funded",'
                          f'IF(NOT(ISNUMBER(H{r})),"Set a target date",'
                          f'IF(N(E{r})*0+N(E{r})>=0,IF(E{r}*(IF(H{r}=0,1,H{r}))<=F{r},"Increase contribution","On track"),"On track"))))')),
    ], rows_d)
    ws.column_dimensions["E"].width = 14
    # fix Status to a simple, correct rule: on track if contribution * months left covers remaining
    sr = REG["fund"]
    for r in range(sr["first"], sr["last"] + 1):
        ws[f"K{r}"].value = (f'=IF(LEN(B{r})=0,"",IF(N(F{r})<=0,"Fully funded",'
                             f'IF(NOT(ISNUMBER(H{r})),"Set a target date",'
                             f'IF(N(E{r})*N(H{r})>=N(F{r}),"On track","Increase contribution"))))')
    cf(ws, "J7:J10", "J7>=1", SUCCESS_BG, SUCCESS, True)
    ws.conditional_formatting.add("J7:J10", DataBarRule(start_type="num", start_value=0, end_type="num",
                                                       end_value=1, color=LAV))
    cf(ws, "K7:K10", '$K7="Increase contribution"', WARN_BG, DARK, True)
    cf(ws, "K7:K10", '$K7="On track"', SUCCESS_BG, SUCCESS, True)
    cf(ws, "K7:K10", '$K7="Fully funded"', SOFT_LAV, DARK, True)
    label(ws, "B12", "Totals", True)
    calc(ws, "C12", "=SUM(C7:C10)", FMT_MONEY, True, "right", SOFT_LAV)
    calc(ws, "D12", "=SUM(D7:D10)", FMT_MONEY, True, "right", SOFT_LAV)
    calc(ws, "E12", "=SUM(E7:E10)", FMT_MONEY, True, "right", SOFT_LAV)
    label(ws, "B14", "Status: On track when monthly contribution times months left covers what remains.", False)
    legend(ws, 16, 2)
    ws.freeze_panes = "B6"


# ------------------------------------------------------------------ 25 Debt calculator
def build_debt(ws):
    page(ws, "Debt Calculator", "Each debt with its payoff date. Choose snowball (smallest balance first) or avalanche (highest rate first).",
         LAV, 13, demo=True)
    label(ws, "B4", "Repayment method")
    inp(ws, "C4", "Avalanche")
    dv_list(ws, "C4", '"Snowball,Avalanche"')
    rows = [
        ("Credit card", "Credit card", 3250, 3250, 0.229, 95, 100),
        ("Car loan", "Loan", 8400, 8400, 0.065, 350, 0),
        ("Student loan", "Loan", 12800, 12800, 0.042, 180, 50),
    ]
    rows_d = [dict(zip(["Debt", "Type", "Starting Balance", "Current Balance", "APR", "Minimum Payment", "Extra Payment"], r_))
              for r_ in rows]
    s = REG["debt"]

    def pay_f(r):
        return f"IF(ISNUMBER(H{r}),N(H{r})+N(I{r}),\"\")"

    write_table(ws, "debt", [
        dict(h="Debt", kind="in", w=20),
        dict(h="Type", kind="in", w=13),
        dict(h="Starting Balance", kind="in", w=15, fmt=FMT_MONEY),
        dict(h="Current Balance", kind="in", w=15, fmt=FMT_MONEY),
        dict(h="APR", kind="in", w=9, fmt=FMT_PCT, align="center"),
        dict(h="Minimum Payment", kind="in", w=15, fmt=FMT_MONEY),
        dict(h="Extra Payment", kind="in", w=14, fmt=FMT_MONEY),
        dict(h="Total Monthly Payment", kind="calc", w=16, fmt=FMT_MONEY, f=lambda r: pay_f(r)),
        dict(h="Months to Payoff", kind="calc", w=14, align="center",
             f=lambda r: (f'IF(OR(NOT(ISNUMBER(E{r})),N(E{r})<=0),"",IF(N(E{r})>0,IFERROR(NPER(F{r}/12,-N(I{r}),N(E{r})),""),'
                          f'""))') if False else
             (f'IF(NOT(ISNUMBER(E{r})),"",IF(N(E{r})<=0,0,IF(N(I{r})<=0,"no payment",'
              f'IFERROR(IF(N(F{r})=0,N(E{r})/N(I{r}),NPER(N(F{r})/12,-N(I{r}),N(E{r}))),"no payment"))))')),
        dict(h="Payoff Date", kind="calc", w=14, fmt=FMT_DATE,
             f=lambda r: f'IF(ISNUMBER(J{r}),EDATE(TODAY(),ROUNDUP(J{r},0)),"")'),
        dict(h="Snowball Rank", kind="calc", w=12, align="center",
             f=lambda r: f'IF(LEN(B{r})=0,"",COUNTIF($E${s["first"]}:$E${s["last"]},"<"&E{r})+COUNTIF($E${s["first"]}:E{r},E{r}))'),
        dict(h="Avalanche Rank", kind="calc", w=12, align="center",
             f=lambda r: f'IF(LEN(B{r})=0,"",COUNTIF($F${s["first"]}:$F${s["last"]},">"&F{r})+COUNTIF($F${s["first"]}:F{r},F{r}))'),
    ], rows_d)
    # Rearranged columns: B Debt, C Type, D Starting, E Current, F APR, G Min, H Extra, I Total pay,
    # J Months, K Payoff, L Snowball rank, M Avalanche rank. Rewrite formulas that reference letters.
    for r in range(s["first"], s["last"] + 1):
        ws[f"I{r}"].value = f'=IF(LEN(B{r})=0,"",N(G{r})+N(H{r}))'
        ws[f"J{r}"].value = (f'=IF(LEN(B{r})=0,"",IF(N(E{r})<=0,0,IF(N(I{r})<=0,"no payment",'
                             f'IFERROR(IF(N(F{r})=0,N(E{r})/N(I{r}),NPER(N(F{r})/12,-N(I{r}),N(E{r}))),"no payment"))))')
        ws[f"K{r}"].value = f'=IF(ISNUMBER(J{r}),EDATE(TODAY(),ROUNDUP(J{r},0)),"")'
        ws[f"L{r}"].value = (f'=IF(LEN(B{r})=0,"",COUNTIF($E${s["first"]}:$E${s["last"]},"<"&E{r})'
                             f'+COUNTIF($E${s["first"]}:E{r},E{r}))')
        ws[f"M{r}"].value = (f'=IF(LEN(B{r})=0,"",COUNTIF($F${s["first"]}:$F${s["last"]},">"&F{r})'
                             f'+COUNTIF($F${s["first"]}:F{r},F{r}))')
        ws[f"F{r}"].number_format = FMT_PCT
    # Payoff order table
    band(ws, 18, 2, 8, "PAYOFF ORDER (for the chosen method)")
    for j, h in enumerate(["Order", "Debt", "Current balance", "APR", "Payment", "Payoff date"]):
        c = ws.cell(19, 2 + j, h)
        c.font = fnt(9, True, WHITE)
        c.fill = fill(NAVY)
        c.alignment = Alignment(horizontal="center")
    rankcol = f'IF($C$4="Snowball",$L${s["first"]}:$L${s["last"]},$M${s["first"]}:$M${s["last"]})'
    for n in range(1, 6):
        r = 19 + n
        calc(ws, f"B{r}", n, "0", False, "center")
        m = f'MATCH({n},{rankcol},0)'
        calc(ws, f"C{r}", f'=IFERROR(INDEX($B${s["first"]}:$B${s["last"]},{m}),"")', None, True, "left")
        calc(ws, f"D{r}", f'=IFERROR(INDEX($E${s["first"]}:$E${s["last"]},{m}),"")', FMT_MONEY)
        calc(ws, f"E{r}", f'=IFERROR(INDEX($F${s["first"]}:$F${s["last"]},{m}),"")', FMT_PCT, False, "center")
        calc(ws, f"F{r}", f'=IFERROR(INDEX($I${s["first"]}:$I${s["last"]},{m}),"")', FMT_MONEY)
        calc(ws, f"G{r}", f'=IFERROR(INDEX($K${s["first"]}:$K${s["last"]},{m}),"")', FMT_DATE)
    label(ws, "B16", "Totals", True)
    calc(ws, "D16", f'=SUM(D{s["first"]}:D{s["last"]})', FMT_MONEY, True, "right", SOFT_LAV)
    calc(ws, "E16", f'=SUM(E{s["first"]}:E{s["last"]})', FMT_MONEY, True, "right", SOFT_LAV)
    calc(ws, "I16", f'=SUM(I{s["first"]}:I{s["last"]})', FMT_MONEY, True, "right", SOFT_LAV)
    label(ws, "B27", "Estimates use each debt's APR and total monthly payment. Interest is approximate; check your lender's statement.", False)
    label(ws, "B28", "Set the payment method, then compare the two orders. Avalanche usually saves the most interest.", False)
    legend(ws, 30, 2)
    ws.freeze_panes = "A6"


# ------------------------------------------------------------------ 26 Net worth
def build_networth(ws):
    page(ws, "Net Worth", "Assets minus liabilities. Bank balances and debts link automatically; enter the rest.",
         LAV, 6, demo=True)
    set_widths(ws, {"B": 30, "C": 18, "D": 3, "E": 30, "F": 18})
    band(ws, 4, 2, 3, "ASSETS")
    assets = [("Cash on hand", 350, True), ("Bank accounts (from Bank Accounts)", "=SUMIF(BankBalances,\">0\")", False),
              ("Investments", 15000, True), ("Property", 0, True), ("Other assets", 800, True)]
    for i, (lab, v, editable) in enumerate(assets):
        r = 5 + i
        label(ws, f"B{r}", lab, False)
        if editable:
            inp(ws, f"C{r}", v, FMT_MONEY)
        else:
            calc(ws, f"C{r}", v, FMT_MONEY, False, "right")
    label(ws, "B10", "Total assets", True)
    calc(ws, "C10", "=SUM(C5:C9)", FMT_MONEY, True, "right", SOFT_TEAL)
    band(ws, 4, 5, 6, "LIABILITIES")
    liab = [("Credit cards (from Debt Calculator)", f'=SUMIF({DEBT_TYPE},"Credit card",{DEBT_BAL})'),
            ("Loans (from Debt Calculator)", f'=SUMIF({DEBT_TYPE},"Loan",{DEBT_BAL})'),
            ("Other liabilities", 0)]
    for i, (lab, v) in enumerate(liab):
        r = 5 + i
        label(ws, f"E{r}", lab, False)
        if isinstance(v, str):
            calc(ws, f"F{r}", v, FMT_MONEY, False, "right")
        else:
            inp(ws, f"F{r}", v, FMT_MONEY)
    label(ws, "E10", "Total liabilities", True)
    calc(ws, "F10", "=SUM(F5:F7)", FMT_MONEY, True, "right", DANGER_BG)
    band(ws, 13, 2, 6, "NET WORTH", BLUE)
    label(ws, "B14", "Net worth (assets minus liabilities)", True)
    calc(ws, "C14", "=C10-F10", FMT_MONEY, True, "right", SOFT_TEAL)
    ws.conditional_formatting.add("C14", FormulaRule(formula=["C14<0"], fill=fill(DANGER_BG),
                                                    font=Font(color=DANGER, bold=True)))
    label(ws, "B16", "Update the blue cells monthly. Bank balances and debts update automatically from the ledger and Debt Calculator.", False)
    legend(ws, 18, 2)


# ------------------------------------------------------------------ 27 Investment forecast
def build_forecast(ws):
    page(ws, "Investment Forecast", "Hypothetical projection only. Returns are assumed, not guaranteed, and past performance does not predict future results.",
         LAV, 9, demo=True)
    set_widths(ws, {"B": 30, "C": 16, "D": 3, "E": 12, "F": 17, "G": 17, "H": 17, "I": 3})
    inputs = [
        ("Initial investment", 5000, FMT_MONEY),
        ("Contribution per period", 300, FMT_MONEY),
        ("Contribution frequency (Monthly or Annually)", "Monthly", None),
        ("Assumed annual return (hypothetical)", 0.06, FMT_PCT),
        ("Investment period (years, up to 30)", 20, "0"),
    ]
    band(ws, 4, 2, 3, "INPUTS")
    for i, (lab, v, fmt) in enumerate(inputs):
        r = 5 + i
        label(ws, f"B{r}", lab, False)
        inp(ws, f"C{r}", v, fmt, "right")
    dv_list(ws, "C7", '"Monthly,Annually"')
    dv_list(ws, "C9", '"' + ",".join(str(i) for i in range(1, 31)) + '"')
    band(ws, 11, 2, 3, "RESULT (HYPOTHETICAL)")
    ppy = 'IF($C$7="Monthly",12,1)'
    rate = f"($C$8/{ppy})"
    n = f"({ppy}*$C$9)"
    fv = (f"=IFERROR($C$5*(1+{rate})^{n}+$C$6*(((1+{rate})^{n}-1)/{rate}),"
          f"$C$5*(1+$C$8)^$C$9+$C$6*(((1+$C$8)^$C$9-1)/$C$8))")
    label(ws, "B12", "Estimated future value", True)
    calc(ws, "C12", fv, FMT_MONEY, True, "right", SOFT_TEAL)
    label(ws, "B13", "Total you contribute", True)
    calc(ws, "C13", f"=$C$5+$C$6*{ppy}*$C$9", FMT_MONEY, True, "right")
    label(ws, "B14", "Growth from returns", True)
    calc(ws, "C14", "=C12-C13", FMT_MONEY, True, "right", SOFT_LAV)
    band(ws, 4, 5, 8, "YEAR-BY-YEAR (hypothetical)")
    for j, h in enumerate(["Year", "Contributed", "Growth", "Value"]):
        c = ws.cell(5, 5 + j, h)
        c.font = fnt(9, True, WHITE)
        c.fill = fill(NAVY)
        c.alignment = Alignment(horizontal="center")
    for y in range(1, 31):
        r = 5 + y
        calc(ws, f"E{r}", f'=IF({y}<=$C$9,{y},"")', "0", False, "center")
        pyr = f"{ppy}*E{r}"
        rr = f"({rate})"
        v = (f"IFERROR($C$5*(1+{rr})^({ppy}*E{r})+$C$6*(((1+{rr})^({ppy}*E{r})-1)/{rr}),"
             f"$C$5*(1+$C$8)^E{r}+$C$6*(((1+$C$8)^E{r}-1)/$C$8))")
        calc(ws, f"H{r}", f'=IF(E{r}="","",{v})', FMT_MONEY, True)
        calc(ws, f"F{r}", f'=IF(E{r}="","",$C$5+$C$6*{pyr})', FMT_MONEY)
        calc(ws, f"G{r}", f'=IF(E{r}="","",H{r}-F{r})', FMT_MONEY)
    lc = LineChart()
    lc.title = "Hypothetical growth (not guaranteed)"
    lc.add_data(Reference(ws, min_col=8, min_row=5, max_row=35), titles_from_data=True)
    lc.set_categories(Reference(ws, min_col=5, min_row=6, max_row=35))
    lc.series[0].graphicalProperties.line.solidFill = LAV
    lc.width, lc.height = 16, 8
    lc.legend = None
    ws.add_chart(lc, "B17")
    label(ws, "B33", "This is a simplified projection with a constant return and regular contributions. Taxes, fees and market", False)
    label(ws, "B34", "volatility are ignored. Real investments can lose value. Consider a licensed adviser for decisions.", False)


# ------------------------------------------------------------------ 28 No-spending challenge
def build_challenge(ws):
    page(ws, "No-Spending Challenge", "Log each day: no spend, or spent (with a reason). See your progress and the money you kept.",
         LAV, 9, demo=True)
    set_widths(ws, {"B": 30, "C": 16, "D": 3, "E": 16, "F": 16, "G": 18, "H": 30, "I": 3})
    label(ws, "B4", "Challenge length (days)")
    inp(ws, "C4", 30, "0")
    label(ws, "B5", "Start date")
    inp(ws, "C5", D(2026, 10, 25), FMT_DATE)
    label(ws, "B6", "End date")
    calc(ws, "C6", "=C5+C4-1", FMT_DATE, True, "right")
    label(ws, "B7", "Average daily spend (from Easy Setup)")
    calc(ws, "C7", "=DailyAvg", FMT_MONEY, False, "right")
    band(ws, 9, 2, 3, "PROGRESS")
    stats = [
        ("Days logged", '=COUNTIF(G13:G42,"?*")', "0"),
        ("No-spend days", '=COUNTIF(G13:G42,"No spend")', "0"),
        ("Days with spending", '=COUNTIF(G13:G42,"Spent")', "0"),
        ("Money saved (no-spend days x daily average)", "=C11*C7", FMT_MONEY),
        ("Progress through challenge", "=IFERROR(C10/C4,0)", FMT_PCT),
    ]
    for i, (lab, f, fmt) in enumerate(stats):
        r = 10 + i
        label(ws, f"B{r}", lab, False)
        calc(ws, f"C{r}", f, fmt, True, "right", SOFT_TEAL if i in (1, 3) else LGRAY)
    ws.conditional_formatting.add("C14", DataBarRule(start_type="num", start_value=0, end_type="num",
                                                    end_value=1, color=TEAL))
    band(ws, 12, 5, 8, "DAILY LOG")
    for j, h in enumerate(["Day", "Date", "Status", "Reason or exception"]):
        c = ws.cell(12, 5 + j, h)
        c.font = fnt(9, True, WHITE)
        c.fill = fill(NAVY)
        c.alignment = Alignment(horizontal="center")
    logs = {1: ("No spend", ""), 2: ("No spend", ""), 3: ("Spent", "Birthday lunch"), 4: ("No spend", ""),
            5: ("No spend", ""), 6: ("No spend", ""), 7: ("Spent", "Groceries (planned)"), 8: ("No spend", ""),
            9: ("No spend", ""), 10: ("No spend", ""), 11: ("No spend", ""), 12: ("Spent", "Medication"),
            13: ("No spend", "")}
    for d in range(1, 31):
        r = 12 + d
        calc(ws, f"E{r}", d, "0", False, "center")
        calc(ws, f"F{r}", f"=$C$5+E{r}-1", FMT_DATE, False, "center")
        inp(ws, f"G{r}", logs[d][0] if d in logs else None, None, "center")
        inp(ws, f"H{r}", logs[d][1] if d in logs and logs[d][1] else None)
    dv_list(ws, "G13:G42", '"No spend,Spent"')
    cf(ws, "G13:G42", '$G13="No spend"', SUCCESS_BG, SUCCESS, True)
    cf(ws, "G13:G42", '$G13="Spent"', DANGER_BG, DANGER, True)
    label(ws, "B16", "Use the Daily log: choose No spend or Spent for each day. Days after today stay blank until you log them.", False)
    label(ws, "B17", "Money saved uses your average daily spend, so it's an estimate of what you avoided, not a bank balance.", False)
    legend(ws, 19, 2)
    ws.freeze_panes = "A13"


# ------------------------------------------------------------------ main
def main():
    wb = Workbook()
    wb.remove(wb.active)
    names = (["Easy Setup", "Bank Accounts", "Recurring Transactions", "Payments", "Variable Transactions",
              "All-in-One Dashboard", "Annual Totals", "Automated Calendar", "Paycheck Dashboard"]
             + MONTHS
             + ["50-30-20 Dashboard", "Expense Distribution", "Sinking Funds", "Debt Calculator",
                "Net Worth", "Investment Forecast", "No-Spending Challenge"])
    assert len(names) == 28, len(names)
    S = {n: wb.create_sheet(n) for n in names}

    build_setup(S["Easy Setup"], wb)
    build_bank(S["Bank Accounts"], wb)
    build_recurring(S["Recurring Transactions"])
    build_payments(S["Payments"])
    build_tx(S["Variable Transactions"])
    build_dashboard(S["All-in-One Dashboard"])
    build_annual(S["Annual Totals"])
    build_cal(S["Automated Calendar"])
    build_paycheck(S["Paycheck Dashboard"])
    for m in range(1, 13):
        build_month(S[MONTHS[m - 1]], m)
    build_5030(S["50-30-20 Dashboard"])
    build_distribution(S["Expense Distribution"])
    build_funds(S["Sinking Funds"])
    build_debt(S["Debt Calculator"])
    build_networth(S["Net Worth"])
    build_forecast(S["Investment Forecast"])
    build_challenge(S["No-Spending Challenge"])

    for n in ("Variable Transactions", "Payments", "Recurring Transactions", "Paycheck Dashboard",
              "Sinking Funds", "Debt Calculator"):
        ws = S[n]
        hdr = {"Variable Transactions": 5, "Payments": 5, "Recurring Transactions": 5,
               "Paycheck Dashboard": 6, "Sinking Funds": 6, "Debt Calculator": 6}[n]
        ws.print_title_rows = f"{hdr}:{hdr}"
    for ws in wb.worksheets:
        ws.page_setup.orientation = "landscape"
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True
    wb["All-in-One Dashboard"].page_setup.fitToHeight = 0
    wb["All-in-One Dashboard"].print_area = "A1:N70"
    wb.calculation = CalcProperties(fullCalcOnLoad=True)
    wb.active = 0
    wb.save(OUT)
    print("saved", OUT, "tabs:", len(wb.sheetnames))


if __name__ == "__main__":
    main()
