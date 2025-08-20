from django.db import models
from products.models import Product
from registration.models import CustomUser
from uuid import uuid4

class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    buyer = models.ForeignKey('registration.Profile', on_delete=models.CASCADE, related_name='carts')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart {self.id} for {self.buyer.full_name}"
    
    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())
    
    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())
    
class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    choice_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        unique_together = ('cart', 'product')
    
    def save(self, *args, **kwargs):
        if not self.choice_price:
            self.choice_price = self.product.min_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} @ {self.choice_price} each in Cart {self.cart.id}"

    @property
    def subtotal(self):
        return self.quantity * self.choice_price