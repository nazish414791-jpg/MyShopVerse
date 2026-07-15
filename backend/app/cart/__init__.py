"""
Cart Blueprint — handles shopping cart, wishlist, and checkout flow.
"""

from flask import Blueprint

cart_bp = Blueprint(
    "cart",
    __name__,
    template_folder="../../../frontend/templates/cart",
    url_prefix="/cart",
)

from app.cart import routes  # noqa: E402,F401
