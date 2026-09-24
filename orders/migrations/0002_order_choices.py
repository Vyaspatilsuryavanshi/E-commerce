from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="delivery_method",
            field=models.CharField(
                choices=[
                    ("standard", "Standard Luxury Courier (3-5 Days) - ₹149 (Free over ₹1,999)"),
                    ("express_local", "Express Local Courier (24-48 Hours) - ₹299"),
                    ("same_day", "Same-Day Boutique Concierge Delivery - ₹499"),
                ],
                default="standard",
                max_length=30,
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="payment_status",
            field=models.CharField(default="Pending", max_length=30),
        ),
    ]
