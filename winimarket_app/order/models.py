from django.db import models
from registration.models import Profile
from uuid import uuid4
from django.utils import timezone

class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    buyer = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='orders')
    address = models.CharField(max_length=250)
    postal_code = models.CharField(max_length=250)
    city = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=100, choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ], default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    payment_reference = models.CharField(max_length=250, null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def cancel_at(self):
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.save()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at'])
        ]

    def __str__(self):
        return f'Order {self.id} by {self.buyer.user.email}'
    
class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.quantity} x {self.product.name}'
