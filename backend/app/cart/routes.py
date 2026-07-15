"""
Cart Routes

Handles shopping cart operations (add/update/remove), wishlist
toggling, and the full checkout flow (shipping details -> payment
method -> order creation -> stock deduction -> confirmation).
"""

from decimal import Decimal

from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user

from app.cart import cart_bp
from app.extensions import db, csrf
from app.models.product import Product
from app.models.cart import CartItem, Wishlist
from app.models.order import Order, OrderItem
from app.utils.helpers import calculate_cart_summary, get_standard_shipping_fee
from app.utils import stripe_client
from app.utils.stripe_client import StripeError


# ============================================================
#  CART
# ============================================================

@cart_bp.route("/")
@login_required
def view_cart():
    cart_items = (
        CartItem.query.filter_by(user_id=current_user.id)
        .join(Product)
        .order_by(CartItem.added_at.desc())
        .all()
    )

    summary = calculate_cart_summary(cart_items)
    shipping_fee = get_standard_shipping_fee(summary["subtotal"])
    summary = calculate_cart_summary(cart_items, shipping_fee)

    return render_template("cart/cart.html", cart_items=cart_items, summary=summary)


@cart_bp.route("/add/<int:product_id>", methods=["POST"])
@login_required
def add_to_cart(product_id):
    product = Product.query.filter_by(id=product_id, is_active=True).first_or_404()

    quantity = request.form.get("quantity", 1, type=int)
    quantity = max(1, quantity)

    if not product.in_stock:
        flash(f"'{product.name}' is currently out of stock.", "danger")
        return redirect(request.referrer or url_for("products.listing"))

    existing_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product.id).first()

    if existing_item:
        new_quantity = existing_item.quantity + quantity
        if new_quantity > product.stock_quantity:
            flash(f"Only {product.stock_quantity} units of '{product.name}' available.", "warning")
            new_quantity = product.stock_quantity
        existing_item.quantity = new_quantity
    else:
        if quantity > product.stock_quantity:
            quantity = product.stock_quantity
        existing_item = CartItem(user_id=current_user.id, product_id=product.id, quantity=quantity)
        db.session.add(existing_item)

    db.session.commit()
    flash(f"'{product.name}' added to your cart.", "success")
    return redirect(request.referrer or url_for("products.listing"))


@cart_bp.route("/update/<int:item_id>", methods=["POST"])
@login_required
def update_cart_item(item_id):
    item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()

    quantity = request.form.get("quantity", 1, type=int)

    if quantity <= 0:
        db.session.delete(item)
        flash("Item removed from your cart.", "info")
    else:
        if quantity > item.product.stock_quantity:
            quantity = item.product.stock_quantity
            flash(f"Only {item.product.stock_quantity} units of '{item.product.name}' available.", "warning")
        item.quantity = quantity
        flash("Cart updated.", "success")

    db.session.commit()
    return redirect(url_for("cart.view_cart"))


@cart_bp.route("/remove/<int:item_id>", methods=["POST"])
@login_required
def remove_from_cart(item_id):
    item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    product_name = item.product.name
    db.session.delete(item)
    db.session.commit()
    flash(f"'{product_name}' removed from your cart.", "info")
    return redirect(url_for("cart.view_cart"))


# ============================================================
#  WISHLIST
# ============================================================

@cart_bp.route("/wishlist")
@login_required
def view_wishlist():
    wishlist_items = (
        Wishlist.query.filter_by(user_id=current_user.id)
        .join(Product)
        .order_by(Wishlist.added_at.desc())
        .all()
    )
    return render_template("cart/wishlist.html", wishlist_items=wishlist_items)


@cart_bp.route("/wishlist/toggle/<int:product_id>", methods=["POST"])
@login_required
def toggle_wishlist(product_id):
    product = Product.query.filter_by(id=product_id, is_active=True).first_or_404()

    existing = Wishlist.query.filter_by(user_id=current_user.id, product_id=product.id).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        flash(f"'{product.name}' removed from your wishlist.", "info")
    else:
        db.session.add(Wishlist(user_id=current_user.id, product_id=product.id))
        db.session.commit()
        flash(f"'{product.name}' added to your wishlist.", "success")

    return redirect(request.referrer or url_for("products.listing"))


@cart_bp.route("/wishlist/remove/<int:item_id>", methods=["POST"])
@login_required
def remove_from_wishlist(item_id):
    item = Wishlist.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash("Removed from wishlist.", "info")
    return redirect(url_for("cart.view_wishlist"))


# ============================================================
#  CHECKOUT
# ============================================================

@cart_bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).join(Product).all()

    if not cart_items:
        flash("Your cart is empty. Add some products before checking out.", "warning")
        return redirect(url_for("products.listing"))

    # Validate stock availability before showing/checking out
    out_of_stock_items = [item for item in cart_items if item.quantity > item.product.stock_quantity]
    if out_of_stock_items:
        names = ", ".join(item.product.name for item in out_of_stock_items)
        flash(f"Some items no longer have enough stock: {names}. Please update your cart.", "danger")
        return redirect(url_for("cart.view_cart"))

    subtotal = sum((item.subtotal for item in cart_items), Decimal("0"))
    shipping_fee = get_standard_shipping_fee(subtotal)
    summary = calculate_cart_summary(cart_items, shipping_fee)

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        address_line = request.form.get("address_line", "").strip()
        city = request.form.get("city", "").strip()
        postal_code = request.form.get("postal_code", "").strip()
        country = request.form.get("country", "").strip()
        payment_method = request.form.get("payment_method", "Cash on Delivery")
        notes = request.form.get("notes", "").strip()

        # --- Server-side validation of required shipping fields ---
        errors = []
        if not full_name:
            errors.append("Full name is required.")
        if not address_line:
            errors.append("Address is required.")
        if not city:
            errors.append("City is required.")
        if not country:
            errors.append("Country is required.")
        if payment_method not in ("Cash on Delivery", "Card Payment (Stripe)"):
            errors.append("Please select a valid payment method.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("cart/checkout.html", cart_items=cart_items, summary=summary)

        # --- Create the order (snapshot shipping + line items) ---
        order = Order(
            customer_id=current_user.id,
            shipping_full_name=full_name,
            shipping_phone=phone,
            shipping_address_line=address_line,
            shipping_city=city,
            shipping_postal_code=postal_code,
            shipping_country=country,
            shipping_fee=shipping_fee,
            payment_method=payment_method,
            is_paid=False,
            notes=notes,
        )
        db.session.add(order)
        db.session.flush()  # get order.id before adding items

        for cart_item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product.id,
                product_name=cart_item.product.name,
                product_image_url=cart_item.product.image_url,
                unit_price=cart_item.product.price,
                quantity=cart_item.quantity,
            )
            order.items.append(order_item)
            cart_item.product.reduce_stock(cart_item.quantity)  # raises if insufficient
            db.session.delete(cart_item)  # clear from cart after purchase

        order.recalculate_totals()
        db.session.commit()

        # --- Cash on Delivery: order is placed immediately, no gateway involved ---
        if payment_method == "Cash on Delivery":
            flash(f"Order {order.order_number} placed successfully!", "success")
            return redirect(url_for("cart.order_confirmation", order_number=order.order_number))

        # --- Card Payment: hand off to Stripe's hosted, PCI-compliant checkout page ---
        return redirect(url_for("cart.stripe_checkout", order_number=order.order_number))

    return render_template("cart/checkout.html", cart_items=cart_items, summary=summary)


# ============================================================
#  STRIPE CARD PAYMENTS
# ============================================================

@cart_bp.route("/checkout/stripe/<order_number>")
@login_required
def stripe_checkout(order_number):
    """Creates (or re-creates) a Stripe Checkout Session for an unpaid order and redirects to it."""
    order = Order.query.filter_by(order_number=order_number, customer_id=current_user.id).first_or_404()

    if order.is_paid:
        return redirect(url_for("cart.order_confirmation", order_number=order.order_number))

    success_url = url_for("cart.stripe_success", order_number=order.order_number, _external=True) + "?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = url_for("cart.stripe_cancel", order_number=order.order_number, _external=True)

    try:
        session = stripe_client.create_checkout_session(order, success_url, cancel_url)
    except StripeError as exc:
        current_app.logger.error("Stripe checkout session creation failed: %s", exc)
        flash(f"Payment could not be started: {exc}", "danger")
        return redirect(url_for("cart.order_confirmation", order_number=order.order_number))

    order.stripe_checkout_session_id = session["id"]
    db.session.commit()

    return redirect(session["url"])


@cart_bp.route("/checkout/stripe/success/<order_number>")
@login_required
def stripe_success(order_number):
    """Stripe redirects here after a successful payment; we double-check the session before marking paid."""
    order = Order.query.filter_by(order_number=order_number, customer_id=current_user.id).first_or_404()
    session_id = request.args.get("session_id")

    if session_id and not order.is_paid:
        try:
            session = stripe_client.retrieve_checkout_session(session_id)
            if session.get("payment_status") == "paid":
                order.is_paid = True
                order.stripe_payment_intent_id = session.get("payment_intent")
                db.session.commit()
                flash(f"Payment received — order {order.order_number} is confirmed!", "success")
        except StripeError as exc:
            current_app.logger.error("Stripe session verification failed: %s", exc)

    if not order.is_paid:
        flash("We couldn't confirm your payment yet. If you were charged, this will update shortly.", "warning")

    return redirect(url_for("cart.order_confirmation", order_number=order.order_number))


@cart_bp.route("/checkout/stripe/cancel/<order_number>")
@login_required
def stripe_cancel(order_number):
    """Stripe redirects here if the customer backs out of the hosted payment page."""
    order = Order.query.filter_by(order_number=order_number, customer_id=current_user.id).first_or_404()
    flash("Payment was cancelled. Your order is saved — you can retry payment anytime from your order history.", "info")
    return redirect(url_for("orders.order_detail", order_number=order.order_number) if _has_order_detail() else url_for("cart.order_confirmation", order_number=order.order_number))


def _has_order_detail():
    return "orders.order_detail" in current_app.view_functions


@cart_bp.route("/checkout/stripe/webhook", methods=["POST"])
@csrf.exempt
def stripe_webhook():
    """
    Stripe calls this server-to-server whenever a payment event happens —
    the reliable source of truth, independent of whether the customer's
    browser makes it back to the success page.

    Configure at https://dashboard.stripe.com/webhooks pointing to:
        <your-domain>/cart/checkout/stripe/webhook
    Listening for event: checkout.session.completed
    """
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature", "")

    if not stripe_client.verify_webhook_signature(payload, sig_header):
        return {"error": "invalid signature"}, 400

    import json
    event = json.loads(payload)

    if event.get("type") == "checkout.session.completed":
        session = event["data"]["object"]
        order_number = session.get("metadata", {}).get("order_number") or session.get("client_reference_id")
        if order_number:
            order = Order.query.filter_by(order_number=order_number).first()
            if order and not order.is_paid and session.get("payment_status") == "paid":
                order.is_paid = True
                order.stripe_payment_intent_id = session.get("payment_intent")
                db.session.commit()

    return {"received": True}, 200


@cart_bp.route("/order-confirmation/<order_number>")
@login_required
def order_confirmation(order_number):
    order = Order.query.filter_by(order_number=order_number, customer_id=current_user.id).first_or_404()
    return render_template("cart/order_confirmation.html", order=order)
