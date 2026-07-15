"""
Product & Category Models

Category: top-level groupings (Electronics, Fashion, Home Accessories).
Product: individual sellable items with inventory tracking, pricing,
and fields optimized for search/filter (name, description, tags).
"""

import re
from datetime import datetime
from sqlalchemy import CheckConstraint

from app.extensions import db


def slugify(text: str) -> str:
    """Converts 'Photo Camera Pro' -> 'photo-camera-pro' for clean URLs."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_]+", "-", text)


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255), nullable=True)
    image_url = db.Column(db.String(255), nullable=True)  # category banner/icon
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # --- Relationships ---
    products = db.relationship("Product", back_populates="category", lazy="dynamic")

    def __repr__(self):
        return f"<Category {self.name}>"


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)

    # --- Core Info ---
    name = db.Column(db.String(150), nullable=False, index=True)
    slug = db.Column(db.String(180), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    tags = db.Column(db.String(255), nullable=True)  # comma-separated, powers search
    subcategory = db.Column(db.String(100), nullable=True, index=True)  # e.g. "Rings", "Chains", "Bracelets"

    # --- Pricing ---
    price = db.Column(db.Numeric(10, 2), nullable=False)
    compare_at_price = db.Column(db.Numeric(10, 2), nullable=True)  # for "was $X" strikethrough

    # --- Inventory ---
    stock_quantity = db.Column(db.Integer, default=0, nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=True)
    low_stock_threshold = db.Column(db.Integer, default=5, nullable=False)

    # --- Media ---
    image_url = db.Column(db.String(255), nullable=True)
    image_gallery = db.Column(db.Text, nullable=True)  # comma-separated additional gallery image URLs

    # --- Status ---
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # visible in storefront
    is_featured = db.Column(db.Boolean, default=False, nullable=False)  # homepage highlight

    # --- Timestamps ---
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # --- Foreign Keys ---
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)

    # --- Relationships ---
    category = db.relationship("Category", back_populates="products")
    cart_items = db.relationship("CartItem", back_populates="product", cascade="all, delete-orphan")
    wishlist_items = db.relationship("Wishlist", back_populates="product", cascade="all, delete-orphan")
    order_items = db.relationship("OrderItem", back_populates="product")

    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_product_price_non_negative"),
        CheckConstraint("stock_quantity >= 0", name="ck_product_stock_non_negative"),
    )

    # --- Stock helpers ---
    @property
    def in_stock(self) -> bool:
        return self.stock_quantity > 0

    @property
    def is_low_stock(self) -> bool:
        return 0 < self.stock_quantity <= self.low_stock_threshold

    @property
    def stock_status_label(self) -> str:
        """Maps to the mockup's status badges: Roso/Stotus style indicators."""
        if self.stock_quantity <= 0:
            return "Out of Stock"
        if self.is_low_stock:
            return "Low Stock"
        return "In Stock"

    @property
    def gallery_images(self):
        """Returns the full ordered list of image URLs for this product's gallery
        (main image first, then any additional angles), never empty duplicates."""
        images = []
        if self.image_url:
            images.append(self.image_url)
        if self.image_gallery:
            for url in self.image_gallery.split(","):
                url = url.strip()
                if url and url not in images:
                    images.append(url)
        return images

    @property
    def discount_percentage(self):
        if self.compare_at_price and self.compare_at_price > self.price:
            return round(100 * (1 - (self.price / self.compare_at_price)))
        return None

    def reduce_stock(self, quantity: int) -> None:
        """Called at checkout — raises if insufficient stock."""
        if quantity > self.stock_quantity:
            raise ValueError(f"Insufficient stock for '{self.name}'. Available: {self.stock_quantity}")
        self.stock_quantity -= quantity

    def restock(self, quantity: int) -> None:
        self.stock_quantity += quantity

    def __repr__(self):
        return f"<Product {self.name} (${self.price})>"
