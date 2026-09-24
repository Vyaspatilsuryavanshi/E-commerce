from decimal import Decimal

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0002_order_choices"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="courier_partner",
            field=models.CharField(default="Blue Dart Luxury Express", max_length=80),
        ),
        migrations.AddField(
            model_name="order",
            name="delivered_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="order",
            name="delivery_estimate_text",
            field=models.CharField(
                default="Estimated delivery within 2-3 business days",
                max_length=150,
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="shipping_cost",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                max_digits=12,
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("placed", "Order Placed"),
                    ("processing", "Preparing in Atelier"),
                    ("shipped", "Shipped with Courier"),
                    ("out_for_delivery", "Out for Delivery"),
                    ("delivered", "Delivered"),
                    ("return_requested", "Return Requested"),
                    ("return_approved", "Return Approved - Reverse Pickup Scheduled"),
                    ("returned", "Returned & Refunded"),
                    ("cancelled", "Cancelled"),
                ],
                default="placed",
                max_length=30,
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="subtotal",
            field=models.DecimalField(decimal_places=2, max_digits=12),
        ),
        migrations.AlterField(
            model_name="order",
            name="total",
            field=models.DecimalField(decimal_places=2, max_digits=12),
        ),
        migrations.AlterField(
            model_name="orderitem",
            name="price",
            field=models.DecimalField(decimal_places=2, max_digits=12),
        ),
        migrations.CreateModel(
            name="OrderReturn",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("reason", models.CharField(max_length=40, choices=[
                    ("size_fit", "Size / Fit Issue"),
                    ("defective", "Defective / Damaged Item Received"),
                    ("wrong_item", "Wrong Shade / Item Received"),
                    ("quality", "Fabric / Quality Did Not Meet Expectations"),
                    ("changed_mind", "Changed Mind / Dissatisfied"),
                ])),
                ("item_condition", models.CharField(default="unopened", max_length=40, choices=[
                    ("unopened", "Unopened / With Original Security Seals"),
                    ("tried_once", "Tried Once / Tags Intact"),
                    ("damaged", "Damaged in Transit"),
                ])),
                ("refund_preference", models.CharField(default="original", max_length=30, choices=[
                    ("original", "Refund to Original Payment Mode (Bank / UPI)"),
                    ("store_credits", "AURA Store Credits (+5% Instant Loyalty Bonus)"),
                ])),
                (
                    "comments",
                    models.TextField(blank=True, help_text="Customer notes on return/exchange"),
                ),
                ("return_auth_code", models.CharField(editable=False, max_length=40, unique=True)),
                ("status", models.CharField(default="requested", max_length=30, choices=[
                    ("requested", "Return Requested"),
                    ("approved", "Return Approved (Reverse Courier Scheduled)"),
                    ("picked_up", "Picked Up by Courier"),
                    ("refunded", "Inspected & Refund Issued"),
                    ("rejected", "Declined"),
                ])),
                ("pickup_date", models.DateField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="returns",
                        to="orders.order",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
