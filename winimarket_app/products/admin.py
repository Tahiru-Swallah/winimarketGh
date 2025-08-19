from django.contrib import admin
from .models import Category, Product, ProductImage, WishList

# Inline for product images in the product admin
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('created_at',)
    ordering = ('-created_at',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'seller', 'category', 'condition','min_price', 'max_price', 'quantity', 'is_active', 'created_at')
    search_fields = ('name', 'seller__store_name', 'category__name')
    list_filter = ('is_active', 'category', 'created_at')
    inlines = [ProductImageInline]
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('-created_at',)

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'image', 'uploaded_at')
    search_fields = ('product__name',)
    list_filter = ('uploaded_at',)

@admin.register(WishList)
class WishListAdmin(admin.ModelAdmin):
    list_display = ('buyer', 'products', 'added_at')
    search_fields = ('buyer__user__email', 'products__name')
    list_filter = ('added_at',)
    ordering = ('-added_at',)
