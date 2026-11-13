"""Inventory operations shared by order cancellation and expiry workflows."""
from store.models import Product, ProductVariant


def restore_order_inventory(order):
    """Restore the exact stock counters reserved by an order.

    Call inside transaction.atomic() after locking the order row.
    """
    for item in order.items.all():
        if not item.product_id:
            continue
        product = Product.objects.select_for_update().filter(pk=item.product_id).first()
        if product is None:
            continue
        if item.variant_id:
            variant = ProductVariant.objects.select_for_update().filter(
                pk=item.variant_id, product_id=product.pk
            ).first()
            if variant is not None:
                variant.stock += item.quantity
                variant.save(update_fields=["stock"])
                continue
        product.stock += item.quantity
        product.save(update_fields=["stock"])
