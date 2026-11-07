# Ultimate Productivity Bundle

Four products, built from scripts in this folder. Each product has its own folder with the deliverable, a PDF guide, and the build script.

```
productivity-bundle/
├── README.md
├── Ultimate-Productivity-Bundle.zip        # everything for delivery (product folders, guides, design system)
├── design-system/design-tokens.json        # palette, typography, cell conventions, number formats
├── product-1-ultimate-project-manager/     # Excel, 15 tabs
│   ├── Ultimate_Project_Manager.xlsx
│   ├── USER_GUIDE.md / USER_GUIDE.pdf
│   └── build/build_project_manager.py
├── product-2-ultimate-onenote-planner/     # HTML pages for OneNote, 225 pages
│   ├── pages/                              # index.html is the General Index
│   ├── USER_GUIDE.pdf
│   └── build/build_onenote_planner.py
├── product-3-weekly-planner-pro/           # Excel, 8 tabs
│   ├── Weekly_Planner_Pro.xlsx
│   ├── README.md / USER_GUIDE.pdf
│   └── build/build_weekly_planner.py
└── product-4-ultimate-budget-spreadsheet/  # Excel, 28 tabs
    ├── Ultimate_Budget_Spreadsheet.xlsx
    ├── README.md / USER_GUIDE.pdf
    └── build/build_budget.py
```

## What was checked

| Product | Check performed | Result |
|---|---|---|
| 1. Project Manager | LibreOffice recalculation; figures checked by hand; dashboard rendered | 0 formula errors |
| 2. OneNote Planner | Generated pages; every internal link resolved; layout rendered | 225 pages, 0 broken links |
| 3. Weekly Planner Pro | LibreOffice recalculation; figures checked by hand; Week 1 rendered | 0 formula errors |
| 4. Budget Spreadsheet | LibreOffice recalculation; figures checked by hand; dashboard rendered | 0 formula errors, 28 tabs |

None of the Excel files has been opened in desktop Excel or Google Sheets.

## Known limits

- **OneNote:** the planner is HTML pages, not a native `.one` notebook. OneNote cannot be written as a native file from this build. Import the pages into OneNote as the guide describes.
- **Google Sheets:** no separate Google Sheets versions are built. The three Excel workbooks use functions Google Sheets supports (SUMIFS, COUNTIFS, EDATE, DATEDIF, NPER, TEXT, INDEX/MATCH and named ranges), so import is expected to work, but it has not been tested.
- **Excel:** tested only in LibreOffice. Desktop Excel may show minor spacing or chart differences.
- **Budget recurring items** are reminders; each occurrence still has to be entered as a transaction.
- **Sample data** is labelled DEMO DATA in every workbook.

## Rebuild everything

```bash
python3 product-1-ultimate-project-manager/build/build_project_manager.py product-1-ultimate-project-manager/Ultimate_Project_Manager.xlsx
python3 product-2-ultimate-onenote-planner/build/build_onenote_planner.py product-2-ultimate-onenote-planner/pages
python3 product-3-weekly-planner-pro/build/build_weekly_planner.py product-3-weekly-planner-pro/Weekly_Planner_Pro.xlsx
python3 product-4-ultimate-budget-spreadsheet/build/build_budget.py product-4-ultimate-budget-spreadsheet/Ultimate_Budget_Spreadsheet.xlsx
```
