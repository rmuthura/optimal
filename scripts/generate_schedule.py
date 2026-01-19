#!/usr/bin/env python3
"""
One-off schedule generation script.

Usage:
    python scripts/generate_schedule.py

Edit the test_user dict below to customize your inputs.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scheduler import generate_schedule


def main():
    # Customize your inputs here
    test_user = {
        "wake_time": "07:00",
        "sleep_time": "23:00",
        "workout_time": "17:00",
        "workout_type": "lifting",
        "workout_duration_min": 60,
        "daily_calories": 2500,
        "daily_protein_g": 180,
        "daily_carbs_g": 280,
        "daily_fat_g": 70,
        "num_meals": 4,
        "goal": "muscle_gain"
    }

    print("Generating meal schedule...")
    print()

    schedule = generate_schedule(test_user)
    print(schedule)

    # Also print individual meal details
    print("\n" + "=" * 63)
    print("DETAILED BREAKDOWN")
    print("=" * 63)

    for meal in schedule.meals:
        print(f"\nMEAL {meal.meal_number} — {meal.time_str}")
        print(f"  Type: {meal.meal_type.value}")
        print(f"  {meal.calories} cal | {meal.protein_g}g P | {meal.carbs_g}g C | {meal.fat_g}g F")
        print(f"  → {meal.reasoning}")


if __name__ == "__main__":
    main()
