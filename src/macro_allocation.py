"""
Macro distribution across meals based on timing and biochemistry.

Implements intelligent macro allocation considering:
- Circadian insulin sensitivity for carb timing
- MPS windows for protein distribution
- Pre-workout fat reduction for gastric emptying
- Pre-sleep macro adjustments for sleep quality
"""

from datetime import time
from typing import List, Tuple, Optional
from dataclasses import dataclass

from .models import UserInputs, MealType
from .circadian import get_insulin_sensitivity, hours_since_waking
from .mps import (
    get_post_workout_protein_boost,
    MIN_PROTEIN_PER_MEAL,
    MAX_PROTEIN_PER_MEAL
)
from .meal_timing import time_difference_minutes, get_workout_end_time


@dataclass
class MealMacros:
    """Macro allocation for a single meal."""
    protein_g: int
    carbs_g: int
    fat_g: int
    calories: int

    @classmethod
    def calculate_calories(cls, protein: int, carbs: int, fat: int) -> int:
        """Calculate total calories from macros."""
        return protein * 4 + carbs * 4 + fat * 9


def allocate_macros(
    meal_times: List[Tuple[time, MealType]],
    user: UserInputs
) -> List[MealMacros]:
    """
    Distribute macros across meals based on timing and context.

    Algorithm:
    1. Calculate base allocation (daily / num_meals)
    2. Adjust protein for post-workout (+30%)
    3. Weight carbs by insulin sensitivity
    4. Reduce fat for pre-workout meals
    5. Adjust pre-sleep meal
    6. Normalize to hit daily targets

    Args:
        meal_times: List of (time, meal_type) tuples
        user: User input parameters

    Returns:
        List of MealMacros for each meal
    """
    num_meals = len(meal_times)
    workout_end = get_workout_end_time(user)

    # Step 1: Calculate base allocations
    base_protein = user.daily_protein_g / num_meals
    base_carbs = user.daily_carbs_g / num_meals
    base_fat = user.daily_fat_g / num_meals

    # Step 2: Calculate raw allocations with adjustments
    raw_allocations = []

    for meal_time, meal_type in meal_times:
        protein = base_protein
        carbs = base_carbs
        fat = base_fat

        # Get context
        insulin_sens = get_insulin_sensitivity(user.wake_time, meal_time)
        is_post_workout = meal_type == MealType.POST_WORKOUT
        is_pre_workout = meal_type == MealType.PRE_WORKOUT
        hours_to_sleep = time_difference_minutes(meal_time, user.sleep_time) / 60

        # Adjust protein for post-workout
        if is_post_workout and user.workout_type:
            protein = get_post_workout_protein_boost(
                int(base_protein),
                True,
                user.workout_type.value if user.workout_type else None
            )

        # Weight carbs by insulin sensitivity
        carbs = base_carbs * (insulin_sens / 0.7)  # Normalize around moderate

        # Pre-workout: reduce fat for gastric emptying
        if is_pre_workout:
            fat = base_fat * 0.5
            carbs = base_carbs * 1.2  # Slightly more carbs

        # Pre-sleep adjustments
        if 0 < hours_to_sleep <= 3:
            # Reduce carbs close to bed
            carbs = base_carbs * 0.6
            # Keep protein moderate for overnight MPS
            protein = min(protein, 35)
            # Fat is fine

        raw_allocations.append({
            'protein': protein,
            'carbs': carbs,
            'fat': fat,
            'meal_type': meal_type
        })

    # Step 3: Normalize to hit daily targets
    total_protein = sum(a['protein'] for a in raw_allocations)
    total_carbs = sum(a['carbs'] for a in raw_allocations)
    total_fat = sum(a['fat'] for a in raw_allocations)

    # Calculate scaling factors
    protein_scale = user.daily_protein_g / total_protein if total_protein > 0 else 1
    carbs_scale = user.daily_carbs_g / total_carbs if total_carbs > 0 else 1
    fat_scale = user.daily_fat_g / total_fat if total_fat > 0 else 1

    # Apply scaling and create final allocations
    final_allocations = []
    running_protein = 0
    running_carbs = 0
    running_fat = 0

    for i, alloc in enumerate(raw_allocations):
        is_last = i == len(raw_allocations) - 1

        if is_last:
            # Last meal gets remainder to hit exact targets
            protein = user.daily_protein_g - running_protein
            carbs = user.daily_carbs_g - running_carbs
            fat = user.daily_fat_g - running_fat
        else:
            protein = round(alloc['protein'] * protein_scale)
            carbs = round(alloc['carbs'] * carbs_scale)
            fat = round(alloc['fat'] * fat_scale)

        # Ensure minimum protein threshold
        protein = max(protein, MIN_PROTEIN_PER_MEAL)

        running_protein += protein
        running_carbs += carbs
        running_fat += fat

        calories = MealMacros.calculate_calories(protein, carbs, fat)

        final_allocations.append(MealMacros(
            protein_g=int(protein),
            carbs_g=int(carbs),
            fat_g=int(fat),
            calories=calories
        ))

    return final_allocations


def generate_meal_reasoning(
    meal_time: time,
    meal_type: MealType,
    user: UserInputs
) -> str:
    """
    Generate a brief biochemical explanation for the meal timing/composition.

    Args:
        meal_time: Time of the meal
        meal_type: Type of meal
        user: User parameters

    Returns:
        Human-readable reasoning string
    """
    reasons = []

    hours_since_wake = hours_since_waking(user.wake_time, meal_time)
    insulin_sens = get_insulin_sensitivity(user.wake_time, meal_time)
    hours_to_sleep = time_difference_minutes(meal_time, user.sleep_time) / 60

    # Time-based reasoning
    if hours_since_wake < 1.5:
        reasons.append("Post-wake cortisol clearing, high insulin sensitivity")
        reasons.append("Hit leucine threshold to kickstart MPS")
    elif insulin_sens >= 0.9:
        reasons.append("Peak circadian insulin sensitivity window")
        reasons.append("Optimal time for carbohydrate intake")
    elif insulin_sens >= 0.7:
        reasons.append("Good insulin sensitivity")
    elif insulin_sens <= 0.5:
        reasons.append("Lower insulin sensitivity, carbs minimized")

    # Workout-based reasoning
    if meal_type == MealType.PRE_WORKOUT:
        mins_to_workout = time_difference_minutes(meal_time, user.workout_time)
        reasons.append(f"{mins_to_workout}min pre-workout")
        reasons.append("Low fat for fast gastric emptying")
        reasons.append("Carbs to top off muscle glycogen")

    elif meal_type == MealType.POST_WORKOUT:
        reasons.append("MPS peak window (1-4hr post-workout)")
        reasons.append("Glycogen synthase elevated")
        reasons.append("Largest protein bolus for maximum MPS")

    # Pre-sleep reasoning
    if 0 < hours_to_sleep <= 3.5:
        reasons.append("Pre-sleep protein supports overnight MPS")
        if hours_to_sleep < 2.5:
            reasons.append("Reduced carbs to preserve sleep quality")

    # Limit to 2-3 reasons for readability
    if len(reasons) > 3:
        reasons = reasons[:3]

    return " ".join(reasons) if reasons else "Balanced meal timing"
