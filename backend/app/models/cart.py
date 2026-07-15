"""
Cart & Wishlist Models

CartItem: one row per (user, product) pair with a quantity — represents
what's currently in a customer's shopping cart.

Wishlist: one row per (user, product) pair — the "save for later" list
shown on the customer profile page.
"""

from datetime import datetime
from sqlalchemy import CheckConstraint, UniqueConstraint

from app.extensions import db


class CartItem(db.Model):
    __tablename__ = "cart_items"

    id = db.Column(db.Integer, primary_key=True)

    quantity = db.Column(db.Integer, default=1, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)

    added_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # --- Relationships ---
    user = db.relationship("User", back_populates="cart_items")
    product = db.relationship("Product", back_populates="cart_items")

    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_cart_user_product"),
        CheckConstraint("quantity > 0", name="ck_cart_quantity_positive"),
    )

    @property
    def subtotal(self):
        from decimal import Decimal
        return (self.product.price * self.quantity).quantize(Decimal("0.01"))

    def __repr__(self):
        return f"<CartItem user={self.user_id} product={self.product_id} qty={self.quantity}>"


class Wishlist(db.Model):
    __tablename__ = "wishlist_items"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)

    added_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # --- Relationships ---
    user = db.relationship("User", back_populates="wishlist_items")
    product = db.relationship("Product", back_populates="wishlist_items")

    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_wishlist_user_product"),
    )

    def __repr__(self):
        return f"<Wishlist user={self.user_id} product={self.product_id}>"
