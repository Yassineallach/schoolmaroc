# Ultimate Budget Spreadsheet (Excel .xlsx)

28 tabs in four sections, no macros: Transactions (5), Dashboards (4), Monthly insights (12, January to December), Build your wealth (7).

## Build and verify
```bash
python3 product-4-ultimate-budget-spreadsheet/build/build_budget.py product-4-ultimate-budget-spreadsheet/Ultimate_Budget_Spreadsheet.xlsx
```
Recalculated in LibreOffice: 28 tabs, 0 formula error cells. Checked by hand against the demo data: year income, spending, savings and net cash flow; bank balances; net worth; debt payoff dates; the sinking-fund monthly needs; the investment forecast (for example, 5,000 at 6% with 300 a month for 20 years gives 155,163); the no-spend totals; the 50/30/20 buckets.

## How it works
- **Easy Setup:** budget year, monthly spending budget, savings target, categories with a group (Fixed, Variable, Debt, Savings) and a 50/30/20 class, payment methods, accounts, frequencies.
- **Variable Transactions** is the ledger. Every dashboard, monthly sheet and chart reads from it.
- **Spending** excludes savings transfers. Savings are counted separately. Net cash flow = income minus spending minus savings.
- **Monthly sheets** (January to December) use the budget year on Easy Setup and list each month's transactions automatically.
- **Recurring Transactions** shows the next payment date from today. It does not post entries to the ledger.
- **Payments** flags overdue and due-soon bills.
- **Debt Calculator** switches between snowball and avalanche order and estimates payoff dates.
- **Investment Forecast** is hypothetical. It is labelled as not guaranteed.

## Limits
- Excel only. The Google Sheets version is not built yet.
- Recurring items are reminders, not automatic entries. Enter each occurrence in the ledger.
- Debt interest and payoff dates are estimates from a fixed rate and payment.
- The monthly transaction list shows the first 30 entries for a month; the totals include all of them.
- Charts show zero for months with no entries yet, including future months.
- Sheets are not protected; grey cells are calculated.
