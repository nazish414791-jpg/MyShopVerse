"""
Auth Blueprint — handles registration, login, logout, and profile management.
"""

from flask import Blueprint

auth_bp = Blueprint(
    "auth",
    __name__,
    template_folder="../../../frontend/templates/auth",
    url_prefix="/auth",
)

from app.auth import routes  # noqa: E402,F401  (import at bottom avoids circular import)
