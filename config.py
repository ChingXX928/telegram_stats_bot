# your_bot_project/config.py (更新版)

import os
from zoneinfo import ZoneInfo

# from dotenv import load_dotenv # 如果在本地端運行，取消註解此行
# load_dotenv()

# --- Secrets Configuration ---
def get_secret(key, default=None):
    """
    Tries to get a secret from an environment variable first. If not found,
    falls back to Colab userdata. This is more robust for shell execution.
    """
    # 1. 優先從環境變數讀取
    value = os.environ.get(key)
    if value:
        return value
    
    # 2. 如果環境變數中沒有，再嘗試從 Colab Secrets 讀取
    try:
        from google.colab import userdata
        return userdata.get(key)
    except (ImportError, NameError, AttributeError):
        # 如果不在 Colab 或 Colab Secrets 讀取失敗，回傳預設值
        return default

TELEGRAM_BOT_TOKEN = get_secret("TELEGRAM_BOT_TOKEN")
TRADINGVIEW_USERNAME = get_secret("TRADINGVIEW_USERNAME")
TRADINGVIEW_PASSWORD = get_secret("TRADINGVIEW_PASSWORD")


# --- Asset and Exchange Mapping ---
ASSET_EXCHANGE_MAP = {
    "NQ1!": "CME_MINI",
    "ES1!": "CME_MINI",
    "YM1!": "CME_MINI",
    "XAUUSD": "FX_IDC",
    "HK50": "PEPPERSTONE",
    "BTCUSDT": "BINANCE"
}

# --- Timezone Constant ---
NEW_YORK_TIMEZONE = ZoneInfo('America/New_York')

# --- State Constants for User Flow ---
class State:
    START = 0
    DAILY_STATS_ASSET_SELECTION = 1
    WEEKLY_STATS_ASSET_SELECTION = 2