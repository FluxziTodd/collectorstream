"""
Configuration for CollectorStream API
"""

import os
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

class Config:
    # Server
    HOST = os.environ.get("API_HOST", "0.0.0.0")
    PORT = int(os.environ.get("API_PORT", 8000))
    DEBUG = os.environ.get("API_DEBUG", "true").lower() == "true"

    # Security
    JWT_SECRET = os.environ.get("JWT_SECRET")
    if not JWT_SECRET:
        raise ValueError("JWT_SECRET environment variable must be set in production!")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24 * 7  # 1 week

    # Database
    DATABASE_PATH = os.environ.get(
        "DATABASE_PATH",
        os.path.join(os.path.dirname(__file__), "..", "data", "collectorstream.db")
    )

    # AWS S3
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
    S3_BUCKET = os.environ.get("S3_BUCKET", "collectorstream-cards")

    # Ximilar API (card identification)
    XIMILAR_API_KEY = os.environ.get("XIMILAR_API_KEY", "")

    # Email (for password reset)
    SMTP_HOST = os.environ.get("SMTP_HOST", "")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    EMAIL_FROM = os.environ.get("EMAIL_FROM", "noreply@collectorstream.com")

config = Config()
