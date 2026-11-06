# Ultimate Productivity Bundle

Status of the four-product bundle, with what is built and tested and what is not yet built.

```
productivity-bundle/
├── README.md
├── design-system/
│   └── design-tokens.json                  # palette, typography, cell conventions, number formats
├── product-1-ultimate-project-manager/
│   ├── Ultimate_Project_Manager.xlsx       # built and recalculation-tested (macro-free)
│   └── build/
│       └── build_project_manager.py        # generator; re-run to rebuild the workbook
├── product-2-ultimate-onenote-planner/     # not started
├── product-3-weekly-planner-pro/           # not started
└── product-4-ultimate-budget-spreadsheet/  # not started
```

## Product 1: Ultimate Project Manager (Excel .xlsx)

Built with openpyxl; 15 tabs in the order of the brief. Rebuild with:

```bash
python3 product-1-ultimate-project-manager/build/build_project_manager.py product-1-ultimate-project-manager/Ultimate_Project_Manager.xlsx
```

### Verification performed

- Recalculated in LibreOffice headless; scanned all 15 sheets: **0 formula error cells**.
- Hand-checked against the demo data: project and task KPIs, budget totals, overdue and upcoming
  lists, monthly and weekly calendar grids, weekly workload and stats, Kanban counts, the task
  filter count, Gantt rows, decision-matrix totals and winner, recurring next-occurrence dates.
- Rendered the Dashboard to an image to confirm the KPI cards and charts populate.

### Known limitations

- **Excel only for now.** The Google Sheets-compatible version is not built. Formulas use plain
  ranges (not structured references) to keep recalculation and Google Sheets import predictable.
- **No sheet protection.** Formula cells are grey and labelled, but not locked.
- **Calendars** show counts per day and a day agenda; the monthly grid does not colour individual
  tasks by category. The weekly grid colours by priority letter.
- **Weekly grid** shows one block per time slot; a second block starting in the same hour is hidden.
- **Generated IDs** (PRJ-, TSK-, EXP-, REC-, SCH-) come from row position. Sorting a table renumbers
  them, so add new rows at the bottom.
- The workbook has not been opened in desktop Excel; it was validated by LibreOffice recalculation.

## Products 2–4 and deliverables not yet built

- Product 2, Ultimate OneNote Planner (native OneNote structure, PDF guide, templates)
- Product 3, Weekly Planner Pro (.xlsx and Google Sheets version)
- Product 4, Ultimate Budget Spreadsheet (28 tabs, .xlsx and Google Sheets version)
- Google Sheets version of Product 1
- Standalone PDF user guide, Getting Started, installation, formula, sample-data and troubleshooting guides
- ZIP archive of all deliverables

These follow the same design system and build method as Product 1.
