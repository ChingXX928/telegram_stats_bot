# your_bot_project/bot/handlers.py (最終修正版)

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import ContextTypes

from tvDatafeed import Interval

from bot.state_manager import StateManager
from services.data_provider import TradingViewDataProvider
import services.statistics as stats
import reporting.formatters as formatters
from config import ASSET_EXCHANGE_MAP, State

logger = logging.getLogger(__name__)

class BotHandlers:
    def __init__(self, state_manager: StateManager, data_provider: TradingViewDataProvider):
        self.state_manager = state_manager
        self.data_provider = data_provider

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        keyboard = [
            [InlineKeyboardButton("📈 日內高低點統計", callback_data='start_daily_stats')],
            [InlineKeyboardButton("🗓️ 每週高低點統計", callback_data='start_weekly_stats')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "哈囉！我是你的金融數據分析小幫手。\n"
            "我可以幫你統計資產的日內或每週高低點創立時間。\n\n"
            "請點擊下方按鈕開始：",
            reply_markup=reply_markup
        )

    async def _present_asset_selection(self, query, stats_type: str) -> None:
        asset_buttons = [
            InlineKeyboardButton(symbol, callback_data=f'select_asset_{stats_type}:{symbol}')
            for symbol in ASSET_EXCHANGE_MAP.keys()
        ]
        keyboard_rows = [asset_buttons[i:i + 3] for i in range(0, len(asset_buttons), 3)]
        reply_markup = InlineKeyboardMarkup(keyboard_rows)
        await query.edit_message_text("請選擇您想統計的資產：", reply_markup=reply_markup)

    async def start_daily_stats_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        self.state_manager.set_state(user_id, State.DAILY_STATS_ASSET_SELECTION)
        await self._present_asset_selection(query, 'daily')

    async def start_weekly_stats_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        self.state_manager.set_state(user_id, State.WEEKLY_STATS_ASSET_SELECTION)
        await self._present_asset_selection(query, 'weekly')

    async def select_asset_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        callback_type, asset_symbol = query.data.split(':', 1)
        self.state_manager.set_data(user_id, 'asset_symbol', asset_symbol)
        current_state = self.state_manager.get_state(user_id)
        if current_state == State.DAILY_STATS_ASSET_SELECTION:
            await query.edit_message_text(f"您已選擇資產：{asset_symbol}\n請輸入您想統計的天數 N（例如：30）：")
        elif current_state == State.WEEKLY_STATS_ASSET_SELECTION:
            await query.edit_message_text(f"您已選擇資產：{asset_symbol}\n請輸入您想統計的週數 N（例如：10）：")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        text = update.message.text
        current_state = self.state_manager.get_state(user_id)
        if current_state not in [State.DAILY_STATS_ASSET_SELECTION, State.WEEKLY_STATS_ASSET_SELECTION]:
            return
        try:
            n_value = int(text.strip())
            if n_value <= 0: raise ValueError("N must be positive")
        except ValueError:
            await update.message.reply_text("輸入無效，請輸入一個正整數。")
            return
        user_session_data = self.state_manager.get_data(user_id)
        asset_symbol = user_session_data.get('asset_symbol')
        exchange = ASSET_EXCHANGE_MAP.get(asset_symbol)
        if not asset_symbol or not exchange:
            await update.message.reply_text("系統錯誤，請重新 /start 開始。")
            self.state_manager.clear_state(user_id)
            return
        
        if current_state == State.DAILY_STATS_ASSET_SELECTION:
            await update.message.reply_text(f"收到！正在為 {asset_symbol} 獲取並分析最近 {n_value} 天的數據，請稍候...")
            raw_data = self.data_provider.get_historical_data(asset_symbol, exchange, Interval.in_1_hour, n_bars=n_value * 24 + 5)
            result = stats.calculate_daily_stats(raw_data, n_value) if raw_data is not None else None
            if result:
                high_counts, low_counts, days_processed = result
                report = formatters.format_daily_report(asset_symbol, days_processed, high_counts, low_counts)
                # 【修正】使用 parse_mode=None 來發送純文字報告
                await update.message.reply_text(report, parse_mode=None)
            else:
                await update.message.reply_text(f"抱歉，無法為 {asset_symbol} 獲取或分析數據。")
        elif current_state == State.WEEKLY_STATS_ASSET_SELECTION:
            await update.message.reply_text(f"收到！正在為 {asset_symbol} 獲取並分析最近 {n_value} 個完整週的數據，請稍候...")
            raw_data = self.data_provider.get_historical_data(asset_symbol, exchange, Interval.in_1_hour, n_bars=(n_value + 2) * 7 * 24)
            result = stats.calculate_weekly_stats(raw_data, n_value) if raw_data is not None else None
            if result:
                high_counts, low_counts, weeks_processed = result
                if weeks_processed > 0:
                    report = formatters.format_weekly_report(asset_symbol, weeks_processed, high_counts, low_counts)
                    # 【修正】使用 parse_mode=None 來發送純文字報告
                    await update.message.reply_text(report, parse_mode=None)
                else:
                    await update.message.reply_text(f"抱歉，在獲取的數據範圍內找不到足夠的完整週來進行統計。")
            else:
                await update.message.reply_text(f"抱歉，無法為 {asset_symbol} 獲取或分析數據。")
        self.state_manager.clear_state(user_id)