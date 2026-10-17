"""
Nutrition and Energy Expenditure Calculator using clinical formulas
(Mifflin-St Jeor, WHO/FAO Activity Multipliers, and Macro Partitioning).
"""

def calculate_bmi(weight_kg: float, height_cm: float) -> dict:
    if height_cm <= 0 or weight_kg <= 0:
        return {"bmi": 0, "category": "Unknown", "color": "gray"}
    
    height_m = height_cm / 100.0
    bmi = round(weight_kg / (height_m ** 2), 1)
    
    if bmi < 18.5:
        category = "Underweight"
        color = "#3b82f6"
    elif bmi < 24.9:
        category = "Normal weight"
        color = "#10b981"
    elif bmi < 29.9:
        category = "Overweight"
        color = "#f59e0b"
    else:
        category = "Obese"
        color = "#ef4444"
        
    return {"bmi": bmi, "category": category, "color": color}


def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    """Mifflin-St Jeor formula for Basal Metabolic Rate."""
    gender = (gender or "").lower()
    base = (10.0 * weight_kg) + (6.25 * height_cm) - (5.0 * age)
    
    if gender in ["male", "man", "m"]:
        bmr = base + 5
    elif gender in ["female", "woman", "f"]:
        bmr = base - 161
    else:
        bmr = base - 78  # Gender-neutral average
        
    return max(800.0, round(bmr, 1))


def calculate_tdee(bmr: float, activity_level: str) -> float:
    """Total Daily Energy Expenditure based on activity multiplier."""
    multipliers = {
        "sedentary": 1.2,          # Desk job, little to no exercise
        "lightly_active": 1.375,   # Light exercise 1-3 days/week
        "moderately_active": 1.55, # Moderate exercise 3-5 days/week
        "very_active": 1.725,      # Hard exercise 6-7 days/week
        "extra_active": 1.9        # Very heavy workout or physical job
    }
    
    act_key = (activity_level or "").lower().replace(" ", "_").replace("-", "_")
    multiplier = multipliers.get(act_key, 1.375)
    
    return round(bmr * multiplier, 1)


def calculate_targets(weight_kg: float, height_cm: float, age: int, gender: str, 
                      activity_level: str, goal: str, dietary_pref: str) -> dict:
    """Calculate exact daily calories and macro targets (Protein, Carbs, Fats)."""
    bmi_info = calculate_bmi(weight_kg, height_cm)
    bmr = calculate_bmr(weight_kg, height_cm, age, gender)
    tdee = calculate_tdee(bmr, activity_level)
    
    goal_key = (goal or "").lower()
    diet_key = (dietary_pref or "").lower()
    
    # Caloric adjustment according to user goal
    if "loss" in goal_key or "cut" in goal_key or "fat" in goal_key:
        calorie_target = tdee - 500
        # Safe minimums: don't starve
        min_cal = 1200 if gender.lower() in ["female", "f"] else 1500
        calorie_target = max(min_cal, calorie_target)
        macro_ratio = {"protein": 0.35, "carbs": 0.40, "fat": 0.25}
        goal_description = "Fat Loss (500 kcal deficit with high protein retention)"
        
    elif "muscle" in goal_key or "gain" in goal_key or "bulk" in goal_key:
        calorie_target = tdee + 350
        macro_ratio = {"protein": 0.30, "carbs": 0.45, "fat": 0.25}
        goal_description = "Lean Muscle Gain (350 kcal surplus for hypertrophy)"
        
    elif "keto" in goal_key or "keto" in diet_key:
        calorie_target = tdee - 300
        macro_ratio = {"protein": 0.25, "carbs": 0.05, "fat": 0.70}
        goal_description = "Ketogenic State (Ultra-low carb, high healthy fats)"
        
    elif "diabetic" in goal_key or "sugar" in goal_key:
        calorie_target = tdee - 250
        macro_ratio = {"protein": 0.30, "carbs": 0.35, "fat": 0.35}
        goal_description = "Blood Sugar Stabilization (Low Glycemic Index & High Fiber)"
        
    else:  # Maintenance / General Wellness
        calorie_target = tdee
        macro_ratio = {"protein": 0.25, "carbs": 0.50, "fat": 0.25}
        goal_description = "Body Recomposition & Daily Vitality"
        
    calorie_target = round(calorie_target)
    
    # Gram calculations: 4 kcal per gram of protein/carb, 9 kcal per gram of fat
    protein_cal = calorie_target * macro_ratio["protein"]
    carbs_cal = calorie_target * macro_ratio["carbs"]
    fat_cal = calorie_target * macro_ratio["fat"]
    
    protein_g = round(protein_cal / 4.0)
    carbs_g = round(carbs_cal / 4.0)
    fat_g = round(fat_cal / 9.0)
    
    # Recommended Daily Hydration (liters): ~35ml per kg body weight
    water_liters = round(max(2.0, (weight_kg * 0.035)), 1)
    
    return {
        "bmi": bmi_info["bmi"],
        "bmi_category": bmi_info["category"],
        "bmi_color": bmi_info["color"],
        "bmr": bmr,
        "tdee": tdee,
        "calorie_target": calorie_target,
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g,
        "protein_pct": int(macro_ratio["protein"] * 100),
        "carbs_pct": int(macro_ratio["carbs"] * 100),
        "fat_pct": int(macro_ratio["fat"] * 100),
        "water_liters": water_liters,
        "goal_description": goal_description
    }
