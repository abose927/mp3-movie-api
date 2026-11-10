from pathlib import Path
import logging
import pandas as pd
import json
import yaml 

logger = logging.getLogger(__name__)

def load_csv(filepath):
    """Load a CSV file into a DataFrame. filepath is a Path object. """
    file_path = Path(filepath)
    df = pd.read_csv(file_path)
    logger.info(f"Loaded CSV File: {file_path}, ({len(df)} rows)")
    return df

def load_json(filepath):
    """Load a JSON file into a Python object (dict or list). filepath is a Path object. """
    file_path = Path(filepath)
    with open(file_path, "r") as f:
        data = json.load(f)
    logger.info(f"Loaded JSON file: {file_path}")
    return data

def load_yaml(filepath):
    """Load a YAML file into a Python object. filepath is a Path object. """
    file_path = Path(filepath)
    with open(file_path, "r") as f:
        config = yaml.safe_load(f)
    logger.info(f"Loaded YAML file: {file_path}")
    return config

def load_data(filepath):
    """Load a file based on its extension. filepath is a string, such as 'fixtures/sample.csv' """
    file_path = Path(filepath)
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        returned = load_csv(file_path)
    elif suffix == ".json":
        returned = load_json(file_path)
    elif suffix == ".yaml":
        returned = load_yaml(file_path)
    else:
        logger.error(f"Unsupported file format: {suffix}")
        raise ValueError
    return returned