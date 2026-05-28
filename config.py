"""config.py"""
import os
from datetime import timedelta

def _bool(v: str, default: bool = False) -> bool:
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")

class Config:
    SECRET_KEY               = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
    JWT_SECRET_KEY           = os.getenv("JWT_SECRET_KEY", "jwt-secret-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    SQLALCHEMY_DATABASE_URI  = os.getenv("DATABASE_URL", "sqlite:///learnai.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TEACHER_REGISTRATION_CODE = os.getenv("TEACHER_CODE", "TEACHER2024")
    # Open admin self-registration is on in dev so the demo Register page works.
    # Flip to false in production and create admins from another admin account.
    ALLOW_ADMIN_SELF_REGISTER = _bool(os.getenv("ALLOW_ADMIN_SELF_REGISTER"), default=True)
