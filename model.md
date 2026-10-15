# Data Model Outline

## Tables

### Orders (Fact Table)

**Grain**: One row per order transaction.

**Columns**:
- `order_date` (Date) – Transaction date; primary key component for time bucketing.
- `product_name` (Text) – Product identifier; supports product-level analysis.
- `amount` (Number, decimal) – Revenue per order; the primary measure column.

**Source**: S3 CSV `s3://ignitho-development-bucket/input/sample-orders.csv` (loaded via Power Query script `Orders.m`).

**Relationships**: Many-to-one to Calendar on `order_date` = `Calendar[Date]`.

---

### Calendar (Dimension Table)

**Grain**: One row per calendar date, 2022-01-01 to 2025-12-31.

**Columns**:
- `Date` (Date) – Calendar date; primary key and time intelligence anchor. **This column must be marked as the date table in Power BI Desktop** (Model → Calendar → Mark as date table).
- `Year` (Number) – Calendar year (e.g., 2024).
- `Month` (Number) – Month number (1–12).
- `Month Name` (Text) – Month name (e.g., "January").
- `Quarter` (Text) – Quarter label (e.g., "Q1").
- `Day of Week` (Text) – Day name (e.g., "Monday").

**Source**: Generated in Power Query script `Calendar.m`; no external source file.

**Relationships**: One-to-many to Orders on `Calendar[Date]` = `Orders[order_date]` (Calendar is the "one" side, Orders is the "many" side).

**Special Handling**: This table **must** be marked as a date table in Power BI Desktop for SAMEPERIODLASTYEAR and other time intelligence DAX functions to work. No other table should be marked as a date table.

---

## Relationships

| From | To | Column | Type | Cardinality | Direction |
|------|----|---------|----|---|---|
| Calendar | Orders | Calendar[Date] → Orders[order_date] | Active | 1:* | One-to-many |

**Notes**:
- Calendar is the "one" side (each date appears once); Orders is the "many" side (multiple orders per date).
- This relationship enables SAMEPERIODLASTYEAR to correctly shift the filter context backward by exactly one year.
- No other relationships are required for the initial report; if additional dimensions (e.g., Product, Region, Customer) are added later, each would follow the same pattern: dimension (1) to Orders (*).

---

## Measures (DAX)

All measures are calculated columns defined in the Orders table and are documented in `measures.dax`:

1. **Total Revenue** – SUM(Orders[amount]); base revenue aggregation.
2. **Prior Year Revenue** – CALCULATE with SAMEPERIODLASTYEAR; requires Calendar marked as date table.
3. **Revenue YoY %** – DIVIDE(current - prior, prior); shows -100% for new periods with no prior-year data (expected).
4. **Top Products Rank** – RANKX for product-level ranking by revenue (optional; used in bar charts).

---

## Design Decisions

- **Star Schema**: Orders (fact) related to Calendar (dimension) follows the standard star schema pattern, keeping fact and dimension concerns separate and enabling efficient time intelligence.
- **Calendar Scope**: Calendar extends from 2022-01-01 to 2025-12-31 to cover multiple years for YoY analysis; adjust the dates in `Calendar.m` if a different range is needed.
- **No Product Dimension**: Products are stored as text in Orders[product_name] rather than in a separate dimension table. If the same product name always refers to the same item (no homonyms), this is sufficient for the initial requirement ("top products by revenue"). If products have IDs, attributes, or hierarchies, a separate Product dimension should be added later.
- **Grain Purity**: Orders is kept at transaction level (one row per order); aggregation happens in DAX measures, not in the source data, preserving the ability to slice by order-level attributes if needed in future.
