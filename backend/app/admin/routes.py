"""
Admin Routes

The admin dashboard: sales analytics, product/category CRUD, order
status management, and customer overview. Every route here requires
both @login_required and @admin_required.
"""

from datetime import datetime, timedelta
from decimal import Decimal

from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from sqlalchemy import func

from app.admin import admin_bp
from app.admin.forms import ProductForm, CategoryForm, OrderStatusForm
from app.extensions import db
from app.models.user import User
from app.models.product import Product, Category, slugify
from app.models.order import Order, OrderItem, ORDER_STATUSES
from app.utils.decorators import admin_required
from app.utils.helpers import save_uploaded_image


@admin_bp.before_request
@login_required
@admin_required
def guard_admin_routes():
    """Runs before every admin route — enforces login + admin role."""
    pass


# ============================================================
#  DASHBOARD
# ============================================================

@admin_bp.route("/")
def dashboard():
    total_sales = (
        db.session.query(func.coalesce(func.sum(Order.total), 0))
        .filter(Order.status != "Cancelled")
        .scalar()
    )
    total_orders = Order.query.count()
    total_customers = User.query.filter_by(is_admin=False).count()
    total_products = Product.query.count()
    out_of_stock_count = Product.query.filter_by(stock_quantity=0, is_active=True).count()

    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(6).all()

    low_stock_products = (
        Product.query.filter(Product.stock_quantity <= Product.low_stock_threshold, Product.is_active.is_(True))
        .order_by(Product.stock_quantity.asc())
        .limit(6)
        .all()
    )

    # --- Sales-by-month for the last 6 months (for the chart) ---
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    monthly_rows = (
        db.session.query(
            func.strftime("%Y-%m", Order.created_at).label("month"),
            func.sum(Order.total).label("sales"),
            func.count(Order.id).label("order_count"),
        )
        .filter(Order.created_at >= six_months_ago, Order.status != "Cancelled")
        .group_by("month")
        .order_by("month")
        .all()
    )
    chart_labels = [row.month for row in monthly_rows]
    chart_sales = [float(row.sales) for row in monthly_rows]
    chart_orders = [row.order_count for row in monthly_rows]

    # --- Order status breakdown (for the donut chart) ---
    status_rows = (
        db.session.query(Order.status, func.count(Order.id))
        .group_by(Order.status)
        .all()
    )
    status_counts = {status: count for status, count in status_rows}
    status_labels = list(ORDER_STATUSES)
    status_values = [status_counts.get(s, 0) for s in status_labels]

    # --- Top 5 best-selling products (by units sold), for the horizontal bar list ---
    top_products_rows = (
        db.session.query(
            OrderItem.product_name,
            func.sum(OrderItem.quantity).label("units_sold"),
        )
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.status != "Cancelled")
        .group_by(OrderItem.product_name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(6)
        .all()
    )
    top_products = [{"name": row.product_name, "units": int(row.units_sold)} for row in top_products_rows]
    max_units = max([p["units"] for p in top_products], default=1)

    # --- Revenue by category (for the donut chart) ---
    line_total_expr = OrderItem.unit_price * OrderItem.quantity
    category_revenue_rows = (
        db.session.query(
            Category.name,
            func.sum(line_total_expr).label("revenue"),
        )
        .select_from(OrderItem)
        .join(Order, Order.id == OrderItem.order_id)
        .join(Product, Product.id == OrderItem.product_id)
        .join(Category, Category.id == Product.category_id)
        .filter(Order.status != "Cancelled")
        .group_by(Category.name)
        .order_by(func.sum(line_total_expr).desc())
        .all()
    )
    category_labels = [row.name for row in category_revenue_rows]
    category_values = [float(row.revenue) for row in category_revenue_rows]

    return render_template(
        "admin/dashboard.html",
        total_sales=total_sales,
        total_orders=total_orders,
        total_customers=total_customers,
        total_products=total_products,
        out_of_stock_count=out_of_stock_count,
        recent_orders=recent_orders,
        low_stock_products=low_stock_products,
        chart_labels=chart_labels,
        chart_sales=chart_sales,
        chart_orders=chart_orders,
        status_labels=status_labels,
        status_values=status_values,
        top_products=top_products,
        max_units=max_units,
        category_labels=category_labels,
        category_values=category_values,
    )


# ============================================================
#  PRODUCTS
# ============================================================

@admin_bp.route("/products")
def manage_products():
    page = request.args.get("page", 1, type=int)
    query = request.args.get("q", "").strip()

    products_query = Product.query
    if query:
        products_query = products_query.filter(Product.name.ilike(f"%{query}%"))

    pagination = products_query.order_by(Product.created_at.desc()).paginate(page=page, per_page=10, error_out=False)

    return render_template("admin/manage_products.html", products=pagination.items, pagination=pagination, query=query)


@admin_bp.route("/products/new", methods=["GET", "POST"])
def new_product():
    form = ProductForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]

    if form.validate_on_submit():
        image_path = save_uploaded_image(form.image.data, current_app.config["UPLOAD_FOLDER"])

        product = Product(
            name=form.name.data.strip(),
            slug=slugify(form.name.data),
            description=form.description.data,
            tags=form.tags.data,
            category_id=form.category_id.data,
            subcategory=form.subcategory.data or None,
            price=form.price.data,
            compare_at_price=form.compare_at_price.data or None,
            stock_quantity=form.stock_quantity.data,
            low_stock_threshold=form.low_stock_threshold.data,
            sku=form.sku.data or None,
            image_url=url_for("static", filename=image_path) if image_path else None,
            is_active=form.is_active.data,
            is_featured=form.is_featured.data,
        )
        db.session.add(product)
        db.session.commit()

        flash(f"Product '{product.name}' created successfully.", "success")
        return redirect(url_for("admin.manage_products"))

    return render_template("admin/product_form.html", form=form, mode="create")


@admin_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]

    if request.method == "GET":
        form.category_id.data = product.category_id

    if form.validate_on_submit():
        image_path = save_uploaded_image(form.image.data, current_app.config["UPLOAD_FOLDER"])

        product.name = form.name.data.strip()
        product.slug = slugify(form.name.data)
        product.description = form.description.data
        product.tags = form.tags.data
        product.category_id = form.category_id.data
        product.subcategory = form.subcategory.data or None
        product.price = form.price.data
        product.compare_at_price = form.compare_at_price.data or None
        product.stock_quantity = form.stock_quantity.data
        product.low_stock_threshold = form.low_stock_threshold.data
        product.sku = form.sku.data or None
        product.is_active = form.is_active.data
        product.is_featured = form.is_featured.data
        if image_path:
            product.image_url = url_for("static", filename=image_path)

        db.session.commit()
        flash(f"Product '{product.name}' updated successfully.", "success")
        return redirect(url_for("admin.manage_products"))

    return render_template("admin/product_form.html", form=form, mode="edit", product=product)


@admin_bp.route("/products/<int:product_id>/delete", methods=["POST"])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    name = product.name

    # Soft-delete pattern: if the product has order history, deactivate rather than hard-delete
    if product.order_items:
        product.is_active = False
        db.session.commit()
        flash(f"'{name}' has order history, so it was deactivated instead of deleted.", "warning")
    else:
        db.session.delete(product)
        db.session.commit()
        flash(f"'{name}' deleted successfully.", "success")

    return redirect(url_for("admin.manage_products"))


# ============================================================
#  CATEGORIES
# ============================================================

@admin_bp.route("/categories")
def manage_categories():
    categories = Category.query.order_by(Category.name.asc()).all()
    return render_template("admin/manage_categories.html", categories=categories)


@admin_bp.route("/categories/new", methods=["GET", "POST"])
def new_category():
    form = CategoryForm()

    if form.validate_on_submit():
        image_path = save_uploaded_image(form.image.data, current_app.config["UPLOAD_FOLDER"])

        category = Category(
            name=form.name.data.strip(),
            slug=slugify(form.name.data),
            description=form.description.data,
            image_url=url_for("static", filename=image_path) if image_path else None,
            is_active=form.is_active.data,
        )
        db.session.add(category)
        db.session.commit()

        flash(f"Category '{category.name}' created successfully.", "success")
        return redirect(url_for("admin.manage_categories"))

    return render_template("admin/category_form.html", form=form, mode="create")


@admin_bp.route("/categories/<int:category_id>/edit", methods=["GET", "POST"])
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)

    if form.validate_on_submit():
        image_path = save_uploaded_image(form.image.data, current_app.config["UPLOAD_FOLDER"])

        category.name = form.name.data.strip()
        category.slug = slugify(form.name.data)
        category.description = form.description.data
        category.is_active = form.is_active.data
        if image_path:
            category.image_url = url_for("static", filename=image_path)

        db.session.commit()
        flash(f"Category '{category.name}' updated successfully.", "success")
        return redirect(url_for("admin.manage_categories"))

    return render_template("admin/category_form.html", form=form, mode="edit", category=category)


@admin_bp.route("/categories/<int:category_id>/delete", methods=["POST"])
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)

    if category.products.count() > 0:
        flash(f"Cannot delete '{category.name}' — it still has products assigned to it.", "danger")
        return redirect(url_for("admin.manage_categories"))

    name = category.name
    db.session.delete(category)
    db.session.commit()
    flash(f"Category '{name}' deleted successfully.", "success")
    return redirect(url_for("admin.manage_categories"))


# ============================================================
#  ORDERS
# ============================================================

@admin_bp.route("/orders")
def manage_orders():
    page = request.args.get("page", 1, type=int)
    status_filter = request.args.get("status", "").strip()

    orders_query = Order.query
    if status_filter in ORDER_STATUSES:
        orders_query = orders_query.filter_by(status=status_filter)

    pagination = orders_query.order_by(Order.created_at.desc()).paginate(page=page, per_page=15, error_out=False)

    return render_template(
        "admin/manage_orders.html",
        orders=pagination.items,
        pagination=pagination,
        status_filter=status_filter,
        order_statuses=ORDER_STATUSES,
    )


@admin_bp.route("/orders/<order_number>", methods=["GET", "POST"])
def admin_order_detail(order_number):
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    form = OrderStatusForm(status=order.status)

    if form.validate_on_submit():
        new_status = form.status.data

        if new_status == "Delivered" and order.status != "Delivered":
            order.mark_delivered()
        elif new_status == "Shipped":
            order.mark_shipped()
        elif new_status == "Cancelled":
            order.mark_cancelled()
        else:
            order.status = new_status

        db.session.commit()
        flash(f"Order {order.order_number} status updated to '{new_status}'.", "success")
        return redirect(url_for("admin.admin_order_detail", order_number=order.order_number))

    return render_template("admin/order_detail.html", order=order, form=form)


# ============================================================
#  CUSTOMERS
# ============================================================

@admin_bp.route("/customers")
def manage_customers():
    page = request.args.get("page", 1, type=int)
    query = request.args.get("q", "").strip()

    customers_query = User.query.filter_by(is_admin=False)
    if query:
        customers_query = customers_query.filter(
            (User.full_name.ilike(f"%{query}%")) | (User.email.ilike(f"%{query}%"))
        )

    pagination = customers_query.order_by(User.created_at.desc()).paginate(page=page, per_page=15, error_out=False)

    return render_template("admin/manage_customers.html", customers=pagination.items, pagination=pagination, query=query)


@admin_bp.route("/customers/<int:customer_id>")
def customer_detail(customer_id):
    customer = User.query.filter_by(id=customer_id, is_admin=False).first_or_404()
    orders = Order.query.filter_by(customer_id=customer.id).order_by(Order.created_at.desc()).all()
    total_spent = sum((o.total for o in orders if o.status != "Cancelled"), Decimal("0"))

    return render_template("admin/customer_detail.html", customer=customer, orders=orders, total_spent=total_spent)


# ============================================================
#  ANALYTICS
# ============================================================

@admin_bp.route("/analytics")
def analytics():
    from app.models.order import OrderItem

    top_products = (
        db.session.query(
            OrderItem.product_name,
            func.sum(OrderItem.quantity).label("units_sold"),
            func.sum(OrderItem.unit_price * OrderItem.quantity).label("revenue"),
        )
        .group_by(OrderItem.product_name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(10)
        .all()
    )

    orders_by_status = (
        db.session.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
    )

    return render_template("admin/analytics.html", top_products=top_products, orders_by_status=dict(orders_by_status))
