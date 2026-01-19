#!/usr/bin/env python3
"""
Daily notification daemon.

This script runs continuously and sends Telegram notifications
at scheduled meal times.

Usage:
    python scripts/run_scheduler.py

Make sure to set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in your .env file.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.scheduler import generate_schedule
from src.notifier import TelegramNotifier, ScheduledNotifier


def main():
    # Customize your inputs here
    user_data = {
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

    print("Generating today's meal schedule...")
    schedule = generate_schedule(user_data)
    print(schedule)
    print()

    # Initialize notifier
    try:
        notifier = TelegramNotifier.from_env()
    except ValueError as e:
        print(f"Error: {e}")
        print("\nMake sure to set these environment variables:")
        print("  TELEGRAM_BOT_TOKEN=your_bot_token")
        print("  TELEGRAM_CHAT_ID=your_chat_id")
        sys.exit(1)

    # Send daily overview
    print("Sending daily schedule to Telegram...")
    if notifier.send_daily_schedule(schedule):
        print("Daily schedule sent!")
    else:
        print("Failed to send daily schedule")

    # Set up scheduled notifications
    scheduled_notifier = ScheduledNotifier(notifier)
    scheduled_notifier.schedule_meals(schedule)

    print(f"\nScheduled {len(schedule.meals)} meal notifications:")
    for meal in schedule.meals:
        print(f"  - {meal.time_24h}: Meal {meal.meal_number} ({meal.meal_type.value})")

    print("\nStarting scheduler daemon...")
    print("Press Ctrl+C to stop\n")

    # Run the scheduler loop
    scheduled_notifier.run()


if __name__ == "__main__":
    main()
