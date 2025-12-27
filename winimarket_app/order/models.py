from django.db import models
from uuid import uuid4
from django.utils import timezone
from registration.models import Profile, SellerProfile

class OrderStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PAID = 'paid', 'Paid'
    PROCESSING = 'processing', 'Processing'
    SHIPPED = 'shipped', 'Shipped'
    DELIVERED = 'delivered', 'Delivered'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'

class OrderTrackingStatus(models.TextChoices):
    PROCESSING = 'processing', 'Processing'
    SHIPPED = 'shipped', 'Shipped'
    OUT_FOR_DELIVERY = 'out_for_delivery', 'Out for Delivery'
    DELIVERED = 'delivered', 'Delivered'

class ShippingAddress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    buyer = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='shipping_addresses'
    )
    address = models.CharField(max_length=250)
    state_region = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Ghana')
    phonenumber = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.address}, {self.state_region}, {self.city} ({self.buyer.user.email})"


class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    buyer = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    seller = models.ForeignKey(SellerProfile, on_delete=models.SET_NULL, related_name='seller_orders', null=True, blank=True)
    shipping_address = models.ForeignKey(
        ShippingAddress,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )

    is_escrow_released = models.BooleanField(default=False)
    escrow_released_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING
    )

    track_status = models.CharField(
        max_length=20,
        choices=OrderTrackingStatus.choices,
        default=OrderTrackingStatus.PROCESSING
    )

    cancelled_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f'Order {self.id} by {self.buyer.user.email}'

    @property
    def total_cost(self):
        return sum(item.subtotal for item in self.items.all())

    def cancel(self):
        if self.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            raise ValueError("Cannot cancel an order that has been shipped or delivered.")
        
        self.status = OrderStatus.CANCELLED
        self.cancelled_at = timezone.now()
        self.save()


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_items'
    )
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['order', 'product'], name='unique_order_product')
        ]
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['product']),
        ]

    def __str__(self):
        return f'{self.quantity} x {self.product.name if self.product else "Deleted Product"}'
    
    @property
    def subtotal(self):
        if self.price is None:
            return 0
        return self.price * self.quantity


    def save(self, *args, **kwargs):
        # Ensure price is always set from product if missing
        if not self.price and self.product and self.product.price:
            self.price = self.product.price
        elif not self.price:
            self.price = 0  # fallback in case product has no price

        super().save(*args, **kwargs)

class PaymentStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    SUCCESS = 'success', 'Success'
    FAILED = 'failed', 'Failed'
    REFUNDED = 'refunded', 'Refunded'

class Payment(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    
    buyer = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='payments')

    orders = models.ManyToManyField(Order, related_name='payments')

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    reference = models.CharField(max_length=100, unique=True)

    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)

    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.order.id} - {self.status}"