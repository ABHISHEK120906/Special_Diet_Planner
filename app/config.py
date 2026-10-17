import os
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse
from dotenv import load_dotenv

# Load local environment variables if available
load_dotenv()


def _sanitize_db_url(url: str) -> str:
    """
    Sanitize PostgreSQL URL for psycopg2 compatibility:
    - Fix legacy postgres:// -> postgresql://
    - Strip channel_binding=require (psycopg3-only, crashes psycopg2 on Vercel)
    - Strip sslmode from query string (passed via connect_args instead)
    """
    if not url:
        return url
    # Fix dialect prefix
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    # Strip psycopg3-only / conflicting query params
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    for remove_key in ("channel_binding",):
        params.pop(remove_key, None)
    clean_query = urlencode({k: v[0] for k, v in params.items()})
    cleaned = urlunparse(parsed._replace(query=clean_query))
    return cleaned


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "special-diet-planner-fallback-secret-2026")
    
    # Database URL sanitization for PostgreSQL & Serverless resilience
    raw_db_url = os.getenv("DATABASE_URL", "").strip()
    
    if raw_db_url:
        SQLALCHEMY_DATABASE_URI = _sanitize_db_url(raw_db_url)
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_pre_ping": True,
            "pool_recycle": 300,
            "connect_args": {"sslmode": "require"},
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
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # AI Config
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    # Support multiple models in order of fallback
    GEMINI_MODELS = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-2.0-flash-exp",
    ]
