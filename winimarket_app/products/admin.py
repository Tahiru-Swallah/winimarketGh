from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from .models import Category, Product, ProductImage, WishList

# ========== CATEGORY ADMIN ==========
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at", "product_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("-created_at",)

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = "Products"


# ========== INLINE PRODUCT IMAGE ==========
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ("thumbnail_preview",)
    fields = ("image", "is_primary", "thumbnail_preview")

    def thumbnail_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:60px; height:60px; object-fit:cover; border-radius:6px;" />',
                obj.image.url,
            )
        return "No image"
    thumbnail_preview.short_description = "Preview"

    # ===== Validation: Max 3 images per product =====
    def get_max_num(self, request, obj=None, **kwargs):
        return 3

    # ===== Enforce single primary image =====
    def save_model(self, request, obj, form, change):
        if obj.is_primary:
            # Set all other images for this product to is_primary=False
            ProductImage.objects.filter(product=obj.product, is_primary=True).exclude(pk=obj.pk).update(is_primary=False)
        super().save_model(request, obj, form, change)

    # ===== Validate image size/type inline =====
    def clean(self):
        for form in self.get_formset(request=None).forms:
            image = form.cleaned_data.get("image")
            if image:
                if image.size > 5 * 1024 * 1024:
                    raise ValidationError("Each image must be ≤5MB")
                if image.content_type not in ['image/jpeg', 'image/png', 'image/jpg']:
                    raise ValidationError("Only JPEG and PNG images allowed.")


# ========== PRODUCT ADMIN ==========
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "seller_display",
        "name",
        "slug",
        "category",
        "min_price",
        "max_price",
        "quantity",
        "condition",
        "is_active",
        "created_at",
        "product_thumbnail_display",
    )
    list_filter = (
        "category",
        "condition",
        "is_active",
        "created_at",
        "seller__store_name",
    )
    search_fields = ("name", "description", "seller__store_name", "category__name")
    list_editable = ("is_active",)
    list_per_page = 20
    inlines = [ProductImageInline]
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("-created_at",)

    fieldsets = (
        ("Product Info", {
            "fields": ("name", "slug", "category", "description", "seller", "condition", "is_active")
        }),
        ("Pricing & Stock", {
            "fields": ("min_price", "max_price", "quantity"),
            "classes": ("collapse",)
        }),
        ("Timestamps", {
            "fields": ("created_at",),
            "classes": ("collapse",)
        }),
    )

    readonly_fields = ("created_at",)

    # ===== Display helpers =====
    def seller_display(self, obj):
        return obj.seller.store_name
    seller_display.short_description = "Seller"

    def product_thumbnail_display(self, obj):
        primary_img = obj.images.filter(is_primary=True).first()
        if primary_img and primary_img.image:
            return format_html(
                '<img src="{}" style="width:60px; height:60px; object-fit:cover; border-radius:6px;" />',
                primary_img.image.url,
            )
        return "—"
    product_thumbnail_display.short_description = "Thumbnail"


# ========== PRODUCT IMAGE ADMIN ==========
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "is_primary", "image_preview", "uploaded_at")
    list_filter = ("is_primary", "uploaded_at")
    search_fields = ("product__name",)
    readonly_fields = ("uploaded_at", "image_preview")
    ordering = ("-uploaded_at",)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:70px; height:70px; object-fit:cover; border-radius:8px;" />',
                obj.image.url,
            )
        return "—"
    image_preview.short_description = "Preview"

    # ===== Enforce single primary image in standalone admin =====
    def save_model(self, request, obj, form, change):
        if obj.is_primary:
            ProductImage.objects.filter(product=obj.product, is_primary=True).exclude(pk=obj.pk).update(is_primary=False)
        super().save_model(request, obj, form, change)
