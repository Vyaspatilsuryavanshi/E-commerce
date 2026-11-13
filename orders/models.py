import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from store.models import Product, ProductVariant


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending_payment', 'Awaiting Payment'),
        ('payment_review', 'Payment Review Required'),
        ('placed', 'Order Placed'),
        ('processing', 'Preparing in Atelier'),
        ('shipped', 'Shipped with Courier'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('return_requested', 'Return Requested'),
        ('return_approved', 'Return Approved - Reverse Pickup Scheduled'),
        ('returned', 'Returned & Refunded'),
        ('cancelled', 'Cancelled'),
    )

    DELIVERY_METHODS = (
        ('standard', 'Standard Luxury Courier (3-5 Days) - ₹149 (Free over ₹1,999)'),
        ('express_local', 'Express Local Courier (24-48 Hours) - ₹299'),
        ('same_day', 'Same-Day Boutique Concierge Delivery - ₹499'),
    )

    PAYMENT_METHODS = (
        ('card', 'Credit / Debit Card (Visa, Mastercard, RuPay)'),
        ('upi', 'Instant UPI / QR / NetBanking'),
        ('apple_pay', 'Apple Pay / Google Pay'),
        ('cod', 'Cash on Delivery / Concierge Handover'),
    )

    order_number = models.CharField(max_length=36, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')

    # Customer Contact
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    email = models.EmailField()
    phone = models.CharField(max_length=30)

    # Shipping Address (Geolocation Assisted)
    address_line_1 = models.CharField(max_length=250)
    address_line_2 = models.CharField(max_length=250, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=30)
    country = models.CharField(max_length=80, default='India')

    # GPS coordinates captured via browser location access
    shipping_latitude = models.FloatField(null=True, blank=True, help_text="GPS Latitude captured at checkout")
    shipping_longitude = models.FloatField(null=True, blank=True, help_text="GPS Longitude captured at checkout")
    location_autodetected = models.BooleanField(default=False)

    delivery_method = models.CharField(max_length=30, choices=DELIVERY_METHODS, default='standard')
    delivery_estimate_text = models.CharField(max_length=150, default='Estimated delivery within 2-3 business days')
    courier_partner = models.CharField(max_length=80, default='Blue Dart Luxury Express')

    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHODS, default='card')
    payment_status = models.CharField(max_length=30, default='Pending')
    razorpay_order_id = models.CharField(max_length=64, blank=True, db_index=True)
    razorpay_payment_id = models.CharField(max_length=64, blank=True, null=True, unique=True)

    # Financials in Indian Rupees (₹)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=12, decimal_places=2)
    coupon_used = models.CharField(max_length=50, blank=True, null=True)

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='placed')
    tracking_number = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)

    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.order_number} - {self.first_name} {self.last_name} (₹{self.total})"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"AL-{uuid.uuid4().hex[:8].upper()}"
        if not self.tracking_number:
            self.tracking_number = f"BD-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_address(self):
        parts = [self.address_line_1]
        if self.address_line_2:
            parts.append(self.address_line_2)
        parts.extend([f"{self.city}, {self.state} {self.postal_code}", self.country])
        return ", ".join(parts)

    @property
    def is_delivered(self):
        return self.status in ('delivered', 'return_requested', 'return_approved', 'returned')

    @property
    def can_cancel(self):
        return self.status in ('pending_payment', 'placed', 'processing')

    @property
    def can_return(self):
        return self.status == 'delivered'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name='order_items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)

    product_name = models.CharField(max_length=220)
    variant_name = models.CharField(max_length=100, blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.quantity}x {self.product_name} in #{self.order.order_number}"

    @property
    def total_price(self):
        return self.price * self.quantity


class OrderReturn(models.Model):
    """Customer return and exchange requests"""
    REASON_CHOICES = (
        ('size_fit', 'Size / Fit Issue'),
        ('defective', 'Defective / Damaged Item Received'),
        ('wrong_item', 'Wrong Shade / Item Received'),
        ('quality', 'Fabric / Quality Did Not Meet Expectations'),
        ('changed_mind', 'Changed Mind / Dissatisfied'),
    )

    CONDITION_CHOICES = (
        ('unopened', 'Unopened / With Original Security Seals'),
        ('tried_once', 'Tried Once / Tags Intact'),
        ('damaged', 'Damaged in Transit'),
    )

    REFUND_CHOICES = (
        ('original', 'Refund to Original Payment Mode (Bank / UPI)'),
        ('store_credits', 'AURA Store Credits (+5% Instant Loyalty Bonus)'),
    )

    STATUS_CHOICES = (
        ('requested', 'Return Requested'),
        ('approved', 'Return Approved (Reverse Courier Scheduled)'),
        ('picked_up', 'Picked Up by Courier'),
        ('refunded', 'Inspected & Refund Issued'),
        ('rejected', 'Declined'),
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='returns')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.CharField(max_length=40, choices=REASON_CHOICES)
    item_condition = models.CharField(max_length=40, choices=CONDITION_CHOICES, default='unopened')
    refund_preference = models.CharField(max_length=30, choices=REFUND_CHOICES, default='original')
    comments = models.TextField(blank=True, help_text="Customer notes on return/exchange")

    return_auth_code = models.CharField(max_length=40, unique=True, editable=False)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='requested')
    pickup_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Return #{self.return_auth_code} for Order #{self.order.order_number}"

    def save(self, *args, **kwargs):
        if not self.return_auth_code:
            self.return_auth_code = f"RET-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
