from django.db import models
from registration.models import Profile
from products.models import Product
from django.utils import timezone
from uuid import uuid4

class Cart(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('checked_out', 'Checked Out'),
        ('abandoned', 'Abandoned'),
    )

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    buyer = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='carts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['status'])]

    def __str__(self):
        return f"Cart {self.id} for {self.buyer.user.email} - Status: {self.status}"
    
    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())
    
class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    choice_price = models.DecimalField(max_digits=10, decimal_places=2)

    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product')
        indexes = [models.Index(fields=['cart', 'product'])]

    def save(self, *args, **kwargs):
        if not self.choice_price:
            self.choice_price = self.product.price

        if not self.product.is_active:
            raise ValueError("Cannot add inactive product to cart.")
        
        if self.quantity > self.product.quantity:
            raise ValueError("Requested quantity exceeds available stock.")
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Cart {self.cart.id}"

    @property
    def subtotal(self):
        return self.quantity * self.choice_price