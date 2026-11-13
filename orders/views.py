import json
import requests
from decimal import Decimal

from django.conf import settings

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt

from cart.cart import Cart, CartError, FREE_SHIPPING_THRESHOLD, STANDARD_SHIPPING_COST
from store.models import Product, ProductVariant
from .models import Order, OrderItem, OrderReturn
from .payments import (RazorpayError, create_razorpay_order, fetch_razorpay_payment,
                       verify_checkout_signature, verify_webhook_signature, amount_in_paise)

DELIVERY_CONFIG = {
    "standard": {"cost": STANDARD_SHIPPING_COST, "estimate": "3 to 5 business days"},
    "express_local": {"cost": Decimal("299.00"), "estimate": "Within 24 to 48 hours"},
    "same_day": {"cost": Decimal("499.00"), "estimate": "Today, subject to local courier availability"},
}
VALID_PAYMENT_METHODS = {choice[0] for choice in Order.PAYMENT_METHODS}


def _render_checkout(request, cart, message=None):
    if message:
        messages.error(request, message)
    profile_data = {"first_name": "", "last_name": "", "email": ""}
    saved_location = request.session.get("user_location", {})
    if request.user.is_authenticated:
        profile_data.update({
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "email": request.user.email,
        })
        try:
            profile = request.user.profile
            if not saved_location:
                saved_location = {
                    "city": profile.default_city,
                    "state": profile.default_state,
                    "postal_code": profile.default_postal_code,
                    "country": profile.default_country,
                }
        except Exception:
            pass
    return render(request, "orders/checkout.html", {
        "cart": cart,
        "saved_location": saved_location,
        "user_initials": profile_data,
        "delivery_config": DELIVERY_CONFIG,
    })


def _validate_cart_stock(cart):
    problems = []
    for item in cart:
        product = Product.objects.filter(pk=item["product"].pk).first()
        if product is None:
            problems.append("One of the items in your bag is no longer available.")
            continue
        variant = None
        if item["variant"]:
            variant = ProductVariant.objects.filter(pk=item["variant"].pk, product=product).first()
            if variant is None:
                problems.append(f"{product.name}: the selected option is no longer available.")
                continue
        available = variant.stock if variant else product.stock
        if item["quantity"] > available:
            label = f"{product.name} ({variant.name})" if variant else product.name
            problems.append(f"{label}: only {available} unit(s) are available.")
    return problems


def checkout(request):
    cart = Cart(request)
    cart.refresh_prices()
    if len(cart) == 0:
        messages.warning(request, "Your bag is empty. Add at least one item before checking out.")
        return redirect("store:catalog")
    if request.method != "POST":
        return _render_checkout(request, cart)

    first_name = request.POST.get("first_name", "").strip()
    last_name = request.POST.get("last_name", "").strip()
    email = request.POST.get("email", "").strip().lower()
    phone = request.POST.get("phone", "").strip()
    address_1 = request.POST.get("address_line_1", "").strip()
    address_2 = request.POST.get("address_line_2", "").strip()
    city = request.POST.get("city", "").strip()
    state = request.POST.get("state", "").strip()
    postal_code = request.POST.get("postal_code", "").strip()
    country = request.POST.get("country", "India").strip() or "India"
    delivery_method = request.POST.get("delivery_method", "standard")
    payment_method = request.POST.get("payment_method", "card")

    if not all([first_name, last_name, email, phone, address_1, city, state, postal_code, country]):
        return _render_checkout(request, cart, "Please complete all required contact and shipping fields.")
    if delivery_method not in DELIVERY_CONFIG:
        return _render_checkout(request, cart, "Please select a valid delivery method.")
    if payment_method not in VALID_PAYMENT_METHODS:
        return _render_checkout(request, cart, "Please select a valid payment method.")

    try:
        lat_val = float(request.POST.get("shipping_latitude")) if request.POST.get("shipping_latitude") else None
        lon_val = float(request.POST.get("shipping_longitude")) if request.POST.get("shipping_longitude") else None
    except (TypeError, ValueError):
        return _render_checkout(request, cart, "The supplied GPS coordinates are invalid. You can still enter the address manually.")
    if lat_val is not None and not (-90 <= lat_val <= 90):
        return _render_checkout(request, cart, "Invalid GPS latitude.")
    if lon_val is not None and not (-180 <= lon_val <= 180):
        return _render_checkout(request, cart, "Invalid GPS longitude.")

    location_autodetected = request.POST.get("location_autodetected") == "1"
    order = None
    try:
        with transaction.atomic():
            locked_items = []
            subtotal = Decimal("0.00")
            for item in cart:
                product = Product.objects.select_for_update().get(pk=item["product"].pk)
                variant = None
                if item["variant"]:
                    variant = ProductVariant.objects.select_for_update().get(pk=item["variant"].pk, product=product)
                available = variant.stock if variant else product.stock
                if item["quantity"] > available:
                    raise CartError(f"{product.name}: only {available} unit(s) remain in stock.")
                unit_price = product.price + (variant.additional_price if variant else Decimal("0.00"))
                subtotal += unit_price * item["quantity"]
                locked_items.append((product, variant, item["quantity"], unit_price))

            subtotal = subtotal.quantize(Decimal("0.01"))
            coupon_code = cart.coupon_code
            if coupon_code == "LUXE15":
                discount = (subtotal * Decimal("15") / Decimal("100")).quantize(Decimal("0.01"))
            elif coupon_code == "WELCOME10":
                discount = (subtotal * Decimal("10") / Decimal("100")).quantize(Decimal("0.01"))
            elif coupon_code == "BEAUTY500":
                discount = min(Decimal("500.00"), subtotal)
            else:
                discount, coupon_code = Decimal("0.00"), None

            delivery = DELIVERY_CONFIG[delivery_method]
            shipping_cost = Decimal("0.00") if delivery_method == "standard" and subtotal >= FREE_SHIPPING_THRESHOLD else delivery["cost"]
            total = max(Decimal("0.00"), subtotal - discount) + shipping_cost
            payment_status = "Pending - Cash on Delivery" if payment_method == "cod" else "Pending - Razorpay"

            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                first_name=first_name, last_name=last_name, email=email, phone=phone,
                address_line_1=address_1, address_line_2=address_2, city=city, state=state,
                postal_code=postal_code, country=country,
                shipping_latitude=lat_val, shipping_longitude=lon_val,
                location_autodetected=location_autodetected,
                delivery_method=delivery_method, delivery_estimate_text=delivery["estimate"],
                payment_method=payment_method, payment_status=payment_status,
                subtotal=subtotal, discount=discount, shipping_cost=shipping_cost,
                total=total, coupon_used=coupon_code, status="placed" if payment_method == "cod" else "pending_payment",
            )
            for product, variant, quantity, unit_price in locked_items:
                if variant:
                    variant.stock -= quantity
                    variant.save(update_fields=["stock"])
                else:
                    product.stock -= quantity
                    product.save(update_fields=["stock"])
                OrderItem.objects.create(
                    order=order, product=product, variant=variant,
                    product_name=product.name, variant_name=variant.name if variant else None,
                    price=unit_price.quantize(Decimal("0.01")), quantity=quantity,
                )
    except (CartError, Product.DoesNotExist, ProductVariant.DoesNotExist) as exc:
        return _render_checkout(request, cart, str(exc))

    if payment_method != "cod":
        try:
            gateway_order = create_razorpay_order(order.total, order.order_number)
            order.razorpay_order_id = gateway_order["id"]
            order.save(update_fields=["razorpay_order_id", "updated_at"])
        except RazorpayError as exc:
            # The local reservation is rolled back if the gateway cannot start checkout.
            with transaction.atomic():
                failed_order = Order.objects.select_for_update().get(pk=order.pk)
                for item in failed_order.items.select_related("product").all():
                    if item.product_id:
                        product = Product.objects.select_for_update().filter(pk=item.product_id).first()
                        if product:
                            if item.variant_id:
                                variant = ProductVariant.objects.select_for_update().filter(pk=item.variant_id).first()
                                if variant:
                                    variant.stock += item.quantity
                                    variant.save(update_fields=["stock"])
                                else:
                                    product.stock += item.quantity
                                    product.save(update_fields=["stock"])
                            else:
                                product.stock += item.quantity
                                product.save(update_fields=["stock"])
                failed_order.status = "cancelled"
                failed_order.payment_status = "Payment Setup Failed"
                failed_order.save(update_fields=["status", "payment_status", "updated_at"])
            return _render_checkout(request, cart, str(exc))

    if request.user.is_authenticated:
        request.session.pop("guest_order_number", None)
    else:
        request.session["guest_order_number"] = order.order_number
    cart.clear()
    return redirect("orders:order_success", order_number=order.order_number)

def _order_accessible_to_user(request, order):
    if request.user.is_staff:
        return True
    if order.user_id:
        return request.user.is_authenticated and order.user_id == request.user.id
    return request.session.get("guest_order_number") == order.order_number


def order_success(request, order_number):
    order = get_object_or_404(Order.objects.prefetch_related("items__product", "returns"), order_number=order_number)
    if not _order_accessible_to_user(request, order):
        messages.error(request, "That order is not available in this session.")
        return redirect("store:home")
    return render(request, "orders/order_success.html", {"order": order, "razorpay_key_id": settings.RAZORPAY_KEY_ID, "razorpay_amount": amount_in_paise(order.total) if order.razorpay_order_id else 0})



@require_POST
def payment_verify(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if not _order_accessible_to_user(request, order):
        return JsonResponse({"status": "error", "message": "Order access denied."}, status=403)
    if order.payment_status == "Paid":
        return JsonResponse({"status": "success", "message": "Payment is already verified."})
    if not order.razorpay_order_id:
        return JsonResponse({"status": "error", "message": "No active payment session exists for this order."}, status=400)

    payment_id = request.POST.get("razorpay_payment_id", "").strip()
    signature = request.POST.get("razorpay_signature", "").strip()
    submitted_order_id = request.POST.get("razorpay_order_id", "").strip()
    if submitted_order_id != order.razorpay_order_id or not verify_checkout_signature(submitted_order_id, payment_id, signature):
        return JsonResponse({"status": "error", "message": "Payment signature verification failed."}, status=400)
    try:
        payment = fetch_razorpay_payment(payment_id)
    except RazorpayError as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=502)

    if (
        payment.get("order_id") != order.razorpay_order_id
        or int(payment.get("amount", -1)) != amount_in_paise(order.total)
        or payment.get("currency") != "INR"
        or payment.get("status") != "captured"
    ):
        return JsonResponse({"status": "error", "message": "The provider has not confirmed the expected captured payment."}, status=400)

    try:
        with transaction.atomic():
            locked_order = Order.objects.select_for_update().get(pk=order.pk)
            if locked_order.status == "cancelled":
                locked_order.status = "payment_review"
                locked_order.payment_status = "Payment Captured - Review Required"
                locked_order.save(update_fields=["status", "payment_status", "updated_at"])
                return JsonResponse({"status": "review", "message": "Payment was captured after order cancellation. Support must review this payment."}, status=409)
            if locked_order.payment_status != "Paid":
                locked_order.razorpay_payment_id = payment_id
                locked_order.payment_status = "Paid"
                locked_order.status = "placed"
                locked_order.save(update_fields=["razorpay_payment_id", "payment_status", "status", "updated_at"])
    except IntegrityError:
        return JsonResponse({"status": "error", "message": "This payment reference is already linked to another order."}, status=409)
    return JsonResponse({"status": "success", "message": "Payment verified successfully."})


@csrf_exempt
@require_POST
def razorpay_webhook(request):
    signature = request.headers.get("X-Razorpay-Signature", "")
    if not verify_webhook_signature(request.body, signature):
        return JsonResponse({"status": "error", "message": "Invalid webhook signature."}, status=400)
    try:
        event = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"status": "error", "message": "Invalid webhook payload."}, status=400)
    if event.get("event") != "payment.captured":
        return JsonResponse({"status": "ignored"})
    entity = event.get("payload", {}).get("payment", {}).get("entity", {})
    gateway_order_id = entity.get("order_id")
    payment_id = entity.get("id")
    if not gateway_order_id or not payment_id:
        return JsonResponse({"status": "error", "message": "Payment event is incomplete."}, status=400)
    try:
        with transaction.atomic():
            order = Order.objects.select_for_update().get(razorpay_order_id=gateway_order_id)
            if int(entity.get("amount", -1)) != amount_in_paise(order.total) or entity.get("currency") != "INR":
                return JsonResponse({"status": "error", "message": "Payment amount mismatch."}, status=400)
            if order.status == "cancelled":
                order.status = "payment_review"
                order.payment_status = "Payment Captured - Review Required"
                order.save(update_fields=["status", "payment_status", "updated_at"])
                return JsonResponse({"status": "ok", "review_required": True})
            if order.payment_status != "Paid":
                order.razorpay_payment_id = payment_id
                order.payment_status = "Paid"
                order.status = "placed"
                order.save(update_fields=["razorpay_payment_id", "payment_status", "status", "updated_at"])
    except Order.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Order not found."}, status=404)
    except IntegrityError:
        # Duplicate webhook deliveries are safe; payment references are unique.
        existing = Order.objects.filter(razorpay_payment_id=payment_id).first()
        if existing and existing.razorpay_order_id == gateway_order_id:
            return JsonResponse({"status": "ok", "duplicate": True})
        return JsonResponse({"status": "error", "message": "Payment reference conflict."}, status=409)
    return JsonResponse({"status": "ok"})

def order_detail(request, order_number):
    order = get_object_or_404(Order.objects.prefetch_related("items__product", "returns"), order_number=order_number)
    if not _order_accessible_to_user(request, order):
        messages.error(request, "You do not have permission to view this order.")
        return redirect("store:home")
    return render(request, "orders/order_detail.html", {
        "order": order,
        "return_reasons": OrderReturn.REASON_CHOICES,
        "return_conditions": OrderReturn.CONDITION_CHOICES,
        "refund_options": OrderReturn.REFUND_CHOICES,
    })


@require_POST
def cancel_order(request, order_number):
    with transaction.atomic():
        order = get_object_or_404(Order.objects.select_for_update().prefetch_related("items__product"), order_number=order_number)
        if not _order_accessible_to_user(request, order):
            messages.error(request, "You do not have permission to cancel this order.")
            return redirect("store:home")
        if not order.can_cancel:
            messages.error(request, "This order can no longer be cancelled because fulfillment has started.")
            return redirect("orders:order_detail", order_number=order_number)
        if order.payment_status == "Paid":
            messages.error(request, "This order has already been paid. Please contact support to request cancellation and a verified refund.")
            return redirect("orders:order_detail", order_number=order_number)
        for item in order.items.all():
            if item.product_id:
                product = Product.objects.select_for_update().filter(pk=item.product_id).first()
                if product:
                    if item.variant_id:
                        variant = ProductVariant.objects.select_for_update().filter(pk=item.variant_id).first()
                        if variant:
                            variant.stock += item.quantity
                            variant.save(update_fields=["stock"])
                        else:
                            product.stock += item.quantity
                            product.save(update_fields=["stock"])
                    else:
                        product.stock += item.quantity
                        product.save(update_fields=["stock"])
        order.status = "cancelled"
        order.payment_status = "Cancelled - Unpaid" if order.payment_method != "cod" else "Cancelled - COD"
        order.save(update_fields=["status", "payment_status", "updated_at"])
    messages.success(request, f"Order #{order.order_number} has been cancelled.")
    return redirect("orders:order_detail", order_number=order_number)


@login_required
@require_POST
def request_return(request, order_number):
    with transaction.atomic():
        order = get_object_or_404(Order.objects.select_for_update(), order_number=order_number, user=request.user)
        if not order.can_return:
            messages.error(request, "Returns can only be requested for delivered orders.")
            return redirect("orders:order_detail", order_number=order_number)
        if order.returns.filter(status__in=["requested", "approved", "picked_up"]).exists():
            messages.error(request, "A return request is already in progress for this order.")
            return redirect("orders:order_detail", order_number=order_number)
        reason = request.POST.get("reason", "").strip()
        item_condition = request.POST.get("item_condition", "unopened").strip()
        refund_preference = request.POST.get("refund_preference", "original").strip()
        valid_reasons = {choice[0] for choice in OrderReturn.REASON_CHOICES}
        valid_conditions = {choice[0] for choice in OrderReturn.CONDITION_CHOICES}
        valid_refunds = {choice[0] for choice in OrderReturn.REFUND_CHOICES}
        if reason not in valid_reasons or item_condition not in valid_conditions or refund_preference not in valid_refunds:
            messages.error(request, "Please select a valid return reason, item condition, and refund preference.")
            return redirect("orders:order_detail", order_number=order_number)
        OrderReturn.objects.create(
            order=order,
            user=request.user,
            reason=reason,
            item_condition=item_condition,
            refund_preference=refund_preference,
            comments=request.POST.get("comments", "").strip(),
        )
        order.status = "return_requested"
        order.save(update_fields=["status", "updated_at"])
    messages.success(request, "Your return request has been submitted for review.")
    return redirect("orders:order_detail", order_number=order_number)


@require_GET
def api_reverse_geocode(request):
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")
    try:
        lat_value = float(lat)
        lon_value = float(lon)
    except (TypeError, ValueError):
        return JsonResponse({"status": "error", "message": "Invalid coordinates"}, status=400)
    if not (-90 <= lat_value <= 90 and -180 <= lon_value <= 180):
        return JsonResponse({"status": "error", "message": "Coordinates out of range"}, status=400)
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"format": "json", "lat": lat_value, "lon": lon_value, "addressdetails": 1},
            headers={"User-Agent": "AURALuxeEcommerce/1.0"},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
        addr = data.get("address", {})
        road = addr.get("road") or addr.get("pedestrian") or addr.get("street") or ""
        house_number = addr.get("house_number", "")
        street_address = f"{house_number} {road}".strip() if house_number and road else (road or addr.get("suburb", ""))
        city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("county") or ""
        state = addr.get("state") or addr.get("province") or ""
        postal_code = addr.get("postcode") or ""
        country = addr.get("country") or "India"
        result = {
            "status": "success", "street_address": street_address, "city": city, "state": state,
            "postal_code": postal_code, "country": country, "display_name": data.get("display_name", ""),
            "lat": str(lat_value), "lon": str(lon_value),
        }
        request.session["user_location"] = {
            "city": city, "state": state, "postal_code": postal_code, "country": country,
            "lat": str(lat_value), "lon": str(lon_value),
            "display": f"{city}, {state}" if city and state else (city or "Detected Location"),
        }
        request.session.modified = True
        return JsonResponse(result)
    except requests.RequestException:
        return JsonResponse({"status": "error", "message": "Location service is temporarily unavailable."}, status=502)
    except (TypeError, ValueError):
        return JsonResponse({"status": "error", "message": "Invalid location response."}, status=502)
