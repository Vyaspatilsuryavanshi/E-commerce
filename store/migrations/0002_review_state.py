from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("store", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="productreview",
            name="verified_buyer",
            field=models.BooleanField(default=False),
        ),
        migrations.AddConstraint(
            model_name="productreview",
            constraint=models.UniqueConstraint(fields=("product", "user"), name="unique_product_user_review"),
        ),
    ]
