from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse
from decimal import Decimal


class Department(models.Model):
    """Top-level department: Clothing, Skincare, Makeup"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    tagline = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='✨')
    banner_image = models.ImageField(upload_to='departments/', blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('store:catalog_department', kwargs={'department_slug': self.slug})


class Category(models.Model):
    """Subcategories under departments (e.g. Dresses, Serums, Lipsticks)"""
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = 'Categories'
        unique_together = ('department', 'slug')
        ordering = ['department', 'order', 'name']

    def __str__(self):
        return f"{self.department.name} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('store:catalog_category', kwargs={
            'department_slug': self.department.slug,
            'category_slug': self.slug
        })


class Brand(models.Model):
    """Luxury brands and house labels"""
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    origin_country = models.CharField(max_length=80, blank=True, default='France')
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """Core product catalog items"""
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')

    name = models.CharField(max_length=220)
    slug = models.SlugField(max_length=240, unique=True, blank=True)
    sku = models.CharField(max_length=60, unique=True)

    short_description = models.CharField(max_length=300)
    description = models.TextField()
    details = models.TextField(help_text="Key specifications, fit, volume, or fabric composition", blank=True)
    ingredients = models.TextField(help_text="Full ingredients for skincare/makeup or fabric care for clothing", blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Original price for showing discounts")

    primary_image = models.ImageField(upload_to='products/', blank=True, null=True)
    secondary_image = models.ImageField(upload_to='products/', blank=True, null=True)
    # Fallback / high-def CDN URLs for easy seeding & demonstration
    primary_image_url = models.URLField(max_length=500, blank=True)
    secondary_image_url = models.URLField(max_length=500, blank=True)

    # Visual search attributes
    dominant_color_hex = models.CharField(max_length=10, default='#1E293B', help_text="Primary color HEX code (e.g. #D97706, #E11D48)")
    visual_tags = models.CharField(max_length=400, blank=True, help_text="Comma-separated keywords for similarity matching: silk, satin, red, serum, glow, velvet")

    stock = models.PositiveIntegerField(default=50)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('4.80'))
    review_count = models.PositiveIntegerField(default=12)

    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    is_bestseller = models.BooleanField(default=False)
    is_new_arrival = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} (₹{self.price})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.name}-{self.sku}")
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('store:product_detail', kwargs={'slug': self.slug})

    @property
    def is_on_sale(self):
        return bool(self.compare_at_price and self.compare_at_price > self.price)

    @property
    def discount_percent(self):
        if self.is_on_sale:
            saving = (self.compare_at_price - self.price) / self.compare_at_price * 100
            return int(round(saving))
        return 0

    @property
    def display_image(self):
        if self.primary_image:
            return self.primary_image.url
        if self.primary_image_url:
            return self.primary_image_url
        return '/static/img/product-placeholder.svg'

    @property
    def display_secondary_image(self):
        if self.secondary_image:
            return self.secondary_image.url
        if self.secondary_image_url:
            return self.secondary_image_url
        return self.display_image

    @property
    def in_stock(self):
        if hasattr(self, "_prefetched_objects_cache") and "variants" in self._prefetched_objects_cache:
            variants = self._prefetched_objects_cache["variants"]
            if variants:
                return any(variant.stock > 0 for variant in variants)
            return self.stock > 0
        variants = self.variants.all()
        if variants.exists():
            return variants.filter(stock__gt=0).exists()
        return self.stock > 0


class ProductVariant(models.Model):
    """Size, Shade (Makeup), or Volume (Skincare) options"""
    VARIANT_TYPES = (
        ('size', 'Size (Apparel)'),
        ('shade', 'Shade (Makeup Swatch)'),
        ('volume', 'Volume (Skincare Bottle)'),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    variant_type = models.CharField(max_length=20, choices=VARIANT_TYPES, default='size')
    name = models.CharField(max_length=80, help_text="e.g. S, M, L or '01 Velvet Rose' or '50ml'")
    sku_suffix = models.CharField(max_length=20, blank=True)
    hex_color = models.CharField(max_length=10, blank=True, help_text="HEX color for makeup swatches, e.g. #A8203E")
    additional_price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    stock = models.PositiveIntegerField(default=25)

    class Meta:
        ordering = ['variant_type', 'id']

    def __str__(self):
        return f"{self.product.name} - {self.get_variant_type_display()}: {self.name}"

    @property
    def final_price(self):
        return self.product.price + self.additional_price


class ProductReview(models.Model):
    """Customer reviews and ratings; verified_buyer is set only after purchase validation."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    author_name = models.CharField(max_length=120)
    rating = models.PositiveSmallIntegerField(default=5)
    title = models.CharField(max_length=180)
    comment = models.TextField()
    verified_buyer = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['product', 'user'], name='unique_product_user_review'),
        ]

    def __str__(self):
        return f"{self.author_name} ({self.rating}★) - {self.product.name}"


class StoreLocation(models.Model):
    """Physical luxury boutiques / delivery hubs for location services"""
    name = models.CharField(max_length=150)
    address = models.CharField(max_length=250)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=30)
    country = models.CharField(max_length=80, default='United States')
    latitude = models.FloatField(help_text="GPS Latitude")
    longitude = models.FloatField(help_text="GPS Longitude")
    phone = models.CharField(max_length=50)
    hours = models.CharField(max_length=150, default='Mon - Sat: 10:00 AM - 9:00 PM, Sun: 11:00 AM - 6:00 PM')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['city', 'name']

    def __str__(self):
        return f"{self.name} - {self.city}, {self.country}"
