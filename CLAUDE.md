# Chrono-Nutrition Meal Scheduler

## Project Overview

Build a Python application that generates a personalized meal schedule based on circadian biology, workout timing, and sleep patterns. The app sends push notifications at optimal meal times with macro targets.

### Core Value Proposition
Instead of generic "eat every 3 hours" advice, this tool uses real biochemistry—circadian insulin sensitivity, muscle protein synthesis windows, cortisol rhythms, and glycogen kinetics—to tell the user exactly when and what to eat.

---

## User Inputs

```python
user_inputs = {
    "wake_time": "07:00",           # 24hr format
    "sleep_time": "23:00",          # 24hr format
    "workout_time": "17:00",        # 24hr format, None if rest day
    "workout_type": "lifting",      # "lifting", "cardio", "hybrid", or None
    "workout_duration_min": 60,     # minutes
    "daily_calories": 2500,
    "daily_protein_g": 180,
    "daily_carbs_g": 280,           # optional, can auto-calculate
    "daily_fat_g": 80,              # optional, can auto-calculate
    "num_meals": 4,                 # 3, 4, 5, or 6
    "goal": "muscle_gain"           # "muscle_gain", "fat_loss", "maintenance", "performance"
}
```

---

## The Biochemistry (Implement This Logic)

### 1. Circadian Insulin Sensitivity Curve

Insulin sensitivity follows a predictable pattern based on wake time:

```
Time since waking    | Insulin Sensitivity | Carb Priority
---------------------|---------------------|---------------
0-2 hours            | High (0.9)          | Good for carbs
2-6 hours            | Peak (1.0)          | Best for carbs
6-10 hours           | Moderate (0.7)      | Moderate carbs
10-14 hours          | Low (0.5)           | Minimize carbs
14+ hours            | Very Low (0.3)      | Avoid large carb loads
```

**Implementation:** Create a function that takes `wake_time` and `meal_time` and returns an insulin sensitivity score (0-1). Use this to weight carbohydrate distribution across meals.

### 2. Muscle Protein Synthesis (MPS) Windows

Key parameters from literature:
- MPS is elevated for 24-48 hours post-resistance training
- Peak MPS occurs 1-4 hours post-workout
- Leucine threshold: ~2.5-3g leucine required to maximally stimulate MPS
- ~25-40g protein per meal optimally stimulates MPS (more doesn't help much)
- Protein distribution matters: spreading intake across meals > one large bolus

**Implementation:** 
- Post-workout meal (60-120 min after) should have highest protein allocation
- Pre-sleep meal should include protein (MPS continues overnight)
- Each meal should hit minimum 25g protein if possible
- Calculate leucine content: ~8-10% of protein from typical sources

### 3. Pre-Workout Nutrition Timing

Based on gastric emptying and blood glucose optimization:

```
Time before workout | Meal Size    | Composition
--------------------|--------------|---------------------------
3-4 hours           | Full meal    | Balanced macros, any fat
2-3 hours           | Medium meal  | Moderate protein/carb, low fat
1-2 hours           | Small meal   | High carb, low protein, minimal fat
0-1 hour            | Snack only   | Simple carbs only (optional)
```

**Implementation:** If a meal falls within 2 hours pre-workout, adjust its composition (lower fat, faster-digesting carbs).

### 4. Post-Workout Nutrition Window

- Glycogen synthase activity elevated for ~2 hours post-exercise
- Muscle is insulin-sensitive for ~2-4 hours post-exercise
- MPS peaks 1-4 hours post-exercise

**Implementation:** Schedule a meal 60-120 minutes post-workout with:
- Highest protein allocation of the day (35-50g)
- High carbs (glycogen replenishment)
- Moderate fat is fine (doesn't blunt MPS as once thought)

### 5. Pre-Sleep Nutrition

- Large meals within 2 hours of sleep impair sleep quality
- Casein/slow protein before bed supports overnight MPS
- High glycemic carbs close to bed can impair sleep onset

**Implementation:** 
- Last meal should be 2-3 hours before sleep
- If meal is within 3 hours of sleep: moderate protein, lower carbs, moderate fat
- Avoid very large caloric loads close to bed

### 6. Cortisol Rhythm Consideration

- Cortisol peaks 30-45 minutes after waking (cortisol awakening response)
- High cortisol = catabolic environment
- First meal timing: 30-60 minutes post-wake is generally optimal

**Implementation:** Schedule first meal 30-60 minutes after wake time.

---

## Meal Timing Algorithm

### Step 1: Define Fixed Anchor Points

```python
def calculate_anchor_points(wake_time, sleep_time, workout_time):
    anchors = {
        "first_meal": wake_time + 30-60 minutes,
        "last_meal": sleep_time - 2.5-3 hours,
    }
    
    if workout_time:
        anchors["pre_workout"] = workout_time - 1.5-2 hours
        anchors["post_workout"] = workout_time + workout_duration + 60-90 minutes
    
    return anchors
```

### Step 2: Distribute Remaining Meals

Fill gaps between anchor points with remaining meals, ensuring:
- Minimum 2.5 hours between meals (digestion/MPS refractory period)
- Maximum 5 hours between meals (prevent excessive catabolism)
- Align with circadian peaks when possible

### Step 3: Allocate Macros Per Meal

```python
def allocate_macros(meals, daily_targets, workout_time, wake_time):
    for meal in meals:
        # Base allocation
        meal.protein = daily_targets.protein / num_meals
        
        # Adjustments:
        # 1. Post-workout gets +30% protein
        # 2. Carbs weighted by insulin sensitivity score
        # 3. Pre-workout gets lower fat
        # 4. Pre-sleep gets moderate protein, lower carbs
        
    # Normalize to hit daily targets exactly
    return meals
```

### Step 4: Generate Meal Schedule Output

```python
@dataclass
class ScheduledMeal:
    meal_number: int
    time: datetime
    calories: int
    protein_g: int
    carbs_g: int
    fat_g: int
    reasoning: str  # Brief biochem explanation
    meal_type: str  # "breakfast", "pre_workout", "post_workout", "dinner", etc.
```

---

## Example Output

For inputs: Wake 7am, Sleep 11pm, Workout 5pm (lifting), 2500 cal, 180g protein, 4 meals

```
═══════════════════════════════════════════════════════════════
                    YOUR MEAL SCHEDULE
═══════════════════════════════════════════════════════════════

MEAL 1 — 7:45 AM (Breakfast)
├─ Calories: 550
├─ Protein: 40g | Carbs: 65g | Fat: 15g
└─ Why: Post-wake cortisol clearing, high insulin sensitivity.
        Hit leucine threshold to kickstart MPS.

MEAL 2 — 12:30 PM (Lunch)  
├─ Calories: 650
├─ Protein: 45g | Carbs: 70g | Fat: 18g
└─ Why: Peak circadian insulin sensitivity window.
        Largest carb opportunity of the day.

MEAL 3 — 3:30 PM (Pre-Workout)
├─ Calories: 450
├─ Protein: 30g | Carbs: 60g | Fat: 8g
└─ Why: 90min pre-workout. Low fat for fast gastric emptying.
        Carbs to top off muscle glycogen.

MEAL 4 — 7:00 PM (Post-Workout)
├─ Calories: 850
├─ Protein: 65g | Carbs: 85g | Fat: 22g
└─ Why: MPS peak window (2hr post-lift). Glycogen synthase 
        elevated. Largest protein bolus for maximum MPS.

═══════════════════════════════════════════════════════════════
DAILY TOTALS: 2500 cal | 180g protein | 280g carbs | 63g fat ✓
═══════════════════════════════════════════════════════════════
```

---

## Push Notification System

### Option 1: Telegram Bot (Recommended)

**Setup:**
1. Message @BotFather on Telegram, create new bot, get API token
2. Get your chat_id by messaging the bot and calling getUpdates API
3. Store credentials in `.env` file

**Implementation:**
```python
import requests
from datetime import datetime
import schedule
import time

def send_telegram_notification(bot_token, chat_id, meal):
    message = f"""
🍽️ MEAL {meal.meal_number} — {meal.time.strftime('%I:%M %p')}

📊 Targets:
• Calories: {meal.calories}
• Protein: {meal.protein_g}g
• Carbs: {meal.carbs_g}g  
• Fat: {meal.fat_g}g

🧬 {meal.reasoning}
"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    requests.post(url, json=payload)

def schedule_notifications(meals, bot_token, chat_id):
    for meal in meals:
        schedule.every().day.at(meal.time.strftime("%H:%M")).do(
            send_telegram_notification, bot_token, chat_id, meal
        )
    
    while True:
        schedule.run_pending()
        time.sleep(60)
```

### Option 2: Pushover (iOS/Android native notifications)

- One-time $5 purchase
- Cleaner notifications
- Use `python-pushover` library

### Option 3: Email (Simplest)

- Use `smtplib` with Gmail
- Less immediate but no setup required

---

## Project Structure

```
chrono-nutrition/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
│
├── src/
│   ├── __init__.py
│   ├── models.py              # Dataclasses for User, Meal, Schedule
│   ├── circadian.py           # Insulin sensitivity, cortisol curves
│   ├── mps.py                 # Muscle protein synthesis logic
│   ├── meal_timing.py         # Core scheduling algorithm
│   ├── macro_allocation.py    # Distribute macros across meals
│   ├── scheduler.py           # Generate full day schedule
│   └── notifier.py            # Telegram/push notification logic
│
├── app/
│   ├── __init__.py
│   ├── main.py                # Flask/Streamlit app
│   └── templates/
│       └── index.html
│
├── tests/
│   ├── test_circadian.py
│   ├── test_meal_timing.py
│   └── test_scheduler.py
│
└── scripts/
    ├── run_scheduler.py       # Daily notification daemon
    └── generate_schedule.py   # One-off schedule generation
```

---

## Requirements.txt

```
flask>=2.0.0
python-telegram-bot>=20.0
schedule>=1.2.0
python-dotenv>=1.0.0
dataclasses-json>=0.6.0
pytest>=7.0.0
```

---

## Flask Web Interface

Build a simple form that:
1. Accepts all user inputs
2. Generates and displays the meal schedule
3. Has a "Start Notifications" button to activate the Telegram bot
4. Allows saving/loading of user profiles

### Minimal UI Requirements:
- Time pickers for wake/sleep/workout times
- Number inputs for calorie/macro targets
- Dropdown for goal selection
- Toggle for rest day (no workout)
- Display generated schedule in a clean format
- Copy schedule to clipboard button

---

## Deployment

### PythonAnywhere (Free Tier)
- Host Flask app
- Use scheduled tasks for notifications (limited on free tier)

### Railway (Recommended)
- Free tier available
- Supports background workers for notifications
- Easy GitHub integration

### Render
- Free tier with limitations
- Good for Flask apps

---

## README.md Content

The README should include:

1. **What it does** — One paragraph explanation
2. **The science** — Brief overview of circadian biology, MPS, etc. with citations
3. **Screenshots** — Show the UI and example notifications
4. **Setup instructions** — How to get Telegram bot working
5. **Usage** — How to input your schedule and start notifications
6. **The algorithm** — Explain the timing logic at a high level
7. **Future improvements** — Wearable integration, food suggestions, etc.

---

## Key Citations for README

Include these to show scientific grounding:

1. Circadian insulin sensitivity: Poggiogalle et al. (2018) "Circadian regulation of glucose, lipid, and energy metabolism in humans"
2. MPS timing: Schoenfeld & Aragon (2018) "How much protein can the body use in a single meal for muscle-building?"
3. Nutrient timing: Kerksick et al. (2017) "ISSN position stand: nutrient timing"
4. Pre-sleep protein: Trommelen & Van Loon (2016) "Pre-sleep protein ingestion to improve the skeletal muscle adaptive response to exercise training"

---

## Testing Checklist

Before considering MVP complete:

- [ ] Schedule generates correctly for morning workout
- [ ] Schedule generates correctly for evening workout  
- [ ] Schedule generates correctly for rest day (no workout)
- [ ] Schedule generates correctly for different meal counts (3, 4, 5, 6)
- [ ] Macros sum to daily targets (within 5g tolerance)
- [ ] No meals scheduled within 2 hours of sleep
- [ ] No meals scheduled within 30 min of workout start
- [ ] Post-workout meal is within 2 hours of workout end
- [ ] Telegram notifications send at correct times
- [ ] Web UI accepts inputs and displays schedule

---

## Stretch Goals (Post-MVP)

1. **Food suggestions**: "For 40g protein, 65g carbs, try: 6oz chicken breast + 1 cup rice + vegetables"
2. **Wearable integration**: Pull sleep data from Apple Health/Fitbit to auto-adjust wake time
3. **Feedback loop**: Log energy levels, adjust timing algorithm based on personal response
4. **Genetic variants**: If user has 23andMe data, adjust for CYP1A2 (caffeine), CLOCK genes, etc.
5. **Weekly meal prep**: Generate grocery list based on the week's scheduled macros

---

## Build Order

### Week 1: Core Logic
1. Implement `circadian.py` — insulin sensitivity function
2. Implement `meal_timing.py` — anchor points and meal distribution
3. Implement `macro_allocation.py` — distribute macros per meal
4. Implement `scheduler.py` — tie it together, output schedule
5. Test with hardcoded inputs, print to console

### Week 2: Notifications
1. Set up Telegram bot
2. Implement `notifier.py`
3. Test sending a single notification
4. Implement scheduled notifications for full day
5. Run for yourself for a few days

### Week 3: Web UI + Deploy
1. Build Flask app with input form
2. Display generated schedule
3. Add "activate notifications" functionality
4. Deploy to Railway or PythonAnywhere
5. Write README with screenshots

---

## Example Hardcoded Test

Use this to verify your logic before building the UI:

```python
# test_hardcoded.py
from src.scheduler import generate_schedule

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

schedule = generate_schedule(test_user)

for meal in schedule.meals:
    print(f"\nMEAL {meal.meal_number} — {meal.time}")
    print(f"  {meal.calories} cal | {meal.protein_g}g P | {meal.carbs_g}g C | {meal.fat_g}g F")
    print(f"  → {meal.reasoning}")

print(f"\nTOTALS: {schedule.total_calories} cal | {schedule.total_protein}g protein")
```

---

