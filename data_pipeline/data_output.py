# src/data_output.py
import logging
from pathlib import Path
import pandas as pd
logger = logging.getLogger(__name__)
def save_data(df, filepath):
    """Save a DataFrame as a CSV file."""
    file_path = Path(filepath)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(file_path, index=False)
    logger.debug(f"Saved {len(df)} rows to {file_path}")
    return file_path


