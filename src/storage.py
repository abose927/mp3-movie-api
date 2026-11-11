import logging
import sqlite3
import pandas as pd
from .database import get_connection, initialize_database
logger = logging.getLogger(__name__)
MOVIE_COLUMNS = ["title", "release_year", "rating", "genre"]
class MovieStorage:
    def __init__(self, db_path="data/movies.db"):
        self.db_path = db_path
        initialize_database(self.db_path)
   
    def save(self, df):
        """Replace all movie rows in one transaction."""
        connection = get_connection(self.db_path)
        cleaned_df = df[MOVIE_COLUMNS].astype(object).where(df[MOVIE_COLUMNS].notna(), None)
        rows = cleaned_df.values.tolist()
        statement = """ 
        INSERT INTO movies (title, release_year, rating, genre) VALUES (?,?,?,?)
        """
        try:
            connection.execute("DELETE FROM movies")
            connection.executemany(statement,rows)
            connection.commit()
            logger.debug(f"Stored movies in SQLite: rows={len(rows)}")
        except sqlite3.Error:
            connection.rollback()
            raise
        finally:
            connection.close()
    
    def get(self):
        """Return the four movie columns as a DataFrame, ordered by id."""
        connection = get_connection(self.db_path)
        statement = """
        SELECT title, release_year, rating, genre 
        FROM movies
        ORDER BY id
        """
        try:
            data = connection.execute(statement)
            df = pd.DataFrame(data.fetchall(), columns=MOVIE_COLUMNS)
        finally:
            connection.close()
        return df
    
    def select_columns(self, columns, limit=5):
        """Return id plus the requested movie columns, ordered by id."""
        if not columns:
            logger.error("Select at least one column")
            raise ValueError("Select at least one column")
        
        for column in columns:
            if column not in MOVIE_COLUMNS:
                logger.error(f"Unsupported column: {column}")
                raise ValueError(f"Unsupported column: {column}")
        selected_columns = ", ".join(["id"] + columns)
        connection = get_connection(self.db_path)
        
        try:
            cols = connection.execute(f"SELECT {selected_columns} from movies ORDER BY id LIMIT ?",(limit,))
            rows = cols.fetchall()
            dictlist = [dict(row) for row in rows]
            logger.debug(f"Selected columns: {selected_columns}, rows={len(dictlist)}")
            return dictlist
        finally:
            connection.close()
        
    def count_movies(self):
        """Return the number of stored movies using SQL COUNT(*)."""
        connection = get_connection(self.db_path)
        try: 
           movie = connection.execute("SELECT COUNT(*) FROM movies")
           returned = movie.fetchone()[0]
           return returned
        finally:
            connection.close()


    def query_movies(self, columns, min_rating, limit):
        """Return selected fields from matching movies using SQL."""
        if not columns:
            logger.error("Select at least one column")
            raise ValueError("Select at least one column")
        
        for column in columns:
            if column not in MOVIE_COLUMNS:
                logger.error(f"Unsupported column: {column}")
                raise ValueError(f"Unsupported column: {column}")
        selected_columns = ", ".join(["id"] + columns)
        connection = get_connection(self.db_path)
        
        try:
            cols = connection.execute(f"SELECT {selected_columns} FROM movies WHERE rating >= ? ORDER BY rating DESC, id ASC LIMIT ?",(min_rating, limit,))
            rows = cols.fetchall()
            dictlist = [dict(row) for row in rows]
            logger.debug(f"Selected columns: {selected_columns}, rows={len(dictlist)}")
            return dictlist
        finally:
            connection.close()