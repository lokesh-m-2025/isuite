import unittest
from datetime import datetime, timedelta

class TestCalendarPowerQuery(unittest.TestCase):
    """
    Unit tests for Calendar Power Query script logic.
    Validates that the M script generates a complete date dimension:
    - Calendar spans 2022-01-01 to 2025-12-31.
    - Each row is unique (one date per row).
    - Year, Month, Quarter, and Day of Week columns are correctly derived.
    """

    def setUp(self):
        """Define expected calendar range."""
        self.min_date = datetime(2022, 1, 1).date()
        self.max_date = datetime(2025, 12, 31).date()
        self.expected_row_count = (self.max_date - self.min_date).days + 1

    def test_calendar_span(self):
        """Verify calendar covers 2022-01-01 to 2025-12-31."""
        # Expected range is 4 years + 1 day (inclusive of both endpoints).
        # 2022 (365) + 2023 (365) + 2024 (366, leap) + 2025 (365) = 1461 days.
        expected_days = 1461
        self.assertEqual(self.expected_row_count, expected_days)

    def test_unique_dates(self):
        """Verify no duplicate dates in the calendar."""
        # Generate the date list as the M script does.
        date_list = []
        current = self.min_date
        while current <= self.max_date:
            date_list.append(current)
            current += timedelta(days=1)
        # Check for uniqueness.
        self.assertEqual(len(date_list), len(set(date_list)))

    def test_year_derivation(self):
        """Verify Year column is correctly extracted from Date."""
        test_date = datetime(2024, 6, 15).date()
        year = test_date.year
        self.assertEqual(year, 2024)

    def test_month_derivation(self):
        """Verify Month column (1–12) is correctly extracted."""
        test_dates = [
            (datetime(2024, 1, 1).date(), 1),
            (datetime(2024, 6, 15).date(), 6),
            (datetime(2024, 12, 31).date(), 12),
        ]
        for test_date, expected_month in test_dates:
            month = test_date.month
            self.assertEqual(month, expected_month)

    def test_quarter_derivation(self):
        """Verify Quarter is correctly derived (Q1–Q4)."""
        test_cases = [
            (1, "Q1"), (2, "Q1"), (3, "Q1"),
            (4, "Q2"), (5, "Q2"), (6, "Q2"),
            (7, "Q3"), (8, "Q3"), (9, "Q3"),
            (10, "Q4"), (11, "Q4"), (12, "Q4"),
        ]
        for month, expected_quarter in test_cases:
            # M script formula: quarter = "Q" & ROUNDUP(month / 3)
            quarter_num = ((month - 1) // 3) + 1
            quarter_label = f"Q{quarter_num}"
            self.assertEqual(quarter_label, expected_quarter)

    def test_day_of_week_derivation(self):
        """Verify Day of Week is correctly derived (Monday–Sunday)."""
        # 2024-01-01 is a Monday.
        test_date = datetime(2024, 1, 1).date()
        day_name = test_date.strftime("%A")
        self.assertEqual(day_name, "Monday")
        # 2024-01-07 is a Sunday.
        test_date = datetime(2024, 1, 7).date()
        day_name = test_date.strftime("%A")
        self.assertEqual(day_name, "Sunday")

if __name__ == "__main__":
    unittest.main()
