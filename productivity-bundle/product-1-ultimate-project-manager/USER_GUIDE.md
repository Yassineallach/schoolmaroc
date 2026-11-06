# Ultimate Project Manager: User Guide

**File:** `Ultimate_Project_Manager.xlsx` (Microsoft Excel 2019 or Microsoft 365)
**Contains:** 15 tabs, no macros, sample data labelled DEMO DATA

---

## 1. Getting started

1. Open the file in Excel. If Excel asks to enable editing, choose **Enable Editing**.
2. Explore the sample data. Every dashboard, calendar, chart and list is already populated.
3. Begin on the **Setup** tab, then follow section 3 to replace the sample data with your own.

**Colour key** (shown in a legend on most tabs):

| Colour | Meaning |
|---|---|
| Light blue | You type here (input) |
| Light grey | Calculated; do not type over |
| Light teal | Positive result or completed |
| Light red | Warning, overdue, or negative |
| Light lavender | Optional or secondary |

## 2. Tab map

| Section | Tab | Purpose |
|---|---|---|
| A. Setup | Setup | Profile, currency, week start, and every dropdown list |
| B. Dashboards | Dashboard | KPI cards, charts, deadlines, overdue tasks, project health |
| | Monthly Calendar | Month view, due counts, day agenda |
| | Weekly Calendar | Seven-day time-slot grid, workload, weekly stats |
| C. Project management | Project Overview | Portfolio: one row per project |
| | Project Manager | Objectives, milestones, risks, team, dependencies |
| | Project Budget | Expense lines, utilisation, budget alerts |
| D. Tasks | Variable Tasks | One-time task database |
| | Recurring Tasks | Repeating tasks with next-occurrence dates |
| | Task Schedule | Time-blocked schedule (feeds the Weekly Calendar) |
| | Task Filter | Combine filters to find matching tasks |
| E. Extra resources | Decision Matrix | Weighted scoring and recommended option |
| | Kanban Board | Tasks grouped by status |
| | Gantt Chart | Timeline bars per project |
| | Instructions | Built-in reference (this guide, condensed) |

## 3. Setup

Open **Setup**.

- **Profile:** workspace name, owner, currency, week start (Monday or Sunday), working hours.
- **Dropdown lists:** project categories, task categories, priorities, task statuses, project statuses, team members, departments, budget categories, recurrence options, risk levels, and filter options.
- Each list has room for 15 items. Keep the items in one unbroken column with no blank rows between them.
- Edit a list and every dropdown in the workbook updates. Do not rename a status used by the Kanban board (Backlog, To Do, In Progress, Review, Completed) unless you also update its list position.

## 4. Adding a project

1. Open **Project Overview**.
2. In column **Project Name**, type the project name. The **Project ID** (PRJ-001, PRJ-002, ...) appears automatically.
3. Choose **Category**, **Project Manager**, **Start Date**, **Due Date**, **Priority** and **Status**.
4. Progress, Budget, Actual Cost, Remaining Budget and Days Remaining calculate automatically.
5. Optional: on **Project Manager**, use the same row to add objectives, deliverables, milestones, dependencies, risks and notes.

Add new projects at the bottom of the list. IDs come from row position, so sorting the table renumbers them. Sort only before you link tasks and budget lines to projects, or not at all.

## 5. Creating tasks

**Variable Tasks** (one-time tasks):

1. Type a **Task Name**.
2. Choose **Project ID**, **Category**, **Assigned To**, **Priority** and **Status**.
3. Enter **Start Date**, **Due Date**, estimated and actual hours, and **Progress** (0% to 100%).
4. **Days Left** and **Overdue** update automatically.
5. Set Status to **Completed** when finished. Completed tasks drop out of the deadline and overdue lists.

**Recurring Tasks:** choose a **Frequency** (Daily, Weekly, Biweekly, Monthly, Quarterly, Annually or Custom). For Custom, enter the number of days in **Custom Every**. Each time you finish an occurrence, enter its date in **Last Completed**. **Next Occurrence** moves forward automatically. A Schedule Flag shows Overdue, Due soon, On schedule or Paused.

**Task Schedule:** enter a date, start and end time, task, project, priority, status and person. Each block appears on the Weekly Calendar in its start hour.

**Project Budget:** one row per expense. Enter the **Project ID**, **Budget Category**, **Planned Budget** and **Actual Expense**. Budget Utilisation and Budget Alert calculate automatically.

## 6. Using the dashboards

- **Dashboard:** all twelve KPI cards, four charts, and four lists (upcoming deadlines, overdue tasks, recent activity, project performance). Nothing is typed in; everything is calculated from the input tables.
- **Monthly Calendar:** choose a Month and Year in the blue cells. Dates show how many open tasks and project deadlines fall on each day. Overdue days are shaded red and today is blue. Enter a date in **Agenda for** to list that day's tasks.
- **Weekly Calendar:** enter any date in **Week containing**. The week runs from your Setup week-start day. Blocks show priority letter, task and project. Stats include tasks due, completion rate, scheduled hours and the busiest day.
- **Gantt Chart:** choose a Project ID. Each task is a bar from its start to due date. Colours: blue in progress, teal completed, lavender in review, grey not started. A diamond (◆) marks milestones. The lavender column is the week containing today.
- **Kanban Board:** tasks as cards in their status column. The first letter is the priority (C, H, M, L).
- **Task Filter:** choose filters in the blue boxes (project, priority, status, category, person, due window, completion, overdue). The matching tasks list below.

## 7. Decision Matrix

1. Enter the decision name.
2. Enter up to six criteria, each with a weight. Weights must total 100%; the check cell turns red if not.
3. Score each option from 1 (poor) to 10 (excellent).
4. The **Recommended option** is the one with the highest weighted total.

## 8. Formula explanations

| Result | Calculation |
|---|---|
| Days Left | Due Date minus today |
| Overdue | Yes if the due date has passed and the status is not Completed |
| Project Progress | Average progress of that project's tasks |
| Task Completion % | Completed tasks divided by all tasks for the project |
| Budget Utilisation | Actual divided by planned. 90% or more = Near limit; over 100% = Over budget |
| Remaining Budget | Planned minus actual |
| Next Occurrence | Last completed plus the frequency step (months and years use EDATE) |
| Weighted score | Criterion weight multiplied by option score |

## 9. Resetting the sample data

1. On each table tab, select only the **blue** columns and press Delete. Leave grey columns alone; they empty automatically.
2. On **Setup**, clear the blue cells in the profile block and the lists, then re-enter your own values.
3. Check that the dashboard shows zeros and no error messages.

## 10. Troubleshooting

| Problem | Fix |
|---|---|
| Dashboard shows zeros | Check that each task and budget line's Project ID matches an ID on Project Overview. |
| A date appears as a number | Select the cells and set the format to Date. |
| A dropdown lacks an option | Add it to the list on Setup (up to 15 items per list). |
| Only one task appears per hour on the Weekly Calendar | Only the first block in an hour is shown. Schedule blocks in separate hours. |
| A dashboard value looks wrong | Confirm the blue input cells on the source tab hold the values you expect, then recalculate (F9). |
| Excel reports a repair message | Save a copy, then reopen it. If the problem remains, re-download the file. |
| Calendar or overdue flags look different tomorrow | They use today's date by design. |

## 11. Compatibility notes

- Built and tested for Excel 2019 and Microsoft 365. It uses standard functions only (no macros, no dynamic-array functions).
- The file has been checked by recalculating it in LibreOffice, with no formula errors. It has not yet been checked in desktop Excel or Google Sheets.
- Google Sheets: a separate Google Sheets version is **not yet provided**. Importing this file may keep most formulas and dropdowns, but data bars and some chart styling may need to be recreated.
- Sheets are not protected. Grey formula cells are labelled but can be overwritten.

## 12. Limitations

- The monthly calendar shows counts and an agenda; it does not colour individual tasks by category.
- The weekly grid shows one block per hour.
- Generated IDs follow row position; add new rows at the bottom.
