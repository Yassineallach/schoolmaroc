#!/usr/bin/env python3
"""Generates the Ultimate OneNote Planner as linked HTML pages.

Usage: python3 build_onenote_planner.py OUTPUT_DIR

OneNote cannot be written as a native .one file from here. These pages are
built to be imported into OneNote (Insert > File Printout, or open the HTML in
a browser and copy/paste sections). Each page links back to the General Index.
"""
import calendar
import datetime as dt
import html
import os
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "pages"

NAVY = "#17243A"; MIDNIGHT = "#223653"; BLUE = "#4169E1"; SOFT_BLUE = "#EAF1FB"
TEAL = "#24A89A"; SOFT_TEAL = "#E2F4F0"; LAV = "#8B7BE8"; SOFT_LAV = "#F0EDFC"
BG = "#F5F7FA"; GRAY = "#E9EDF2"; BORDER = "#DCE3EA"; SEC = "#6B7785"; DARK = "#263445"

YEAR = 2026
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

CSS = f"""
body{{font-family:Arial,Helvetica,sans-serif;color:{DARK};background:#fff;margin:24px;max-width:960px;}}
h1{{background:{NAVY};color:#fff;padding:14px 18px;margin:0 0 12px 0;font-size:22px;}}
h2{{color:{BLUE};font-size:16px;border-bottom:2px solid {BLUE};padding-bottom:4px;margin-top:22px;}}
h3{{color:{MIDNIGHT};font-size:14px;margin:14px 0 6px 0;}}
.sub{{color:{SEC};font-size:12px;margin-bottom:12px;}}
.nav{{background:{SOFT_BLUE};padding:8px 12px;margin-bottom:14px;font-size:12px;}}
.nav a{{margin-right:12px;color:{BLUE};}}
table{{border-collapse:collapse;width:100%;margin:6px 0 12px 0;font-size:12px;}}
th{{background:{MIDNIGHT};color:#fff;padding:6px;text-align:left;}}
td{{border:1px solid {BORDER};padding:8px;min-height:22px;vertical-align:top;}}
.sec-teal h2{{color:{TEAL};border-color:{TEAL};}}
.sec-lav h2{{color:{LAV};border-color:{LAV};}}
.box{{border:1px solid {BORDER};background:{BG};padding:10px;margin:6px 0;min-height:60px;}}
.check{{font-size:13px;line-height:1.9;}}
.cal td{{height:70px;width:14%;}}
.cal th{{text-align:center;}}
.num{{color:{SEC};font-size:11px;}}
"""


def esc(s):
    return html.escape(str(s))


def page(title, body, crumbs, section_class=""):
    body = body.replace("<table", '<table width="100%"')
    nav = " ".join(f'<a href="{href}">{esc(label)}</a>' for label, href in crumbs)
    return (f'<!doctype html><html><head><meta charset="utf-8"><title>{esc(title)}</title>'
            f'<style>{CSS}</style></head><body class="{section_class}">'
            f'<div class="nav">{nav}</div><h1>{esc(title)}</h1>{body}</body></html>')


def table(headers, rows=3, blank_width=None):
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join("<td>&nbsp;</td>" for _ in headers) + "</tr>" for _ in range(rows))
    return f"<table><tr>{head}</tr>{body}</table>"


def checklist(n):
    return '<div class="check">' + "<br>".join("☐ ______________________________" for _ in range(n)) + "</div>"


def box(label, lines=3):
    return f'<h3>{esc(label)}</h3><div class="box">' + "<br>".join("&nbsp;" for _ in range(lines)) + "</div>"


# ------------------------------------------------------------------ template library
TEMPLATES = {
    "Task Management": {
        "folder": "task-management", "color": "",
        "names": ["Daily task list", "Weekly task planner", "Priority matrix", "Task tracker",
                  "Waiting-for list", "Delegation tracker", "Task breakdown", "Recurring task log",
                  "Completed task review"],
        "fields": [("Tasks", ["Task", "Priority", "Due", "Status"]),
                   ("Next actions", ["Action", "Owner", "Due"])],
    },
    "Project Management": {
        "folder": "project-management", "color": "",
        "names": ["Project brief", "Project charter", "Scope statement", "Stakeholder map", "Project plan",
                  "Milestone tracker", "Risk register", "Issue log", "Change request", "Status report",
                  "RACI matrix", "Budget tracker", "Resource plan", "Meeting agenda", "Kickoff checklist",
                  "Sprint planner", "Retrospective", "Lessons learned", "Requirements list", "Deliverables tracker",
                  "Dependencies log", "Communication plan", "Team roster", "Timeline overview", "Quality checklist",
                  "Go-live checklist", "Vendor tracker", "Decision log", "Project closure checklist"],
        "fields": [("Objectives", ["Objective", "Measure", "Target"]),
                   ("Items", ["Item", "Owner", "Due", "Status"])],
    },
    "Meeting Notes": {
        "folder": "meeting-notes", "color": "",
        "names": ["Standard meeting notes", "Stand-up notes", "One-to-one notes", "Client call notes",
                  "Board meeting minutes", "Workshop notes", "Interview notes", "Action follow-up"],
        "fields": [("Attendees and agenda", ["Name", "Role", "Topic"]),
                   ("Action items", ["Action", "Owner", "Due"])],
    },
    "Goal Setting": {
        "folder": "goal-setting", "color": "",
        "names": ["SMART goal worksheet", "Goal tracker", "Vision board notes", "Habit goal plan",
                  "Quarterly goals", "Goal action steps", "Obstacles and solutions", "Goal review"],
        "fields": [("Goal", ["Goal", "Why it matters", "Deadline"]),
                   ("Steps", ["Step", "Target date", "Done"])],
    },
    "Time Management": {
        "folder": "time-management", "color": "",
        "names": ["Time audit", "Time blocking planner", "Pomodoro log", "Energy planner",
                  "Meeting time budget", "Interruption log", "Weekly time review"],
        "fields": [("Blocks", ["Time", "Activity", "Category"]),
                   ("Review", ["What worked", "What to change"])],
    },
    "Professional Development": {
        "folder": "professional-development", "color": "",
        "names": ["Skills inventory", "Learning plan", "Course tracker", "Certification tracker",
                  "Mentor meeting notes", "Reading log", "Career goals", "Networking log",
                  "Presentation prep", "Feedback log", "Performance review prep", "Training budget",
                  "Conference notes", "Portfolio index", "Competency matrix", "Annual development review"],
        "fields": [("Focus", ["Skill or topic", "Current level", "Target level"]),
                   ("Practice", ["Activity", "Date", "Result"])],
    },
    "Client and Customer Tracking": {
        "folder": "client-tracking", "color": "",
        "names": ["Client profile", "Customer feedback log", "Contact log", "Pipeline tracker",
                  "Renewal tracker", "Support case log", "Client onboarding checklist",
                  "Account review", "Complaint log"],
        "fields": [("Contact", ["Name", "Company", "Email", "Phone"]),
                   ("Interactions", ["Date", "Channel", "Summary", "Next step"])],
    },
    "Invoice and Expense Tracking": {
        "folder": "invoice-expense", "color": "",
        "names": ["Invoice log", "Invoice template", "Expense log", "Mileage log", "Receipts index",
                  "Payment reminders", "Monthly expense summary", "Reimbursement request"],
        "fields": [("Items", ["Date", "Description", "Amount", "Status"]),
                   ("Totals", ["Subtotal", "Tax", "Total"])],
    },
    "Reports and Analytics": {
        "folder": "reports-analytics", "color": "",
        "names": ["KPI dashboard", "Monthly report", "Weekly metrics", "Trend analysis",
                  "Survey results", "Performance scorecard"],
        "fields": [("Metrics", ["Metric", "Target", "Actual", "Variance"]),
                   ("Insights", ["Finding", "Action"])],
    },
    "Creative Brainstorming": {
        "folder": "creative-brainstorming", "color": "",
        "names": ["Brainstorm session", "Mind map", "Idea capture", "Idea scoring grid", "Concept sketch notes",
                  "Storyboard", "Mood board notes", "Content calendar ideas", "Naming ideas",
                  "Problem reframing", "Idea to action plan"],
        "fields": [("Ideas", ["Idea", "Why it could work", "Effort", "Impact"]),
                   ("Next", ["Chosen idea", "First step"])],
    },
}

NOTES = ["General Notes", "Quick Notes", "Research Notes", "Meeting Notes", "Reading Notes",
         "Project Notes", "Ideas and Brainstorming", "Personal Reflection"]


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def rel(*parts):
    return "/".join(parts)


def main():
    root = OUT
    index = "index.html"
    crumbs_index = [("General Index", "../index.html")]

    # ---- General index (root) -------------------------------------------
    sections = [
        ("Yearly goals", "yearly/goals.html"),
        ("Monthly calendars", "monthly/index.html"),
        ("Monthly goals", "monthly/index.html"),
        ("Monthly reflections", "monthly/index.html"),
        ("Weekly trackers", "weekly/index.html"),
        ("Task management", "templates/task-management/index.html"),
        ("Project management", "templates/project-management/index.html"),
        ("Notes", "notes/index.html"),
        ("Resources", "resources/index.html"),
    ]
    body = ('<h2>Sections</h2><table><tr><th>Section</th><th>What is inside</th></tr>'
            '<tr><td><a href="yearly/goals.html">Yearly goals</a></td><td>Vision and 12-month goals</td></tr>'
            '<tr><td><a href="monthly/index.html">Monthly planning</a></td><td>12 months: calendar, goals, reflection</td></tr>'
            '<tr><td><a href="weekly/index.html">Weekly trackers</a></td><td>53 weekly planning pages</td></tr>'
            '<tr><td><a href="templates/index.html">Templates</a></td><td>Task, project, meeting, goal, time, development, client, expense, report and brainstorm templates</td></tr>'
            '<tr><td><a href="notes/index.html">Notes</a></td><td>8 note templates</td></tr>'
            '<tr><td><a href="resources/index.html">Resources</a></td><td>How to use this planner</td></tr></table>')
    write(os.path.join(root, index), page("General Index", f'<p class="sub">Planner for {YEAR}. Click any section to open it.</p>' + body,
                                          [("General Index", index)]))

    # ---- yearly -----------------------------------------------------------
    yb = (f'<h2>Vision for {YEAR}</h2>{box("Vision statement", 4)}'
          f'<h2>Top 5 goals</h2>{table(["#", "Goal", "Why", "Target date", "Progress"], 5)}'
          f'<h2>Areas of focus</h2>{table(["Area", "Goal", "Measure"], 6)}')
    write(os.path.join(root, "yearly", "goals.html"),
          page("Yearly Goals", yb, [("General Index", "../index.html")], "sec-teal"))

    # ---- monthly (3 pages each) -----------------------------------------
    m_index = ['<h2>Months</h2><table><tr><th>Month</th><th>Calendar</th><th>Goals</th><th>Reflection</th></tr>']
    for mi, name in enumerate(MONTHS, start=1):
        slug = f"{mi:02d}-{name.lower()}"
        cal_path = f"monthly/{slug}-calendar.html"
        goal_path = f"monthly/{slug}-goals.html"
        ref_path = f"monthly/{slug}-reflection.html"
        m_index.append(f'<tr><td>{name}</td><td><a href="{slug}-calendar.html">Calendar</a></td>'
                       f'<td><a href="{slug}-goals.html">Goals</a></td><td><a href="{slug}-reflection.html">Reflection</a></td></tr>')
        # calendar
        weeks = calendar.Calendar(firstweekday=0).monthdayscalendar(YEAR, mi)
        rows = ""
        for w in weeks:
            rows += "<tr>" + "".join(f'<td><span class="num">{d if d else ""}</span><br>&nbsp;</td>' for d in w) + "</tr>"
        cal = ('<table class="cal"><tr>' + "".join(f"<th>{d}</th>" for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
               + "</tr>" + rows + "</table>")
        cal_body = (f'<p class="sub">{name} {YEAR}</p>{cal}'
                    f'<h2>Important dates and appointments</h2>{table(["Date", "Event or appointment", "Notes"], 5)}'
                    f'<h2>Deadlines</h2>{table(["Date", "Deadline", "Done"], 4)}')
        write(os.path.join(root, cal_path),
              page(f"{name} Calendar", cal_body,
                   [("General Index", "../index.html"), ("Months", "index.html"), ("Goals", f"{slug}-goals.html"),
                    ("Reflection", f"{slug}-reflection.html")], "sec-teal"))
        goal_body = (f'<h2>Main goals</h2>{table(["Goal", "Category", "Target date", "Progress", "Complete?"], 3)}'
                     f'<h2>Action steps</h2>{table(["Step", "Goal", "Target date", "Done"], 6)}'
                     f'<h2>Progress</h2>{checklist(4)}')
        write(os.path.join(root, goal_path),
              page(f"{name} Goals", goal_body,
                   [("General Index", "../index.html"), ("Months", "index.html"), ("Calendar", f"{slug}-calendar.html"),
                    ("Reflection", f"{slug}-reflection.html")], "sec-lav"))
        ref_body = (f'{box("Major achievements", 3)}{box("Challenges", 3)}{box("Lessons learned", 3)}'
                    f'{box("What went well", 2)}{box("What needs improvement", 2)}{box("Priorities for next month", 3)}')
        write(os.path.join(root, ref_path),
              page(f"{name} Reflection", ref_body,
                   [("General Index", "../index.html"), ("Months", "index.html"), ("Calendar", f"{slug}-calendar.html"),
                    ("Goals", f"{slug}-goals.html")], "sec-lav"))
    m_index.append("</table>")
    write(os.path.join(root, "monthly", "index.html"),
          page("Monthly Planning", "".join(m_index), [("General Index", "../index.html")], "sec-teal"))

    # ---- weekly (53 pages) ----------------------------------------------
    w_index = ['<h2>Weekly trackers</h2><table><tr><th>Week</th><th>Page</th></tr>']
    for wk in range(1, 54):
        slug = f"week-{wk:02d}"
        w_index.append(f'<tr><td>Week {wk}</td><td><a href="{slug}.html">Open</a></td></tr>')
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_rows = "".join(f"<tr><td>{d}</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>" for d in days)
        habit_rows = "".join(f"<tr><td>Habit {h}</td>" + "<td>&nbsp;</td>" * 7 + "</tr>" for h in range(1, 4))
        wbody = (f'<p class="sub">Week of: ____________</p>'
                 f'<h2>Weekly priorities</h2>{checklist(3)}'
                 f'<h2>Top three goals</h2>{table(["Goal", "Done"], 3)}'
                 f'<h2>Monday to Sunday</h2>{table(["Day", "Daily tasks", "Appointments", "Notes"], 0).replace("</table>", day_rows + "</table>")}'
                 f'<h2>Habit tracking</h2><table><tr><th>Habit</th>' + "".join(f"<th>{d[:3]}</th>" for d in days)
                 + f'</tr>{habit_rows}</table>'
                 f'<h2>Notes</h2>{box("Notes", 3)}'
                 f'<h2>Weekly achievements</h2>{box("Achievements", 2)}'
                 f'<h2>Weekly reflection</h2>{box("Reflection", 3)}')
        write(os.path.join(root, "weekly", f"{slug}.html"),
              page(f"Week {wk}", wbody, [("General Index", "../index.html"), ("Weekly index", "index.html")], "sec-teal"))
    w_index.append("</table>")
    write(os.path.join(root, "weekly", "index.html"),
          page("Weekly Trackers", "".join(w_index), [("General Index", "../index.html")], "sec-teal"))

    # ---- templates --------------------------------------------------------
    t_index = ['<h2>Template categories</h2><table><tr><th>Category</th><th>Templates</th></tr>']
    total = 0
    for cat, spec in TEMPLATES.items():
        folder = spec["folder"]
        names = spec["names"]
        total += len(names)
        t_index.append(f'<tr><td><a href="{folder}/index.html">{esc(cat)}</a></td><td>{len(names)}</td></tr>')
        items = []
        for i, nm in enumerate(names, start=1):
            slug = f"{folder}-{i:02d}"
            items.append(f'<tr><td>{i:02d}</td><td><a href="{slug}.html">{esc(nm)}</a></td></tr>')
            fields_html = ""
            for sec_title, cols in spec["fields"]:
                fields_html += f"<h2>{esc(sec_title)}</h2>{table(cols, 4)}"
            fields_html += f"<h2>Notes</h2>{box('Notes', 3)}"
            write(os.path.join(root, "templates", folder, f"{slug}.html"),
                  page(f"{cat}: {nm}", fields_html,
                       [("General Index", "../../index.html"), (cat, "index.html")], "sec-lav"))
        write(os.path.join(root, "templates", folder, "index.html"),
              page(cat, f'<table><tr><th>#</th><th>Template</th></tr>{"".join(items)}</table>',
                   [("General Index", "../../index.html"), ("Templates", "../index.html")], "sec-lav"))
    t_index.append(f"</table><p class=\"sub\">{total} templates in total.</p>")
    write(os.path.join(root, "templates", "index.html"),
          page("Templates", "".join(t_index), [("General Index", "../index.html")], "sec-lav"))

    # ---- notes (8) ---------------------------------------------------------
    n_index = ['<h2>Note templates</h2><table><tr><th>#</th><th>Note</th></tr>']
    for i, nm in enumerate(NOTES, start=1):
        slug = f"note-{i:02d}"
        n_index.append(f'<tr><td>{i}</td><td><a href="{slug}.html">{esc(nm)}</a></td></tr>')
        body_n = f'<p class="sub">Date: ____________ &nbsp; Topic: ____________</p>{box("Notes", 12)}'
        write(os.path.join(root, "notes", f"{slug}.html"),
              page(nm, body_n, [("General Index", "../index.html"), ("Notes", "index.html")], "sec-lav"))
    n_index.append("</table>")
    write(os.path.join(root, "notes", "index.html"),
          page("Notes", "".join(n_index), [("General Index", "../index.html")], "sec-lav"))

    # ---- resources --------------------------------------------------------
    res = ("<h2>Getting started</h2><ol><li>Import the folder into OneNote, or open index.html in a browser and copy the sections across.</li>"
           "<li>Start at the General Index. Every page links back to it.</li>"
           "<li>Use one weekly page per week, one monthly set per month, and copy templates as needed.</li></ol>"
           "<h2>Colour key</h2><table><tr><th>Colour</th><th>Used for</th></tr>"
           f'<tr><td style="background:{BLUE};color:#fff">Blue</td><td>Headings and primary actions</td></tr>'
           f'<tr><td style="background:{TEAL};color:#fff">Teal</td><td>Yearly, monthly and weekly planning</td></tr>'
           f'<tr><td style="background:{LAV};color:#fff">Lavender</td><td>Goals, templates and notes</td></tr></table>')
    write(os.path.join(root, "resources", "index.html"),
          page("Resources", res, [("General Index", "../index.html")], ""))

    count = sum(len(fs) for _, _, fs in os.walk(root))
    print("pages written:", count, "templates:", total, "notes:", len(NOTES))


if __name__ == "__main__":
    main()
