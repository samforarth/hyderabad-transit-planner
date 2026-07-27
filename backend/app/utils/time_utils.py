"""
Time utility functions.

Handles GTFS specific time formats and standard time conversions.
"""

from datetime import datetime
from typing import Tuple

def parse_gtfs_time(time_str: str) -> Tuple[int, int, int]:
    """
    Parse a GTFS time string into hours, minutes, and seconds.
    
    GTFS allows times greater than 24:00:00 to represent trips that 
    continue past midnight (overnight trips) on the same operational day.
    For example, 25:30:00 means 1:30 AM the next day, but belonging to 
    the current day's service schedule.
    """
    parts = time_str.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = int(parts[2]) if len(parts) > 2 else 0
    return hours, minutes, seconds

def time_to_minutes(time_str: str) -> int:
    """
    Convert a 'HH:MM:SS' time string to total minutes since midnight.
    """
    h, m, s = parse_gtfs_time(time_str)
    return h * 60 + m

def minutes_to_display(minutes: int) -> str:
    """
    Convert a total minutes integer into a human-readable display string.
    E.g., 62 mins -> '1h 2m', or 45 mins -> '45 mins'
    """
    if minutes < 60:
        return f"{minutes} mins"
    hours = minutes // 60
    remaining_mins = minutes % 60
    return f"{hours}h {remaining_mins}m"

def time_difference_minutes(time1: str, time2: str) -> int:
    """
    Calculate the difference in minutes between two GTFS time strings.
    Returns (time1 - time2) in minutes.
    """
    mins1 = time_to_minutes(time1)
    mins2 = time_to_minutes(time2)
    return mins1 - mins2

def is_time_after(time1: str, time2: str) -> bool:
    """
    Check if time1 occurs after time2.
    """
    return time_to_minutes(time1) > time_to_minutes(time2)

def current_time_str() -> str:
    """
    Get the current time as a GTFS-compatible 'HH:MM:SS' string.
    """
    now = datetime.now()
    return now.strftime("%H:%M:%S")
