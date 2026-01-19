"""
Main scheduler module - orchestrates meal timing and macro allocation.

This is the primary interface for generating meal schedules.
"""

from datetime import datetime, time
from typing import Dict, Any, Optional

from .models import (
    UserInputs, ScheduledMeal, DaySchedule,
    WorkoutType, Goal, MealType
)
from .meal_timing import (
    calculate_anchor_points, distribute_meals,
    validate_meal_schedule
)
from .macro_allocation import allocate_macros, generate_meal_reasoning


def parse_time(time_str: str) -> time:
    """Parse a time string (HH:MM) to a time object."""
    if isinstance(time_str, time):
        return time_str
    parts = time_str.split(":")
    return time(hour=int(parts[0]), minute=int(parts[1]))


def parse_user_inputs(data: Dict[str, Any]) -> UserInputs:
    """
    Parse a dictionary of user inputs into a UserInputs object.

    Args:
        data: Dictionary with keys matching UserInputs fields

    Returns:
        Validated UserInputs object
    """
    # Parse times
    wake_time = parse_time(data["wake_time"])
    sleep_time = parse_time(data["sleep_time"])
    workout_time = parse_time(data["workout_time"]) if data.get("workout_time") else None

    # Parse enums
    workout_type = None
    if data.get("workout_type"):
        workout_type = WorkoutType(data["workout_type"])

    goal = Goal(data.get("goal", "maintenance"))

    return UserInputs(
        wake_time=wake_time,
        sleep_time=sleep_time,
        workout_time=workout_time,
        workout_type=workout_type,
        workout_duration_min=data.get("workout_duration_min", 60),
        daily_calories=data["daily_calories"],
        daily_protein_g=data["daily_protein_g"],
        daily_carbs_g=data.get("daily_carbs_g"),
        daily_fat_g=data.get("daily_fat_g"),
        num_meals=data.get("num_meals", 4),
        goal=goal
    )


def generate_schedule(user_data: Dict[str, Any]) -> DaySchedule:
    """
    Generate a complete meal schedule from user inputs.

    This is the main entry point for schedule generation.

    Args:
        user_data: Dictionary containing:
            - wake_time: str "HH:MM"
            - sleep_time: str "HH:MM"
            - workout_time: str "HH:MM" or None
            - workout_type: str "lifting"/"cardio"/"hybrid" or None
            - workout_duration_min: int
            - daily_calories: int
            - daily_protein_g: int
            - daily_carbs_g: int (optional)
            - daily_fat_g: int (optional)
            - num_meals: int (3-6)
            - goal: str "muscle_gain"/"fat_loss"/"maintenance"/"performance"

    Returns:
        DaySchedule object with complete meal plan
    """
    # Parse inputs
    user = parse_user_inputs(user_data)

    # Calculate anchor points (fixed meal times)
    anchors = calculate_anchor_points(user)

    # Distribute all meals across the day
    meal_times = distribute_meals(user, anchors)

    # Validate schedule
    violations = validate_meal_schedule(meal_times, user)
    if violations:
        # Log warnings but continue - real app might want to raise
        for v in violations:
            print(f"Warning: {v}")

    # Allocate macros to each meal
    macro_allocations = allocate_macros(meal_times, user)

    # Build scheduled meals with reasoning
    base_date = datetime.now()
    meals = []

    for i, ((meal_time, meal_type), macros) in enumerate(zip(meal_times, macro_allocations)):
        reasoning = generate_meal_reasoning(meal_time, meal_type, user)

        meal = ScheduledMeal(
            meal_number=i + 1,
            time=datetime.combine(base_date.date(), meal_time),
            calories=macros.calories,
            protein_g=macros.protein_g,
            carbs_g=macros.carbs_g,
            fat_g=macros.fat_g,
            reasoning=reasoning,
            meal_type=meal_type
        )
        meals.append(meal)

    return DaySchedule(meals=meals, user_inputs=user)


def generate_schedule_from_inputs(user: UserInputs) -> DaySchedule:
    """
    Generate schedule directly from a UserInputs object.

    Alternative entry point when inputs are already parsed.
    """
    # Calculate anchor points
    anchors = calculate_anchor_points(user)

    # Distribute meals
    meal_times = distribute_meals(user, anchors)

    # Allocate macros
    macro_allocations = allocate_macros(meal_times, user)

    # Build meals
    base_date = datetime.now()
    meals = []

    for i, ((meal_time, meal_type), macros) in enumerate(zip(meal_times, macro_allocations)):
        reasoning = generate_meal_reasoning(meal_time, meal_type, user)

        meal = ScheduledMeal(
            meal_number=i + 1,
            time=datetime.combine(base_date.date(), meal_time),
            calories=macros.calories,
            protein_g=macros.protein_g,
            carbs_g=macros.carbs_g,
            fat_g=macros.fat_g,
            reasoning=reasoning,
            meal_type=meal_type
        )
        meals.append(meal)

    return DaySchedule(meals=meals, user_inputs=user)
