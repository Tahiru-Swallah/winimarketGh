from django.contrib import admin
from order.models import Payment
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('buyer', 'order_id_short', 'amount', 'status', 'reference', 'paid_at', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('orders__id', 'amount', 'status')  # works for searching by order ID
    date_hierarchy = 'created_at'

    def order_id_short(self, obj):
        # Display all related orders as comma-separated, first 8 characters of each ID
        orders = obj.orders.all()
        if orders.exists():
            return ", ".join(str(order.id)[:8] for order in orders)
        return "-"
    
    order_id_short.short_description = "Order ID"
    order_id_short.admin_order_field = 'orders__id'  # allows searching via related field

