from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from .models import CustomerProfile, Wishlist
from store.models import Category, Department, Product


class AccountsTests(TestCase):
    def setUp(self):
        self.department = Department.objects.create(name="Clothing", slug="clothing")
        self.category = Category.objects.create(department=self.department, name="Dresses", slug="dresses")
        self.product = Product.objects.create(
            department=self.department, category=self.category, name="Test Dress", sku="ACC-001",
            short_description="Test", description="Test product", price="100.00", stock=10,
        )
        self.user = User.objects.create_user(username="customer", email="customer@example.com", password="StrongPass123!")
        self.client = Client()

    def test_profile_created_for_user(self):
        self.assertTrue(CustomerProfile.objects.filter(user=self.user).exists())

    def test_login_redirects_home(self):
        response = self.client.post(reverse("accounts:login"), {"username": "customer", "password": "StrongPass123!"})
        self.assertRedirects(response, reverse("store:home"))

    def test_logout_requires_post(self):
        self.client.login(username="customer", password="StrongPass123!")
        response = self.client.get(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("store:home"))
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_wishlist_toggle_requires_post_and_login(self):
        response = self.client.post(reverse("accounts:wishlist_toggle", args=[self.product.id]), HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 401)
        self.client.login(username="customer", password="StrongPass123!")
        response = self.client.post(reverse("accounts:wishlist_toggle", args=[self.product.id]), HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Wishlist.objects.filter(user=self.user, product=self.product).exists())
