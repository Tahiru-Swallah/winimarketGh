from django.contrib import admin
from order.models import Payment
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('buyer', 'order_id_short', 'amount', 'status', 'reference', 'paid_at', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('orders__id', 'amount', 'status')
    date_hierarchy = 'created_at'

    def order_id_short(self, obj):
        return str(obj.orders.id)[:8]

    order_id_short.short_description = "Order ID"
