import pandas as pd
import pytest

import main
from src import MovieStorage
from src.storage import MOVIE_COLUMNS


def test_movies_persist(client, test_storage, uploaded_movies):
    fresh_storage = MovieStorage(test_storage.db_path)
    df = fresh_storage.get()
    assert len(df) == 20
    assert fresh_storage.count_movies() == 20
    assert list(df.columns) == MOVIE_COLUMNS
    expected_titles = pd.read_csv("fixtures/sample_movies.csv")["title"].tolist()
    assert df["title"].tolist() == expected_titles
    expected_ids = list(range(1, 21))
    storage_ids = [row["id"] for row in fresh_storage.select_columns(["title"], limit=100)]
    assert storage_ids == expected_ids
    response = client.get("/movies", params={"limit": 100})
    assert response.status_code == 200
    api_ids = [row["id"] for row in response.json()["data"]]
    assert api_ids == expected_ids


def test_cache_and_processing(client, uploaded_movies, processing_body):
    response_100 = client.get("/movies", params={"limit": 100})
    assert response_100.status_code == 200
    assert main.cache.get(100) == response_100.json()
    response_1 = client.get("/movies", params={"limit": 1})
    assert response_1.status_code == 200
    assert main.cache.get(1) == response_1.json()
    repeat_100 = client.get("/movies", params={"limit": 100})
    assert repeat_100.status_code == 200
    assert repeat_100.json() == response_100.json()
    process = client.post("/movies/process", json=processing_body)
    assert process.status_code == 200
    report = process.json()
    assert report["validation_rows_removed"] == 0
    assert report["cleaning_report"]["rows_before"] == 20
    assert report["cleaning_report"]["rows_after"] == 16
    assert main.cache.get(100) is None
    assert main.cache.get(1) is None
    after = client.get("/movies", params={"limit": 100})
    assert after.status_code == 200
    body = after.json()
    assert body["total_rows"] == 16
    expected_titles = [f"Movie {letter}" for letter in "ABCDEFGHIJKLMNOP"]
    assert [row["title"] for row in body["data"]] == expected_titles
    assert [row["id"] for row in body["data"]] == list(range(1, 17))
    assert main.cache.get(100) == body


def test_cache_hit_skips_database(client, uploaded_movies, monkeypatch):
    first = client.get("/movies", params={"limit": 100})
    assert first.status_code == 200
    def fail_if_called(*args, **kwargs):
        pytest.fail("Database was read on a cache hit")
    monkeypatch.setattr(main.storage, "select_columns", fail_if_called)
    monkeypatch.setattr(main.storage, "count_movies", fail_if_called)
    second = client.get("/movies", params={"limit": 100})
    assert second.status_code == 200
    assert second.json() == first.json()