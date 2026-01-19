"""
Push notification system for meal reminders.

Supports Telegram Bot notifications with optional scheduling.
"""

import os
import time as time_module
from datetime import datetime, time
from typing import List, Optional
import requests
import schedule

from .models import ScheduledMeal, DaySchedule


class TelegramNotifier:
    """Send notifications via Telegram Bot API."""

    def __init__(self, bot_token: str, chat_id: str):
        """
        Initialize the Telegram notifier.

        Args:
            bot_token: Telegram Bot API token from @BotFather
            chat_id: Your Telegram chat ID
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    @classmethod
    def from_env(cls) -> "TelegramNotifier":
        """Create notifier from environment variables."""
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")

        if not bot_token or not chat_id:
            raise ValueError(
                "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in environment"
            )

        return cls(bot_token, chat_id)

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """
        Send a message via Telegram.

        Args:
            text: Message text (supports HTML formatting)
            parse_mode: "HTML" or "Markdown"

        Returns:
            True if sent successfully
        """
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except requests.RequestException as e:
            print(f"Failed to send Telegram message: {e}")
            return False

    def send_meal_notification(self, meal: ScheduledMeal) -> bool:
        """
        Send a meal reminder notification.

        Args:
            meal: The scheduled meal to notify about

        Returns:
            True if sent successfully
        """
        message = self._format_meal_message(meal)
        return self.send_message(message)

    def send_daily_schedule(self, schedule: DaySchedule) -> bool:
        """
        Send the complete daily schedule as a single message.

        Args:
            schedule: The full day's meal schedule

        Returns:
            True if sent successfully
        """
        message = self._format_schedule_message(schedule)
        return self.send_message(message)

    def _format_meal_message(self, meal: ScheduledMeal) -> str:
        """Format a single meal as a notification message."""
        meal_type_display = meal.meal_type.value.replace('_', ' ').title()

        return f"""🍽️ <b>MEAL {meal.meal_number}</b> — {meal.time_str}
<i>{meal_type_display}</i>

📊 <b>Targets:</b>
• Calories: {meal.calories}
• Protein: {meal.protein_g}g
• Carbs: {meal.carbs_g}g
• Fat: {meal.fat_g}g

🧬 <i>{meal.reasoning}</i>
"""

    def _format_schedule_message(self, schedule: DaySchedule) -> str:
        """Format the complete schedule as a message."""
        lines = ["📅 <b>TODAY'S MEAL SCHEDULE</b>\n"]

        for meal in schedule.meals:
            meal_type_display = meal.meal_type.value.replace('_', ' ').title()
            lines.append(
                f"<b>{meal.time_str}</b> - {meal_type_display}\n"
                f"  {meal.calories} cal | {meal.protein_g}g P | "
                f"{meal.carbs_g}g C | {meal.fat_g}g F\n"
            )

        lines.append(
            f"\n<b>Daily Totals:</b> {schedule.total_calories} cal | "
            f"{schedule.total_protein}g protein"
        )

        return "\n".join(lines)

    def test_connection(self) -> bool:
        """Test the Telegram connection with a simple message."""
        return self.send_message("✅ Chrono-Nutrition notifications connected!")


class ScheduledNotifier:
    """Manage scheduled meal notifications."""

    def __init__(self, notifier: TelegramNotifier):
        """
        Initialize the scheduled notifier.

        Args:
            notifier: A TelegramNotifier instance
        """
        self.notifier = notifier
        self._scheduled_meals: List[ScheduledMeal] = []

    def schedule_meals(self, day_schedule: DaySchedule):
        """
        Schedule notifications for all meals in a day schedule.

        Args:
            day_schedule: The day's meal schedule
        """
        # Clear any existing scheduled jobs
        schedule.clear()
        self._scheduled_meals = day_schedule.meals.copy()

        for meal in day_schedule.meals:
            schedule.every().day.at(meal.time_24h).do(
                self._send_meal_notification,
                meal=meal
            )

        print(f"Scheduled {len(day_schedule.meals)} meal notifications")

    def _send_meal_notification(self, meal: ScheduledMeal):
        """Internal callback for scheduled notifications."""
        success = self.notifier.send_meal_notification(meal)
        if success:
            print(f"Sent notification for meal {meal.meal_number}")
        else:
            print(f"Failed to send notification for meal {meal.meal_number}")

    def run(self):
        """
        Run the scheduler loop.

        This will block and run continuously, checking for scheduled
        notifications every minute.
        """
        print("Starting notification scheduler...")
        print("Press Ctrl+C to stop")

        try:
            while True:
                schedule.run_pending()
                time_module.sleep(60)
        except KeyboardInterrupt:
            print("\nScheduler stopped")

    def run_once(self):
        """Run any pending scheduled tasks once (for testing)."""
        schedule.run_pending()


def send_test_notification():
    """Send a test notification using environment variables."""
    try:
        notifier = TelegramNotifier.from_env()
        success = notifier.test_connection()
        if success:
            print("Test notification sent successfully!")
        else:
            print("Failed to send test notification")
        return success
    except ValueError as e:
        print(f"Configuration error: {e}")
        return False
