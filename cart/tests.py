from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse

from store.models import Category, Department, Product, ProductVariant
from .cart import Cart


class CartTests(TestCase):
    def setUp(self):
        department = Department.objects.create(name="Beauty", slug="beauty")
        category = Category.objects.create(department=department, name="Serums", slug="serums")
        self.product = Product.objects.create(
            department=department, category=category, name="Test Serum", sku="CART-001",
            short_description="Test", description="Test product", price=Decimal("1200.00"), stock=3,
        )
        self.variant_product = Product.objects.create(
            department=department, category=category, name="Variant Serum", sku="CART-002",
            short_description="Test", description="Test product", price=Decimal("1000.00"), stock=20,
        )
        self.variant = ProductVariant.objects.create(product=self.variant_product, variant_type="volume", name="50ml", stock=2)
        self.client = Client()

    def test_add_respects_stock(self):
        response = self.client.post(reverse("cart:cart_add", args=[self.product.id]), {"quantity": 4})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(Cart(self.client.session)), 0)

    def test_coupon_and_free_shipping(self):
        self.client.post(reverse("cart:cart_add", args=[self.product.id]), {"quantity": 2})
        response = self.client.post(reverse("cart:apply_coupon"), {"code": "LUXE15"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.json()["status"], "success")
        self.assertEqual(response.json()["cart"]["discount"], "360.00")

    def test_zero_quantity_removes_item(self):
        self.client.post(reverse("cart:cart_add", args=[self.product.id]), {"quantity": 1})
        key = next(iter(self.client.session.get("aura_luxe_cart", {})))
        response = self.client.post(reverse("cart:cart_update"), {"key": key, "quantity": 0}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["cart"]["item_count"], 0)

    def test_variant_is_required_when_variants_exist(self):
        response = self.client.post(reverse("cart:cart_add", args=[self.variant_product.id]), {"quantity": 1})
        self.assertEqual(response.status_code, 302)
        session = self.client.session
        self.assertEqual(session.get("aura_luxe_cart", {}), {})
