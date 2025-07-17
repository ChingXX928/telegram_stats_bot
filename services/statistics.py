# your_bot_project/services/statistics.py

import logging
import pandas as pd
from datetime import datetime, timedelta
from config import NEW_YORK_TIMEZONE

logger = logging.getLogger(__name__)

def calculate_daily_stats(data: pd.DataFrame, days_n: int):
    """
    Calculates the hourly distribution of daily highs and lows.

    Args:
        data (pd.DataFrame): The raw historical data from the data provider.
        days_n (int): The number of days to look back for the analysis.

    Returns:
        A tuple containing:
        - high_counts (list[int]): A 24-element list with counts for high of the day.
        - low_counts (list[int]): A 24-element list with counts for low of the day.
        - processed_days (int): The actual number of unique days processed.
        Returns None if data is insufficient.
    """
    if data is None or data.empty:
        logger.warning("Daily stats calculation received no data.")
        return None

    # --- Timezone and Data Preparation ---
    if data.index.tz is None:
        data.index = data.index.tz_localize('UTC')
    data.index = data.index.tz_convert(NEW_YORK_TIMEZONE)
    logger.debug(f"Data index converted to '{NEW_YORK_TIMEZONE}' for daily stats.")

    data_reset = data.reset_index()
    data_reset.rename(columns={'datetime': 'Datetime'}, inplace=True)

    # --- Filtering for the exact N-day period in the specified timezone ---
    end_date_filter = datetime.now(NEW_YORK_TIMEZONE)
    start_date_filter = end_date_filter - timedelta(days=days_n)

    data_filtered = data_reset[
        (data_reset['Datetime'] >= start_date_filter) &
        (data_reset['Datetime'] <= end_date_filter)
    ].copy()

    if data_filtered.empty:
        logger.warning(f"Insufficient data after filtering for the last {days_n} days.")
        return None

    data_filtered['DateOnly'] = data_filtered['Datetime'].dt.date
    
    high_point_hourly_counts = [0] * 24
    low_point_hourly_counts = [0] * 24

    unique_days_processed = data_filtered['DateOnly'].nunique()
    logger.info(f"Processing daily stats for {unique_days_processed} unique days.")

    # --- Calculation Loop ---
    for date_only, daily_data in data_filtered.groupby('DateOnly'):
        if daily_data.empty:
            continue

        daily_max_high = daily_data['high'].max()
        daily_min_low = daily_data['low'].min()

        # Find the first occurrence of the high and low
        high_hour_of_day = daily_data[daily_data['high'] == daily_max_high]['Datetime'].min().hour
        low_hour_of_day = daily_data[daily_data['low'] == daily_min_low]['Datetime'].min().hour
        
        logger.debug(f"Date: {date_only}, Daily High Hour: {high_hour_of_day}, Daily Low Hour: {low_hour_of_day}")

        if high_hour_of_day is not None:
            high_point_hourly_counts[high_hour_of_day] += 1
        if low_hour_of_day is not None:
            low_point_hourly_counts[low_hour_of_day] += 1
            
    return high_point_hourly_counts, low_point_hourly_counts, unique_days_processed


def calculate_weekly_stats(data: pd.DataFrame, weeks_n: int):
    """
    Calculates the weekday distribution of weekly highs and lows for N complete weeks.

    Args:
        data (pd.DataFrame): The raw historical data from the data provider.
        weeks_n (int): The number of complete weeks to analyze.

    Returns:
        A tuple containing:
        - high_counts (list[int]): A 7-element list with counts for high of the week.
        - low_counts (list[int]): A 7-element list with counts for low of the week.
        - processed_weeks (int): The actual number of unique weeks processed.
        Returns None if data is insufficient.
    """
    if data is None or data.empty:
        logger.warning("Weekly stats calculation received no data.")
        return None

    # --- Timezone and Data Preparation ---
    if data.index.tz is None:
        data.index = data.index.tz_localize('UTC')
    data.index = data.index.tz_convert(NEW_YORK_TIMEZONE)
    logger.debug(f"Data index converted to '{NEW_YORK_TIMEZONE}' for weekly stats.")

    data_reset = data.reset_index()
    data_reset.rename(columns={'datetime': 'Datetime'}, inplace=True)

    # --- Find the boundaries of the last N complete weeks ---
    today = datetime.now(NEW_YORK_TIMEZONE).date()
    # Find the end of the last complete week (last Sunday)
    end_of_last_full_week_date = today - timedelta(days=(today.weekday() + 1) % 7)
    end_of_last_full_week = datetime.combine(end_of_last_full_week_date, datetime.max.time()).replace(tzinfo=NEW_YORK_TIMEZONE)

    # Find the start of the N-week period (the Monday N-1 weeks before the start of the last full week)
    start_of_period_date = end_of_last_full_week_date - timedelta(weeks=weeks_n -1, days=6)
    start_of_period = datetime.combine(start_of_period_date, datetime.min.time()).replace(tzinfo=NEW_YORK_TIMEZONE)
    
    logger.info(f"Filtering for {weeks_n} full weeks from {start_of_period} to {end_of_last_full_week}")

    data_filtered = data_reset[
        (data_reset['Datetime'] >= start_of_period) &
        (data_reset['Datetime'] <= end_of_last_full_week)
    ].copy()

    if data_filtered.empty:
        logger.warning(f"No data after filtering for {weeks_n} full weeks.")
        return None

    # Use the Monday of the week as the unique week identifier
    data_filtered['WeekStart'] = data_filtered['Datetime'].dt.to_period('W-SUN').apply(lambda r: r.start_time).dt.date

    weekly_high_weekday_counts = [0] * 7  # Monday=0, Sunday=6
    weekly_low_weekday_counts = [0] * 7

    unique_weeks_processed = data_filtered['WeekStart'].nunique()
    logger.info(f"Processing weekly stats for {unique_weeks_processed} unique weeks.")
    
    # --- Calculation Loop ---
    for week_start_date, weekly_data in data_filtered.groupby('WeekStart'):
        if weekly_data.empty:
            continue

        weekly_max_high = weekly_data['high'].max()
        weekly_min_low = weekly_data['low'].min()
        
        # Find the first occurrence of the high and low
        high_day = weekly_data[weekly_data['high'] == weekly_max_high]['Datetime'].min()
        low_day = weekly_data[weekly_data['low'] == weekly_min_low]['Datetime'].min()

        high_weekday = high_day.weekday() # Monday=0, Sunday=6
        low_weekday = low_day.weekday()

        logger.debug(f"Week of {week_start_date}, High on: {high_weekday}, Low on: {low_weekday}")

        if high_weekday is not None:
            weekly_high_weekday_counts[high_weekday] += 1
        if low_weekday is not None:
            weekly_low_weekday_counts[low_weekday] += 1
            
    return weekly_high_weekday_counts, weekly_low_weekday_counts, unique_weeks_processed