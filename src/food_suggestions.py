"""
Food suggestion engine based on available groceries and macro targets.

Matches foods from a grocery list to meal macro requirements.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class FoodItem:
    """Nutritional info for a food item."""
    name: str
    protein_per_100g: float
    carbs_per_100g: float
    fat_per_100g: float
    calories_per_100g: float
    typical_serving_g: float
    category: str  # protein, carb, fat, vegetable, dairy


# Common food database with nutritional info per 100g
FOOD_DATABASE: Dict[str, FoodItem] = {
    # Proteins
    "chicken breast": FoodItem("chicken breast", 31, 0, 3.6, 165, 150, "protein"),
    "chicken": FoodItem("chicken", 27, 0, 14, 239, 150, "protein"),
    "turkey": FoodItem("turkey", 29, 0, 7, 189, 150, "protein"),
    "beef": FoodItem("beef", 26, 0, 15, 250, 150, "protein"),
    "ground beef": FoodItem("ground beef", 26, 0, 20, 290, 150, "protein"),
    "steak": FoodItem("steak", 27, 0, 15, 250, 200, "protein"),
    "salmon": FoodItem("salmon", 20, 0, 13, 208, 150, "protein"),
    "tuna": FoodItem("tuna", 30, 0, 1, 130, 150, "protein"),
    "shrimp": FoodItem("shrimp", 24, 0, 0.3, 99, 150, "protein"),
    "fish": FoodItem("fish", 22, 0, 5, 140, 150, "protein"),
    "eggs": FoodItem("eggs", 13, 1, 11, 155, 100, "protein"),
    "egg whites": FoodItem("egg whites", 11, 0.7, 0, 52, 150, "protein"),
    "tofu": FoodItem("tofu", 8, 2, 4, 76, 150, "protein"),
    "tempeh": FoodItem("tempeh", 19, 9, 11, 193, 100, "protein"),
    "pork": FoodItem("pork", 27, 0, 14, 242, 150, "protein"),
    "bacon": FoodItem("bacon", 37, 1, 42, 541, 30, "protein"),

    # Dairy
    "greek yogurt": FoodItem("greek yogurt", 10, 4, 0.7, 59, 200, "dairy"),
    "cottage cheese": FoodItem("cottage cheese", 11, 3, 4, 98, 200, "dairy"),
    "milk": FoodItem("milk", 3.4, 5, 3.2, 60, 250, "dairy"),
    "cheese": FoodItem("cheese", 25, 1, 33, 402, 30, "dairy"),
    "whey protein": FoodItem("whey protein", 80, 8, 3, 380, 30, "dairy"),
    "protein powder": FoodItem("protein powder", 80, 8, 3, 380, 30, "dairy"),

    # Carbs
    "rice": FoodItem("rice", 2.7, 28, 0.3, 130, 150, "carb"),
    "white rice": FoodItem("white rice", 2.7, 28, 0.3, 130, 150, "carb"),
    "brown rice": FoodItem("brown rice", 2.6, 23, 0.9, 111, 150, "carb"),
    "pasta": FoodItem("pasta", 5, 25, 1, 131, 150, "carb"),
    "bread": FoodItem("bread", 9, 49, 3, 265, 60, "carb"),
    "oatmeal": FoodItem("oatmeal", 13, 68, 7, 389, 50, "carb"),
    "oats": FoodItem("oats", 13, 68, 7, 389, 50, "carb"),
    "potato": FoodItem("potato", 2, 17, 0.1, 77, 200, "carb"),
    "potatoes": FoodItem("potatoes", 2, 17, 0.1, 77, 200, "carb"),
    "sweet potato": FoodItem("sweet potato", 1.6, 20, 0.1, 86, 200, "carb"),
    "quinoa": FoodItem("quinoa", 4.4, 21, 1.9, 120, 150, "carb"),
    "tortilla": FoodItem("tortilla", 8, 50, 8, 310, 50, "carb"),
    "bagel": FoodItem("bagel", 10, 53, 1, 257, 100, "carb"),
    "cereal": FoodItem("cereal", 7, 84, 2, 378, 40, "carb"),
    "beans": FoodItem("beans", 9, 23, 0.5, 127, 150, "carb"),
    "black beans": FoodItem("black beans", 9, 24, 0.5, 132, 150, "carb"),
    "lentils": FoodItem("lentils", 9, 20, 0.4, 116, 150, "carb"),
    "chickpeas": FoodItem("chickpeas", 9, 27, 3, 164, 150, "carb"),

    # Fats
    "avocado": FoodItem("avocado", 2, 9, 15, 160, 100, "fat"),
    "olive oil": FoodItem("olive oil", 0, 0, 100, 884, 15, "fat"),
    "coconut oil": FoodItem("coconut oil", 0, 0, 100, 862, 15, "fat"),
    "butter": FoodItem("butter", 0.9, 0.1, 81, 717, 14, "fat"),
    "almonds": FoodItem("almonds", 21, 22, 49, 579, 30, "fat"),
    "peanuts": FoodItem("peanuts", 26, 16, 49, 567, 30, "fat"),
    "peanut butter": FoodItem("peanut butter", 25, 20, 50, 588, 32, "fat"),
    "almond butter": FoodItem("almond butter", 21, 19, 56, 614, 32, "fat"),
    "nuts": FoodItem("nuts", 20, 20, 50, 580, 30, "fat"),
    "walnuts": FoodItem("walnuts", 15, 14, 65, 654, 30, "fat"),
    "cashews": FoodItem("cashews", 18, 30, 44, 553, 30, "fat"),
    "seeds": FoodItem("seeds", 18, 20, 45, 540, 30, "fat"),
    "chia seeds": FoodItem("chia seeds", 17, 42, 31, 486, 30, "fat"),

    # Vegetables
    "broccoli": FoodItem("broccoli", 2.8, 7, 0.4, 34, 150, "vegetable"),
    "spinach": FoodItem("spinach", 2.9, 3.6, 0.4, 23, 100, "vegetable"),
    "kale": FoodItem("kale", 4.3, 9, 0.9, 49, 100, "vegetable"),
    "lettuce": FoodItem("lettuce", 1.4, 2.9, 0.2, 15, 100, "vegetable"),
    "tomato": FoodItem("tomato", 0.9, 3.9, 0.2, 18, 150, "vegetable"),
    "tomatoes": FoodItem("tomatoes", 0.9, 3.9, 0.2, 18, 150, "vegetable"),
    "cucumber": FoodItem("cucumber", 0.7, 3.6, 0.1, 15, 150, "vegetable"),
    "peppers": FoodItem("peppers", 1, 6, 0.3, 31, 150, "vegetable"),
    "bell pepper": FoodItem("bell pepper", 1, 6, 0.3, 31, 150, "vegetable"),
    "onion": FoodItem("onion", 1.1, 9, 0.1, 40, 100, "vegetable"),
    "carrots": FoodItem("carrots", 0.9, 10, 0.2, 41, 100, "vegetable"),
    "mushrooms": FoodItem("mushrooms", 3.1, 3.3, 0.3, 22, 100, "vegetable"),
    "zucchini": FoodItem("zucchini", 1.2, 3.1, 0.3, 17, 150, "vegetable"),
    "asparagus": FoodItem("asparagus", 2.2, 3.9, 0.1, 20, 150, "vegetable"),
    "green beans": FoodItem("green beans", 1.8, 7, 0.2, 31, 150, "vegetable"),
    "cauliflower": FoodItem("cauliflower", 1.9, 5, 0.3, 25, 150, "vegetable"),

    # Fruits
    "banana": FoodItem("banana", 1.1, 23, 0.3, 89, 120, "carb"),
    "apple": FoodItem("apple", 0.3, 14, 0.2, 52, 180, "carb"),
    "berries": FoodItem("berries", 0.7, 14, 0.3, 57, 150, "carb"),
    "blueberries": FoodItem("blueberries", 0.7, 14, 0.3, 57, 150, "carb"),
    "strawberries": FoodItem("strawberries", 0.7, 8, 0.3, 32, 150, "carb"),
    "orange": FoodItem("orange", 0.9, 12, 0.1, 47, 150, "carb"),
}


def match_grocery_to_database(grocery_item: str) -> Optional[FoodItem]:
    """
    Match a grocery item string to our food database.

    Uses fuzzy matching - looks for database keys within the grocery item.
    """
    grocery_lower = grocery_item.lower().strip()

    # Direct match
    if grocery_lower in FOOD_DATABASE:
        return FOOD_DATABASE[grocery_lower]

    # Partial match - check if any database key is in the grocery item
    for key, food in FOOD_DATABASE.items():
        if key in grocery_lower or grocery_lower in key:
            return food

    return None


def get_available_foods(grocery_list: List[str]) -> Dict[str, List[FoodItem]]:
    """
    Categorize available foods from grocery list.

    Returns dict with categories as keys and lists of FoodItems as values.
    """
    categorized = {
        "protein": [],
        "carb": [],
        "fat": [],
        "vegetable": [],
        "dairy": []
    }

    for item in grocery_list:
        food = match_grocery_to_database(item)
        if food:
            categorized[food.category].append(food)

    return categorized


def suggest_meal(
    protein_g: int,
    carbs_g: int,
    fat_g: int,
    available_foods: Dict[str, List[FoodItem]],
    meal_type: str = "regular"
) -> str:
    """
    Suggest a meal combination to hit macro targets.

    Args:
        protein_g: Target protein in grams
        carbs_g: Target carbs in grams
        fat_g: Target fat in grams
        available_foods: Categorized available foods
        meal_type: Type of meal (affects suggestions)

    Returns:
        String describing suggested meal
    """
    suggestions = []

    # Pick a protein source
    proteins = available_foods.get("protein", []) + available_foods.get("dairy", [])
    if proteins:
        # Sort by protein content
        proteins.sort(key=lambda f: f.protein_per_100g, reverse=True)
        protein_food = proteins[0]

        # Calculate serving size to hit ~60-70% of protein target
        target_protein_from_main = protein_g * 0.65
        serving_g = (target_protein_from_main / protein_food.protein_per_100g) * 100
        serving_g = min(serving_g, protein_food.typical_serving_g * 1.5)  # Cap at 1.5x typical

        if serving_g >= 50:
            suggestions.append(f"{int(serving_g)}g {protein_food.name}")

    # Pick a carb source (if carbs needed)
    carbs = available_foods.get("carb", [])
    if carbs and carbs_g > 20:
        carb_food = carbs[0]
        serving_g = (carbs_g * 0.6 / carb_food.carbs_per_100g) * 100
        serving_g = min(serving_g, carb_food.typical_serving_g * 1.5)

        if serving_g >= 30:
            suggestions.append(f"{int(serving_g)}g {carb_food.name}")

    # Add a vegetable
    vegetables = available_foods.get("vegetable", [])
    if vegetables:
        veg = vegetables[0]
        suggestions.append(f"{int(veg.typical_serving_g)}g {veg.name}")

    # Add fat if needed and not enough from protein
    fats = available_foods.get("fat", [])
    if fats and fat_g > 15:
        fat_food = fats[0]
        if fat_food.category == "fat":
            serving_g = (fat_g * 0.4 / fat_food.fat_per_100g) * 100
            serving_g = min(serving_g, fat_food.typical_serving_g)
            if serving_g >= 5:
                suggestions.append(f"{int(serving_g)}g {fat_food.name}")

    if not suggestions:
        return ""

    return " + ".join(suggestions)


def generate_meal_suggestions(
    meals_data: List[dict],
    grocery_list: List[str]
) -> List[str]:
    """
    Generate food suggestions for each meal.

    Args:
        meals_data: List of meal dicts with protein, carbs, fat targets
        grocery_list: User's available groceries

    Returns:
        List of suggestion strings, one per meal
    """
    if not grocery_list:
        return [""] * len(meals_data)

    available_foods = get_available_foods(grocery_list)

    # Check if we have enough variety
    total_foods = sum(len(foods) for foods in available_foods.values())
    if total_foods < 2:
        return [""] * len(meals_data)

    suggestions = []
    used_proteins = set()

    for meal in meals_data:
        # Try to vary protein sources across meals
        proteins = available_foods.get("protein", []) + available_foods.get("dairy", [])
        available_proteins = [p for p in proteins if p.name not in used_proteins]

        if not available_proteins and proteins:
            available_proteins = proteins

        meal_foods = available_foods.copy()
        if available_proteins:
            meal_foods["protein"] = [p for p in available_proteins if p.category == "protein"]
            meal_foods["dairy"] = [p for p in available_proteins if p.category == "dairy"]

        suggestion = suggest_meal(
            meal.get("protein", 40),
            meal.get("carbs", 50),
            meal.get("fat", 20),
            meal_foods,
            meal.get("type", "regular")
        )

        # Track used protein
        if suggestion and meal_foods.get("protein"):
            used_proteins.add(meal_foods["protein"][0].name if meal_foods["protein"] else "")

        suggestions.append(suggestion)

    return suggestions
