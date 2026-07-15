"""
Models Package

All model modules are imported here so that:
  1. Flask-Migrate can detect every table when running `flask db migrate`.
  2. Other modules can simply do `from app.models import User, Product, ...`
"""

from app.models.user import User
from app.models.product import Category, Product
from app.models.cart import CartItem, Wishlist
from app.models.order import Order, OrderItem

__all__ = ["User", "Category", "Product", "CartItem", "Wishlist", "Order", "OrderItem"]
