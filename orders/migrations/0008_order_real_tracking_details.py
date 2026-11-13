from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0007_order_payment_review_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="tracking_url",
            field=models.URLField(blank=True, max_length=500),
        ),
        migrations.AlterField(
            model_name="order",
            name="courier_partner",
            field=models.CharField(default="Not assigned", max_length=80),
        ),
    ]
