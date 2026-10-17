import json
import unittest
from api.index import app
from app.models import db, DietPlan

class TestDietPlanner(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()

    def test_health(self):
        res = self.client.get('/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "healthy")
        print("[PASS] /health passed:", data)

    def test_index_page(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"NutriGen", res.data)
        self.assertIn(b"Diet Plan", res.data)
        print("[PASS] GET / passed")

    def test_calculate_api(self):
        payload = {
            "weight": 75,
            "height": 178,
            "age": 28,
            "gender": "male",
            "activity_level": "moderately_active",
            "goal": "weight_loss",
            "dietary_preference": "vegetarian"
        }
        res = self.client.post('/api/calculate', 
                               data=json.dumps(payload), 
                               content_type='application/json')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertGreater(data["targets"]["calorie_target"], 1200)
        print("[PASS] POST /api/calculate passed:", data["targets"]["calorie_target"], "kcal")

    def test_generate_api(self):
        payload = {
            "user_name": "Test User",
            "weight": 70,
            "height": 172,
            "age": 25,
            "gender": "male",
            "activity_level": "moderately_active",
            "goal": "weight_loss",
            "dietary_preference": "vegetarian",
            "allergies": "Peanuts",
            "title": "Test 30-Day Diet Plan"
        }
        res = self.client.post('/api/generate',
                               data=json.dumps(payload),
                               content_type='application/json')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIsNotNone(data["plan_data"])
        self.assertIn("meals", data["plan_data"])
        self.assertEqual(len(data["plan_data"]["meals"]), 5)
        print("[PASS] POST /api/generate passed. Meals count:", len(data["plan_data"]["meals"]))
        
        # Test viewing the plan
        if data.get("plan_id"):
            view_res = self.client.get(f"/plan/{data['plan_id']}")
            self.assertEqual(view_res.status_code, 200)
            self.assertIn(b"Test 30-Day Diet Plan", view_res.data)
            print(f"[PASS] GET /plan/{data['plan_id']} passed")

    def test_auth_pages(self):
        login_res = self.client.get('/auth/login')
        self.assertEqual(login_res.status_code, 200)
        self.assertIn(b"Welcome back", login_res.data)
        print("[PASS] GET /auth/login passed")

        signup_res = self.client.get('/auth/signup')
        self.assertEqual(signup_res.status_code, 200)
        self.assertIn(b"Create your account", signup_res.data)
        print("[PASS] GET /auth/signup passed")

if __name__ == "__main__":
    unittest.main()
