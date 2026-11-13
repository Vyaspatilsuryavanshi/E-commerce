from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0005_order_razorpay_payment_references"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="status",
            field=__import__("django.db.models", fromlist=["models"]).CharField(
                choices=[
                    ("pending_payment", "Awaiting Payment"),
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
    ]
