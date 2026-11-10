# src/data_validator.py
import logging
import pandas as pd
logger = logging.getLogger(__name__)
def validate_dataframe(df, required_columns, numeric_columns):
    """Validate the DataFrame and return valid data.
    required_columns: a list of column names that must exist.
    numeric_columns: a list of column names whose values should be
    numeric.
    """
    original_rows = len(df)
    for col in required_columns:
        if col not in df.columns:
            logger.error(f"Required column not present: {col}")
            raise ValueError
    
    for col in numeric_columns:
        invalid_rows = []
        for i, value in df[col].items():
            if pd.notna(value):
                try:
                    float(value)
                except ValueError:
                    logger.warning(f"Invalid row: {i}")
                    invalid_rows.append(i)
        df = df.drop(invalid_rows)
        
        #convert to a numeric data type
        df[col] = pd.to_numeric(df[col])
    logger.debug(f"Dropped {original_rows-len(df)} rows")
    return df