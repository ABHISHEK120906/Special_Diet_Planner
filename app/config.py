import os
import ssl
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from dotenv import load_dotenv

# Load local environment variables if available
load_dotenv()


def _build_pg8000_url(url: str):
    """
    Convert a standard postgresql:// URL into a pg8000-compatible URL.
    - Switches dialect to postgresql+pg8000://
    - Strips query params that pg8000/SQLAlchemy don't accept in URL
      (sslmode, channel_binding)
    - Returns (clean_url, connect_args) tuple
    """
    if not url:
        return url, {}

    # Fix legacy dialect prefix
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)

    # Determine if SSL was requested
    sslmode = params.pop("sslmode", [None])[0]
    params.pop("channel_binding", None)  # psycopg3-only, not understood by pg8000

    # Rebuild URL with pg8000 dialect, clean query string
    clean_query = urlencode({k: v[0] for k, v in params.items()})
    pg8000_url = urlunparse(parsed._replace(
        scheme="postgresql+pg8000",
        query=clean_query
    ))

    # SSL connect_args for pg8000
    connect_args = {}
    if sslmode == "require":
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        connect_args["ssl_context"] = ssl_ctx

    return pg8000_url, connect_args


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "special-diet-planner-fallback-secret-2026")

    # Database URL — build for pg8000 or fall back to SQLite
    raw_db_url = os.getenv("DATABASE_URL", "").strip()

    if raw_db_url:
        _pg_url, _ssl_args = _build_pg8000_url(raw_db_url)
        SQLALCHEMY_DATABASE_URI = _pg_url
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_pre_ping": True,
            "pool_recycle": 300,
            "connect_args": _ssl_args,
        }
    else:
        # Vercel /tmp or local file-based SQLite fallback
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
    GEMINI_MODELS = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-2.0-flash-exp",
    ]
