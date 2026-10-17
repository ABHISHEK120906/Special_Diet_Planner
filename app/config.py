import os
from dotenv import load_dotenv

# Load local environment variables if available
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "special-diet-planner-fallback-secret-2026")
    
    # Database URL sanitization for PostgreSQL & Serverless resilience
    raw_db_url = os.getenv("DATABASE_URL", "").strip()
    
    if raw_db_url:
        # Fix legacy postgres:// dialect prefix which breaks in SQLAlchemy 1.4+
        if raw_db_url.startswith("postgres://"):
            raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = raw_db_url
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_pre_ping": True,
            "pool_recycle": 300,
        }
    else:
        # Check if running in Vercel lambda (where /tmp is writable) or local
        if os.getenv("VERCEL"):
            SQLALCHEMY_DATABASE_URI = "sqlite:////tmp/diet_planner.db"
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            local_db = os.path.join(base_dir, "diet_planner.db")
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{local_db}"
        SQLALCHEMY_ENGINE_OPTIONS = {
            "connect_args": {"check_same_thread": False}
        }
    
    # AI Config
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    # Support multiple models in order of fallback
    GEMINI_MODELS = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-2.0-flash-exp",
    ]
