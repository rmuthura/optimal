"""
Circadian rhythm calculations for insulin sensitivity and cortisol patterns.

Based on: Poggiogalle et al. (2018) "Circadian regulation of glucose, lipid,
and energy metabolism in humans"
"""

from datetime import datetime, time, timedelta
from typing import Union


def time_to_datetime(t: time, base_date: datetime = None) -> datetime:
    """Convert a time object to datetime using today's date or provided base."""
    if base_date is None:
        base_date = datetime.now()
    return datetime.combine(base_date.date(), t)


def hours_since_waking(wake_time: time, current_time: time) -> float:
    """
    Calculate hours elapsed since waking.

    Handles cases where current_time might be past midnight (next day).
    """
    wake_dt = time_to_datetime(wake_time)
    current_dt = time_to_datetime(current_time)

    # If current time is before wake time, assume it's the next day
    if current_dt < wake_dt:
        current_dt += timedelta(days=1)

    delta = current_dt - wake_dt
    return delta.total_seconds() / 3600


def get_insulin_sensitivity(wake_time: time, meal_time: time) -> float:
    """
    Calculate insulin sensitivity score (0-1) based on circadian rhythm.

    Insulin sensitivity follows a predictable pattern based on wake time:
    - 0-2 hours post-wake: High (0.9)
    - 2-6 hours post-wake: Peak (1.0)
    - 6-10 hours post-wake: Moderate (0.7)
    - 10-14 hours post-wake: Low (0.5)
    - 14+ hours post-wake: Very Low (0.3)

    Args:
        wake_time: User's wake time
        meal_time: Time of the meal

    Returns:
        Insulin sensitivity score between 0.3 and 1.0
    """
    hours = hours_since_waking(wake_time, meal_time)

    if hours < 0:
        # Before waking - shouldn't happen but handle gracefully
        return 0.3
    elif hours < 2:
        # Early morning - high sensitivity
        return 0.9
    elif hours < 6:
        # Mid-morning to early afternoon - peak sensitivity
        return 1.0
    elif hours < 10:
        # Afternoon - moderate sensitivity
        return 0.7
    elif hours < 14:
        # Evening - low sensitivity
        return 0.5
    else:
        # Late night - very low sensitivity
        return 0.3


def get_cortisol_level(wake_time: time, current_time: time) -> float:
    """
    Estimate relative cortisol level based on circadian rhythm.

    Cortisol follows a diurnal pattern:
    - Peaks 30-45 minutes after waking (Cortisol Awakening Response)
    - Gradually declines throughout the day
    - Lowest around midnight

    Args:
        wake_time: User's wake time
        current_time: Current time to check

    Returns:
        Relative cortisol level (0-1, where 1 is peak)
    """
    hours = hours_since_waking(wake_time, current_time)

    if hours < 0:
        return 0.2
    elif hours < 0.5:
        # Rising phase
        return 0.7 + (hours / 0.5) * 0.3
    elif hours < 1:
        # Peak phase (CAR)
        return 1.0
    elif hours < 4:
        # Rapid decline
        return 1.0 - ((hours - 1) / 3) * 0.4
    elif hours < 12:
        # Gradual decline
        return 0.6 - ((hours - 4) / 8) * 0.3
    else:
        # Low evening/night levels
        return 0.3


def get_carb_priority(insulin_sensitivity: float) -> str:
    """
    Get carbohydrate priority recommendation based on insulin sensitivity.

    Args:
        insulin_sensitivity: Score from get_insulin_sensitivity()

    Returns:
        String describing carb priority for this meal
    """
    if insulin_sensitivity >= 0.9:
        return "Best for carbs"
    elif insulin_sensitivity >= 0.7:
        return "Good for carbs"
    elif insulin_sensitivity >= 0.5:
        return "Moderate carbs"
    else:
        return "Minimize carbs"


def is_optimal_first_meal_window(wake_time: time, meal_time: time) -> bool:
    """
    Check if meal time falls within optimal first meal window (30-60 min post-wake).

    The first meal should be timed after the cortisol awakening response
    has peaked and begun to decline, typically 30-60 minutes after waking.
    """
    hours = hours_since_waking(wake_time, meal_time)
    return 0.5 <= hours <= 1.0
