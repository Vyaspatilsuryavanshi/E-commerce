from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

from django.conf import settings

from store.models import Product, ProductVariant


VALID_COUPONS = {
    "LUXE15": {"type": "percent", "value": Decimal("15"), "desc": "15% off your order"},
    "BEAUTY500": {"type": "fixed", "value": Decimal("500"), "desc": "₹500 off your order"},
    "WELCOME10": {"type": "percent", "value": Decimal("10"), "desc": "10% welcome discount"},
}

FREE_SHIPPING_THRESHOLD = Decimal("1999.00")
STANDARD_SHIPPING_COST = Decimal("149.00")


class CartError(ValueError):
    """Raised when a requested cart operation cannot be completed."""


class Cart:
    """Session-backed shopping cart with live catalog validation."""

    def __init__(self, request):
        self.session = request.session if hasattr(request, "session") else request
        self.cart = self.session.get(settings.CART_SESSION_ID) or {}
        self.session[settings.CART_SESSION_ID] = self.cart
        self.coupon_code = self.session.get("coupon_code")

    def _get_key(self, product_id, variant_id=None):
        return f"{product_id}_{variant_id or '0'}"

    @staticmethod
    def _coerce_quantity(quantity):
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            raise CartError("Quantity must be a whole number.")
        if quantity < 1:
            raise CartError("Quantity must be at least 1.")
        return quantity

    @staticmethod
    def _stock_for(product, variant=None):
        return variant.stock if variant is not None else product.stock

    @staticmethod
    def _unit_price(product, variant=None):
        return product.price + (variant.additional_price if variant else Decimal("0.00"))

    def add(self, product, variant=None, quantity=1, override_quantity=False):
        quantity = self._coerce_quantity(quantity)
        if variant is not None and variant.product_id != product.id:
            raise CartError("The selected variant does not belong to this product.")
        if product.variants.exists() and variant is None:
            raise CartError("Please select a product option before adding this item.")

        available = self._stock_for(product, variant)
        if available < 1:
            raise CartError("This item is currently out of stock.")

        key = self._get_key(product.id, variant.id if variant else None)
        current = self.cart.get(key, {})
        current_qty = int(current.get("quantity", 0)) if current else 0
        target_qty = quantity if override_quantity else current_qty + quantity

        if target_qty > available:
            raise CartError(f"Only {available} unit(s) are currently available.")

        self.cart[key] = {
            "product_id": product.id,
            "variant_id": variant.id if variant else None,
            "quantity": target_qty,
            "price": str(self._unit_price(product, variant).quantize(Decimal("0.01"))),
        }
        self.save()
        return target_qty

    def update(self, key, quantity):
        if key not in self.cart:
            raise CartError("That cart item no longer exists.")
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            raise CartError("Quantity must be a whole number.")
        if quantity == 0:
            self.remove(key)
            return 0
        if quantity < 0:
            raise CartError("Quantity cannot be negative.")

        raw_item = self.cart[key]
        product = Product.objects.filter(id=raw_item.get("product_id")).first()
        if not product:
            self.remove(key)
            return 0

        variant_id = raw_item.get("variant_id")
        variant = ProductVariant.objects.filter(id=variant_id, product=product).first() if variant_id else None
        if variant_id and variant is None:
            self.remove(key)
            raise CartError("That product option is no longer available.")

        available = self._stock_for(product, variant)
        if available < 1:
            self.remove(key)
            raise CartError("That item is now out of stock.")
        if quantity > available:
            raise CartError(f"Only {available} unit(s) are currently available.")

        raw_item["quantity"] = quantity
        raw_item["price"] = str(self._unit_price(product, variant).quantize(Decimal("0.01")))
        self.save()
        return quantity

    def remove(self, key):
        if key in self.cart:
            del self.cart[key]
            self.save()

    def save(self):
        self.session.modified = True

    def clear(self):
        self.session[settings.CART_SESSION_ID] = {}
        self.coupon_code = None
        self.session.pop("coupon_code", None)
        self.cart = self.session[settings.CART_SESSION_ID]
        self.save()

    def refresh_prices(self):
        """Refresh stored item prices from the current catalog before checkout."""
        changed = False
        for key in list(self.cart):
            raw_item = self.cart[key]
            product = Product.objects.filter(id=raw_item.get("product_id")).first()
            if not product:
                del self.cart[key]
                changed = True
                continue
            variant_id = raw_item.get("variant_id")
            variant = ProductVariant.objects.filter(id=variant_id, product=product).first() if variant_id else None
            if variant_id and variant is None:
                del self.cart[key]
                changed = True
                continue
            new_price = str(self._unit_price(product, variant).quantize(Decimal("0.01")))
            if raw_item.get("price") != new_price:
                raw_item["price"] = new_price
                changed = True
        if changed:
            self.save()

    def apply_coupon(self, code):
        code = (code or "").strip().upper()
        rule = VALID_COUPONS.get(code)
        if not rule:
            return False, "Invalid coupon code. Try LUXE15, BEAUTY500, or WELCOME10."
        if len(self) == 0:
            return False, "Add an item to your bag before applying a coupon."
        self.session["coupon_code"] = code
        self.coupon_code = code
        self.save()
        return True, f"Coupon '{code}' applied: {rule['desc']}"

    def remove_coupon(self):
        self.session.pop("coupon_code", None)
        self.coupon_code = None
        self.save()

    def __iter__(self):
        item_keys = list(self.cart.keys())
        product_ids = [self.cart[k].get("product_id") for k in item_keys]
        products = {
            p.id: p
            for p in Product.objects.filter(id__in=product_ids).select_related("department", "category", "brand")
        }
        variant_ids = [self.cart[k].get("variant_id") for k in item_keys if self.cart[k].get("variant_id")]
        variants = {v.id: v for v in ProductVariant.objects.filter(id__in=variant_ids)}

        for key in item_keys:
            raw_item = self.cart[key]
            product = products.get(raw_item.get("product_id"))
            if not product:
                continue
            variant = variants.get(raw_item.get("variant_id")) if raw_item.get("variant_id") else None
            try:
                price = Decimal(str(raw_item.get("price", self._unit_price(product, variant))))
                quantity = int(raw_item.get("quantity", 0))
            except (InvalidOperation, TypeError, ValueError):
                continue
            if quantity < 1:
                continue
            yield {
                "key": key,
                "product": product,
                "variant": variant,
                "price": price,
                "quantity": quantity,
                "total_price": (price * quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                "available_stock": self._stock_for(product, variant),
            }

    def __len__(self):
        total = 0
        for item in self.cart.values():
            try:
                total += max(0, int(item.get("quantity", 0)))
            except (TypeError, ValueError):
                continue
        return total

    @property
    def subtotal(self):
        total = sum((item["total_price"] for item in self), Decimal("0.00"))
        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def discount_amount(self):
        rule = VALID_COUPONS.get(self.coupon_code)
        if not rule or self.subtotal <= 0:
            return Decimal("0.00")
        if rule["type"] == "percent":
            discount = self.subtotal * rule["value"] / Decimal("100")
        else:
            discount = min(rule["value"], self.subtotal)
        return discount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def discounted_subtotal(self):
        return max(Decimal("0.00"), self.subtotal - self.discount_amount)

    @property
    def is_free_shipping(self):
        return self.subtotal >= FREE_SHIPPING_THRESHOLD and len(self) > 0

    @property
    def shipping_cost(self):
        if len(self) == 0:
            return Decimal("0.00")
        return Decimal("0.00") if self.is_free_shipping else STANDARD_SHIPPING_COST

    @property
    def free_shipping_remaining(self):
        return max(Decimal("0.00"), FREE_SHIPPING_THRESHOLD - self.subtotal)

    @property
    def free_shipping_progress(self):
        if self.subtotal >= FREE_SHIPPING_THRESHOLD:
            return 100
        if self.subtotal <= 0:
            return 0
        return min(99, int((self.subtotal / FREE_SHIPPING_THRESHOLD) * 100))

    @property
    def grand_total(self):
        return max(Decimal("0.00"), self.discounted_subtotal + self.shipping_cost)

    def to_dict(self):
        items = []
        for item in self:
            items.append({
                "key": item["key"],
                "product_id": item["product"].id,
                "product_name": item["product"].name,
                "product_url": item["product"].get_absolute_url(),
                "product_image": item["product"].display_image,
                "variant_name": item["variant"].name if item["variant"] else None,
                "variant_type": item["variant"].get_variant_type_display() if item["variant"] else None,
                "price": str(item["price"]),
                "quantity": item["quantity"],
                "total_price": str(item["total_price"]),
                "available_stock": item["available_stock"],
            })
        return {
            "items": items,
            "item_count": len(self),
            "subtotal": str(self.subtotal),
            "discount": str(self.discount_amount),
            "shipping": str(self.shipping_cost),
            "grand_total": str(self.grand_total),
            "coupon_code": self.coupon_code,
            "is_free_shipping": self.is_free_shipping,
            "free_shipping_progress": self.free_shipping_progress,
            "free_shipping_remaining": str(self.free_shipping_remaining),
        }
