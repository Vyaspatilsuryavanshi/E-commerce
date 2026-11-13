"""Razorpay API helpers. All secrets stay server-side."""
import hashlib
import hmac
from decimal import Decimal, ROUND_HALF_UP

import requests
from django.conf import settings


RAZORPAY_API_URL = "https://api.razorpay.com/v1"


class RazorpayError(Exception):
    """Raised when Razorpay is unavailable or returns an invalid response."""


def is_razorpay_configured():
    return bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET)


def amount_in_paise(amount):
    return int((Decimal(amount) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def create_razorpay_order(amount, receipt):
    if not is_razorpay_configured():
        raise RazorpayError("Online payments are not configured. Please choose Cash on Delivery or contact the store.")
    amount_paise = amount_in_paise(amount)
    try:
        response = requests.post(
            f"{RAZORPAY_API_URL}/orders",
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET),
            json={"amount": amount_paise, "currency": "INR", "receipt": receipt, "partial_payment": False},
            timeout=(4, 15),
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise RazorpayError("The payment provider could not create a checkout session. Please try again.") from exc

    if (
        not isinstance(payload, dict)
        or not payload.get("id")
        or payload.get("currency") != "INR"
        or int(payload.get("amount", -1)) != amount_paise
    ):
        raise RazorpayError("The payment provider returned an invalid checkout order.")
    return payload


def verify_checkout_signature(order_id, payment_id, signature):
    secret = settings.RAZORPAY_KEY_SECRET
    if not secret or not order_id or not payment_id or not signature:
        return False
    message = f"{order_id}|{payment_id}".encode("utf-8")
    expected = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def verify_webhook_signature(raw_body, signature):
    secret = settings.RAZORPAY_WEBHOOK_SECRET
    if not secret or not signature:
        return False
    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def fetch_razorpay_payment(payment_id):
    if not is_razorpay_configured():
        raise RazorpayError("Online payments are not configured.")
    try:
        response = requests.get(
            f"{RAZORPAY_API_URL}/payments/{payment_id}",
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET),
            timeout=(4, 15),
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise RazorpayError("Payment status could not be verified with the provider.") from exc
    if not isinstance(payload, dict):
        raise RazorpayError("The payment provider returned an invalid payment response.")
    return payload



def fetch_razorpay_order_payments(order_id):
    """Return the provider's payment attempts for a Razorpay order."""
    if not is_razorpay_configured():
        raise RazorpayError("Online payments are not configured.")
    try:
        response = requests.get(
            f"{RAZORPAY_API_URL}/orders/{order_id}/payments",
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET),
            timeout=(4, 15),
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise RazorpayError("Payment attempts could not be checked with the provider.") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise RazorpayError("The payment provider returned an invalid order-payment response.")
    return payload["items"]
