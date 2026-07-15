"""
Orders Blueprint — handles order placement, status tracking, and order history.
"""

from flask import Blueprint

orders_bp = Blueprint(
    "orders",
    __name__,
    template_folder="../../../frontend/templates/orders",
    url_prefix="/orders",
)

from app.orders import routes  # noqa: E402,F401
