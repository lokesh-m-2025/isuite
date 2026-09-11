from typing import Tuple, List
import pandas as pd
import logging


class SchemaValidator:
    """Validates that DataFrame has required columns."""

    def __init__(self, required_columns: List[str]):
        self.required_columns = required_columns
        self.logger = logging.getLogger(__name__)

    def validate(self, df: pd.DataFrame) -> List[str]:
        """Validate schema against required columns.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        missing_columns = set(self.required_columns) - set(df.columns)
        if missing_columns:
            msg = f"Missing required columns: {missing_columns}"
            errors.append(msg)
        
        extra_columns = set(df.columns) - set(self.required_columns)
        if extra_columns:
            self.logger.debug(f"Extra columns found (ignored): {extra_columns}")
        
        return errors


class DataValidator:
    """Validates individual records and separates valid from invalid."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def validate_and_separate(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Separate valid records from invalid ones.
        
        Valid records have:
        - non-null customer_id
        - non-null amount
        - amount is numeric
        
        Returns:
            Tuple of (valid_df, invalid_df)
        """
        if df.empty:
            return df, pd.DataFrame()

        # Create a copy to avoid SettingWithCopyWarning
        df = df.copy()
        df["_validation_error"] = ""
        
        # Check for null customer_id
        null_customer_mask = df["customer_id"].isna() | (df["customer_id"] == "")
        df.loc[null_customer_mask, "_validation_error"] = "Null or empty customer_id"
        
        # Check for null amount
        null_amount_mask = df["amount"].isna()
        df.loc[null_amount_mask, "_validation_error"] = "Null amount"
        
        # Try to convert amount to numeric, mark failures
        amount_errors = []
        for idx, val in df["amount"].items():
            if pd.isna(val):
                continue
            try:
                float(val)
            except (ValueError, TypeError):
                if df.loc[idx, "_validation_error"]:
                    df.loc[idx, "_validation_error"] += "; "
                df.loc[idx, "_validation_error"] += f"Non-numeric amount: {val}"
                amount_errors.append(idx)
        
        # Separate valid from invalid
        valid_mask = df["_validation_error"] == ""
        valid_df = df[valid_mask].drop(columns=["_validation_error"])
        invalid_df = df[~valid_mask]
        
        # Convert amount to numeric in valid dataframe
        if not valid_df.empty:
            valid_df = valid_df.copy()
            valid_df["amount"] = pd.to_numeric(valid_df["amount"], errors="coerce")
            # This should not happen after validation, but defensive check
            valid_df = valid_df.dropna(subset=["amount"])
        
        if len(invalid_df) > 0:
            self.logger.info(f"Found {len(invalid_df)} invalid records")
            for idx, row in invalid_df.iterrows():
                self.logger.debug(
                    f"Invalid record at index {idx}: {row['_validation_error']}"
                )
        
        return valid_df, invalid_df
