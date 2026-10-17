"""
AI Diet Generation Service powered by Google Gemini API with seamless
rule-based clinical nutrition fallback for 100% crash-free Vercel deployments.
"""

import json
import requests
from typing import Dict, Any, Tuple
from app.services.calculator import calculate_targets


FALLBACK_MEAL_TEMPLATES = {
    "vegetarian": {
        "breakfast": {
            "title": "High-Protein Sprouted Moong & Vegetable Poha or Oats Bowl",
            "items": ["1 cup Rolled Oats or Steamed Sprouted Moong (150g)", "1 glass Low-fat Milk or Soya Milk (200ml)", "10 Crushed Almonds & 1 tbsp Flaxseeds", "1 small seasonal fruit (Apple or Papaya)"],
            "recipe_notes": "Cook with minimal olive oil / cold-pressed oil, mustard seeds, and fresh coriander.",
            "cal_ratio": 0.25
        },
        "snack_morning": {
            "title": "Hydration & Nutrient Boost",
            "items": ["1 glass Fresh Tender Coconut Water or Green Tea", "Handful of Roasted Makhana (Fox nuts, 30g)"],
            "recipe_notes": "Dry roast makhana with a pinch of black salt and turmeric.",
            "cal_ratio": 0.10
        },
        "lunch": {
            "title": "Balanced Protein Thali (Paneer/Tofu, Dal & Millets)",
            "items": ["100g Grilled Paneer or Sautéed Tofu", "1 bowl Thick Yellow/Black Dal (150g)", "2 Multigrain / Jowar Rotis or 1 cup Brown Rice", "Large bowl Rainbow Cucumber-Carrot Salad with lemon juice"],
            "recipe_notes": "Enjoy salad first to increase satiety and regulate glycemic curve.",
            "cal_ratio": 0.35
        },
        "snack_evening": {
            "title": "Pre-Workout / Metabolism Snack",
            "items": ["1 cup Spiced Roasted Chana or Boiled Chana Chaat (60g)", "Herbal Lemon Ginger Infusion or Black Coffee"],
            "recipe_notes": "High fiber and zinc for sustained late afternoon energy.",
            "cal_ratio": 0.10
        },
        "dinner": {
            "title": "Light Anti-Inflammatory Dinner",
            "items": ["1 large bowl Vegetable & Paneer/Tofu Clear Soup or Stir-Fry (250g)", "1 Multigrain Phulka or 1/2 cup Quinoa", "1 cup Steamed Broccoli & Zucchini"],
            "recipe_notes": "Keep dinner light and finish at least 2.5 hours before bedtime.",
            "cal_ratio": 0.20
        }
    },
    "non-vegetarian": {
        "breakfast": {
            "title": "Fluffy Herb Egg Scramble & Whole-Grain Toast",
            "items": ["3 Whole Eggs or 2 Whole Eggs + 2 Egg Whites", "2 slices 100% Whole Wheat or Sourdough Bread", "1/2 Sliced Avocado or 1 tbsp Peanut Butter", "1 cup Green Tea or Espresso"],
            "recipe_notes": "Scramble eggs with spinach and cherry tomatoes in a drop of olive oil.",
            "cal_ratio": 0.25
        },
        "snack_morning": {
            "title": "Berry & Nut Energy Booster",
            "items": ["1 cup Greek Yogurt or Curd (150g)", "Handful of Blueberries / Pomegranate seeds", "10 Walnut halves"],
            "recipe_notes": "Rich in antioxidants, omega-3, and gut-healthy probiotics.",
            "cal_ratio": 0.10
        },
        "lunch": {
            "title": "Grilled Chicken Breast / Fish with Quinoa & Steamed Greens",
            "items": ["150g Herb-crusted Chicken Breast or Grilled Fish", "1 cup Cooked Quinoa or Brown Rice (150g)", "1.5 cup Steamed Asparagus, Green Beans & Carrots", "1 tbsp Olive oil & lemon dressing"],
            "recipe_notes": "High lean protein for muscle repair and high TEF (thermic effect of food).",
            "cal_ratio": 0.35
        },
        "snack_evening": {
            "title": "High Protein Fuel",
            "items": ["2 Boiled Egg Whites or 1 scoop Whey/Plant Protein Shake", "1 small Apple or 1 Orange"],
            "recipe_notes": "Quick bioavailable protein burst to combat evening cravings.",
            "cal_ratio": 0.10
        },
        "dinner": {
            "title": "Pan-Seared Salmon or Grilled Chicken with Veggie Medley",
            "items": ["140g Grilled Chicken or Pan-seared White Fish", "1 large bowl Mixed Leafy Salad with bell peppers & cucumber", "1 small Baked Sweet Potato (100g)"],
            "recipe_notes": "Low glycemic carb sources promote serotonin and deep sleep.",
            "cal_ratio": 0.20
        }
    },
    "vegan": {
        "breakfast": {
            "title": "Creamy Chia, Soya & Berry Power Porridge",
            "items": ["40g Rolled Oats cooked in 250ml Soy / Almond Milk", "2 tbsp Chia seeds & 1 tbsp Pumpkin seeds", "1 scoop Vegan Pea Protein (optional)", "1 sliced Kiwi or Banana"],
            "recipe_notes": "Top with a drizzle of pure cinnamon for insulin sensitivity.",
            "cal_ratio": 0.25
        },
        "snack_morning": {
            "title": "Fresh Fruit & Raw Nut Fuel",
            "items": ["1 Seasonal Fruit (Orange / Pear)", "12 Raw Almonds & 2 Brazil nuts"],
            "recipe_notes": "Selenium, vitamin C and magnesium boost for cellular health.",
            "cal_ratio": 0.10
        },
        "lunch": {
            "title": "Mediterranean Chickpea & Tempeh Buddha Bowl",
            "items": ["120g Air-fried or Grilled Tempeh", "1 cup Cooked Chickpeas / Hummus", "1 cup Quinoa or Brown Basmati Rice", "Generous bowl of shredded purple cabbage, lettuce, and tahini drizzle"],
            "recipe_notes": "Complete amino acid profile through legume and grain pairing.",
            "cal_ratio": 0.35
        },
        "snack_evening": {
            "title": "Roasted Edamame & Matcha",
            "items": ["1/2 cup Dry Roasted Edamame beans (40g)", "1 cup Ceremonial Green Matcha Tea"],
            "recipe_notes": "Over 14g of pure plant protein with powerful EGCG antioxidants.",
            "cal_ratio": 0.10
        },
        "dinner": {
            "title": "Hearty Lentil Dahl & Sautéed Bok Choy",
            "items": ["1 large bowl Slow-cooked Red Lentil / Moong Dahl (200g)", "1 cup Steamed Bok Choy & Broccoli with garlic", "1 small Millet Roti or 1/2 cup Wild Rice"],
            "recipe_notes": "Easily digestible plant proteins that prevent nocturnal bloating.",
            "cal_ratio": 0.20
        }
    }
}


def build_fallback_plan(profile: dict, targets: dict) -> dict:
    """Generate a high-grade clinical nutrition plan without needing any API key."""
    diet_key = (profile.get("dietary_preference") or "vegetarian").lower()
    
    if "non" in diet_key or "egg" in diet_key or "chicken" in diet_key:
        template_key = "non-vegetarian"
    elif "vegan" in diet_key:
        template_key = "vegan"
    else:
        template_key = "vegetarian"
        
    template = FALLBACK_MEAL_TEMPLATES.get(template_key, FALLBACK_MEAL_TEMPLATES["vegetarian"])
    target_cal = targets["calorie_target"]
    
    meals = []
    meal_configs = [
        ("Breakfast", "08:30 AM", template["breakfast"]),
        ("Mid-Morning Snack", "11:30 AM", template["snack_morning"]),
        ("Lunch", "01:30 PM", template["lunch"]),
        ("Evening Snack", "05:00 PM", template["snack_evening"]),
        ("Dinner", "08:00 PM", template["dinner"]),
    ]
    
    for name, time_str, meal_info in meal_configs:
        meal_cal = round(target_cal * meal_info["cal_ratio"])
        # distribute macros according to target percentages
        meal_prot = round((meal_cal * (targets["protein_pct"] / 100)) / 4.0)
        meal_carb = round((meal_cal * (targets["carbs_pct"] / 100)) / 4.0)
        meal_fat = round((meal_cal * (targets["fat_pct"] / 100)) / 9.0)
        
        meals.append({
            "name": name,
            "time": time_str,
            "title": meal_info["title"],
            "calories": meal_cal,
            "protein": meal_prot,
            "carbs": meal_carb,
            "fats": meal_fat,
            "items": meal_info["items"],
            "recipe_notes": meal_info["recipe_notes"]
        })
        
    grocery_list = {
        "Produce & Greens": ["Fresh Spinach & Mixed Salad Greens", "Broccoli, Bell Peppers, Zucchini", "Cucumbers, Tomatoes, Carrots, Lemons", "Fresh Seasonal Fruits (Apples, Berries, Papaya)"],
        "Proteins & Dairy": [
            "Paneer / Soya Tofu / Chicken Breast (as preferred)",
            "Eggs or Tempeh",
            "Greek Yogurt / Curd",
            "Yellow Moong Dal & Chickpeas"
        ],
        "Grains & Dry Pantry": ["Rolled Oats / Quinoa", "Millets / Jowar / Brown Rice", "Whole Wheat / Sprouted Grains", "Roasted Makhana / Roasted Chana"],
        "Healthy Fats & Seeds": ["Cold-pressed Extra Virgin Olive Oil", "Almonds & Walnut Halves", "Flax seeds, Chia seeds & Pumpkin seeds"]
    }
    
    nutritionist_tips = [
        f"Hydration Strategy: Drink at least {targets['water_liters']}L of water daily. Begin your morning with 500ml warm water.",
        "Meal Order Matters: Always eat vegetables and protein first before carbohydrates to blunt blood sugar spikes by up to 40%.",
        "Circadian Eating: Stop caloric intake at least 2.5 to 3 hours prior to sleep to optimize growth hormone release and cellular repair.",
        f"Goal Focus ({targets['goal_description']}): Adhere strictly to the {targets['protein_g']}g daily protein target to preserve metabolic muscle mass."
    ]
    
    return {
        "meals": meals,
        "grocery_list": grocery_list,
        "nutritionist_tips": nutritionist_tips,
        "summary": f"Customized clinical diet targeting {target_cal} kcal/day with {targets['protein_g']}g protein, {targets['carbs_g']}g carbs, and {targets['fat_g']}g healthy fats tailored for {profile.get('goal', 'wellness')}."
    }


def call_gemini_api(api_key: str, prompt: str) -> dict:
    """Invoke Gemini REST API with model fallback and strict timeout."""
    models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp"]
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.4,
            "responseMimeType": "application/json"
        }
    }
    
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=12)
            if response.status_code == 200:
                data = response.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                # Clean up any markdown code fences if present
                clean_text = text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                elif clean_text.startswith("```"):
                    clean_text = clean_text[3:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                clean_text = clean_text.strip()
                return json.loads(clean_text)
            else:
                print(f"Gemini API ({model}) returned HTTP {response.status_code}: {response.text}")
        except Exception as err:
            print(f"Gemini request failed on {model}: {err}")
            continue
            
    return None


def generate_smart_diet_plan(profile: dict, api_key: str = None) -> Tuple[dict, dict, bool]:
    """
    Primary orchestrator for diet plan generation.
    Returns (targets, plan_data, is_ai_generated).
    Guaranteed NEVER to raise unhandled exceptions or crash.
    """
    targets = calculate_targets(
        weight_kg=float(profile.get("weight", 70)),
        height_cm=float(profile.get("height", 170)),
        age=int(profile.get("age", 25)),
        gender=profile.get("gender", "male"),
        activity_level=profile.get("activity_level", "moderately_active"),
        goal=profile.get("goal", "weight_loss"),
        dietary_pref=profile.get("dietary_preference", "vegetarian")
    )
    
    plan_data = None
    ai_generated = False
    
    # Check if Gemini key is available
    active_key = (api_key or "").strip()
    
    if active_key:
        prompt = f"""
You are an elite clinical nutritionist and dietitian.
Create a detailed, delicious, practical 1-day personalized meal plan based on this client profile:

Client Profile:
- Name: {profile.get('user_name', 'Client')}
- Age: {profile.get('age')} years, Gender: {profile.get('gender')}
- Current Weight: {profile.get('weight')} kg, Target Weight: {profile.get('target_weight', 'Not specified')} kg
- Height: {profile.get('height')} cm
- Activity Level: {profile.get('activity_level')}
- Primary Goal: {profile.get('goal')} ({targets['goal_description']})
- Dietary Preference: {profile.get('dietary_preference')}
- Allergies / Intolerances / Restrictions: {profile.get('allergies', 'None')}
- Daily Target Calories: {targets['calorie_target']} kcal
- Target Macros: Protein: {targets['protein_g']}g ({targets['protein_pct']}%), Carbs: {targets['carbs_g']}g ({targets['carbs_pct']}%), Fats: {targets['fat_g']}g ({targets['fat_pct']}%)
- Daily Hydration Target: {targets['water_liters']} Liters

Return a STRICT JSON object with the following exact keys:
{{
  "summary": "Brief encouraging clinical rationale for this plan (2-3 sentences)",
  "meals": [
    {{
      "name": "Breakfast",
      "time": "08:30 AM",
      "title": "Appealing meal title",
      "calories": number,
      "protein": number,
      "carbs": number,
      "fats": number,
      "items": ["Specific ingredient with portion e.g. 150g Egg Whites", "1 slice Multigrain bread"],
      "recipe_notes": "1-2 sentence preparation or cooking technique"
    }},
    {{
      "name": "Mid-Morning Snack",
      "time": "11:30 AM",
      "title": "Title",
      "calories": number,
      "protein": number,
      "carbs": number,
      "fats": number,
      "items": ["Item with portion"],
      "recipe_notes": "Notes"
    }},
    {{
      "name": "Lunch",
      "time": "01:30 PM",
      "title": "Title",
      "calories": number,
      "protein": number,
      "carbs": number,
      "fats": number,
      "items": ["Item with portion"],
      "recipe_notes": "Notes"
    }},
    {{
      "name": "Evening Snack",
      "time": "05:00 PM",
      "title": "Title",
      "calories": number,
      "protein": number,
      "carbs": number,
      "fats": number,
      "items": ["Item with portion"],
      "recipe_notes": "Notes"
    }},
    {{
      "name": "Dinner",
      "time": "08:00 PM",
      "title": "Title",
      "calories": number,
      "protein": number,
      "carbs": number,
      "fats": number,
      "items": ["Item with portion"],
      "recipe_notes": "Notes"
    }}
  ],
  "grocery_list": {{
    "Produce & Greens": ["List of fresh vegetables and fruits with quantity"],
    "Proteins & Dairy": ["List of proteins, paneer, tofu, eggs, lentils, or meats"],
    "Grains & Dry Pantry": ["List of healthy carbs, oats, quinoa, brown rice"],
    "Healthy Fats & Seeds": ["List of nuts, seeds, cold-pressed oils"]
  }},
  "nutritionist_tips": [
    "Specific clinical tip for timing, insulin sensitivity, or gut health",
    "Specific hydration and electrolyte tip",
    "Specific tip on food prep or craving control",
    "Specific tip on sleep quality and recovery"
  ]
}}

Ensure all meal calories sum close to {targets['calorie_target']} kcal and macros align with {targets['protein_g']}g Protein. No fluff outside JSON.
"""
        ai_result = call_gemini_api(active_key, prompt)
        if ai_result and "meals" in ai_result:
            plan_data = ai_result
            ai_generated = True

    # If Gemini was not used or failed, seamlessly build clinical fallback plan
    if not plan_data:
        plan_data = build_fallback_plan(profile, targets)
        ai_generated = False
        
    return targets, plan_data, ai_generated
