"""
Flask web application for Chrono-Nutrition Meal Scheduler.
"""

import os
import sys
from flask import Flask, render_template, request, jsonify

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scheduler import generate_schedule
from src.notifier import TelegramNotifier, ScheduledNotifier
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Global scheduler instance for notifications
scheduled_notifier = None


@app.route("/")
def index():
    """Render the main form page."""
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    """Generate a meal schedule from form inputs."""
    try:
        data = request.get_json()

        # Parse form data
        user_data = {
            "wake_time": data.get("wake_time", "07:00"),
            "sleep_time": data.get("sleep_time", "23:00"),
            "workout_time": data.get("workout_time") or None,
            "workout_type": data.get("workout_type") or None,
            "workout_duration_min": int(data.get("workout_duration", 60)),
            "daily_calories": int(data.get("calories", 2500)),
            "daily_protein_g": int(data.get("protein", 180)),
            "daily_carbs_g": int(data.get("carbs")) if data.get("carbs") else None,
            "daily_fat_g": int(data.get("fat")) if data.get("fat") else None,
            "num_meals": int(data.get("num_meals", 4)),
            "goal": data.get("goal", "maintenance")
        }

        schedule = generate_schedule(user_data)

        # Format response
        meals = []
        for meal in schedule.meals:
            meals.append({
                "number": meal.meal_number,
                "time": meal.time_str,
                "time_24h": meal.time_24h,
                "type": meal.meal_type.value.replace("_", " ").title(),
                "calories": meal.calories,
                "protein": meal.protein_g,
                "carbs": meal.carbs_g,
                "fat": meal.fat_g,
                "reasoning": meal.reasoning
            })

        return jsonify({
            "success": True,
            "meals": meals,
            "totals": {
                "calories": schedule.total_calories,
                "protein": schedule.total_protein,
                "carbs": schedule.total_carbs,
                "fat": schedule.total_fat
            }
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400


@app.route("/start-notifications", methods=["POST"])
def start_notifications():
    """Start Telegram notifications for the generated schedule."""
    global scheduled_notifier

    try:
        data = request.get_json()

        # Generate schedule
        user_data = {
            "wake_time": data.get("wake_time", "07:00"),
            "sleep_time": data.get("sleep_time", "23:00"),
            "workout_time": data.get("workout_time") or None,
            "workout_type": data.get("workout_type") or None,
            "workout_duration_min": int(data.get("workout_duration", 60)),
            "daily_calories": int(data.get("calories", 2500)),
            "daily_protein_g": int(data.get("protein", 180)),
            "daily_carbs_g": int(data.get("carbs")) if data.get("carbs") else None,
            "daily_fat_g": int(data.get("fat")) if data.get("fat") else None,
            "num_meals": int(data.get("num_meals", 4)),
            "goal": data.get("goal", "maintenance")
        }

        schedule = generate_schedule(user_data)

        # Initialize notifier
        notifier = TelegramNotifier.from_env()
        scheduled_notifier = ScheduledNotifier(notifier)

        # Send daily schedule overview
        notifier.send_daily_schedule(schedule)

        # Schedule individual meal notifications
        scheduled_notifier.schedule_meals(schedule)

        return jsonify({
            "success": True,
            "message": f"Scheduled {len(schedule.meals)} meal notifications"
        })

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": f"Configuration error: {str(e)}"
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/test-telegram", methods=["POST"])
def test_telegram():
    """Test the Telegram connection."""
    try:
        notifier = TelegramNotifier.from_env()
        success = notifier.test_connection()

        if success:
            return jsonify({
                "success": True,
                "message": "Test notification sent!"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to send notification"
            }), 500

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400


if __name__ == "__main__":
    app.run(debug=True, port=5000)
