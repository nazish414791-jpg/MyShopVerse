"""
Orders Routes

Customer-facing order management: paginated order history and
individual order detail pages with a visual status timeline.
"""

from flask import render_template, request, current_app
from flask_login import login_required, current_user

from app.orders import orders_bp
from app.models.order import Order


@orders_bp.route("/")
@login_required
def order_history():
    page = request.args.get("page", 1, type=int)

    pagination = (
        Order.query.filter_by(customer_id=current_user.id)
        .order_by(Order.created_at.desc())
        .paginate(page=page, per_page=current_app.config["ORDERS_PER_PAGE"], error_out=False)
    )

    return render_template("orders/order_history.html", orders=pagination.items, pagination=pagination)


@orders_bp.route("/<order_number>")
@login_required
def order_detail(order_number):
    order = Order.query.filter_by(order_number=order_number, customer_id=current_user.id).first_or_404()

    # Defines the visual timeline steps — Cancelled is handled separately in the template
    timeline_steps = ["Pending", "Shipped", "Delivered"]
    current_step_index = timeline_steps.index(order.status) if order.status in timeline_steps else -1

    return render_template(
        "orders/order_detail.html",
        order=order,
        timeline_steps=timeline_steps,
        current_step_index=current_step_index,
    )
