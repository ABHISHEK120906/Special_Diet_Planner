from datetime import datetime, timezone
import json
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class DietPlan(db.Model):
    __tablename__ = 'diet_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False, default="Personalized Diet Plan")
    user_name = db.Column(db.String(100), nullable=False, default="Guest")
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    target_weight = db.Column(db.Float, nullable=True)
    height = db.Column(db.Float, nullable=False)
    activity_level = db.Column(db.String(50), nullable=False)
    goal = db.Column(db.String(80), nullable=False)
    dietary_preference = db.Column(db.String(80), nullable=False)
    allergies = db.Column(db.String(255), nullable=True)
    
    # Calculated Metrics
    bmr = db.Column(db.Float, nullable=False)
    tdee = db.Column(db.Float, nullable=False)
    target_calories = db.Column(db.Float, nullable=False)
    protein_g = db.Column(db.Float, nullable=False)
    carbs_g = db.Column(db.Float, nullable=False)
    fat_g = db.Column(db.Float, nullable=False)
    
    # Structured Plan Payload (stored as JSON string for maximum portability between SQLite and PostgreSQL)
    plan_json = db.Column(db.Text, nullable=False)
    ai_generated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def get_plan_data(self):
        try:
            return json.loads(self.plan_json)
        except Exception:
            return {}

    def set_plan_data(self, data):
        self.plan_json = json.dumps(data)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "user_name": self.user_name,
            "age": self.age,
            "gender": self.gender,
            "weight": self.weight,
            "target_weight": self.target_weight,
            "height": self.height,
            "activity_level": self.activity_level,
            "goal": self.goal,
            "dietary_preference": self.dietary_preference,
            "allergies": self.allergies,
            "bmr": round(self.bmr, 1),
            "tdee": round(self.tdee, 1),
            "target_calories": round(self.target_calories, 1),
            "protein_g": round(self.protein_g, 1),
            "carbs_g": round(self.carbs_g, 1),
            "fat_g": round(self.fat_g, 1),
            "ai_generated": self.ai_generated,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M"),
            "plan_data": self.get_plan_data()
        }

def init_db(app):
    """Safely initialize the database with resilience against serverless connection faults."""
    with app.app_context():
        try:
            db.create_all()
            print("INFO: Database initialized successfully.")
        except Exception as e:
            # Prevent Vercel function cold start crash if DB credentials or network has temporary hiccups
            print(f"WARNING: Could not initialize database tables immediately: {e}")
