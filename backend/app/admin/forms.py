"""
Admin Forms

Forms used inside the admin dashboard for managing products,
categories, and updating order status.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, TextAreaField, DecimalField, IntegerField,
    BooleanField, SelectField, SubmitField
)
from wtforms.validators import DataRequired, Length, Optional, NumberRange


class CategoryForm(FlaskForm):
    name = StringField("Category Name", validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=255)])
    image = FileField("Category Image", validators=[Optional(), FileAllowed(["png", "jpg", "jpeg", "webp"], "Images only!")])
    is_active = BooleanField("Active (visible in storefront)", default=True)
    submit = SubmitField("Save Category")


class ProductForm(FlaskForm):
    name = StringField("Product Name", validators=[DataRequired(), Length(min=2, max=150)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=2000)])
    tags = StringField("Tags (comma-separated)", validators=[Optional(), Length(max=255)])

    category_id = SelectField("Category", coerce=int, validators=[DataRequired()])
    subcategory = StringField("Subcategory (e.g. Rings, Chains, Bracelets)", validators=[Optional(), Length(max=100)])

    price = DecimalField("Price", places=2, validators=[DataRequired(), NumberRange(min=0)])
    compare_at_price = DecimalField(
        "Compare-at Price (optional)", places=2, validators=[Optional(), NumberRange(min=0)]
    )

    stock_quantity = IntegerField("Stock Quantity", validators=[DataRequired(), NumberRange(min=0)])
    low_stock_threshold = IntegerField("Low Stock Threshold", default=5, validators=[DataRequired(), NumberRange(min=0)])
    sku = StringField("SKU", validators=[Optional(), Length(max=50)])

    image = FileField("Product Image", validators=[Optional(), FileAllowed(["png", "jpg", "jpeg", "webp"], "Images only!")])

    is_active = BooleanField("Active (visible in storefront)", default=True)
    is_featured = BooleanField("Featured (highlight on homepage)", default=False)

    submit = SubmitField("Save Product")


class OrderStatusForm(FlaskForm):
    status = SelectField(
        "Order Status",
        choices=[("Pending", "Pending"), ("Shipped", "Shipped"), ("Delivered", "Delivered"), ("Cancelled", "Cancelled")],
        validators=[DataRequired()],
    )
    submit = SubmitField("Update Status")
