import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    APP_ENV = os.getenv("APP_ENV", "development")
    SECRET_KEY = os.getenv("SECRET_KEY") or ("dev-only-change-me-before-deployment" if APP_ENV != "production" else None)
    if APP_ENV == "production" and not SECRET_KEY:
        raise RuntimeError("Set a strong SECRET_KEY environment variable before running in production.")
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "5000"))
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'attendance.db'}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = APP_ENV == "production"
    COLLEGE_LATITUDE = float(os.getenv("COLLEGE_LATITUDE", "19.076"))
    COLLEGE_LONGITUDE = float(os.getenv("COLLEGE_LONGITUDE", "72.8777"))
    GEOFENCE_RADIUS_METERS = float(os.getenv("GEOFENCE_RADIUS_METERS", "250"))
    FACE_MATCH_THRESHOLD = float(os.getenv("FACE_MATCH_THRESHOLD", "0.78"))
    # Opt-in only: enables clearly fictional demo accounts for a hosted class demo.
    SEED_DEMO_DATA = os.getenv("SEED_DEMO_DATA", "false").strip().lower() in {"1", "true", "yes"}
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
    FACE_UPLOAD_DIR = BASE_DIR / "uploads" / "faces"
