"""Application configuration."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/fraud_detection.db")

# Model paths
MODELS_DIR = BASE_DIR / "models"

# Auth
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production-please")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Demo users, prototype only. Replace with a real users table in production.
DEMO_USERS = {
    "analyst": {"password": "analyst123", "role": "analyst"},
    "admin": {"password": "admin123", "role": "admin"},
}

# CORS
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173,https://fraud-detection-web-jrf0.onrender.com"
).split(",")

# Model settings
DEFAULT_THRESHOLD = 0.5
TOP_SHAP_FEATURES = 6
