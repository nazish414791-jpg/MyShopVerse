"""
Order & OrderItem Models

Order: a single checkout transaction — snapshots the shipping address
and totals at the time of purchase so later edits to a User's profile
never rewrite order history.

OrderItem: line items within an order — snapshots product name/price
at time of purchase, since Product prices can change later.
"""

import random
import string
from datetime import datetime
from sqlalchemy import CheckConstraint

from app.extensions import db

ORDER_STATUSES = ("Pending", "Shipped", "Delivered", "Cancelled")
PAYMENT_METHODS = ("Cash on Delivery", "Card Payment (Stripe)")


def generate_order_number() -> str:
    """Generates a human-friendly order reference, e.g. 'SV-7K2N9X'."""
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"SV-{suffix}"


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False, default=generate_order_number, index=True)

    customer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # --- Status ---
    status = db.Column(db.String(20), default="Pending", nullable=False, index=True)

    # --- Payment ---
    payment_method = db.Column(db.String(30), nullable=False, default="Cash on Delivery")
    is_paid = db.Column(db.Boolean, default=False, nullable=False)
    stripe_checkout_session_id = db.Column(db.String(120), nullable=True, index=True)
    stripe_payment_intent_id = db.Column(db.String(120), nullable=True)

    # --- Snapshot of shipping details (so profile edits don't rewrite history) ---
    shipping_full_name = db.Column(db.String(120), nullable=False)
    shipping_phone = db.Column(db.String(20), nullable=True)
    shipping_address_line = db.Column(db.String(255), nullable=False)
    shipping_city = db.Column(db.String(100), nullable=False)
    shipping_postal_code = db.Column(db.String(20), nullable=True)
    shipping_country = db.Column(db.String(100), nullable=False)

    # --- Totals (snapshotted at checkout time) ---
    subtotal = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    shipping_fee = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    total = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    notes = db.Column(db.String(255), nullable=True)  # customer's delivery instructions

    # --- Timestamps ---
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    delivered_at = db.Column(db.DateTime, nullable=True)

    # --- Relationships ---
    customer = db.relationship("User", back_populates="orders")
    items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("total >= 0", name="ck_order_total_non_negative"),
        CheckConstraint(f"status IN {ORDER_STATUSES}", name="ck_order_status_valid"),
        CheckConstraint(f"payment_method IN {PAYMENT_METHODS}", name="ck_order_payment_valid"),
    )

    # --- Status helpers ---
    def mark_shipped(self):
        self.status = "Shipped"

    def mark_delivered(self):
        self.status = "Delivered"
        self.delivered_at = datetime.utcnow()

    def mark_cancelled(self):
        self.status = "Cancelled"

    @property
    def status_color(self) -> str:
        """Maps order status to the theme's badge colors."""
        return {
            "Pending": "status-pending",
            "Shipped": "status-shipped",
            "Delivered": "status-success",
            "Cancelled": "status-cancelled",
        }.get(self.status, "status-pending")

    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self.items)

    def recalculate_totals(self):
        """Recomputes subtotal/total from current line items — call before commit."""
        from decimal import Decimal
        self.subtotal = sum((item.line_total for item in self.items), Decimal("0"))
        self.total = self.subtotal + self.shipping_fee

    def __repr__(self):
        return f"<Order {self.order_number} ({self.status})>"


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)  # nullable: product may later be deleted

    # --- Snapshot fields (protect order history from later product edits) ---
    product_name = db.Column(db.String(150), nullable=False)
    product_image_url = db.Column(db.String(255), nullable=True)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    # --- Relationships ---
    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product", back_populates="order_items")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_order_item_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_order_item_price_non_negative"),
    )

    @property
    def line_total(self):
        from decimal import Decimal
        return (self.unit_price * self.quantity).quantize(Decimal("0.01"))

    def __repr__(self):
        return f"<OrderItem {self.product_name} x{self.quantity}>"
