from django.contrib import admin
from .models import CustomerProfile, Wishlist

@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'default_city', 'default_country')
    search_fields = ('user__username', 'user__email', 'default_city')

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'added_at')
    list_filter = ('added_at',)
