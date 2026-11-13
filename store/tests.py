import io
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from PIL import Image

from orders.models import Order, OrderItem
from .models import Brand, Category, Department, Product, ProductReview, StoreLocation
from .visual_search import color_distance, hex_to_rgb, search_similar_products


class StoreCatalogTests(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name="Skincare", slug="skincare")
        self.cat = Category.objects.create(department=self.dept, name="Serums", slug="serums")
        self.brand = Brand.objects.create(name="Lumina Botanical", slug="lumina")
        self.product = Product.objects.create(
            department=self.dept, category=self.cat, brand=self.brand, name="Hydra Glow Serum", sku="TEST-001",
            short_description="A hydrating serum", description="Long product description", price=Decimal("1200.00"),
            compare_at_price=Decimal("1500.00"), dominant_color_hex="#38BDF8", visual_tags="serum, blue, glow, hydration", stock=20,
        )
        StoreLocation.objects.create(name="Pune Hub", address="Hinjewadi", city="Pune", state="Maharashtra", postal_code="411057", country="India", latitude=18.59, longitude=73.74, phone="020-0000000")

    def test_homepage_render(self):
        response = self.client.get(reverse("store:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AURA LUXE")

    def test_catalog_search(self):
        response = self.client.get(reverse("store:catalog") + "?q=Hydra")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hydra Glow Serum")

    def test_nearby_stores_api_validates_coordinates(self):
        response = self.client.get(reverse("store:api_nearby_stores") + "?lat=18.5204&lon=73.8567")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        bad = self.client.get(reverse("store:api_nearby_stores") + "?lat=999&lon=73")
        self.assertEqual(bad.status_code, 400)

    def test_visual_search(self):
        img = Image.new("RGB", (100, 100), color=(56, 189, 248))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)
        results = search_similar_products(buf)
        self.assertEqual(results["matches"][0]["product"].id, self.product.id)
        self.assertGreaterEqual(results["matches"][0]["match_score"], 70)


class EmptyCatalogRenderTests(TestCase):
    def test_home_renders_without_seeded_catalog(self):
        response = self.client.get(reverse("store:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Browse Collections")

    def test_catalog_renders_empty_state_without_seeded_products(self):
        response = self.client.get(reverse("store:catalog"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No creations found")


class ReviewTests(TestCase):
    def setUp(self):
        dept = Department.objects.create(name="Makeup", slug="makeup")
        cat = Category.objects.create(department=dept, name="Lips", slug="lips")
        self.product = Product.objects.create(department=dept, category=cat, name="Lip Color", sku="REV-001", short_description="Test", description="Test", price=Decimal("500.00"), stock=10)
        self.user = User.objects.create_user(username="reviewer", password="StrongPass123!", email="reviewer@example.com")
        self.client.login(username="reviewer", password="StrongPass123!")
        order = Order.objects.create(user=self.user, first_name="Review", last_name="User", email=self.user.email, phone="9999999999", address_line_1="1 Main", city="Pune", state="Maharashtra", postal_code="411001", country="India", subtotal=Decimal("500.00"), total=Decimal("500.00"), status="delivered")
        OrderItem.objects.create(order=order, product=self.product, product_name=self.product.name, price=self.product.price, quantity=1)

    def test_verified_review_updates_rating(self):
        response = self.client.post(reverse("store:submit_review", args=[self.product.id]), {"rating": 4, "title": "Lovely", "comment": "A great product."})
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.review_count, 1)
        self.assertEqual(self.product.rating, Decimal("4.00"))
        self.assertEqual(ProductReview.objects.count(), 1)
        self.assertTrue(ProductReview.objects.get().verified_buyer)



class VisualSearchSafetyTests(TestCase):
    def test_visual_search_rejects_malformed_base64(self):
        result = search_similar_products("data:image/jpeg;base64,not-valid-base64!")
        self.assertIn("error", result)
        self.assertEqual(result["matches"], [])

    def test_visual_search_rejects_non_image_bytes(self):
        result = search_similar_products(io.BytesIO(b"not an image"))
        self.assertIn("error", result)
        self.assertEqual(result["matches"], [])

    def test_visual_search_rejects_oversized_image_payload(self):
        oversized = io.BytesIO(b"x" * (10 * 1024 * 1024 + 1))
        result = search_similar_products(oversized)
        self.assertIn("error", result)
        self.assertEqual(result["matches"], [])


    def test_in_stock_filter_respects_variant_inventory(self):
        variant = ProductVariant.objects.create(
            product=self.product, variant_type="size", name="M", stock=0,
        )
        response = self.client.get(reverse("store:catalog") + "?in_stock=1")
        self.assertNotContains(response, "Hydra Glow Serum")

        variant.stock = 2
        variant.save(update_fields=["stock"])
        response = self.client.get(reverse("store:catalog") + "?in_stock=1")
        self.assertContains(response, "Hydra Glow Serum")

    def test_catalog_ignores_non_finite_price_and_rating_filters(self):
        response = self.client.get(reverse("store:catalog") + "?min_price=NaN&max_price=Infinity&rating=NaN")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hydra Glow Serum")
