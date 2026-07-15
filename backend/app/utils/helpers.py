"""
Helper Functions

Shared business logic used across multiple blueprints (cart, checkout,
admin analytics) to avoid duplicating calculations.
"""

import os
import uuid
from decimal import Decimal
from typing import Optional
from werkzeug.utils import secure_filename


def calculate_cart_summary(cart_items, shipping_fee=Decimal("0")):
    """
    Given a list of CartItem objects, returns a dict with subtotal,
    shipping fee, and total — all as Decimal for currency accuracy.
    """
    subtotal = sum((item.subtotal for item in cart_items), Decimal("0"))
    total = subtotal + shipping_fee

    return {
        "subtotal": subtotal,
        "shipping_fee": shipping_fee,
        "total": total,
        "item_count": sum(item.quantity for item in cart_items),
    }


def get_standard_shipping_fee(subtotal: Decimal) -> Decimal:
    """Simple flat-rate shipping logic: free above $50, otherwise $5 flat fee."""
    if subtotal >= Decimal("50"):
        return Decimal("0")
    return Decimal("5.00")


def save_uploaded_image(file_storage, upload_folder, allowed_extensions=None) -> Optional[str]:
    """
    Saves an uploaded image with a unique filename to avoid collisions.
    Returns the relative static path (e.g. 'uploads/abc123.jpg') or None if no file given.
    """
    if not file_storage or not file_storage.filename:
        return None

    allowed_extensions = allowed_extensions or {"png", "jpg", "jpeg", "webp"}
    original_name = secure_filename(file_storage.filename)
    extension = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""

    if extension not in allowed_extensions:
        return None

    unique_name = f"{uuid.uuid4().hex}.{extension}"
    file_storage.save(os.path.join(upload_folder, unique_name))
    return f"uploads/{unique_name}"
