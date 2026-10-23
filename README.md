# Power BI Sales Analysis Report – Setup Guide

This folder contains a Power BI project ready to open in Power BI Desktop. It includes scripts to load sales data from an S3 CSV, a data model with dimensions for Date and Product, and pre-built measures for revenue and year-over-year growth analysis.

## What You'll Get

Once set up, the model will let you:

- See total revenue and order counts filtered by date, product, or any combination.
- Compare revenue this year to last year, with automatic percentage change calculation.
- Rank products by revenue to spot your top sellers.
- Slice and filter by month, quarter, year, or day of week without having to write formulas.

## Prerequisites

1. **Power BI Desktop** (version 2023.08 or later). Download it free from [Microsoft](https://powerbi.microsoft.com/desktop).
2. **Access to the S3 bucket** `s3://ignitho-development-bucket/input/sample-orders.csv`. Your Power BI account must have permission to read this file. If you do not have S3 access, you can download the CSV manually and reference a local file instead (step 3 below notes how).
3. **A text editor** (Notepad, VS Code, or similar) to edit the Power Query scripts if needed. Not required if you paste scripts as-is.

## How to Run This

### Step 1: Configure the S3 Connection

Open the file `.env.example` in a text editor. You will see:

```
S3_BUCKET_PATH=
```

This is a placeholder. The actual S3 path in the Power Query script is:

```
s3://ignitho-development-bucket
```

**If you can access S3 from Power BI Desktop**: Leave the placeholder blank. The Power Query script will use the hardcoded S3 path. Power BI will prompt you for S3 credentials the first time it connects.

**If you cannot access S3 or prefer a local file**: Download `sample-orders.csv` from the S3 bucket manually, save it somewhere on your computer (e.g., `C:\Data\sample-orders.csv`), and in Step 3 below, modify the source step in Power Query to point to your local file instead of S3.

### Step 2: Open Power BI Desktop and Create a New Blank Report

1. Launch **Power BI Desktop**.
2. Click **File** → **New**, or close any open report to get to the start page.
3. Click **Blank report**.

### Step 3: Import the Power Query Scripts

You will add three tables to the data model: Orders, Product, and Date. Do this one at a time, in this order:

#### 3a. Load the Orders Table

1. In the **Home** ribbon at the top, look for the **Get Data** dropdown (usually on the left). Click the small arrow next to it and select **Blank Query**.
   - Note: You are in the Power Query Editor now, not the main report view. The ribbon at the top says "Power Query Editor."
2. On the right side, you will see **Query Settings**. Under the list of steps, click **Advanced Editor** (in the Power Query Editor's **Home** ribbon).
3. A window opens showing the current blank query. **Delete all text** in this window.
4. Open the file `power-query/Orders.m` in a text editor. **Copy the entire contents** (the `let ... in` block).
5. Paste it into the Advanced Editor window in Power BI.
6. At the bottom right, click **Done**. Power BI will attempt to load the data.
   - **If you are using a local CSV file**: On line 2 of the Orders.m script, replace `Web.Contents(S3BucketPath & "/input/sample-orders.csv")` with `File.Contents("C:\\Data\\sample-orders.csv")` (adjust the path to match your local file location).
7. Once the data appears in the preview, click **Close & Apply** (top left of the Power Query Editor ribbon). The Orders table is now in your model.

#### 3b. Load the Product Table

1. Click **Get Data** → **Blank Query** again.
2. Click **Advanced Editor** in the Power Query Editor **Home** ribbon.
3. Delete the blank text.
4. Open `power-query/Product.m`, copy its contents, and paste into the Advanced Editor.
5. Click **Done**. This script references the Orders table you just created; Power BI will use that data to extract unique products.
6. Once the Product preview appears, click **Close & Apply**.

#### 3c. Load the Date Table

1. Click **Get Data** → **Blank Query** again.
2. Click **Advanced Editor**.
3. Delete the blank text.
4. Open `power-query/Date.m`, copy its contents, and paste into the Advanced Editor.
5. Click **Done**. This script generates a calendar from the date range in Orders.
6. Once the Date preview appears, click **Close & Apply**.

### Step 4: Mark the Date Table

**This step is critical for year-over-year growth calculations to work.**

1. You are now back in the main Power BI Desktop report window.
2. On the left side, click the **Model** view (the third icon, looks like a grid or database symbol).
3. In the center, you will see your three tables: Orders, Product, and Date. Click on the **Date** table.
4. On the right side, under **Properties**, you will see a **Mark as date table** button (or toggle). Click it.
5. A dialog asks you to confirm the date column. **Select "Date"** from the dropdown and click **OK**.
   - This tells Power BI that the Date table is a calendar, unlocking year-over-year and other time-based calculations.

### Step 5: Verify Relationships

1. Stay in **Model** view.
2. Look at the diagram in the center. You should see three tables with lines between them:
   - Date → Orders (on OrderDate)
   - Product → Orders (on ProductName)
3. If the lines are not there, or point the wrong direction, drag to create them:
   - From Date[Date] to Orders[OrderDate]
   - From Product[ProductName] to Orders[ProductName]
   - Both should show a `1` on the dimension side and a `*` on the Orders side.
4. If a relationship points the wrong way (e.g., `* to 1` instead of `1 to *`), delete it and recreate it in the correct direction.

### Step 6: Add the DAX Measures

**Important**: Measures must be created one at a time, in dependency order. The order is:

1. Total Revenue
2. Prior Year Revenue
3. Year over Year Growth %
4. Order Count
5. Average Order Value
6. Product Rank by Revenue

For each measure:

1. In the **Model** view, right-click the **Orders** table and select **New Measure**.
2. At the top of the window, you will see a formula bar with "Measure" as a placeholder. This is where you type.
3. **Do not copy the description comment** (the line starting with `--`). Copy only the formula line, which starts with the measure name (e.g., `Total Revenue = `).
4. Open the file `measures.dax` in a text editor. Find the first measure: `Total Revenue = SUM(Orders[Revenue])`.
5. Copy **only** this line: `Total Revenue = SUM(Orders[Revenue])` (not the comment below it).
6. In Power BI, replace the placeholder text in the formula bar with what you copied. Press **Enter**.
7. The new measure appears in the Orders table in the **Fields** pane on the right. Repeat for the next measure.

**Why not copy the comment?** Power BI's formula bar can accidentally merge a comment line (`--`) into the measure name itself when you paste multiple lines at once, creating a measure named `-- Returns the sum of ...` instead of `Total Revenue`, which breaks all references to it. Copying one formula line at a time prevents this.

### Step 7: Build a Test Visual

1. Click the **Report** view (the first icon on the left).
2. On the right side, in the **Visualizations** pane, select a **Table** visual (looks like a grid).
3. Drag **Date[YearMonth]** to the Rows area.
4. Drag **Total Revenue** to the Values area.
5. You should see a table with months and their revenue. Check that the numbers make sense (no zeros or blanks in the middle of your date range is expected; they mean no orders that month).
6. Add **Year over Year Growth %** to the Values area. You will see growth percentages next to revenue.
   - **Expected behaviour**: The first year shown will likely be blank (no prior year to compare), and any months in the current year with no data will show -100% (expected, not an error—current year revenue is 0, prior year might have had data, so (0 - prior) / prior = -100%).
7. Create another visual: Drag **Product[ProductName]** to Rows and **Total Revenue** to Values. Sort by revenue descending to see top products.

### Step 8: Test Slicing

1. Add a **Slicer** visual (in the Visualizations pane, select the filter icon).
2. Drag **Date[Year]** into the slicer. You will see a list of years. Click one.
3. All other visuals should filter to show only that year's data. This confirms that relationships and measures are working correctly.

## Troubleshooting

**"Query "Orders" references a source that doesn't exist."**
- You are trying to load the Product or Date table before Orders exists. Power Query scripts load in the order you create them. Make sure Orders is created first.

**"The 'Date' table is not marked as a date table."**
- If you see this in an error message, go to Model view, click the Date table, and use the Mark as date table button (Step 4).

**Year over Year Growth % shows -100% or "N/A" for every month.**
- This is expected if there is only one year of data or if the prior year has no orders. The measure is working correctly.

**Relationships didn't auto-detect.**
- If you don't see lines between tables in Model view, manually create them by clicking and dragging from a dimension's column to the fact table's column. Make sure the dimension (Date or Product) is on the "one" side (has a `1` symbol) and Orders is on the "many" side (has a `*` symbol).

**S3 connection fails with "credentials not recognised."**
- Power BI needs your AWS access credentials. When Power BI first tries to read from S3, a dialog appears asking for authentication. Provide your AWS Access Key ID and Secret Access Key. Alternatively, use a local CSV file (see Step 3a) or ensure your Power BI tenant has S3 connector permissions.

## Next Steps

Once the data is loaded and measures are working:

- Build visuals: bar charts for top products, line charts for revenue trends, cards for KPIs.
- Add slicers for product, date range, or other dimensions to explore the data interactively.
- Publish to Power BI Service if you want to share the report with colleagues.
- Set up scheduled refresh if you want the report to pull fresh data on a schedule.

For questions about the data model, see `model.md`. For details on each measure, see the descriptions in `measures.dax`.