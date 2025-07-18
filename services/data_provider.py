# your_bot_project/services/data_provider.py

import logging
from tvDatafeed import TvDatafeed, Interval
from .data_cache import DataCache

logger = logging.getLogger(__name__)

class TradingViewDataProvider:
    """
    A class to handle all interactions with the TradingView data feed.
    """
    _instance = None  # Class-level instance for the singleton pattern

    def __new__(cls, username=None, password=None, cache: DataCache = None):
        """
        Singleton pattern to ensure only one instance of TvDatafeed is logged in.
        This prevents multiple login attempts.
        """
        if cls._instance is None:
            cls._instance = super(TradingViewDataProvider, cls).__new__(cls)
            cls._instance.tv = None
            cls._instance.cache = cache
            if username and password:
                logger.info("TradingView credentials provided. Attempting to log in...")
                try:
                    cls._instance.tv = TvDatafeed(username, password)
                    logger.info("Successfully logged into TradingView.")
                except Exception as e:
                    logger.error(f"Failed to log into TradingView: {e}", exc_info=True)
                    cls._instance.tv = None # Ensure instance is None on failure
            else:
                logger.warning("TradingView credentials not provided. Data fetching will likely fail.")
                # Corrected guest session call. The `chromedriver_path` argument is deprecated.
                cls._instance.tv = TvDatafeed() # Guest session
        return cls._instance

    def get_historical_data(self, symbol: str, exchange: str, interval: Interval, n_bars: int):
        """
        Fetches historical data for a given symbol.

        Args:
            symbol (str): The asset symbol (e.g., "NQ1!").
            exchange (str): The exchange code (e.g., "CME_MINI").
            interval (Interval): The time interval (e.g., Interval.in_1_hour).
            n_bars (int): The number of bars to fetch.

        Returns:
            A pandas DataFrame with the data, or None if fetching fails.
        """
        # 1. First, try to get data from cache
        cached_data = None
        if self.cache:
            cached_data = self.cache.get_data(symbol, exchange, interval.value, n_bars)
            if cached_data is not None and len(cached_data) >= n_bars:
                logger.info(f"Full data for {symbol} found in cache. Skipping API call.")
                return cached_data

        # 2. If cache is not sufficient, fetch from the API
        if self.tv is None:
            logger.error("TvDatafeed instance is not available or login failed. Cannot fetch data.")
            return None

        try:
            logger.info(f"Fetching {n_bars} bars for {symbol} from TradingView API...")
            data = self.tv.get_hist(symbol=symbol, exchange=exchange, interval=interval, n_bars=n_bars)

            if data is None or data.empty:
                logger.warning(f"No data returned for {symbol} on {exchange}.")
                return None

            logger.info(f"Successfully fetched {len(data)} bars for {symbol}.")

            # 3. Save the newly fetched data to the cache for future use
            if self.cache and not data.empty:
                self.cache.save_data(data, symbol, exchange, interval.value)

            return data

        except Exception as e:
            logger.error(f"An error occurred while fetching data for {symbol}: {e}", exc_info=True)
            return None