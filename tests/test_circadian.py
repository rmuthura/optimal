"""Tests for circadian rhythm calculations."""

import pytest
from datetime import time

from src.circadian import (
    get_insulin_sensitivity,
    get_cortisol_level,
    hours_since_waking,
    is_optimal_first_meal_window,
    get_carb_priority
)


class TestInsulinSensitivity:
    """Tests for insulin sensitivity calculations."""

    def test_peak_sensitivity_mid_morning(self):
        """Insulin sensitivity should peak 2-6 hours after waking."""
        wake = time(7, 0)
        meal = time(10, 0)  # 3 hours after waking
        sensitivity = get_insulin_sensitivity(wake, meal)
        assert sensitivity == 1.0

    def test_high_sensitivity_early_morning(self):
        """First 2 hours should have high (0.9) sensitivity."""
        wake = time(7, 0)
        meal = time(8, 0)  # 1 hour after waking
        sensitivity = get_insulin_sensitivity(wake, meal)
        assert sensitivity == 0.9

    def test_moderate_sensitivity_afternoon(self):
        """6-10 hours post-wake should have moderate (0.7) sensitivity."""
        wake = time(7, 0)
        meal = time(15, 0)  # 8 hours after waking
        sensitivity = get_insulin_sensitivity(wake, meal)
        assert sensitivity == 0.7

    def test_low_sensitivity_evening(self):
        """10-14 hours post-wake should have low (0.5) sensitivity."""
        wake = time(7, 0)
        meal = time(19, 0)  # 12 hours after waking
        sensitivity = get_insulin_sensitivity(wake, meal)
        assert sensitivity == 0.5

    def test_very_low_sensitivity_late_night(self):
        """14+ hours post-wake should have very low (0.3) sensitivity."""
        wake = time(7, 0)
        meal = time(22, 0)  # 15 hours after waking
        sensitivity = get_insulin_sensitivity(wake, meal)
        assert sensitivity == 0.3


class TestHoursSinceWaking:
    """Tests for time difference calculations."""

    def test_same_day(self):
        """Basic same-day calculation."""
        wake = time(7, 0)
        current = time(12, 0)
        hours = hours_since_waking(wake, current)
        assert hours == 5.0

    def test_past_midnight(self):
        """Handle times that cross midnight."""
        wake = time(7, 0)
        current = time(1, 0)  # Next day
        hours = hours_since_waking(wake, current)
        assert hours == 18.0

    def test_fractional_hours(self):
        """Handle fractional hours correctly."""
        wake = time(7, 0)
        current = time(8, 30)
        hours = hours_since_waking(wake, current)
        assert hours == 1.5


class TestCortisolLevel:
    """Tests for cortisol rhythm calculations."""

    def test_peak_cortisol_after_waking(self):
        """Cortisol should peak ~30-60 min after waking."""
        wake = time(7, 0)
        current = time(7, 45)  # 45 min after waking
        cortisol = get_cortisol_level(wake, current)
        assert cortisol >= 0.9

    def test_declining_cortisol_afternoon(self):
        """Cortisol should be lower in afternoon."""
        wake = time(7, 0)
        current = time(15, 0)  # 8 hours after waking
        cortisol = get_cortisol_level(wake, current)
        assert cortisol < 0.6

    def test_low_cortisol_evening(self):
        """Cortisol should be low in evening."""
        wake = time(7, 0)
        current = time(21, 0)  # 14 hours after waking
        cortisol = get_cortisol_level(wake, current)
        assert cortisol <= 0.3


class TestOptimalFirstMealWindow:
    """Tests for first meal timing."""

    def test_optimal_window(self):
        """30-60 min post-wake should be optimal."""
        wake = time(7, 0)
        meal = time(7, 45)
        assert is_optimal_first_meal_window(wake, meal) is True

    def test_too_early(self):
        """Less than 30 min is too early."""
        wake = time(7, 0)
        meal = time(7, 15)
        assert is_optimal_first_meal_window(wake, meal) is False

    def test_too_late(self):
        """More than 60 min is outside optimal window."""
        wake = time(7, 0)
        meal = time(8, 30)
        assert is_optimal_first_meal_window(wake, meal) is False


class TestCarbPriority:
    """Tests for carb priority recommendations."""

    def test_best_for_carbs(self):
        """High sensitivity should recommend best for carbs."""
        priority = get_carb_priority(1.0)
        assert priority == "Best for carbs"

    def test_good_for_carbs(self):
        """0.9 sensitivity should be good for carbs."""
        priority = get_carb_priority(0.9)
        assert priority == "Best for carbs"

    def test_moderate_carbs(self):
        """0.7 sensitivity should be moderate."""
        priority = get_carb_priority(0.7)
        assert priority == "Good for carbs"

    def test_minimize_carbs(self):
        """Low sensitivity should minimize carbs."""
        priority = get_carb_priority(0.3)
        assert priority == "Minimize carbs"
