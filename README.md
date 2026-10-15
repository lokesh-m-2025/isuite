# Power BI Sales Report – Setup Guide

## What This Does

This Power BI project loads sales orders from an S3 CSV file, builds a date-intelligent data model, and creates three core measures:
- **Total Revenue**: sum of all sales amounts.
- **Revenue YoY %**: the percentage change in revenue from the same period in the prior year.
- **Top Products by Revenue**: a visual ranked list of your best-selling products by total revenue.

No manual data entry or formula typing is needed—everything here is pre-built; you just need to open it.

---

## Prerequisites

- **Power BI Desktop** (version 2023.11 or later). Download from https://powerbi.microsoft.com/en-us/desktop/
- **S3 Access**: your Power BI account must be able to read `s3://ignitho-development-bucket/input/sample-orders.csv`. This is typically handled by Power BI's native S3 connector; if your organisation requires an access key, you will enter it when prompted by Power BI Desktop (the key is not stored in these files).
- A text editor (Notepad, VS Code, etc.) to copy-paste the Power Query scripts.

---

## How to Run This

### 1. Open Power BI Desktop

Launch Power BI Desktop. You will see a blank canvas with a white "Get Data" button in the centre and a ribbon menu at the top.

### 2. Import the Orders Table (Power Query Script 1)

1. Click **Get Data** (centre of screen) or **Home** tab (top ribbon) → **Get Data** → **More...**
2. In the data source dialog, scroll down and select **OData Feed** (or **Web**, depending on your version).
   - **Alternative**: select **Text/CSV** if you have already downloaded the CSV locally instead of using S3 directly.
3. Paste the S3 URL: `s3://ignitho-development-bucket/input/sample-orders.csv`
4. Click **OK**. Power BI will connect; if prompted for credentials, enter your S3 access key and secret (these are stored by Power BI, not saved in the project files).
5. Once the preview appears, click **Load** (not "Transform Data" yet).
6. A new query called "sample-orders" will appear in the **Queries** pane (left side). Right-click it and select **Edit Query**.
   - This opens the **Power Query Editor**, a separate window with its own ribbon at the top.
7. In the Power Query Editor's **Home** tab (top ribbon), click **Advanced Editor** (on the right side).
8. Clear all text in the editor and paste the entire content from the file `power-query/Orders.m` (shown below).
9. Press **Ctrl+Enter** (or click the checkmark icon). Power Query will apply the transformations.
10. Click **Close & Apply** (Home tab → top-right).
11. Power BI Desktop will load the Orders table into the data model.

### 3. Import the Calendar Table (Power Query Script 2)

1. Back in Power BI Desktop's main window, click **Home** tab → **Get Data** → **Enter Data** (or paste the M query directly).
   - **Easier route**: Click **Home** → **New Source** → **Blank Query**.
2. In the Power Query Editor that opens, click **Advanced Editor** and paste the entire content from `power-query/Calendar.m`.
3. Press **Ctrl+Enter**. Power Query will generate a calendar table with one row per date.
4. Click **Close & Apply**.
5. A new table called "Calendar" will appear in your data model.

### 4. Mark the Calendar Table as a Date Table

**This step is essential for year-over-year calculations to work.**

1. In Power BI Desktop, click the **Data** icon (on the left ribbon, looks like a small table) to open the data pane.
2. In the **Fields** pane on the right, right-click the **Calendar** table and select **Mark as date table**.
3. In the dialog that appears, confirm that the **Date Column** is set to `Calendar[Date]`.
4. Click **OK**.

**Note**: Only the Calendar table should be marked as a date table—never the Orders table. This tells Power BI which table to use for time intelligence functions like SAMEPERIODLASTYEAR.

### 5. Create the Relationship Between Orders and Calendar

1. Click the **Model** icon (left ribbon, looks like a diagram) to open the data model view.
2. You should see two tables: **Orders** and **Calendar**.
3. If they are not already connected by a line, drag the **Calendar[Date]** field onto the **Orders[order_date]** field.
   - A line (relationship) will appear between the two tables.
4. Click the line to select it, then right-click → **Edit relationship**.
5. In the relationship dialog, confirm:
   - **First table (1)**: Calendar
   - **Second table (many)**: Orders
   - **Cardinality**: One-to-many (1:*)
   - This is correct: each date in the Calendar appears once, but many orders can occur on the same date.
6. Click **OK**.

### 6. Create the DAX Measures

Measures live in a fact table and hold calculations that summarize data. We will add ours to the Orders table.

**Create measures one at a time, in this order:**

#### Measure 1: Total Revenue

1. In the **Report** view (left icon, looks like a bar chart), click **Home** → **New Measure** (top ribbon).
2. A formula bar appears at the top with a cursor and the text `Measure = `.
3. **Do NOT copy the description comment** (the line starting with `--`). Copy **only** the formula line:
   ```
   Total Revenue = SUM(Orders[amount])
   ```
4. Paste it into the formula bar, replacing the default text.
5. Press **Enter**. The measure appears in the Fields pane under Orders.

#### Measure 2: Prior Year Revenue

1. Click **Home** → **New Measure** again.
2. Copy **only** this formula line (skip the comment):
   ```
   Prior Year Revenue = CALCULATE([Total Revenue], SAMEPERIODLASTYEAR(Calendar[Date]))
   ```
3. Paste and press **Enter**.

**Why it depends on the first measure**: This formula references `[Total Revenue]`, so it must be created *after* Total Revenue exists.

#### Measure 3: Revenue YoY %

1. Click **Home** → **New Measure**.
2. Copy **only** this formula (skip the comment):
   ```
   Revenue YoY % = DIVIDE([Total Revenue] - [Prior Year Revenue], [Prior Year Revenue], 0)
   ```
3. Paste and press **Enter**.

**Expected behaviour**: If the current period has no revenue (empty), this will show 0 (the third argument to DIVIDE). If the current period has revenue but the prior period is empty (first year on record), this will show -100%, because the formula correctly calculates (revenue - 0) / 0 = ∞, and DIVIDE's guard only covers division by zero, not a numerator of zero—this is correct, not a bug.

### 7. Create Visualizations

1. Click the **Report** icon (left, bar chart) if you are not already in report view.
2. In the ribbon, click **Insert** → select a visual type (Card, KPI, Bar Chart, etc.).
3. Drag fields or measures from the **Fields** pane (right) into the visual's **Values** area.
   - **Total Revenue**: use a **Card** visual to display a single number.
   - **Revenue YoY %**: use a **KPI** visual to show growth with a target (or a Card).
   - **Top Products by Revenue**: use a **Bar Chart** with Products on the Y-axis and Total Revenue on the X-axis; sort descending.
4. Adjust filters, titles and formatting as needed.

---

## What to Expect

- **Calendar table with zero rows**: The calendar contains one row for every date in the range (e.g., 365 rows per year). If your Orders CSV has no sales in certain months, the calendar will still show those months with 0 revenue—this is normal and expected. It is how Power BI ensures date continuity in time intelligence calculations.
- **YoY % shows -100% for new periods**: If the current year is 2024 but you have no orders from January 2023 (the prior year), Revenue YoY % will show -100% for January 2024. This is mathematically correct: revenue increased from 0 to some amount, but the prior-year denominator was 0. If you see this, check that your CSV includes data from both the current and prior year.
- **Blank measures after creation**: If a measure shows "blank" or "no data" in a visual, check that the calendar table is marked as a date table (step 4 above) and that the relationship exists (step 5).

---

## Troubleshooting

- **"Expression.Error: The key did not match any rows in the table"** when loading Orders: The S3 path may be incorrect, or your access credentials may be expired. Re-check the URL and credentials in Power BI's data source settings (File → Options → Data Source Settings).
- **Measures display "Error"** after creation: Usually means a field or measure name in the formula is misspelled. Double-check capitalization and table names against the Fields pane.
- **Calendar table not showing time intelligence results**: Confirm the Calendar table is marked as a date table (step 4). If it is already marked, unmark it (right-click → Unmark as date table) and mark it again; sometimes Power BI needs a refresh.
- **Orders and Calendar tables not connected by a line**: Create the relationship manually (step 5). If the line appears but measures still show no data, check cardinality direction: Calendar should be on the "1" (one) side, Orders on the "*" (many) side.

---

## Next Steps

Once the report is open:
- Slice by date using a **Slicer** (Insert → Slicer) to filter visualizations by month or year.
- Add a **Matrix** visual to show Revenue, Prior Year Revenue, and Revenue YoY % broken down by Product and Month for deeper analysis.
- Pin tiles to a dashboard for stakeholder sharing.

---

## Support

If something does not work as expected, verify:
1. S3 access is configured in Power BI (no local file issues).
2. All three tables exist in the Fields pane: Orders, Calendar, and any product dimension if added.
3. Calendar is marked as a date table.
4. All three measures appear in the Fields pane under Orders and show calculated values (not errors) when placed in a visual.
