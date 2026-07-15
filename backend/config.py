"""
Application Configuration

Defines environment-specific configuration classes.
Values are pulled from environment variables (.env) with safe fallbacks
for local development only. Production MUST override SECRET_KEY.
"""

import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration shared across all environments."""

    # --- Core Security ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-not-for-production")

    # --- Database ---
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'instance', 'shopverse.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,  # avoids stale SQLite connections
    }

    # --- File Uploads ---
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 2 * 1024 * 1024))  # 2 MB
    UPLOAD_FOLDER = os.environ.get(
        "UPLOAD_FOLDER", os.path.join(basedir, "..", "frontend", "static", "uploads")
    )
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

    # --- Session / Auth ---
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    REMEMBER_COOKIE_DURATION = timedelta(days=14)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # --- Google OAuth ("Continue with Google") ---
    # Create credentials at https://console.cloud.google.com/apis/credentials
    # and set the authorized redirect URI to: <your-domain>/auth/google/callback
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

    # --- Stripe (real card payments) ---
    # Get your keys from https://dashboard.stripe.com/apikeys
    # Use the sk_test_/pk_test_ keys while developing, sk_live_/pk_live_ once you go live.
    # STRIPE_WEBHOOK_SECRET comes from the webhook endpoint you create at
    # https://dashboard.stripe.com/webhooks (event to listen for: checkout.session.completed)
    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_CURRENCY = os.environ.get("STRIPE_CURRENCY", "usd")

    # --- Pagination ---
    PRODUCTS_PER_PAGE = 12
    ORDERS_PER_PAGE = 10

    # --- Business Settings ---
    STORE_NAME = "ShopVerse"
    CURRENCY_SYMBOL = "$"
    ORDER_STATUSES = ["Pending", "Shipped", "Delivered", "Cancelled"]
    PAYMENT_METHODS = ["Cash on Delivery", "Card Payment (Stripe)"]


class DevelopmentConfig(Config):
    """Local development configuration."""

    DEBUG = True
    SQLALCHEMY_ECHO = False  # set True to log every SQL query while debugging


class ProductionConfig(Config):
    """Production configuration — enforces stricter security."""

    DEBUG = False
    SESSION_COOKIE_SECURE = True  # requires HTTPS

    def __init__(self):
        if self.SECRET_KEY == "dev-key-not-for-production":
            raise RuntimeError(
                "SECRET_KEY must be set via environment variable in production."
            )


class TestingConfig(Config):
    """Configuration used by the automated test suite."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
