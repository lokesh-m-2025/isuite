import json
import logging
from pathlib import Path
from typing import Tuple
import pandas as pd
import numpy as np


logger = logging.getLogger(__name__)


class SchemaValidator:
    """Validates DataFrame schema against expected column definitions."""

    def __init__(self, schema_path: str):
        """Load schema definition from JSON file.
        
        Schema format:
        {
          "columns": [
            {
              "name": "order_id",
              "type": "integer",
              "nullable": false
            },
            {
              "name": "order_date",
              "type": "string",
              "nullable": false
            }
          ]
        }
        """
        if not Path(schema_path).exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        with open(schema_path, "r") as f:
            self.schema = json.load(f)

        self.column_definitions = {col["name"]: col for col in self.schema["columns"]}
        logger.info(f"Loaded schema with {len(self.column_definitions)} columns")

    def validate(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Validate DataFrame against schema.
        
        Returns:
            Tuple of (valid_df, invalid_df) where invalid_df contains rows with schema violations.
        """
        if df.empty:
            logger.warning("Input DataFrame is empty")
            return df, pd.DataFrame()

        invalid_rows = []

        # Check for missing columns
        expected_cols = set(self.column_definitions.keys())
        actual_cols = set(df.columns)
        missing_cols = expected_cols - actual_cols
        extra_cols = actual_cols - expected_cols

        if missing_cols:
            logger.error(f"Missing columns in CSV: {missing_cols}")
            # All rows are invalid if columns are missing
            return pd.DataFrame(columns=df.columns), df.copy()

        if extra_cols:
            logger.warning(f"Extra columns in CSV (will be ignored): {extra_cols}")
            df = df[list(expected_cols)]

        # Reorder columns to match schema
        df = df[list(expected_cols)]

        # Validate each row
        for idx, row in df.iterrows():
            for col_name, col_def in self.column_definitions.items():
                value = row[col_name]
                is_null = pd.isna(value)

                # Check nullability
                if is_null and not col_def.get("nullable", True):
                    invalid_rows.append(idx)
                    break

                # Check type (skip null values)
                if not is_null:
                    if not self._validate_type(value, col_def["type"]):
                        invalid_rows.append(idx)
                        break

        valid_df = df.drop(invalid_rows, errors="ignore").reset_index(drop=True)
        invalid_df = df.loc[invalid_rows].reset_index(drop=True) if invalid_rows else pd.DataFrame()

        logger.info(
            f"Schema validation: {len(valid_df)} valid rows, {len(invalid_df)} invalid rows"
        )
        return valid_df, invalid_df

    def _validate_type(self, value, expected_type: str) -> bool:
        """Check if value matches expected type."""
        if expected_type == "integer":
            return isinstance(value, (int, np.integer)) or (
                isinstance(value, str) and value.strip().lstrip("-").isdigit()
            )
        elif expected_type == "float":
            try:
                float(value)
                return True
            except (ValueError, TypeError):
                return False
        elif expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "boolean":
            return isinstance(value, (bool, np.bool_)) or str(value).lower() in (
                "true",
                "false",
                "1",
                "0",
            )
        elif expected_type == "date":
            try:
                pd.to_datetime(value)
                return True
            except (ValueError, TypeError, pd.errors.ParserError):
                return False
        return True
