from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0002_review_state"),
    ]

    operations = [
        migrations.CreateModel(
            name="NewsletterSubscriber",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("is_active", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("confirmed_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
