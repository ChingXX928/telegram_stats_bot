# your_bot_project/reporting/formatters.py (依照您的舊版邏輯重製)

import logging
from datetime import datetime
from config import NEW_YORK_TIMEZONE

logger = logging.getLogger(__name__)

def format_daily_report(asset_code: str, days_n: int, high_counts: list, low_counts: list) -> str:
    """Generates a plain text report for daily stats, based on the original working code."""
    logger.info(f"Formatting PLAIN TEXT daily report for {asset_code}.")
    
    report_parts = []
    report_parts.append(f"📊 日內高低點統計報告 📊\n\n")
    report_parts.append(f"資產: {asset_code}\n")
    report_parts.append(f"統計天數: {days_n}\n")
    report_parts.append(f"數據時區: {NEW_YORK_TIMEZONE.tzname(datetime.now())} (美國/紐約)\n\n")

    total_high_points = sum(high_counts)
    total_low_points = sum(low_counts)

    # --- Highs Section ---
    report_parts.append("📈 日內高點創立小時統計:\n")
    high_data_for_display = []
    if total_high_points > 0:
        for hour, count in enumerate(high_counts):
            if count > 0:
                percentage = (count / total_high_points) * 100
                high_data_for_display.append((hour, count, percentage))
        high_data_for_display.sort(key=lambda x: x[1], reverse=True)

    max_stars_display = 15
    scaling_factor_high = 1
    if high_data_for_display and high_data_for_display[0][1] > max_stars_display:
        scaling_factor_high = high_data_for_display[0][1] / max_stars_display

    for hour, count, percentage in high_data_for_display:
        num_stars = int(count / scaling_factor_high)
        stars = '*' * num_stars
        report_parts.append(f"{hour:02d}:00: {stars} ({count} 次, {percentage:.1f}%)\n")
    report_parts.append("\n")

    # --- Lows Section ---
    report_parts.append("📉 日內低點創立小時統計:\n")
    low_data_for_display = []
    if total_low_points > 0:
        for hour, count in enumerate(low_counts):
            if count > 0:
                percentage = (count / total_low_points) * 100
                low_data_for_display.append((hour, count, percentage))
        low_data_for_display.sort(key=lambda x: x[1], reverse=True)
        
    scaling_factor_low = 1
    if low_data_for_display and low_data_for_display[0][1] > max_stars_display:
        scaling_factor_low = low_data_for_display[0][1] / max_stars_display

    for hour, count, percentage in low_data_for_display:
        num_stars = int(count / scaling_factor_low)
        stars = '*' * num_stars
        report_parts.append(f"{hour:02d}:00: {stars} ({count} 次, {percentage:.1f}%)\n")
    report_parts.append("\n")

    # --- Summary Section ---
    report_parts.append(f"---總結---\n")
    max_high_count = max(high_counts) if total_high_points > 0 else 0
    if max_high_count > 0:
        max_high_hours = [f'{h:02d}:00' for h, count in enumerate(high_counts) if count == max_high_count]
        report_parts.append(f"🚀 最常創立日內高點的時間是：{', '.join(max_high_hours)} (出現 {max_high_count} 次)\n")

    max_low_count = max(low_counts) if total_low_points > 0 else 0
    if max_low_count > 0:
        max_low_hours = [f'{h:02d}:00' for h, count in enumerate(low_counts) if count == max_low_count]
        report_parts.append(f"⬇️ 最常創立日內低點的時間是：{', '.join(max_low_hours)} (出現 {max_low_count} 次)\n")

    return "".join(report_parts)


def format_weekly_report(asset_code: str, weeks_n: int, high_counts: list, low_counts: list) -> str:
    """Generates a plain text report for weekly stats, based on the original working code."""
    logger.info(f"Formatting PLAIN TEXT weekly report for {asset_code}.")
    
    weekday_names = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    report_parts = []
    report_parts.append(f"📊 每週高低點統計報告 📊\n\n")
    report_parts.append(f"資產: {asset_code}\n")
    report_parts.append(f"統計週數: {weeks_n}\n")
    report_parts.append(f"數據時區: {NEW_YORK_TIMEZONE.tzname(datetime.now())} (美國/紐約)\n\n")

    total_high_points = sum(high_counts)
    total_low_points = sum(low_counts)

    # --- Highs Section ---
    report_parts.append("📈 每週高點創立星期統計:\n")
    high_data_for_display = []
    if total_high_points > 0:
        for i, count in enumerate(high_counts):
            if count > 0:
                percentage = (count / total_high_points) * 100
                high_data_for_display.append((i, count, percentage))
        high_data_for_display.sort(key=lambda x: x[1], reverse=True)
        
    max_stars_display = 15
    scaling_factor_high = 1
    if high_data_for_display and high_data_for_display[0][1] > max_stars_display:
        scaling_factor_high = high_data_for_display[0][1] / max_stars_display

    for weekday_idx, count, percentage in high_data_for_display:
        num_stars = int(count / scaling_factor_high)
        stars = '*' * num_stars
        report_parts.append(f"{weekday_names[weekday_idx]}: {stars} ({count} 次, {percentage:.1f}%)\n")
    report_parts.append("\n")

    # --- Lows Section ---
    report_parts.append("📉 每週低點創立星期統計:\n")
    low_data_for_display = []
    if total_low_points > 0:
        for i, count in enumerate(low_counts):
            if count > 0:
                percentage = (count / total_low_points) * 100
                low_data_for_display.append((i, count, percentage))
        low_data_for_display.sort(key=lambda x: x[1], reverse=True)

    scaling_factor_low = 1
    if low_data_for_display and low_data_for_display[0][1] > max_stars_display:
        scaling_factor_low = low_data_for_display[0][1] / max_stars_display

    for weekday_idx, count, percentage in low_data_for_display:
        num_stars = int(count / scaling_factor_low)
        stars = '*' * num_stars
        report_parts.append(f"{weekday_names[weekday_idx]}: {stars} ({count} 次, {percentage:.1f}%)\n")
    report_parts.append("\n")

    # --- Summary Section ---
    report_parts.append(f"---總結---\n")
    max_high_count = max(high_counts) if total_high_points > 0 else 0
    if max_high_count > 0:
        max_high_weekdays = [weekday_names[h] for h, count in enumerate(high_counts) if count == max_high_count]
        report_parts.append(f"🚀 最常創立每週高點的時間是：{', '.join(max_high_weekdays)} (出現 {max_high_count} 次)\n")

    max_low_count = max(low_counts) if total_low_points > 0 else 0
    if max_low_count > 0:
        max_low_weekdays = [weekday_names[h] for h, count in enumerate(low_counts) if count == max_low_count]
        report_parts.append(f"⬇️ 最常創立每週低點的時間是：{', '.join(max_low_weekdays)} (出現 {max_low_count} 次)\n")

    return "".join(report_parts)