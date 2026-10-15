import pandas as pd
import io
import logging
from typing import Tuple, List, Dict, Any

logger = logging.getLogger(__name__)


class CSVValidator:
    def __init__(self, expected_columns: List[str]):
        self.expected_columns = expected_columns

    def validate_and_parse(
        self, csv_bytes: io.BytesIO
    ) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """
        Parse CSV and separate valid rows from malformed ones.
        Returns (valid_df, malformed_records).
        Malformed records include the raw row and error reason.
        """
        malformed = []
        valid_rows = []

        try:
            csv_bytes.seek(0)
            df = pd.read_csv(csv_bytes, dtype=str, keep_default_na=False)
        except Exception as e:
            logger.error(f"Failed to read CSV: {e}")
            raise

        # Check column presence
        missing_cols = set(self.expected_columns) - set(df.columns)
        if missing_cols:
            logger.error(f"Missing required columns: {missing_cols}")
            raise ValueError(f"Missing required columns: {missing_cols}")

        extra_cols = set(df.columns) - set(self.expected_columns)
        if extra_cols:
            logger.warning(f"Extra columns will be ignored: {extra_cols}")

        # Subset to expected columns
        df = df[self.expected_columns]

        # Validate each row
        for idx, row in df.iterrows():
            try:
                # Check for null values in required fields
                if row.isnull().any():
                    malformed.append(
                        {
                            "row_number": idx + 2,  # +2 for header and 0-indexing
                            "row_data": row.to_dict(),
                            "error_reason": "Contains null values",
                        }
                    )
                    continue

                # Check for empty strings
                if (row == "").any():
                    malformed.append(
                        {
                            "row_number": idx + 2,
                            "row_data": row.to_dict(),
                            "error_reason": "Contains empty strings",
                        }
                    )
                    continue

                valid_rows.append(row.to_dict())

            except Exception as e:
                logger.warning(f"Error validating row {idx + 2}: {e}")
                malformed.append(
                    {
                        "row_number": idx + 2,
                        "row_data": dict(row),
                        "error_reason": str(e),
                    }
                )

        valid_df = pd.DataFrame(valid_rows) if valid_rows else pd.DataFrame()

        if malformed:
            logger.warning(f"Found {len(malformed)} malformed records")
        logger.info(
            f"Parsed {len(valid_rows)} valid and {len(malformed)} malformed records"
        )

        return valid_df, malformed
