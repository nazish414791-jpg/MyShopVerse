"""
Products Blueprint — handles product listing, search, filtering, and category browsing.
"""

from flask import Blueprint

products_bp = Blueprint(
    "products",
    __name__,
    template_folder="../../../frontend/templates/products",
    url_prefix="/products",
)

from app.products import routes  # noqa: E402,F401
