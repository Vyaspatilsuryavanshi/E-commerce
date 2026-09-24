from django.contrib import admin
from .models import Order, OrderItem, OrderReturn


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0


class OrderReturnInline(admin.TabularInline):
    model = OrderReturn
    extra = 0
    readonly_fields = ("return_auth_code", "created_at", "updated_at")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'full_name', 'email', 'city', 'state',
        'delivery_method', 'total', 'status', 'location_autodetected', 'created_at'
    )
    list_filter = ('status', 'delivery_method', 'location_autodetected', 'created_at')
    search_fields = ('order_number', 'first_name', 'last_name', 'email', 'tracking_number', 'city')
    readonly_fields = ('order_number', 'tracking_number', 'created_at', 'updated_at')
    inlines = [OrderItemInline, OrderReturnInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_name', 'variant_name', 'price', 'quantity', 'total_price')
    search_fields = ('product_name', 'order__order_number')


@admin.register(OrderReturn)
class OrderReturnAdmin(admin.ModelAdmin):
    list_display = ("return_auth_code", "order", "user", "reason", "status", "refund_preference", "created_at")
    list_filter = ("status", "reason", "refund_preference", "created_at")
    search_fields = ("return_auth_code", "order__order_number", "user__username")
    readonly_fields = ("return_auth_code", "created_at", "updated_at")
