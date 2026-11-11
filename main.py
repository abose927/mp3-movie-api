import io
import json
import logging
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from src import MovieUploadInfo, MovieDataResponse, ProcessConfig, MovieProcessingReport, HealthResponse, log_requests, setup_logging
from data_pipeline import create_cleaning_report, process_data, validate_dataframe
from src import (
MovieStorage
)
from src.storage import MOVIE_COLUMNS

setup_logging(verbose=True)
logger = logging.getLogger(__name__)

app = FastAPI(title="Data Processing API", version="1.0.0")
app.middleware("http")(log_requests)
storage = MovieStorage()

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Return the application status and version."""
    return {"status": "ok", "version": "1.0.0"}

@app.post("/upload", response_model=MovieUploadInfo)
async def upload_movies(file: UploadFile = File(...)):
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
    

    if df.empty:
        logger.warning(f"Empty file: {file_name}")
        raise HTTPException(status_code=400, detail="Empty file")
    if set(df.columns) != set(MOVIE_COLUMNS):
        logger.warning(f"Columns do not match requirements: {file_name}")
        raise HTTPException(status_code=400, detail="Mismatched columns")
    df = df[MOVIE_COLUMNS]
    storage.save(df)

    logger.info(f"Uploaded dataset: filename={file_name}, rows={len(df)}")
    return {
            "filename": file_name,"rows": len(df), "columns": len(df.columns) ,"column_names": list(df.columns)}



@app.get("/movies", response_model=MovieDataResponse)
def get_movies(limit: int = Query(default=100, ge=1)):
    """Return up to limit movies and the total number stored."""
    records = storage.select_columns(MOVIE_COLUMNS, limit)
    total_rows = storage.count_movies()
    logger.info(f"Retrieved movies: returned_rows={len(records)}, total_rows={total_rows}")
    return {"data": records, "total_rows": total_rows}

@app.get("/movies/search", response_model=list[dict])
def query_movies( columns: list[str] = Query(default=["title"]), min_rating: float = Query(default=0, ge=0, le=10), limit: int = Query(default=100, ge=1)):
    """Return selected fields from movies rated at least min_rating."""
    try:
        results = storage.query_movies(columns, min_rating, limit)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    logger.info(f"Queried movies: columns={columns}, min_rating={min_rating}, returned_rows={len(results)}")
    return results


@app.post("/movies/process", response_model=MovieProcessingReport)
def process_movies(config: ProcessConfig):
    """Validate and process the stored movies using MP1 functions."""
    df = storage.get()
    if df.empty:
        logger.warning("No movies to process")
        raise HTTPException(status_code=400, detail="No movies stored. Upload a CSV first.")

    config_dict = config.model_dump()
    required_columns = config_dict["validation"]["required_columns"]
    numeric_columns = config_dict["validation"]["numeric_columns"]

    missing_columns = [col for col in numeric_columns if col not in df.columns]
    if missing_columns:
        logger.warning(f"Numeric columns not found: {missing_columns}")
        raise HTTPException(status_code=400, detail=f"Numeric columns not found: {missing_columns}")

    try:
        validated_df = validate_dataframe(df, required_columns, numeric_columns)
        validation_rows_removed = len(df) - len(validated_df)
        logger.info(f"Validation successful: {len(df)} -> {len(validated_df)} rows")
        original_df = validated_df.copy()
        cleaned_df = process_data(validated_df, config_dict)
        report = create_cleaning_report(original_df, cleaned_df)
    except ValueError as error:
        logger.warning(f"Processing failed: {error}")
        raise HTTPException(status_code=400, detail=str(error))

    storage.save(cleaned_df)
    logger.info(f"Processed movies: validation_removed={validation_rows_removed}, " f"rows_before={report['rows_before']}, rows_after={report['rows_after']}")

    return {"validation_rows_removed": validation_rows_removed, "cleaning_report": report}