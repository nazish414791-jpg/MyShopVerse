"""
Admin Blueprint — handles the admin dashboard: products, categories,
orders, customers, and sales analytics.
"""

from flask import Blueprint

admin_bp = Blueprint(
    "admin",
    __name__,
    template_folder="../../../frontend/templates/admin",
    url_prefix="/admin",
)

from app.admin import routes  # noqa: E402,F401
