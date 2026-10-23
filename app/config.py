import os
import ssl
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from dotenv import load_dotenv

# Load local environment variables if available
load_dotenv()


def _build_psycopg2_url(url: str):
    """
    Convert a standard postgresql:// or postgres:// URL into a
    psycopg2-compatible URL.
    - Switches dialect to postgresql+psycopg2://
    - Strips query params that psycopg2/SQLAlchemy don't accept in the URL
      (channel_binding, sslmode handled via connect_args)
    - Returns (clean_url, connect_args, engine_options) tuple
    """
    if not url:
        return url, {}, {}

    # Normalise legacy shorthand
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)

    # Lift SSL params out of query string
    sslmode = params.pop("sslmode", [None])[0]
    params.pop("channel_binding", None)   # psycopg3-only, ignored by psycopg2

    # Rebuild URL with psycopg2 dialect
    clean_query = urlencode({k: v[0] for k, v in params.items()})
    pg_url = urlunparse(parsed._replace(
        scheme="postgresql+psycopg2",
        query=clean_query
    ))

    connect_args = {}
    if sslmode in ("require", "verify-ca", "verify-full"):
        connect_args["sslmode"] = sslmode

    engine_options = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
    if connect_args:
        engine_options["connect_args"] = connect_args

    return pg_url, connect_args, engine_options


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "special-diet-planner-fallback-secret-2026")

    # Database URL — build for psycopg2 or fall back to SQLite
    raw_db_url = os.getenv("DATABASE_URL", "").strip()

    if raw_db_url:
        _pg_url, _ssl_args, _engine_opts = _build_psycopg2_url(raw_db_url)
        SQLALCHEMY_DATABASE_URI = _pg_url
        SQLALCHEMY_ENGINE_OPTIONS = _engine_opts
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
