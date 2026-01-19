"""
Muscle Protein Synthesis (MPS) calculations and protein distribution logic.

Based on:
- Schoenfeld & Aragon (2018) "How much protein can the body use in a single
  meal for muscle-building?"
- Trommelen & Van Loon (2016) "Pre-sleep protein ingestion to improve the
  skeletal muscle adaptive response to exercise training"
"""

from datetime import datetime, time, timedelta
from typing import Optional, Tuple


# Constants from literature
MIN_PROTEIN_PER_MEAL = 25  # grams - minimum to stimulate MPS
MAX_PROTEIN_PER_MEAL = 40  # grams - diminishing returns above this
LEUCINE_THRESHOLD = 2.5    # grams - minimum to maximally stimulate MPS
LEUCINE_PERCENTAGE = 0.085 # ~8.5% of protein from typical sources is leucine

# MPS timing windows (hours)
MPS_ELEVATION_DURATION = 24  # MPS elevated for 24-48 hours post-resistance training
MPS_PEAK_START = 1           # Peak MPS begins 1 hour post-workout
MPS_PEAK_END = 4             # Peak MPS ends 4 hours post-workout


def calculate_leucine_content(protein_g: int) -> float:
    """
    Estimate leucine content from protein amount.

    Typical protein sources contain ~8-10% leucine.
    Using 8.5% as a conservative average.
    """
    return protein_g * LEUCINE_PERCENTAGE


def meets_leucine_threshold(protein_g: int) -> bool:
    """Check if protein amount meets the leucine threshold for MPS stimulation."""
    return calculate_leucine_content(protein_g) >= LEUCINE_THRESHOLD


def get_optimal_protein_per_meal(daily_protein: int, num_meals: int) -> Tuple[int, int]:
    """
    Calculate optimal protein distribution per meal.

    Returns:
        Tuple of (base_protein_per_meal, max_protein_per_meal)
    """
    base = daily_protein // num_meals

    # Ensure minimum threshold is met
    if base < MIN_PROTEIN_PER_MEAL and daily_protein >= MIN_PROTEIN_PER_MEAL * num_meals:
        base = MIN_PROTEIN_PER_MEAL

    # Cap at diminishing returns threshold for planning
    max_per_meal = min(base + 15, MAX_PROTEIN_PER_MEAL + 10)

    return base, max_per_meal


def is_in_mps_peak_window(
    meal_time: time,
    workout_end_time: Optional[time]
) -> bool:
    """
    Check if meal falls within the MPS peak window (1-4 hours post-workout).

    Args:
        meal_time: Time of the meal
        workout_end_time: Time workout ended (None if rest day)

    Returns:
        True if meal is in peak MPS window
    """
    if workout_end_time is None:
        return False

    # Convert to datetime for calculation
    base = datetime.now().date()
    meal_dt = datetime.combine(base, meal_time)
    workout_dt = datetime.combine(base, workout_end_time)

    # Handle day boundary
    if meal_dt < workout_dt:
        meal_dt += timedelta(days=1)

    hours_post = (meal_dt - workout_dt).total_seconds() / 3600

    return MPS_PEAK_START <= hours_post <= MPS_PEAK_END


def get_post_workout_protein_boost(
    base_protein: int,
    is_post_workout: bool,
    workout_type: Optional[str] = None
) -> int:
    """
    Calculate protein amount for post-workout meal.

    Post-workout meal should have +30% protein to maximize MPS response.

    Args:
        base_protein: Base protein allocation
        is_post_workout: Whether this is the post-workout meal
        workout_type: Type of workout (lifting gets higher boost)

    Returns:
        Adjusted protein amount
    """
    if not is_post_workout:
        return base_protein

    # 30% boost for post-workout
    boost_factor = 1.30

    # Slightly higher for lifting vs cardio
    if workout_type == "lifting":
        boost_factor = 1.35
    elif workout_type == "hybrid":
        boost_factor = 1.32

    boosted = int(base_protein * boost_factor)

    # Cap at reasonable maximum (50g for post-workout)
    return min(boosted, 50)


def get_pre_sleep_protein_recommendation(
    base_protein: int,
    hours_until_sleep: float
) -> Tuple[int, str]:
    """
    Get protein recommendation for pre-sleep meal.

    Pre-sleep protein supports overnight MPS. Casein or slow-digesting
    protein is ideal but any protein source is beneficial.

    Args:
        base_protein: Base protein allocation
        hours_until_sleep: Hours between meal and sleep

    Returns:
        Tuple of (recommended_protein, reasoning)
    """
    if hours_until_sleep <= 3:
        # Close to bedtime - moderate protein, supports overnight MPS
        protein = min(base_protein + 5, 40)
        reason = "Moderate protein to support overnight MPS without disrupting sleep"
    else:
        protein = base_protein
        reason = "Standard protein allocation"

    return protein, reason


def calculate_mps_score(
    meal_time: time,
    workout_end_time: Optional[time],
    sleep_time: time,
    wake_time: time
) -> float:
    """
    Calculate an MPS optimization score for a given meal time.

    Higher scores indicate better timing for protein synthesis.

    Args:
        meal_time: Proposed meal time
        workout_end_time: When workout ends (None if rest day)
        sleep_time: Bedtime
        wake_time: Wake time

    Returns:
        Score from 0-1, higher is better for MPS
    """
    score = 0.5  # Base score

    # Bonus for post-workout window
    if is_in_mps_peak_window(meal_time, workout_end_time):
        score += 0.3

    # Check if it's a pre-sleep meal (supports overnight MPS)
    base = datetime.now().date()
    meal_dt = datetime.combine(base, meal_time)
    sleep_dt = datetime.combine(base, sleep_time)

    if sleep_dt < meal_dt:
        sleep_dt += timedelta(days=1)

    hours_to_sleep = (sleep_dt - meal_dt).total_seconds() / 3600

    if 2 <= hours_to_sleep <= 3:
        score += 0.1  # Good pre-sleep timing

    # Penalty for very early (within 30 min of waking) - cortisol still high
    wake_dt = datetime.combine(base, wake_time)
    if meal_dt < wake_dt:
        meal_dt += timedelta(days=1)

    hours_since_wake = (meal_dt - wake_dt).total_seconds() / 3600
    if hours_since_wake < 0.5:
        score -= 0.1

    return max(0, min(1, score))
