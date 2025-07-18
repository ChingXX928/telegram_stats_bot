# your_bot_project/main.py (最終修正版)

import os
import logging
import nest_asyncio

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

# Import configurations and components
from config import TELEGRAM_BOT_TOKEN, TRADINGVIEW_USERNAME, TRADINGVIEW_PASSWORD, DATA_DIR
from services.data_provider import TradingViewDataProvider
from services.data_cache import DataCache
from bot.state_manager import StateManager
from bot.handlers import BotHandlers

# Apply nest_asyncio to allow asyncio to run in environments with an existing event loop (like Colab/Jupyter)
nest_asyncio.apply()

# --- Logging Configuration ---
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main() -> None:
    """
    The main function to initialize and run the Telegram bot.
    """
    # --- Pre-run Checks ---
    if not TELEGRAM_BOT_TOKEN:
        logger.critical("FATAL: TELEGRAM_BOT_TOKEN is not configured. The bot cannot start.")
        return
    if not TRADINGVIEW_USERNAME or not TRADINGVIEW_PASSWORD:
         logger.warning("WARNING: TradingView credentials are not fully set. Data fetching might fail.")

    # --- Environment Setup ---
    # Ensure the directory for databases or cache files exists.
    # This prevents the "unable to open database file" error in new/ephemeral environments like Colab.
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        logger.info(f"Ensured data directory exists at: ./{DATA_DIR}")
    except OSError as e:
        logger.critical(f"FATAL: Could not create data directory '{DATA_DIR}': {e}")
        return

    # --- Initialization of Core Components ---
    logger.info("Initializing core components...")
    state_manager = StateManager()
    data_cache = DataCache()
    data_provider = TradingViewDataProvider(TRADINGVIEW_USERNAME, TRADINGVIEW_PASSWORD, cache=data_cache)
    bot_handlers = BotHandlers(state_manager, data_provider)
    logger.info("Components initialized.")

    # --- Telegram Application Setup ---
    logger.info("Setting up Telegram application...")
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # --- Registering Handlers ---
    # Register all the handlers from the BotHandlers class
    application.add_handler(CommandHandler("start", bot_handlers.start))
    
    application.add_handler(CallbackQueryHandler(bot_handlers.start_daily_stats_callback, pattern='^start_daily_stats$'))
    application.add_handler(CallbackQueryHandler(bot_handlers.start_weekly_stats_callback, pattern='^start_weekly_stats$'))

    # 【修正】將一個複雜的正規表示式拆分成兩個更明確、更穩定的處理器。
    # 這樣能確保 'select_asset_daily:SYMBOL' 和 'select_asset_weekly:SYMBOL' 都被精準捕捉。
    # 原始的 `pattern='^select_asset_(daily|weekly):'` 匹配邏輯可能存在問題。
    application.add_handler(CallbackQueryHandler(bot_handlers.select_asset_callback, pattern=r'^select_asset_daily:'))
    application.add_handler(CallbackQueryHandler(bot_handlers.select_asset_callback, pattern=r'^select_asset_weekly:'))

    # Handler for text messages (for N days/weeks input)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot_handlers.handle_message))
    
    logger.info("All handlers registered.")

    # --- Start the Bot ---
    logger.info("Starting bot polling...")
    application.run_polling()
    logger.info("Bot has stopped.")


if __name__ == '__main__':
    main()