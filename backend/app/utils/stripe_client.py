"""
Minimal Stripe API client.

Talks to Stripe's REST API directly with `requests` (already a project
dependency) instead of pulling in the full `stripe` SDK. Covers exactly
what checkout needs:
    - creating a Checkout Session (hosted, Stripe-managed payment page)
    - retrieving a Checkout Session (used on the success redirect)
    - verifying webhook signatures (used on the webhook endpoint)

All real card handling happens on Stripe's own hosted page — card
numbers never touch this server, so no PCI scope is added to the app.
"""

import hashlib
import hmac
import time

import requests
from flask import current_app

STRIPE_API_BASE = "https://api.stripe.com/v1"


class StripeError(Exception):
    """Raised when Stripe's API returns an error response."""


def _secret_key():
    key = current_app.config.get("STRIPE_SECRET_KEY")
    if not key:
        raise StripeError(
            "Stripe is not configured yet. Set STRIPE_SECRET_KEY (and "
            "STRIPE_PUBLISHABLE_KEY) in your environment / .env file. "
            "Get test keys free at https://dashboard.stripe.com/test/apikeys"
        )
    return key


def create_checkout_session(order, success_url, cancel_url):
    """
    Creates a Stripe Checkout Session for the given Order and returns the
    parsed JSON response (includes 'id' and 'url').

    One line item per OrderItem, priced in the smallest currency unit
    (cents for USD), plus a separate line item for shipping when charged.
    """
    currency = current_app.config.get("STRIPE_CURRENCY", "usd")

    data = {
        "mode": "payment",
        "success_url": success_url,
        "cancel_url": cancel_url,
        "customer_email": order.customer.email if order.customer else None,
        "client_reference_id": order.order_number,
        "metadata[order_number]": order.order_number,
        "metadata[order_id]": order.id,
    }

    line_index = 0
    for item in order.items:
        unit_amount = int(round(float(item.unit_price) * 100))
        data[f"line_items[{line_index}][quantity]"] = item.quantity
        data[f"line_items[{line_index}][price_data][currency]"] = currency
        data[f"line_items[{line_index}][price_data][unit_amount]"] = unit_amount
        data[f"line_items[{line_index}][price_data][product_data][name]"] = item.product_name[:250]
        line_index += 1

    if order.shipping_fee and float(order.shipping_fee) > 0:
        data[f"line_items[{line_index}][quantity]"] = 1
        data[f"line_items[{line_index}][price_data][currency]"] = currency
        data[f"line_items[{line_index}][price_data][unit_amount]"] = int(round(float(order.shipping_fee) * 100))
        data[f"line_items[{line_index}][price_data][product_data][name]"] = "Shipping"

    # Drop any None values (Stripe's form encoder rejects them)
    data = {k: v for k, v in data.items() if v is not None}

    response = requests.post(
        f"{STRIPE_API_BASE}/checkout/sessions",
        auth=(_secret_key(), ""),
        data=data,
        timeout=15,
    )
    payload = response.json()
    if response.status_code >= 400:
        message = payload.get("error", {}).get("message", "Stripe request failed.")
        raise StripeError(message)
    return payload


def retrieve_checkout_session(session_id):
    """Fetches a Checkout Session by id — used to confirm payment on the success redirect."""
    response = requests.get(
        f"{STRIPE_API_BASE}/checkout/sessions/{session_id}",
        auth=(_secret_key(), ""),
        timeout=15,
    )
    payload = response.json()
    if response.status_code >= 400:
        message = payload.get("error", {}).get("message", "Stripe request failed.")
        raise StripeError(message)
    return payload


def verify_webhook_signature(payload_body, sig_header, tolerance_seconds=300):
    """
    Verifies the `Stripe-Signature` header per Stripe's documented scheme:
    https://stripe.com/docs/webhooks/signatures

    Returns True if the signature is valid and recent, False otherwise.
    """
    secret = current_app.config.get("STRIPE_WEBHOOK_SECRET")
    if not secret or not sig_header:
        return False

    parts = dict(p.split("=", 1) for p in sig_header.split(",") if "=" in p)
    timestamp = parts.get("t")
    signature = parts.get("v1")
    if not timestamp or not signature:
        return False

    if abs(time.time() - int(timestamp)) > tolerance_seconds:
        return False

    signed_payload = f"{timestamp}.{payload_body.decode('utf-8')}"
    expected = hmac.new(secret.encode("utf-8"), signed_payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
