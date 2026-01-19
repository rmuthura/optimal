from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Optional, List
from enum import Enum


class WorkoutType(Enum):
    LIFTING = "lifting"
    CARDIO = "cardio"
    HYBRID = "hybrid"
    NONE = None


class Goal(Enum):
    MUSCLE_GAIN = "muscle_gain"
    FAT_LOSS = "fat_loss"
    MAINTENANCE = "maintenance"
    PERFORMANCE = "performance"


class MealType(Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    PRE_WORKOUT = "pre_workout"
    POST_WORKOUT = "post_workout"
    SNACK = "snack"


@dataclass
class UserInputs:
    wake_time: time
    sleep_time: time
    daily_calories: int
    daily_protein_g: int
    num_meals: int
    goal: Goal
    workout_time: Optional[time] = None
    workout_type: Optional[WorkoutType] = None
    workout_duration_min: int = 60
    daily_carbs_g: Optional[int] = None
    daily_fat_g: Optional[int] = None

    def __post_init__(self):
        # Auto-calculate macros if not provided
        if self.daily_carbs_g is None or self.daily_fat_g is None:
            protein_cals = self.daily_protein_g * 4
            remaining_cals = self.daily_calories - protein_cals

            # Default split: 50% carbs, 50% fat of remaining calories
            if self.goal == Goal.MUSCLE_GAIN:
                carb_ratio = 0.6
            elif self.goal == Goal.FAT_LOSS:
                carb_ratio = 0.4
            else:
                carb_ratio = 0.5

            if self.daily_carbs_g is None:
                self.daily_carbs_g = int((remaining_cals * carb_ratio) / 4)
            if self.daily_fat_g is None:
                self.daily_fat_g = int((remaining_cals * (1 - carb_ratio)) / 9)


@dataclass
class ScheduledMeal:
    meal_number: int
    time: datetime
    calories: int
    protein_g: int
    carbs_g: int
    fat_g: int
    reasoning: str
    meal_type: MealType

    @property
    def time_str(self) -> str:
        return self.time.strftime("%I:%M %p")

    @property
    def time_24h(self) -> str:
        return self.time.strftime("%H:%M")


@dataclass
class DaySchedule:
    meals: List[ScheduledMeal] = field(default_factory=list)
    user_inputs: Optional[UserInputs] = None

    @property
    def total_calories(self) -> int:
        return sum(m.calories for m in self.meals)

    @property
    def total_protein(self) -> int:
        return sum(m.protein_g for m in self.meals)

    @property
    def total_carbs(self) -> int:
        return sum(m.carbs_g for m in self.meals)

    @property
    def total_fat(self) -> int:
        return sum(m.fat_g for m in self.meals)

    def __str__(self) -> str:
        lines = [
            "═" * 63,
            "                    YOUR MEAL SCHEDULE",
            "═" * 63,
            ""
        ]

        for meal in self.meals:
            lines.append(f"MEAL {meal.meal_number} — {meal.time_str} ({meal.meal_type.value.replace('_', ' ').title()})")
            lines.append(f"├─ Calories: {meal.calories}")
            lines.append(f"├─ Protein: {meal.protein_g}g | Carbs: {meal.carbs_g}g | Fat: {meal.fat_g}g")
            lines.append(f"└─ Why: {meal.reasoning}")
            lines.append("")

        lines.append("═" * 63)
        lines.append(f"DAILY TOTALS: {self.total_calories} cal | {self.total_protein}g protein | {self.total_carbs}g carbs | {self.total_fat}g fat")
        lines.append("═" * 63)

        return "\n".join(lines)
