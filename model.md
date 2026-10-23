# Power BI Data Model

## Overview

This is a star-schema model with one fact table (Orders) and two dimension tables (Date, Product). All relationships are one-to-many from dimension to fact.

---

## Tables

### Fact Table: Orders

**Grain**: One row per order transaction.

| Column     | Type    | Notes                                  |
|------------|---------|----------------------------------------|
| OrderID    | Text    | Surrogate key, unique per row          |
| OrderDate  | Date    | Transaction date; foreign key to Date  |
| ProductName| Text    | Product description; foreign key to Product |
| Revenue    | Decimal | Quantity × UnitPrice (derived)         |

**Purpose**: Captures revenue facts by date and product for analysis.

---

### Dimension Table: Date

**Grain**: One row per calendar day from the minimum to maximum OrderDate in Orders.

| Column     | Type    | Notes                                       |
|------------|---------|---------------------------------------------|
| Date       | Date    | Primary key; marked as date table in PBI    |
| Year       | Integer | Calendar year (e.g., 2023, 2024)            |
| Quarter    | Text    | Quarter label (e.g., Q1, Q2)                |
| Month      | Integer | Month number (1–12)                         |
| MonthName  | Text    | Month name (e.g., January, February)        |
| WeekOfYear | Integer | ISO week number (1–53)                      |
| DayOfWeek  | Text    | Day name (e.g., Monday, Tuesday)            |
| YearMonth  | Text    | Concatenated Year-Month (e.g., 2024-03)    |

**Purpose**: Enables time intelligence analysis (year-over-year, month-over-month). Must be marked as a date table in Power BI Desktop for SAMEPERIODLASTYEAR and similar functions to work.

---

### Dimension Table: Product

**Grain**: One row per unique product.

| Column    | Type | Notes              |
|-----------|------|-----------------|
| ProductID | Text | Surrogate key      |
| ProductName | Text | Product description |

**Purpose**: Lookup table for product dimension; enables product-level filtering and ranking.

---

## Relationships

| From Table | From Column | To Table | To Column | Cardinality | Direction |
|------------|-------------|----------|-----------|-------------|----------|
| Date       | Date        | Orders   | OrderDate | 1:*         | Single   |
| Product    | ProductName | Orders   | ProductName | 1:* | Single |

**Cardinality Notes**:
- Date ("one" side) to Orders ("many" side): Many orders may share the same date.
- Product ("one" side) to Orders ("many" side): Many orders may reference the same product.

Both relationships flow from dimension to fact, supporting correct CALCULATE filter propagation in DAX measures.

---

## Key Design Decisions

1. **Revenue is derived**: Quantity and UnitPrice are removed from the final Orders table after Revenue is calculated, reducing storage and simplifying measures.
2. **Surrogate keys**: OrderID and ProductID are added as unique identifiers to support future relationships or auditing, though the model currently uses natural keys (Date, ProductName).
3. **Full calendar**: The Date table is a complete calendar from min to max OrderDate, not a sparse list of transaction dates. This ensures time-intelligence measures work correctly even when a month has no orders (showing 0, not a blank).
4. **Text-based time attributes**: Year, Month, Quarter, and YearMonth are stored as separate columns rather than derived in DAX, making them available for slicing without formula overhead.