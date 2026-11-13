import math
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST
from django.urls import reverse
from django.utils import timezone

from .models import Brand, Category, Department, NewsletterSubscriber, Product, ProductReview, ProductVariant, StoreLocation
from .visual_search import search_similar_products


def haversine_distance(lat1, lon1, lat2, lon2):
    radius = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    a = min(1.0, max(0.0, a))
    return round(radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 1)


def home(request):
    departments = Department.objects.prefetch_related("categories").all()
    context = {
        "departments": departments,
        "trending_products": Product.objects.filter(is_trending=True).select_related("department", "category", "brand")[:8],
        "bestseller_products": Product.objects.filter(is_bestseller=True).select_related("department", "category", "brand")[:8],
        "new_arrivals": Product.objects.filter(is_new_arrival=True).select_related("department", "category", "brand")[:8],
        "featured_brands": Brand.objects.filter(is_featured=True)[:6],
        "locations": StoreLocation.objects.filter(is_active=True)[:4],
        "clothing_dept": departments.filter(slug="clothing").first(),
        "skincare_dept": departments.filter(slug="skincare").first(),
        "makeup_dept": departments.filter(slug="makeup").first(),
        "clothing_featured": Product.objects.filter(department__slug="clothing").select_related("brand")[:4],
        "skincare_featured": Product.objects.filter(department__slug="skincare").select_related("brand")[:4],
        "makeup_featured": Product.objects.filter(department__slug="makeup").select_related("brand")[:4],
    }
    return render(request, "store/home.html", context)


def catalog(request, department_slug=None, category_slug=None):
    products = Product.objects.select_related("department", "category", "brand").all()
    current_department = get_object_or_404(Department, slug=department_slug) if department_slug else None
    current_category = get_object_or_404(Category, slug=category_slug, department=current_department) if category_slug else None
    if current_department:
        products = products.filter(department=current_department)
    if current_category:
        products = products.filter(category=current_category)

    query = request.GET.get("q", "").strip()[:120]
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(short_description__icontains=query) | Q(description__icontains=query) |
            Q(brand__name__icontains=query) | Q(category__name__icontains=query) | Q(visual_tags__icontains=query)
        )

    brand_slug = request.GET.get("brand", "").strip()
    if brand_slug:
        products = products.filter(brand__slug=brand_slug)

    min_price = request.GET.get("min_price", "").strip()
    max_price = request.GET.get("max_price", "").strip()
    try:
        if min_price:
            min_value = Decimal(min_price)
            if not min_value.is_finite() or min_value < 0:
                raise InvalidOperation
            products = products.filter(price__gte=min_value)
    except (InvalidOperation, ValueError):
        min_price = ""
    try:
        if max_price:
            max_value = Decimal(max_price)
            if not max_value.is_finite() or max_value < 0:
                raise InvalidOperation
            products = products.filter(price__lte=max_value)
    except (InvalidOperation, ValueError):
        max_price = ""

    min_rating = request.GET.get("rating", "").strip()
    try:
        if min_rating:
            rating_value = Decimal(min_rating)
            if not rating_value.is_finite() or not Decimal("0") <= rating_value <= Decimal("5"):
                raise InvalidOperation
            products = products.filter(rating__gte=rating_value)
    except (InvalidOperation, ValueError):
        min_rating = ""

    in_stock_only = request.GET.get("in_stock") == "1"
    if in_stock_only:
        products = products.filter(Q(variants__isnull=True, stock__gt=0) | Q(variants__stock__gt=0)).distinct()

    sort_by = request.GET.get("sort", "featured")
    sort_map = {
        "price_asc": "price", "price_desc": "-price", "rating": "-rating", "newest": "-created_at",
    }
    products = products.order_by(sort_map.get(sort_by, "-is_featured"), "-is_bestseller", "-created_at")

    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get("page"))
    context = {
        "products": page_obj, "page_obj": page_obj, "total_count": paginator.count,
        "current_department": current_department, "current_category": current_category,
        "departments": Department.objects.prefetch_related("categories"), "available_brands": Brand.objects.all(),
        "query": query, "selected_sort": sort_by, "selected_brand": brand_slug,
        "min_price": min_price, "max_price": max_price, "selected_rating": min_rating, "in_stock_only": in_stock_only,
    }
    return render(request, "store/catalog.html", context)


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("department", "category", "brand").prefetch_related("variants", "reviews"),
        slug=slug,
    )
    variants_by_type = {
        "sizes": product.variants.filter(variant_type="size"),
        "shades": product.variants.filter(variant_type="shade"),
        "volumes": product.variants.filter(variant_type="volume"),
    }
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id).select_related("brand")[:4]
    reviews = product.reviews.all()
    can_review = request.user.is_authenticated and product.order_items.filter(order__user=request.user, order__status="delivered").exists()
    return render(request, "store/product_detail.html", {
        "product": product, "variants_by_type": variants_by_type, "related_products": related_products,
        "reviews": reviews, "user_location": request.session.get("user_location", {}), "can_review": can_review,
    })


@require_POST
def submit_review(request, product_id):
    if not request.user.is_authenticated:
        messages.info(request, "Please sign in before writing a product review.")
        return redirect("accounts:login")
    product = get_object_or_404(Product, id=product_id)
    purchased = product.order_items.filter(order__user=request.user, order__status="delivered").exists()
    if not purchased:
        messages.error(request, "Only customers with a delivered order can review this product.")
        return redirect(product.get_absolute_url())
    if ProductReview.objects.filter(product=product, user=request.user).exists():
        messages.info(request, "You have already reviewed this product.")
        return redirect(product.get_absolute_url() + "#reviewsSection")
    try:
        rating = int(request.POST.get("rating", 5))
    except (TypeError, ValueError):
        rating = 0
    title = request.POST.get("title", "").strip()
    comment = request.POST.get("comment", "").strip()
    if rating not in range(1, 6) or not title or not comment:
        messages.error(request, "Please provide a rating from 1–5, a review title, and your comments.")
        return redirect(product.get_absolute_url() + "#reviewsSection")
    ProductReview.objects.create(product=product, user=request.user, author_name=request.user.get_full_name() or request.user.username, rating=rating, title=title, comment=comment, verified_buyer=True)
    aggregate = product.reviews.aggregate(average=Avg("rating"), count=Count("id"))
    product.rating = Decimal(str(round(aggregate["average"] or 0, 2)))
    product.review_count = aggregate["count"] or 0
    product.save(update_fields=["rating", "review_count", "updated_at"])
    messages.success(request, "Thank you for sharing your experience.")
    return redirect(product.get_absolute_url() + "#reviewsSection")


@require_GET
def api_nearby_stores(request):
    try:
        user_lat = float(request.GET.get("lat"))
        user_lon = float(request.GET.get("lon"))
    except (ValueError, TypeError):
        return JsonResponse({"status": "error", "message": "Invalid coordinates"}, status=400)
    if not (-90 <= user_lat <= 90 and -180 <= user_lon <= 180):
        return JsonResponse({"status": "error", "message": "Coordinates out of range"}, status=400)
    stores = StoreLocation.objects.filter(is_active=True)
    store_list = []
    for store in stores:
        dist_km = haversine_distance(user_lat, user_lon, store.latitude, store.longitude)
        store_list.append({
            "id": store.id, "name": store.name, "address": store.address, "city": store.city,
            "state": store.state, "postal_code": store.postal_code, "country": store.country,
            "distance_km": dist_km, "distance_miles": round(dist_km * 0.621371, 1),
            "distance_text": f"{dist_km} km ({round(dist_km * 0.621371, 1)} mi)",
            "phone": store.phone, "hours": store.hours, "express_available": dist_km <= 50,
        })
    store_list.sort(key=lambda row: row["distance_km"])
    closest = store_list[0] if store_list else None
    delivery_estimate = "24–48 Hours" if closest and closest["distance_km"] < 100 else "2–3 Business Days"
    return JsonResponse({"status": "success", "user_coords": {"lat": user_lat, "lon": user_lon}, "closest_store": closest, "delivery_estimate": delivery_estimate, "stores": store_list})


@require_POST
def api_set_user_location(request):
    city = request.POST.get("city", "").strip()
    state = request.POST.get("state", "").strip()
    postal_code = request.POST.get("postal_code", "").strip()
    country = request.POST.get("country", "").strip()
    lat = request.POST.get("lat", "")
    lon = request.POST.get("lon", "")
    location_data = {
        "city": city or "Current Area", "state": state, "postal_code": postal_code, "country": country,
        "lat": lat, "lon": lon, "display": f"{city}, {state}" if city and state else (city or "Detected Location"),
    }
    request.session["user_location"] = location_data
    request.session.modified = True
    return JsonResponse({"status": "success", "location": location_data})


def visual_search_view(request):
    if request.method == "POST":
        image_file = request.FILES.get("image_file")
        camera_data = request.POST.get("camera_data")
        department_filter = request.POST.get("department")
        if image_file and image_file.size > 10 * 1024 * 1024:
            messages.error(request, "Please select an image smaller than 10MB.")
            return redirect("store:visual_search")
        search_input = image_file or camera_data
        if not search_input:
            messages.error(request, "Please upload an image or capture a photo with your camera.")
            return redirect("store:visual_search")
        results = search_similar_products(search_input, department_filter=department_filter)
        if results.get("error"):
            messages.error(request, "We could not process that image. Please try another image.")
            return redirect("store:visual_search")
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            matches = []
            for item in results.get("matches", []):
                prod = item["product"]
                matches.append({
                    "id": prod.id, "name": prod.name, "brand": prod.brand.name if prod.brand else "",
                    "price": str(prod.price), "compare_price": str(prod.compare_at_price) if prod.compare_at_price else None,
                    "image": prod.display_image, "url": prod.get_absolute_url(), "match_score": item["match_score"],
                    "match_label": item["match_label"], "color_hex": prod.dominant_color_hex,
                })
            return JsonResponse({"status": "success", "dominant_hex": results.get("dominant_hex"), "color_name": results.get("color_name"), "palette": results.get("palette"), "matches": matches})
        return render(request, "store/visual_search_results.html", {"results": results, "preview_data": camera_data if camera_data and camera_data.startswith("data:image") else None, "departments": Department.objects.all(), "selected_department": department_filter})
    return render(request, "store/visual_search.html", {"departments": Department.objects.all()})



@require_POST
def newsletter_subscribe(request):
    email = request.POST.get("email", "").strip().lower()
    try:
        validate_email(email)
    except ValidationError:
        messages.error(request, "Enter a valid email address to join the mailing list.")
        return redirect("store:home")

    subscriber, _ = NewsletterSubscriber.objects.get_or_create(email=email)
    if subscriber.is_active:
        messages.info(request, "This email address is already subscribed.")
        return redirect("store:home")

    token = signing.dumps({"email": email}, salt="aura-luxe-newsletter-confirm")
    confirm_url = request.build_absolute_uri(
        reverse("store:newsletter_confirm", kwargs={"token": token})
    )
    try:
        send_mail(
            "Confirm your AURA LUXE mailing-list subscription",
            f"Confirm your subscription within 24 hours using this link:\n\n{confirm_url}\n\nIf you did not request this, ignore this email.",
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
    except Exception:
        messages.error(request, "We could not send the confirmation email. Please try again later.")
        return redirect("store:home")

    messages.success(request, "Check your inbox for a confirmation link. Your subscription is not active until you confirm.")
    return redirect("store:home")


@require_GET
def newsletter_confirm(request, token):
    try:
        payload = signing.loads(token, salt="aura-luxe-newsletter-confirm", max_age=60 * 60 * 24)
        email = payload.get("email", "").strip().lower()
    except (signing.BadSignature, signing.SignatureExpired, AttributeError):
        messages.error(request, "That mailing-list confirmation link is invalid or expired. Please subscribe again.")
        return redirect("store:home")

    subscriber = get_object_or_404(NewsletterSubscriber, email=email)
    if not subscriber.is_active:
        subscriber.is_active = True
        subscriber.confirmed_at = timezone.now()
        subscriber.save(update_fields=["is_active", "confirmed_at"])
    messages.success(request, "Your AURA LUXE mailing-list subscription is confirmed.")
    return redirect("store:home")
