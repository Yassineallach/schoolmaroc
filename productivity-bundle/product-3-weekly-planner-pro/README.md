# Weekly Planner Pro (Excel .xlsx)

Eight tabs, no macros: **Setup**, **Week 1** to **Week 6**, **Monthly Calendar**.

## Build and verify
```bash
python3 product-3-weekly-planner-pro/build/build_weekly_planner.py product-3-weekly-planner-pro/Weekly_Planner_Pro.xlsx
```
Recalculated in LibreOffice: 0 formula error cells. Values checked: week dates, planned and done task counts, progress and productivity percentages, habit completion, water and exercise totals, and monthly weekly-goal links.

## How to use
1. **Setup:** enter your name, the first Monday of your planning, working hours, water and exercise goals, and your habit list.
2. **Week 1–6:** enter the main goal, three priorities, and the daily tasks (priority, time, Done?, notes). Top priority and appointments sit above each day's tasks.
3. **Trackers** (same tab): habit grid (Done / Missed), water glasses, exercise minutes, and a productivity score per day. Weekly progress and the reflection block are at the top and bottom.
4. **Monthly Calendar:** pick a month and year; add important dates and deadlines; weekly goals pull from the Week tabs.

Each week tab is reusable: copy a tab to repeat a week, and change Setup's first Monday to shift all six.

## Limits
- Excel only. The Google Sheets version is not built yet.
- Weekday labels use the Excel TEXT function, so they follow the language of the Excel install.
- Sheets are not protected; grey cells are calculated and should not be typed over.
