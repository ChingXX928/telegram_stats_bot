# your_bot_project/services/data_cache.py

import sqlite3
import pandas as pd
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DB_FILE = "data/historical_data.db"
TABLE_NAME = "klines"

class DataCache:
    """
    Manages a local SQLite cache for historical financial data.
    """
    def __init__(self, db_path: str = DB_FILE):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_table()
        logger.info(f"DataCache initialized with database at '{db_path}'.")

    def _create_table(self):
        """Creates the data table if it doesn't exist."""
        # A composite primary key prevents duplicate entries for the same candle.
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            symbol TEXT NOT NULL,
            exchange TEXT NOT NULL,
            interval TEXT NOT NULL,
            datetime TEXT NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            PRIMARY KEY (symbol, exchange, interval, datetime)
        );
        """
        self._conn.cursor().execute(create_table_query)
        self._conn.commit()

    def save_data(self, df: pd.DataFrame, symbol: str, exchange: str, interval_str: str):
        """Saves a DataFrame to the cache, ignoring duplicates."""
        if df.empty:
            return
        
        df_to_save = df.copy()
        df_to_save['symbol'] = symbol
        df_to_save['exchange'] = exchange
        df_to_save['interval'] = interval_str
        
        # Convert datetime index to a string column for SQLite compatibility
        df_to_save.index.name = 'datetime_index'
        df_to_save.reset_index(inplace=True)
        df_to_save.rename(columns={'datetime_index': 'datetime'}, inplace=True)
        df_to_save['datetime'] = df_to_save['datetime'].astype(str)

        try:
            # 'append' combined with the PRIMARY KEY ensures we only add new rows.
            df_to_save.to_sql(TABLE_NAME, self._conn, if_exists='append', index=False)
            logger.info(f"Saved/updated {len(df_to_save)} rows for {symbol} in cache.")
        except sqlite3.IntegrityError:
            logger.warning(f"Some duplicate data for {symbol} was ignored during save, which is expected.")
        except Exception as e:
            logger.error(f"Error saving data to cache: {e}", exc_info=True)

    def get_data(self, symbol: str, exchange: str, interval_str: str, n_bars: int) -> pd.DataFrame | None:
        """Retrieves the most recent N bars from the cache for a given asset."""
        query = f"""
        SELECT * FROM {TABLE_NAME}
        WHERE symbol = ? AND exchange = ? AND interval = ?
        ORDER BY datetime DESC
        LIMIT ?
        """
        try:
            df = pd.read_sql_query(query, self._conn, params=(symbol, exchange, interval_str, n_bars))
            if df.empty:
                return None
            
            # Convert back to a proper DataFrame structure
            df['datetime'] = pd.to_datetime(df['datetime'])
            df.set_index('datetime', inplace=True)
            df.sort_index(inplace=True)
            df.drop(columns=['symbol', 'exchange', 'interval'], inplace=True)

            logger.info(f"Loaded {len(df)} rows for {symbol} from cache.")
            return df
        except Exception as e:
            logger.error(f"Error retrieving data from cache: {e}", exc_info=True)
            return None

    def close(self):
        self._conn.close()
        logger.info("Database connection closed.")