from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customerprofile",
            name="default_country",
            field=models.CharField(default="India", max_length=80),
        ),
    ]
