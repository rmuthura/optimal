"""
Calorie and macro calculator based on user stats and goals.

Uses Mifflin-St Jeor equation for BMR and activity multipliers for TDEE.
"""

from dataclasses import dataclass
from typing import Tuple, Optional
from enum import Enum


class Gender(Enum):
    MALE = "male"
    FEMALE = "female"


class ActivityLevel(Enum):
    SEDENTARY = "sedentary"           # Desk job, little exercise
    LIGHTLY_ACTIVE = "lightly_active"  # Light exercise 1-3 days/week
    MODERATELY_ACTIVE = "moderately_active"  # Moderate exercise 3-5 days/week
    VERY_ACTIVE = "very_active"        # Hard exercise 6-7 days/week
    EXTREMELY_ACTIVE = "extremely_active"  # Athlete, physical job + training


class Goal(Enum):
    LOSE_FAST = "lose_fast"       # Aggressive cut (-750 cal)
    LOSE = "lose"                 # Moderate cut (-500 cal)
    LOSE_SLOW = "lose_slow"       # Slow cut (-250 cal)
    MAINTAIN = "maintain"         # Maintenance
    GAIN_SLOW = "gain_slow"       # Lean bulk (+250 cal)
    GAIN = "gain"                 # Moderate bulk (+500 cal)
    GAIN_FAST = "gain_fast"       # Aggressive bulk (+750 cal)


# Activity level multipliers for TDEE
ACTIVITY_MULTIPLIERS = {
    ActivityLevel.SEDENTARY: 1.2,
    ActivityLevel.LIGHTLY_ACTIVE: 1.375,
    ActivityLevel.MODERATELY_ACTIVE: 1.55,
    ActivityLevel.VERY_ACTIVE: 1.725,
    ActivityLevel.EXTREMELY_ACTIVE: 1.9,
}

# Calorie adjustments for goals
GOAL_ADJUSTMENTS = {
    Goal.LOSE_FAST: -750,
    Goal.LOSE: -500,
    Goal.LOSE_SLOW: -250,
    Goal.MAINTAIN: 0,
    Goal.GAIN_SLOW: 250,
    Goal.GAIN: 500,
    Goal.GAIN_FAST: 750,
}

# Activity level descriptions
ACTIVITY_DESCRIPTIONS = {
    ActivityLevel.SEDENTARY: "Little or no exercise, desk job",
    ActivityLevel.LIGHTLY_ACTIVE: "Light exercise 1-3 days/week",
    ActivityLevel.MODERATELY_ACTIVE: "Moderate exercise 3-5 days/week",
    ActivityLevel.VERY_ACTIVE: "Hard exercise 6-7 days/week",
    ActivityLevel.EXTREMELY_ACTIVE: "Athlete or very physical job + daily training",
}


@dataclass
class UserStats:
    """Physical stats for calorie calculation."""
    weight_kg: float
    height_cm: float
    age: int
    gender: Gender
    activity_level: ActivityLevel
    goal: Goal
    body_fat_pct: Optional[float] = None  # Optional for more accurate calculations


@dataclass
class CalorieRecommendation:
    """Calculated calorie and macro recommendations."""
    bmr: int                    # Basal Metabolic Rate
    tdee: int                   # Total Daily Energy Expenditure
    target_calories: int        # Adjusted for goal
    protein_g: int
    carbs_g: int
    fat_g: int
    protein_pct: int
    carbs_pct: int
    fat_pct: int
    weekly_change_kg: float     # Expected weight change per week
    explanation: str


def calculate_bmr(stats: UserStats) -> float:
    """
    Calculate Basal Metabolic Rate using Mifflin-St Jeor equation.

    This is the most accurate formula for most people.

    Men: BMR = (10 × weight in kg) + (6.25 × height in cm) - (5 × age) + 5
    Women: BMR = (10 × weight in kg) + (6.25 × height in cm) - (5 × age) - 161
    """
    bmr = (10 * stats.weight_kg) + (6.25 * stats.height_cm) - (5 * stats.age)

    if stats.gender == Gender.MALE:
        bmr += 5
    else:
        bmr -= 161

    return bmr


def calculate_bmr_katch_mcardle(weight_kg: float, body_fat_pct: float) -> float:
    """
    Calculate BMR using Katch-McArdle formula (requires body fat %).

    More accurate if body fat percentage is known.
    BMR = 370 + (21.6 × lean body mass in kg)
    """
    lean_mass = weight_kg * (1 - body_fat_pct / 100)
    return 370 + (21.6 * lean_mass)


def calculate_tdee(bmr: float, activity_level: ActivityLevel) -> float:
    """Calculate Total Daily Energy Expenditure."""
    multiplier = ACTIVITY_MULTIPLIERS[activity_level]
    return bmr * multiplier


def calculate_macros(
    target_calories: int,
    weight_kg: float,
    goal: Goal
) -> Tuple[int, int, int]:
    """
    Calculate macro split based on goal.

    Protein: 1.6-2.2g per kg body weight depending on goal
    Fat: 20-35% of calories
    Carbs: Remainder

    Returns (protein_g, carbs_g, fat_g)
    """
    # Protein based on goal (higher when cutting to preserve muscle)
    if goal in [Goal.LOSE_FAST, Goal.LOSE]:
        protein_per_kg = 2.2
    elif goal == Goal.LOSE_SLOW:
        protein_per_kg = 2.0
    elif goal in [Goal.GAIN, Goal.GAIN_FAST]:
        protein_per_kg = 1.8
    else:
        protein_per_kg = 1.6

    protein_g = int(weight_kg * protein_per_kg)
    protein_calories = protein_g * 4

    # Fat based on goal (higher when cutting for hormones, lower when bulking for carb room)
    if goal in [Goal.LOSE_FAST, Goal.LOSE, Goal.LOSE_SLOW]:
        fat_pct = 0.30  # 30% of calories from fat
    elif goal in [Goal.GAIN_FAST, Goal.GAIN]:
        fat_pct = 0.22  # 22% of calories from fat
    else:
        fat_pct = 0.25  # 25% of calories from fat

    fat_calories = target_calories * fat_pct
    fat_g = int(fat_calories / 9)

    # Carbs are the remainder
    remaining_calories = target_calories - protein_calories - fat_calories
    carbs_g = max(0, int(remaining_calories / 4))

    return protein_g, carbs_g, fat_g


def get_recommendation(stats: UserStats) -> CalorieRecommendation:
    """
    Calculate full calorie and macro recommendation.

    Args:
        stats: User's physical stats and goals

    Returns:
        Complete recommendation with explanation
    """
    # Calculate BMR (use Katch-McArdle if body fat known)
    if stats.body_fat_pct:
        bmr = calculate_bmr_katch_mcardle(stats.weight_kg, stats.body_fat_pct)
    else:
        bmr = calculate_bmr(stats)

    # Calculate TDEE
    tdee = calculate_tdee(bmr, stats.activity_level)

    # Adjust for goal
    adjustment = GOAL_ADJUSTMENTS[stats.goal]
    target_calories = int(tdee + adjustment)

    # Minimum calorie floor for health
    min_calories = 1200 if stats.gender == Gender.FEMALE else 1500
    target_calories = max(target_calories, min_calories)

    # Calculate macros
    protein_g, carbs_g, fat_g = calculate_macros(
        target_calories, stats.weight_kg, stats.goal
    )

    # Calculate percentages
    total_macro_cals = (protein_g * 4) + (carbs_g * 4) + (fat_g * 9)
    protein_pct = int((protein_g * 4 / total_macro_cals) * 100)
    carbs_pct = int((carbs_g * 4 / total_macro_cals) * 100)
    fat_pct = int((fat_g * 9 / total_macro_cals) * 100)

    # Expected weekly change (3500 cal ≈ 0.45kg / 1lb)
    weekly_change_kg = (adjustment * 7) / 7700

    # Generate explanation
    explanation = _generate_explanation(
        stats, int(bmr), int(tdee), target_calories, adjustment, weekly_change_kg
    )

    return CalorieRecommendation(
        bmr=int(bmr),
        tdee=int(tdee),
        target_calories=target_calories,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fat_g=fat_g,
        protein_pct=protein_pct,
        carbs_pct=carbs_pct,
        fat_pct=fat_pct,
        weekly_change_kg=round(weekly_change_kg, 2),
        explanation=explanation
    )


def _generate_explanation(
    stats: UserStats,
    bmr: int,
    tdee: int,
    target: int,
    adjustment: int,
    weekly_change: float
) -> str:
    """Generate human-readable explanation of the calculation."""
    lines = []

    lines.append(f"Your BMR (calories burned at rest): {bmr} cal")
    lines.append(f"Your TDEE (with {stats.activity_level.value.replace('_', ' ')} activity): {tdee} cal")

    if adjustment < 0:
        lines.append(f"Deficit of {abs(adjustment)} cal/day for fat loss")
        lines.append(f"Expected loss: ~{abs(weekly_change):.1f} kg/week ({abs(weekly_change * 2.2):.1f} lbs)")
    elif adjustment > 0:
        lines.append(f"Surplus of {adjustment} cal/day for muscle gain")
        lines.append(f"Expected gain: ~{weekly_change:.1f} kg/week ({weekly_change * 2.2:.1f} lbs)")
    else:
        lines.append("Eating at maintenance to maintain weight")

    return " | ".join(lines)


def get_all_options(stats: UserStats) -> dict:
    """
    Calculate recommendations for all goal options.

    Useful for showing user different paths.
    """
    options = {}
    original_goal = stats.goal

    for goal in Goal:
        stats.goal = goal
        rec = get_recommendation(stats)
        options[goal.value] = {
            "calories": rec.target_calories,
            "protein": rec.protein_g,
            "carbs": rec.carbs_g,
            "fat": rec.fat_g,
            "weekly_change_kg": rec.weekly_change_kg,
            "label": _get_goal_label(goal)
        }

    stats.goal = original_goal
    return options


def _get_goal_label(goal: Goal) -> str:
    """Get human-readable label for goal."""
    labels = {
        Goal.LOSE_FAST: "Aggressive Cut (-0.75kg/week)",
        Goal.LOSE: "Moderate Cut (-0.5kg/week)",
        Goal.LOSE_SLOW: "Slow Cut (-0.25kg/week)",
        Goal.MAINTAIN: "Maintain Weight",
        Goal.GAIN_SLOW: "Lean Bulk (+0.25kg/week)",
        Goal.GAIN: "Moderate Bulk (+0.5kg/week)",
        Goal.GAIN_FAST: "Aggressive Bulk (+0.75kg/week)",
    }
    return labels.get(goal, goal.value)
