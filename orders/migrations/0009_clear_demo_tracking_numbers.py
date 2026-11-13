from django.db import migrations


def clear_generated_tracking_numbers(apps, schema_editor):
    Order = apps.get_model("orders", "Order")
    Order.objects.filter(tracking_number__startswith="BD-").update(tracking_number="")
    Order.objects.filter(courier_partner="Blue Dart Luxury Express").update(courier_partner="Not assigned")


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0008_order_real_tracking_details"),
    ]

    operations = [
        migrations.RunPython(clear_generated_tracking_numbers, migrations.RunPython.noop),
    ]
