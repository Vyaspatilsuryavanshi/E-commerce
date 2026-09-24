from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from orders.models import Order
from store.models import Product
from .models import CustomerProfile, Wishlist


def _safe_next(request):
    next_url = request.GET.get("next") or request.POST.get("next")
    if next_url and url_has_allowed_host_and_scheme(next_url, {request.get_host()}, require_https=request.is_secure()):
        return next_url
    return None


def user_register(request):
    if request.user.is_authenticated:
        return redirect("store:home")
    next_url = _safe_next(request)
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()

        if not (username and email and password):
            messages.error(request, "Please provide username, email, and password.")
        elif len(username) > 150:
            messages.error(request, "Username must be 150 characters or fewer.")
        else:
            try:
                validate_email(email)
                validate_password(password)
            except ValidationError as exc:
                for error in exc.messages:
                    messages.error(request, error)
            else:
                if User.objects.filter(username__iexact=username).exists():
                    messages.error(request, "That username is already in use.")
                elif User.objects.filter(email__iexact=email).exists():
                    messages.error(request, "An account with that email already exists.")
                else:
                    user = User.objects.create_user(username=username, email=email, password=password, first_name=first_name, last_name=last_name)
                    login(request, user)
                    messages.success(request, f"Welcome to AURA LUXE, {user.first_name or user.username}!")
                    return redirect(next_url or "store:home")
    return render(request, "accounts/register.html", {"next": next_url or ""})


def user_login(request):
    if request.user.is_authenticated:
        return redirect("store:home")
    next_url = _safe_next(request)
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_active:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect(next_url or "store:home")
        messages.error(request, "Invalid username or password.")
    return render(request, "accounts/login.html", {"next": next_url or ""})


def user_logout(request):
    logout(request)
    messages.info(request, "You have been signed out.")
    return redirect("store:home")


@login_required
def user_profile(request):
    orders = Order.objects.filter(user=request.user).prefetch_related("items__product", "returns")
    profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        if not email:
            messages.error(request, "Email address is required.")
        elif User.objects.filter(email__iexact=email).exclude(pk=request.user.pk).exists():
            messages.error(request, "That email address is already associated with another account.")
        else:
            request.user.first_name = request.POST.get("first_name", "").strip()
            request.user.last_name = request.POST.get("last_name", "").strip()
            request.user.email = email
            request.user.save(update_fields=["first_name", "last_name", "email"])

            profile.phone = request.POST.get("phone", "").strip()
            profile.default_address = request.POST.get("default_address", "").strip()
            profile.default_city = request.POST.get("default_city", "").strip()
            profile.default_state = request.POST.get("default_state", "").strip()
            profile.default_postal_code = request.POST.get("default_postal_code", "").strip()
            profile.default_country = request.POST.get("default_country", "India").strip() or "India"
            profile.save()
            messages.success(request, "Your profile and saved delivery address have been updated.")
            return redirect("accounts:profile")
    return render(request, "accounts/profile.html", {"orders": orders, "profile": profile})


@login_required
def wishlist_view(request):
    items = Wishlist.objects.filter(user=request.user).select_related("product__brand", "product__category")
    return render(request, "accounts/wishlist.html", {"wishlist_items": items})


@require_POST
def wishlist_toggle(request, product_id):
    if not request.user.is_authenticated:
        return JsonResponse({"status": "unauthenticated", "message": "Please sign in to save items to your wishlist."}, status=401)
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        wishlist_item.delete()
        is_in_wishlist = False
        message = f"Removed '{product.name}' from wishlist."
    else:
        is_in_wishlist = True
        message = f"Saved '{product.name}' to wishlist."
    count = Wishlist.objects.filter(user=request.user).count()
    return JsonResponse({"status": "success", "is_in_wishlist": is_in_wishlist, "message": message, "count": count})
