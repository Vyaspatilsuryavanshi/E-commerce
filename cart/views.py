from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from store.models import Product, ProductVariant
from .cart import Cart, CartError


def _is_ajax(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def cart_detail(request):
    cart = Cart(request)
    cart.refresh_prices()
    return render(request, "cart/cart_detail.html", {"cart": cart})


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    variant = None
    variant_id = request.POST.get("variant_id")
    if variant_id:
        variant = ProductVariant.objects.filter(id=variant_id, product=product).first()
        if variant is None:
            message = "The selected product option is no longer available."
            if _is_ajax(request):
                return JsonResponse({"status": "error", "message": message}, status=400)
            messages.error(request, message)
            return redirect(product.get_absolute_url())

    try:
        quantity = request.POST.get("quantity", 1)
        override = request.POST.get("override") == "1"
        final_quantity = cart.add(product, variant, quantity, override_quantity=override)
    except CartError as exc:
        if _is_ajax(request):
            return JsonResponse({"status": "error", "message": str(exc), "cart": cart.to_dict()}, status=400)
        messages.error(request, str(exc))
        return redirect(product.get_absolute_url())

    message = f"Added '{product.name}' to your bag."
    if _is_ajax(request):
        return JsonResponse({"status": "success", "message": message, "quantity": final_quantity, "cart": cart.to_dict()})
    messages.success(request, message)
    return redirect("cart:cart_detail")


@require_POST
def cart_update(request):
    cart = Cart(request)
    key = request.POST.get("key", "")
    try:
        cart.update(key, request.POST.get("quantity", 1))
    except CartError as exc:
        if _is_ajax(request):
            return JsonResponse({"status": "error", "message": str(exc), "cart": cart.to_dict()}, status=400)
        messages.error(request, str(exc))
    if _is_ajax(request):
        return JsonResponse({"status": "success", "cart": cart.to_dict()})
    return redirect("cart:cart_detail")


@require_POST
def cart_remove(request, key):
    cart = Cart(request)
    cart.remove(key)
    if _is_ajax(request):
        return JsonResponse({"status": "success", "cart": cart.to_dict()})
    messages.info(request, "Item removed from your bag.")
    return redirect("cart:cart_detail")


@require_POST
def apply_coupon(request):
    cart = Cart(request)
    success, message = cart.apply_coupon(request.POST.get("code", ""))
    if _is_ajax(request):
        return JsonResponse({"status": "success" if success else "error", "message": message, "cart": cart.to_dict()}, status=200 if success else 400)
    (messages.success if success else messages.error)(request, message)
    return redirect("cart:cart_detail")


@require_POST
def remove_coupon(request):
    cart = Cart(request)
    cart.remove_coupon()
    if _is_ajax(request):
        return JsonResponse({"status": "success", "message": "Coupon removed.", "cart": cart.to_dict()})
    messages.info(request, "Coupon removed.")
    return redirect("cart:cart_detail")


@require_GET
def cart_drawer_json(request):
    cart = Cart(request)
    cart.refresh_prices()
    return JsonResponse({"cart": cart.to_dict()})
