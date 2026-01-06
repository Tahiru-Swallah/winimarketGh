from django.contrib import admin
from .models import Order, OrderItem, ShippingAddress

# ---------------------------
# SIMPLIFIED SHIPPING ADDRESS INLINE
@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ('buyer', 'city', 'country', 'state_region', 'campus', 'campus_area', 'hall_or_hostel', 'landmark', 'phonenumber')
    search_fields = ('user__email', 'address', 'state_region', 'city', 'country')

# ---------------------------
# ORDER ITEM INLINE
# ---------------------------
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price')
    can_delete = False


# ---------------------------
# ORDER ADMIN
# ---------------------------
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'buyer',
        'status',
        'track_status',
        'total_cost',
        'created_at',
        'paid_at',
    )

    list_filter = (
        'status',
        'track_status',
        'created_at',
    )

    search_fields = (
        'id',
        'buyer__user__email',
    )

    ordering = ('-created_at',)

    readonly_fields = (
        'id',
        'buyer',
        'created_at',
        'updated_at',
        'paid_at',
        'cancelled_at',
        'total_cost',
    )

    fieldsets = (
        ("Order Info", {
            "fields": ("id", "buyer", "status", "track_status")
        }),
        ("Shipping", {
            "fields": ("shipping_address",)
        }),
        ("Payment", {
            "fields": ("paid_at", "total_cost"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at", "cancelled_at"),
            "classes": ("collapse",),
        }),
    )

    inlines = [OrderItemInline]


# ---------------------------
# ORDER ITEM ADMIN
# ---------------------------
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        'order',
        'product',
        'quantity',
        'price',
    )

    search_fields = (
        'order__id',
        'product__name',
    )

    readonly_fields = (
        'order',
        'product',
        'quantity',
        'price',
    )

    ordering = ('-order__created_at',)
