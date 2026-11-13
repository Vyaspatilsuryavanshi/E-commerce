from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0006_order_pending_payment_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending_payment", "Awaiting Payment"),
                    ("payment_review", "Payment Review Required"),
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
