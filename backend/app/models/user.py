"""
User Model

Represents both customers and admins (differentiated via `is_admin`).
Uses Flask-Login's UserMixin for session management and Flask-Bcrypt
for secure password hashing.
"""

from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import CheckConstraint

from app.extensions import db, bcrypt


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    # --- Identity ---
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    # Nullable because accounts created via "Continue with Google" have no local password
    password_hash = db.Column(db.String(255), nullable=True)
    # Set when the account was created (or later linked) via "Continue with Google"
    google_id = db.Column(db.String(255), unique=True, nullable=True, index=True)

    # --- Profile ---
    phone = db.Column(db.String(20), nullable=True)
    address_line = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    postal_code = db.Column(db.String(20), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)

    # --- Role / Status ---
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # soft-disable instead of deleting

    # --- Timestamps ---
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = db.Column(db.DateTime, nullable=True)

    # --- Relationships ---
    cart_items = db.relationship("CartItem", back_populates="user", cascade="all, delete-orphan")
    wishlist_items = db.relationship("Wishlist", back_populates="user", cascade="all, delete-orphan")
    orders = db.relationship("Order", back_populates="customer", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("length(full_name) > 0", name="ck_user_full_name_not_empty"),
    )

    # --- Password helpers ---
    def set_password(self, raw_password: str) -> None:
        self.password_hash = bcrypt.generate_password_hash(raw_password).decode("utf-8")

    def check_password(self, raw_password: str) -> bool:
        if not self.password_hash:
            # Google-only account — there's no local password to check against
            return False
        return bcrypt.check_password_hash(self.password_hash, raw_password)

    # --- Convenience properties ---
    @property
    def initials(self) -> str:
        """Used for avatar placeholders (e.g. 'Alina R.' -> 'AR')."""
        parts = self.full_name.split()
        return "".join(p[0].upper() for p in parts[:2]) if parts else "U"

    @property
    def order_count(self) -> int:
        return len(self.orders)

    def __repr__(self):
        return f"<User {self.email} (admin={self.is_admin})>"
