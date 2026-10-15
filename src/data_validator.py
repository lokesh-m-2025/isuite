import logging
from typing import Tuple
import pandas as pd


logger = logging.getLogger(__name__)


class DataValidator:
    """Performs data quality validation beyond schema checking."""

    def validate(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Apply data quality validations.
        
        Returns:
            Tuple of (valid_df, invalid_df)
        """
        if df.empty:
            return df, pd.DataFrame()

        invalid_rows = set()

        # Detect complete duplicates
        duplicates = df[df.duplicated(keep="first")]
        if not duplicates.empty:
            logger.warning(f"Found {len(duplicates)} duplicate rows")
            invalid_rows.update(duplicates.index.tolist())

        valid_df = df.drop(list(invalid_rows), errors="ignore").reset_index(drop=True)
        invalid_df = df.loc[list(invalid_rows)].reset_index(drop=True) if invalid_rows else pd.DataFrame()

        logger.info(
            f"Data quality validation: {len(valid_df)} valid rows, {len(invalid_df)} invalid rows"
        )
        return valid_df, invalid_df
