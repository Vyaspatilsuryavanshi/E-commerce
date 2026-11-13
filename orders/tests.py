from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase, Client, override_settings
from unittest.mock import patch
from django.urls import reverse

from cart.cart import Cart
from store.models import Category, Department, Product, ProductVariant
from .models import Order, OrderReturn


class OrderFlowTests(TestCase):
    def setUp(self):
        department = Department.objects.create(name="Clothing", slug="clothing")
        category = Category.objects.create(department=department, name="Dresses", slug="dresses")
        self.product = Product.objects.create(
            department=department, category=category, name="Silk Dress", sku="ORDER-001",
            short_description="Test", description="Test product", price=Decimal("1200.00"), stock=5,
        )
        self.user = User.objects.create_user(username="buyer", password="StrongPass123!", email="buyer@example.com")
        self.client = Client()

    def add_item(self, quantity=1):
        self.client.post(reverse("cart:cart_add", args=[self.product.id]), {"quantity": quantity})

    def checkout(self, payment_method="cod"):
        return self.client.post(reverse("orders:checkout"), {
            "first_name": "Test", "last_name": "Buyer", "email": "buyer@example.com", "phone": "9999999999",
            "address_line_1": "1 Main Street", "city": "Pune", "state": "Maharashtra", "postal_code": "411001",
            "country": "India", "delivery_method": "standard", "payment_method": payment_method,
        })

    def test_guest_checkout_decrements_stock_and_secures_confirmation(self):
        self.add_item(2)
        response = self.checkout()
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get(email="buyer@example.com")
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        self.assertEqual(order.total, Decimal("2549.00"))
        self.assertEqual(order.payment_status, "Pending - Cash on Delivery")
        confirmation = self.client.get(reverse("orders:order_success", args=[order.order_number]))
        self.assertEqual(confirmation.status_code, 200)

        other_client = Client()
        denied = other_client.get(reverse("orders:order_success", args=[order.order_number]))
        self.assertRedirects(denied, reverse("store:home"))

    def test_cancel_restores_stock(self):
        self.client.login(username="buyer", password="StrongPass123!")
        self.add_item(2)
        self.checkout()
        order = Order.objects.get(user=self.user)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        response = self.client.post(reverse("orders:cancel_order", args=[order.order_number]))
        self.assertRedirects(response, reverse("orders:order_detail", args=[order.order_number]))
        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.status, "cancelled")
        self.assertEqual(self.product.stock, 5)


    def test_variant_checkout_decrements_variant_stock(self):
        variant = ProductVariant.objects.create(product=self.product, variant_type="size", name="M", stock=2)
        cart = Cart(self.client)
        cart.add(self.product, variant, 2)
        response = self.checkout()
        self.assertEqual(response.status_code, 302)
        variant.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(variant.stock, 0)
        self.assertEqual(self.product.stock, 5)

    def test_cancel_does_not_restore_stock_twice(self):
        self.client.login(username="buyer", password="StrongPass123!")
        self.add_item(2)
        self.checkout()
        order = Order.objects.get(user=self.user)
        self.client.post(reverse("orders:cancel_order", args=[order.order_number]))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)
        self.client.post(reverse("orders:cancel_order", args=[order.order_number]))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)

    def test_order_detail_is_private(self):
        self.add_item()
        self.checkout()
        order = Order.objects.get(email="buyer@example.com")
        other = Client()
        response = other.get(reverse("orders:order_detail", args=[order.order_number]))
        self.assertRedirects(response, reverse("store:home"))

    def test_cod_order_remains_pending(self):
        self.add_item()
        response = self.client.post(reverse("orders:checkout"), {
            "first_name": "Test", "last_name": "Buyer", "email": "buyer@example.com", "phone": "9999999999",
            "address_line_1": "1 Main Street", "city": "Pune", "state": "Maharashtra", "postal_code": "411001",
            "country": "India", "delivery_method": "standard", "payment_method": "cod",
        })
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get(email="buyer@example.com")
        self.assertEqual(order.payment_status, "Pending - Cash on Delivery")

    def test_return_request_only_for_delivered_orders(self):
        self.client.login(username="buyer", password="StrongPass123!")
        self.add_item()
        self.checkout()
        order = Order.objects.get(user=self.user)
        response = self.client.post(reverse("orders:request_return", args=[order.order_number]), {"reason": "changed_mind"})
        self.assertRedirects(response, reverse("orders:order_detail", args=[order.order_number]))
        self.assertEqual(OrderReturn.objects.count(), 0)
        order.status = "delivered"
        order.save(update_fields=["status"])
        response = self.client.post(reverse("orders:request_return", args=[order.order_number]), {
            "reason": "changed_mind", "item_condition": "tried_once", "refund_preference": "original",
            "comments": "No longer needed",
        })
        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, "return_requested")
        self.assertEqual(OrderReturn.objects.count(), 1)


    @override_settings(RAZORPAY_KEY_ID="rzp_test_key", RAZORPAY_KEY_SECRET="test_secret")
    @patch("orders.views.create_razorpay_order")
    def test_online_checkout_creates_pending_gateway_order(self, create_gateway_order):
        create_gateway_order.return_value = {"id": "order_test_123", "amount": 134900, "currency": "INR"}
        self.add_item()
        response = self.checkout(payment_method="card")
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get(email="buyer@example.com")
        self.assertEqual(order.payment_status, "Pending - Razorpay")
        self.assertEqual(order.razorpay_order_id, "order_test_123")
        self.assertEqual(order.status, "pending_payment")
        self.assertEqual(create_gateway_order.call_count, 1)

        invalid = self.client.post(reverse("orders:payment_verify", args=[order.order_number]), {
            "razorpay_order_id": "order_test_123",
            "razorpay_payment_id": "pay_fake",
            "razorpay_signature": "not-a-valid-signature",
        })
        self.assertEqual(invalid.status_code, 400)
        order.refresh_from_db()
        self.assertEqual(order.payment_status, "Pending - Razorpay")

    @override_settings(RAZORPAY_KEY_ID="", RAZORPAY_KEY_SECRET="")
    def test_online_checkout_fails_closed_without_gateway_credentials(self):
        self.add_item()
        response = self.checkout(payment_method="card")
        self.assertEqual(response.status_code, 200)
        order = Order.objects.get(email="buyer@example.com")
        self.product.refresh_from_db()
        self.assertEqual(order.status, "cancelled")
        self.assertEqual(order.payment_status, "Payment Setup Failed")
        self.assertEqual(self.product.stock, 5)

    @override_settings(RAZORPAY_WEBHOOK_SECRET="webhook_secret")
    def test_razorpay_webhook_rejects_invalid_signature(self):
        response = self.client.post(
            reverse("orders:razorpay_webhook"),
            data='{"event":"payment.captured"}',
            content_type="application/json",
            HTTP_X_RAZORPAY_SIGNATURE="invalid",
        )
        self.assertEqual(response.status_code, 400)


    @override_settings(RAZORPAY_KEY_ID="rzp_test_key", RAZORPAY_KEY_SECRET="test_secret")
    @patch("orders.views.fetch_razorpay_payment")
    @patch("orders.views.create_razorpay_order")
    def test_valid_captured_payment_marks_order_paid(self, create_gateway_order, fetch_payment):
        import hashlib
        import hmac

        create_gateway_order.return_value = {"id": "order_test_123", "amount": 134900, "currency": "INR"}
        self.add_item()
        self.checkout(payment_method="card")
        order = Order.objects.get(email="buyer@example.com")
        payment_id = "pay_test_123"
        signature = hmac.new(
            b"test_secret",
            b"order_test_123|pay_test_123",
            hashlib.sha256,
        ).hexdigest()
        fetch_payment.return_value = {
            "id": payment_id,
            "order_id": "order_test_123",
            "amount": 134900,
            "currency": "INR",
            "status": "captured",
        }

        response = self.client.post(reverse("orders:payment_verify", args=[order.order_number]), {
            "razorpay_order_id": "order_test_123",
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        })
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.payment_status, "Paid")
        self.assertEqual(order.status, "placed")
        self.assertEqual(order.razorpay_payment_id, payment_id)
