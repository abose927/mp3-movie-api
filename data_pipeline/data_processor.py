import logging
import pandas as pd
logger = logging.getLogger(__name__)
def remove_duplicates(df):
    """Remove duplicate rows."""
    returned = df.drop_duplicates()
    num_dropped_rows = len(df)-len(returned)
    logger.debug(f"Dropped {num_dropped_rows} rows")
    return returned

def handle_missing(df, axis="rows"):
    """Drop rows or columns containing missing values."""
    if axis == "rows":
        returned = df.dropna(axis = 0)
        num_dropped_rows = len(df) - len(returned)
        logger.debug(f"Dropped {num_dropped_rows} rows")
    elif axis == "columns":
        returned = df.dropna(axis = 1)
        num_dropped_columns = len(df.columns) - len(returned.columns)
        logger.debug(f"Dropped {num_dropped_columns} columns")
    else: 
        logger.error(f"Unsupported axis: {axis}")
        raise ValueError(f"Unsupported axis: {axis}")
    return returned


def remove_outliers(df, columns, method, threshold):
    """Remove outliers from the specified numeric columns."""
    if method.lower() != "iqr" and method.lower() != "zscore":
        logger.error(f"Unsupported method: {method}")
        raise ValueError(f"Unsupported method: {method}")

    for c in columns:
        if c not in df.columns:
            logger.warning(f"{c} does not exist, skipping the column")
            continue

        if not pd.api.types.is_numeric_dtype(df[c]):
            logger.warning(f"{c} is not numeric, skipping the column")
            continue

        if method.lower() == "iqr":
            q1 = df[c].quantile(0.25)
            q3 = df[c].quantile(0.75)
            iqr = q3-q1
            lower = q1 - (threshold*iqr)
            upper = q3 + (threshold*iqr)
            initial_rows = len(df[c])
            df = df[(df[c] >= lower) & (df[c] <= upper)]
            num_dropped_rows = initial_rows - len(df[c])
            logger.debug(f"{num_dropped_rows} rows dropped at a threshold of {threshold} using the iqr method")
        if method.lower() == "zscore":
            mean = df[c].mean()
            std = df[c].std()
            z_score = (df[c] - mean)/std
            initial_rows = len(df[c])
            df = df[z_score.abs() <= threshold]
            num_dropped_rows = initial_rows - len(df[c])
            logger.debug(f"{num_dropped_rows} rows dropped at a threshold of {threshold} using the z-score method")
    return df

def process_data(df, config):
    """Apply the processing steps enabled in the configuration."""
    config_m = config['processing']['missing']
    config_o = config['processing']['outliers']
    if config['processing']['remove_duplicates']:
        df = remove_duplicates(df)
    if config_m['enabled']:
        df = handle_missing(df,config_m['axis'])
    if config_o['enabled']:
        df = remove_outliers(df,config_o['columns'],config_o['method'],config_o['threshold'])
    return df

def create_cleaning_report(df_before, df_after):
    """Return a dictionary summarizing the cleaning results."""
    return {"rows_before": len(df_before), 
            "rows_after" :len(df_after), 
            "rows_removed":len(df_before)-len(df_after), 
            "columns_before": len(df_before.columns),
            "columns_after": len(df_after.columns),
            "columns_removed": len(df_before.columns)-len(df_after.columns)
            }
