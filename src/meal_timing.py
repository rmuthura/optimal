"""
Meal timing algorithm - calculates anchor points and distributes meals.

Implements the core scheduling logic based on:
- Kerksick et al. (2017) "ISSN position stand: nutrient timing"
"""

from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .models import UserInputs, MealType


@dataclass
class AnchorPoint:
    """Represents a fixed time point that meals should be scheduled around."""
    time: time
    meal_type: MealType
    priority: int  # Higher = more important to keep


def time_to_minutes(t: time) -> int:
    """Convert time to minutes since midnight."""
    return t.hour * 60 + t.minute


def minutes_to_time(minutes: int) -> time:
    """Convert minutes since midnight to time object."""
    # Handle wrap-around past midnight
    minutes = minutes % (24 * 60)
    return time(hour=minutes // 60, minute=minutes % 60)


def add_minutes_to_time(t: time, minutes: int) -> time:
    """Add minutes to a time, handling day wrap-around."""
    total_minutes = time_to_minutes(t) + minutes
    return minutes_to_time(total_minutes)


def time_difference_minutes(t1: time, t2: time) -> int:
    """
    Calculate minutes between two times.

    Returns positive if t2 is after t1 (same day assumption for small differences).
    """
    m1 = time_to_minutes(t1)
    m2 = time_to_minutes(t2)

    diff = m2 - m1

    # If difference is very negative, assume t2 is next day
    if diff < -12 * 60:
        diff += 24 * 60

    return diff


def calculate_anchor_points(user: UserInputs) -> Dict[str, AnchorPoint]:
    """
    Calculate fixed anchor points for meal scheduling.

    Anchor points:
    1. First meal: 30-60 minutes after wake (cortisol clearing)
    2. Last meal: 2.5-3 hours before sleep (digestion, sleep quality)
    3. Pre-workout: 1.5-2 hours before workout (gastric emptying)
    4. Post-workout: 60-90 minutes after workout end (MPS peak)

    Args:
        user: User input parameters

    Returns:
        Dictionary of anchor points by type
    """
    anchors = {}

    # First meal: 45 minutes after waking (middle of 30-60 range)
    first_meal_time = add_minutes_to_time(user.wake_time, 45)
    anchors["first_meal"] = AnchorPoint(
        time=first_meal_time,
        meal_type=MealType.BREAKFAST,
        priority=3
    )

    # Last meal: 2.75 hours before sleep (middle of 2.5-3 range)
    last_meal_time = add_minutes_to_time(user.sleep_time, -165)  # -2hr 45min
    anchors["last_meal"] = AnchorPoint(
        time=last_meal_time,
        meal_type=MealType.DINNER,
        priority=3
    )

    # Workout-related anchors
    if user.workout_time:
        # Pre-workout: 1.75 hours before (middle of 1.5-2 range)
        pre_workout_time = add_minutes_to_time(user.workout_time, -105)
        anchors["pre_workout"] = AnchorPoint(
            time=pre_workout_time,
            meal_type=MealType.PRE_WORKOUT,
            priority=4
        )

        # Post-workout: 75 minutes after workout end
        workout_end = add_minutes_to_time(user.workout_time, user.workout_duration_min)
        post_workout_time = add_minutes_to_time(workout_end, 75)
        anchors["post_workout"] = AnchorPoint(
            time=post_workout_time,
            meal_type=MealType.POST_WORKOUT,
            priority=5  # Highest priority
        )

    return anchors


def get_available_window(user: UserInputs) -> Tuple[time, time]:
    """Get the eating window (first possible to last possible meal time)."""
    first_possible = add_minutes_to_time(user.wake_time, 30)
    last_possible = add_minutes_to_time(user.sleep_time, -120)
    return first_possible, last_possible


def distribute_meals(
    user: UserInputs,
    anchors: Dict[str, AnchorPoint]
) -> List[Tuple[time, MealType]]:
    """
    Distribute meals across the day, respecting anchor points and constraints.

    Constraints:
    - Minimum 2.5 hours between meals (150 minutes)
    - Maximum 5 hours between meals (300 minutes)
    - Must fit within eating window

    Args:
        user: User input parameters
        anchors: Calculated anchor points

    Returns:
        List of (time, meal_type) tuples, sorted by time
    """
    MIN_GAP = 150  # 2.5 hours minimum between meals
    MAX_GAP = 300  # 5 hours maximum between meals

    # Start with anchor points
    meals: List[Tuple[time, MealType, int]] = []  # (time, type, priority)

    for anchor in anchors.values():
        meals.append((anchor.time, anchor.meal_type, anchor.priority))

    # Sort by time
    meals.sort(key=lambda x: time_to_minutes(x[0]))

    # Determine how many more meals we need
    current_count = len(meals)
    needed = user.num_meals - current_count

    if needed <= 0:
        # We have enough or too many anchors
        # If too many, keep highest priority ones
        if needed < 0:
            meals.sort(key=lambda x: -x[2])  # Sort by priority descending
            meals = meals[:user.num_meals]
            meals.sort(key=lambda x: time_to_minutes(x[0]))  # Re-sort by time

        return [(m[0], m[1]) for m in meals]

    # Find gaps and insert meals
    window_start, window_end = get_available_window(user)

    for _ in range(needed):
        # Find the largest gap
        largest_gap = 0
        insert_idx = 0
        insert_time = None

        # Check gap before first meal
        first_time = meals[0][0] if meals else window_end
        gap_before = time_difference_minutes(window_start, first_time)
        if gap_before > largest_gap and gap_before >= MIN_GAP * 2:
            largest_gap = gap_before
            insert_idx = 0
            insert_time = add_minutes_to_time(window_start, gap_before // 2)

        # Check gaps between meals
        for i in range(len(meals) - 1):
            gap = time_difference_minutes(meals[i][0], meals[i + 1][0])
            if gap > largest_gap and gap >= MIN_GAP * 2:
                largest_gap = gap
                insert_idx = i + 1
                # Insert at midpoint
                mid_minutes = time_to_minutes(meals[i][0]) + gap // 2
                insert_time = minutes_to_time(mid_minutes)

        # Check gap after last meal
        if meals:
            last_time = meals[-1][0]
            gap_after = time_difference_minutes(last_time, window_end)
            if gap_after > largest_gap and gap_after >= MIN_GAP * 2:
                largest_gap = gap_after
                insert_idx = len(meals)
                insert_time = add_minutes_to_time(last_time, gap_after // 2)

        # Insert the meal if we found a valid spot
        if insert_time:
            # Determine meal type based on time
            meal_type = _determine_meal_type(insert_time, user, meals)
            meals.insert(insert_idx, (insert_time, meal_type, 1))

    # Final sort and return
    meals.sort(key=lambda x: time_to_minutes(x[0]))
    return [(m[0], m[1]) for m in meals]


def _determine_meal_type(
    meal_time: time,
    user: UserInputs,
    existing_meals: List[Tuple[time, MealType, int]]
) -> MealType:
    """Determine the type of meal based on time of day."""
    hours_since_wake = time_difference_minutes(user.wake_time, meal_time) / 60

    existing_types = {m[1] for m in existing_meals}

    if hours_since_wake < 4 and MealType.BREAKFAST not in existing_types:
        return MealType.BREAKFAST
    elif hours_since_wake < 8 and MealType.LUNCH not in existing_types:
        return MealType.LUNCH
    elif hours_since_wake > 10 and MealType.DINNER not in existing_types:
        return MealType.DINNER
    else:
        return MealType.SNACK


def validate_meal_schedule(
    meals: List[Tuple[time, MealType]],
    user: UserInputs
) -> List[str]:
    """
    Validate the meal schedule against constraints.

    Returns list of any violations found.
    """
    violations = []
    MIN_GAP = 150
    MAX_GAP = 300

    # Check gaps between meals
    for i in range(len(meals) - 1):
        gap = time_difference_minutes(meals[i][0], meals[i + 1][0])

        if gap < MIN_GAP:
            violations.append(
                f"Meals {i + 1} and {i + 2} are too close "
                f"({gap} min, minimum is {MIN_GAP})"
            )
        if gap > MAX_GAP:
            violations.append(
                f"Gap between meals {i + 1} and {i + 2} is too large "
                f"({gap} min, maximum is {MAX_GAP})"
            )

    # Check no meals within 2 hours of sleep
    for i, (meal_time, _) in enumerate(meals):
        mins_to_sleep = time_difference_minutes(meal_time, user.sleep_time)
        if 0 < mins_to_sleep < 120:
            violations.append(
                f"Meal {i + 1} is within 2 hours of sleep time"
            )

    # Check no meals within 30 min of workout
    if user.workout_time:
        for i, (meal_time, meal_type) in enumerate(meals):
            mins_to_workout = time_difference_minutes(meal_time, user.workout_time)
            if 0 < mins_to_workout < 30:
                violations.append(
                    f"Meal {i + 1} is within 30 minutes of workout start"
                )

    return violations


def get_workout_end_time(user: UserInputs) -> Optional[time]:
    """Calculate workout end time from start time and duration."""
    if not user.workout_time:
        return None
    return add_minutes_to_time(user.workout_time, user.workout_duration_min)
