import io
import json
import logging
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from src import DatasetInfo, DatasetStorage, HealthResponse, ProcessConfig, ProcessingReport, log_requests, setup_logging
from data_pipeline import create_cleaning_report, process_data, validate_dataframe

setup_logging(verbose=True)
logger = logging.getLogger(__name__)

app = FastAPI(title="Data Processing API", version="1.0.0")
app.middleware("http")(log_requests)
storage = DatasetStorage()

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Return the application status and version."""
    return {"status": "ok", "version": "1.0.0"}

@app.post("/upload", response_model=DatasetInfo)
async def upload_dataset(file: UploadFile = File(...)):
    """Read and store a CSV upload."""
    file_name = file.filename
    suffix = Path(file.filename or "").suffix.lower()
    if suffix != ".csv":
        logger.warning(f"Unsupported file format: {suffix}")
        raise HTTPException(status_code=400, detail="Unsupported file format")
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
    
    except pd.errors.EmptyDataError:
        logger.warning(f"File is empty: {file_name}")
        raise HTTPException(status_code=400, detail="File is empty")
    except pd.errors.ParserError:
        logger.warning(f"Failed to parse the file: {file_name}")
        raise HTTPException(status_code=400, detail="Failed to parse the file")
    except UnicodeDecodeError:
        logger.warning(f"Decoding failed: {file_name}")
        raise HTTPException(status_code=400, detail="Decoding failed")

    dataset_id = storage.save(df, file_name)
    logger.info(f"Uploaded dataset: id={dataset_id}, filename={file_name}, rows={len(df)}")
    return storage.get_metadata(dataset_id)



@app.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: int, limit: int = Query(default=100, ge=1)):
    """Return up to limit rows from a stored dataset."""
    df = storage.get(dataset_id)
    if df is None:
        logger.warning(f"Dataset not found: {dataset_id}")
        raise HTTPException(status_code=404, detail="Dataset not found")

    records = json.loads(df.head(limit).to_json(orient="records"))
    logger.info(f"Retrieved dataset: id={dataset_id}, returned_rows={len(records)}")
    return {"id": dataset_id, "data": records, "total_rows": len(df)}

@app.post("/datasets/{dataset_id}/process",response_model=ProcessingReport)
def process_dataset(dataset_id: int, config: ProcessConfig):
    """Validate and process a stored dataset using MP1 functions."""
    # TODO: retrieve, validate, process, report, update, and return.
    
    df = storage.get(dataset_id)
    if df is None:
        logger.warning(f"Dataset not found: {dataset_id}")
        raise HTTPException(status_code=404, detail="Dataset not found")

    config_dict = config.model_dump()
    required_columns = config_dict["validation"]["required_columns"]
    numeric_columns = config_dict["validation"]["numeric_columns"]

    missing_columns = [col for col in numeric_columns if col not in df.columns]
    if missing_columns:
        logger.warning(f"Numeric columns not found in dataset {dataset_id}: {missing_columns}")
        raise HTTPException(status_code=400, detail=f"Numeric columns not found: {missing_columns}")

    try:
        validated_df = validate_dataframe(df, required_columns, numeric_columns)
        validation_rows_removed = len(df) - len(validated_df)
        logger.info(f"Validation successful: id={dataset_id}, {len(df)} -> {len(validated_df)} rows")
        original_df = validated_df.copy()
        cleaned_df = process_data(validated_df, config_dict)
        report = create_cleaning_report(original_df, cleaned_df)
    except ValueError as error:
        logger.warning(f"Processing failed for dataset {dataset_id}: {error}")
        raise HTTPException(status_code=400, detail=str(error))
    storage.update(dataset_id, cleaned_df)
    logger.info( f"Processed dataset: id={dataset_id}, validation_removed={validation_rows_removed}, " f"rows_before={report['rows_before']}, rows_after={report['rows_after']}")

    return {"id": dataset_id, "validation_rows_removed": validation_rows_removed, "cleaning_report": report}    



