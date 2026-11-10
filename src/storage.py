import logging
import pandas as pd

logger = logging.getLogger(__name__)

class DatasetStorage:
    def __init__(self):
        self._store = {}
        self._counter = 0
    
    def save(self, df, filename):
        """Store a copy of the data and return a new integer ID."""
        self._counter += 1
        dataset_id = self._counter
        self._store[dataset_id] = {"filename": filename, "df": df.copy()}
        logger.debug(f"Stored dataset: id={dataset_id}, rows={len(df)}")
        return dataset_id
    
    def get(self, dataset_id):
        """Return a copy of the stored DataFrame, or None."""
        if dataset_id in self._store:
            df = self._store[dataset_id].copy()
            logger.debug(f"Retrieved dataset copy: id={dataset_id}, rows={len(df)}")
            return self._store[dataset_id]["df"].copy()
        else:
            return None
    
    def get_metadata(self, dataset_id):
        """Return the dataset metadata, or None."""
        if dataset_id not in self._store:
            return None
        entry = self._store[dataset_id]
        df = entry["df"]
        return {
            "id": dataset_id, "filename": entry["filename"],"rows": len(df), "columns": len(df.columns) ,"column_names": list(df.columns)}
    
    def update(self, dataset_id, df):
        """Replace an existing dataset; return True, or False if
        missing."""
        if dataset_id in self._store:
            self._store[dataset_id]["df"] = df.copy()
            logger.debug(f"Updated dataset: id={dataset_id}, rows={len(df)}")
            return True
        else:
            return False


    def clear(self):
        """Clear all data and reset the ID counter."""
        self._store.clear()
        self._counter = 0