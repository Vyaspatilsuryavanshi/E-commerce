from django.contrib import admin
from .models import Department, Category, Brand, Product, ProductVariant, ProductReview, StoreLocation


class CategoryInline(admin.TabularInline):
    model = Category
    extra = 1


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'order')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [CategoryInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'order')
    list_filter = ('department',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'origin_country', 'is_featured')
    list_filter = ('is_featured',)
    prepopulated_fields = {'slug': ('name',)}


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


class ProductReviewInline(admin.TabularInline):
    model = ProductReview
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'category', 'brand', 'price', 'stock', 'rating', 'dominant_color_hex', 'is_featured')
    list_filter = ('department', 'category', 'brand', 'is_featured', 'is_trending', 'is_bestseller')
    search_fields = ('name', 'sku', 'description', 'visual_tags')
    prepopulated_fields = {'slug': ('name', 'sku')}
    inlines = [ProductVariantInline, ProductReviewInline]


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'variant_type', 'name', 'hex_color', 'additional_price', 'stock')
    list_filter = ('variant_type',)


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'author_name', 'rating', 'title', 'verified_buyer', 'created_at')
    list_filter = ('rating', 'verified_buyer')


@admin.register(StoreLocation)
class StoreLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'state', 'country', 'latitude', 'longitude', 'is_active')
    list_filter = ('city', 'country', 'is_active')
