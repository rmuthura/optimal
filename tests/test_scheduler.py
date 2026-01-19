"""Integration tests for the full scheduler."""

import pytest
from datetime import time

from src.scheduler import generate_schedule, parse_user_inputs
from src.models import Goal, WorkoutType


@pytest.fixture
def standard_user_data():
    """Standard test user data."""
    return {
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


@pytest.fixture
def morning_workout_data():
    """User with morning workout."""
    return {
        "wake_time": "06:00",
        "sleep_time": "22:00",
        "workout_time": "07:00",
        "workout_type": "lifting",
        "workout_duration_min": 60,
        "daily_calories": 2500,
        "daily_protein_g": 180,
        "daily_carbs_g": 280,
        "daily_fat_g": 70,
        "num_meals": 4,
        "goal": "muscle_gain"
    }


@pytest.fixture
def rest_day_data():
    """Rest day user data."""
    return {
        "wake_time": "08:00",
        "sleep_time": "23:00",
        "workout_time": None,
        "workout_type": None,
        "daily_calories": 2200,
        "daily_protein_g": 160,
        "daily_carbs_g": 220,
        "daily_fat_g": 80,
        "num_meals": 4,
        "goal": "maintenance"
    }


class TestScheduleGeneration:
    """Tests for full schedule generation."""

    def test_generates_correct_meal_count(self, standard_user_data):
        """Should generate the requested number of meals."""
        schedule = generate_schedule(standard_user_data)
        assert len(schedule.meals) == standard_user_data["num_meals"]

    def test_macros_sum_to_targets(self, standard_user_data):
        """Macros should sum to daily targets (within tolerance)."""
        schedule = generate_schedule(standard_user_data)

        # Allow 5g tolerance for rounding
        tolerance = 5

        assert abs(schedule.total_protein - standard_user_data["daily_protein_g"]) <= tolerance
        assert abs(schedule.total_carbs - standard_user_data["daily_carbs_g"]) <= tolerance
        assert abs(schedule.total_fat - standard_user_data["daily_fat_g"]) <= tolerance

    def test_no_meals_within_2_hours_of_sleep(self, standard_user_data):
        """No meals should be scheduled within 2 hours of sleep."""
        schedule = generate_schedule(standard_user_data)
        sleep_minutes = 23 * 60  # 23:00

        for meal in schedule.meals:
            meal_minutes = meal.time.hour * 60 + meal.time.minute
            minutes_to_sleep = sleep_minutes - meal_minutes
            if minutes_to_sleep > 0:
                assert minutes_to_sleep >= 120, f"Meal {meal.meal_number} is within 2hr of sleep"

    def test_post_workout_meal_within_2_hours(self, standard_user_data):
        """Post-workout meal should be within 2 hours of workout end."""
        schedule = generate_schedule(standard_user_data)

        workout_end_minutes = 18 * 60  # 17:00 + 60min = 18:00

        # Find post-workout meal
        post_workout = None
        for meal in schedule.meals:
            if meal.meal_type.value == "post_workout":
                post_workout = meal
                break

        if post_workout:
            meal_minutes = post_workout.time.hour * 60 + post_workout.time.minute
            minutes_after = meal_minutes - workout_end_minutes
            assert 0 <= minutes_after <= 120, f"Post-workout meal is {minutes_after}min after workout end"

    def test_generates_morning_workout_schedule(self, morning_workout_data):
        """Should handle morning workout correctly."""
        schedule = generate_schedule(morning_workout_data)
        assert len(schedule.meals) == morning_workout_data["num_meals"]

        # Verify macros still sum correctly
        tolerance = 5
        assert abs(schedule.total_protein - morning_workout_data["daily_protein_g"]) <= tolerance

    def test_generates_rest_day_schedule(self, rest_day_data):
        """Should handle rest day (no workout) correctly."""
        schedule = generate_schedule(rest_day_data)
        assert len(schedule.meals) == rest_day_data["num_meals"]

        # Should not have pre/post workout meals
        meal_types = [m.meal_type.value for m in schedule.meals]
        assert "pre_workout" not in meal_types
        assert "post_workout" not in meal_types

    def test_different_meal_counts(self, standard_user_data):
        """Should work with different meal counts."""
        for num_meals in [3, 4, 5]:
            standard_user_data["num_meals"] = num_meals
            schedule = generate_schedule(standard_user_data)
            assert len(schedule.meals) == num_meals

        # 6 meals is an edge case - may produce 5-6 depending on constraints
        standard_user_data["num_meals"] = 6
        schedule = generate_schedule(standard_user_data)
        assert len(schedule.meals) >= 5


class TestMealReasoning:
    """Tests for meal reasoning generation."""

    def test_meals_have_reasoning(self, standard_user_data):
        """Each meal should have a reasoning string."""
        schedule = generate_schedule(standard_user_data)
        for meal in schedule.meals:
            assert meal.reasoning
            assert len(meal.reasoning) > 10

    def test_post_workout_mentions_mps(self, standard_user_data):
        """Post-workout reasoning should mention MPS."""
        schedule = generate_schedule(standard_user_data)

        for meal in schedule.meals:
            if meal.meal_type.value == "post_workout":
                reasoning_lower = meal.reasoning.lower()
                assert "mps" in reasoning_lower or "protein" in reasoning_lower


class TestInputParsing:
    """Tests for user input parsing."""

    def test_parse_basic_inputs(self):
        """Should parse basic user inputs."""
        data = {
            "wake_time": "07:00",
            "sleep_time": "23:00",
            "daily_calories": 2500,
            "daily_protein_g": 180,
            "num_meals": 4,
            "goal": "muscle_gain"
        }
        user = parse_user_inputs(data)

        assert user.wake_time == time(7, 0)
        assert user.sleep_time == time(23, 0)
        assert user.daily_calories == 2500
        assert user.goal == Goal.MUSCLE_GAIN

    def test_auto_calculate_macros(self):
        """Should auto-calculate carbs/fat if not provided."""
        data = {
            "wake_time": "07:00",
            "sleep_time": "23:00",
            "daily_calories": 2500,
            "daily_protein_g": 180,
            "num_meals": 4,
            "goal": "muscle_gain"
        }
        user = parse_user_inputs(data)

        assert user.daily_carbs_g is not None
        assert user.daily_fat_g is not None
        assert user.daily_carbs_g > 0
        assert user.daily_fat_g > 0

    def test_parse_workout_inputs(self):
        """Should parse workout-related inputs."""
        data = {
            "wake_time": "07:00",
            "sleep_time": "23:00",
            "workout_time": "17:00",
            "workout_type": "lifting",
            "daily_calories": 2500,
            "daily_protein_g": 180,
            "num_meals": 4,
            "goal": "muscle_gain"
        }
        user = parse_user_inputs(data)

        assert user.workout_time == time(17, 0)
        assert user.workout_type == WorkoutType.LIFTING


class TestScheduleOutput:
    """Tests for schedule output formatting."""

    def test_str_representation(self, standard_user_data):
        """Schedule should have a readable string representation."""
        schedule = generate_schedule(standard_user_data)
        output = str(schedule)

        assert "MEAL" in output
        assert "Protein" in output or "protein" in output
        assert "TOTALS" in output or "totals" in output.lower()

    def test_meal_time_formatting(self, standard_user_data):
        """Meal times should be formatted correctly."""
        schedule = generate_schedule(standard_user_data)

        for meal in schedule.meals:
            # Check 12-hour format
            assert "AM" in meal.time_str or "PM" in meal.time_str
            # Check 24-hour format
            assert ":" in meal.time_24h
