from django.contrib import admin
from .models import Cart, CartItem


# -------------------------------
# Cart Item Inline (inside Cart)
# -------------------------------
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    can_delete = False
    readonly_fields = (
        'product',
        'choice_price',
        'quantity',
        'subtotal_display',
        'added_at',
    )

    def subtotal_display(self, obj):
        return obj.subtotal
    subtotal_display.short_description = "Subtotal"


# -------------------------------
# Cart Admin
# -------------------------------
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'buyer_email',
        'status',
        'total_items_display',
        'total_price_display',
        'created_at',
        'updated_at',
    )
    list_filter = ('status', 'created_at')
    search_fields = ('buyer__user__email',)
    readonly_fields = (
        'buyer',
        'status',
        'created_at',
        'updated_at',
        'total_items_display',
        'total_price_display',
    )
    ordering = ('-updated_at',)
    inlines = [CartItemInline]

    def buyer_email(self, obj):
        return obj.buyer.user.email
    buyer_email.short_description = "Buyer"

    def total_items_display(self, obj):
        return obj.total_items
    total_items_display.short_description = "Total Items"

    def total_price_display(self, obj):
        return f"GHS {obj.total_price}"
    total_price_display.short_description = "Total Price"


# -------------------------------
# Cart Item Admin (Read-only)
# -------------------------------
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = (
        'cart',
        'product',
        'quantity',
        'choice_price',
        'subtotal_display',
        'added_at',
    )
    list_filter = ('added_at',)
    search_fields = ('product__name', 'cart__buyer__user__email')
    readonly_fields = (
        'cart',
        'product',
        'quantity',
        'choice_price',
        'added_at',
        'subtotal_display',
    )
    ordering = ('-added_at',)

    def subtotal_display(self, obj):
        return obj.subtotal
    subtotal_display.short_description = "Subtotal"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return True
