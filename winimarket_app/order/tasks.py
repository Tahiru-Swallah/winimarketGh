from .models import Order
from django.utils import timezone
from datetime import timedelta

def cancel_expire_order():
    expiry_time = timezone.now() - timedelta(minutes=30)
    expired_order = Order.objects.filter(status='pending', created_at__lt=expiry_time)

    count = expired_order.update(status='cancelled')
    return f"{count} expired orders cancelled"

