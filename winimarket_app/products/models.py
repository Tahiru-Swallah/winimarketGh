from django.db import models
from registration.models import Profile
from uuid import uuid4
from django.utils.text import slugify

# -----------------------------
# Category Model
# -----------------------------
class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)  # Unique identifier for each category
    name = models.CharField(max_length=100, unique=True)                    # Category name (unique)
    slug = models.SlugField(max_length=100, unique=True)                    # URL-friendly slug (unique)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)  # Optional category image
    created_at = models.DateTimeField(auto_now_add=True)                    # Timestamp when category was created
    updated_at = models.DateTimeField(auto_now=True)                        # Timestamp when category was last updated

    def save(self, *args, **kwargs):
        # Automatically generate slug from name if not provided
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

# -----------------------------
# Product Model
# -----------------------------
class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)  # Unique identifier for each product
    seller = models.ForeignKey('registration.SellerProfile', related_name='products', on_delete=models.CASCADE)  # Seller who owns the product
    name = models.CharField(max_length=200)                                 # Product name
    slug = models.SlugField(max_length=200, unique=True)                    # URL-friendly slug (unique)
    description = models.TextField()                                        # Product description
    min_price = models.DecimalField(max_digits=10, decimal_places=2)        # Minimum price (for price range)
    max_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)        # Maximum price (for price range)
    quantity = models.PositiveIntegerField(default=1)                       # Stock quantity
    category = models.ForeignKey(Category, related_name='products', on_delete=models.SET_NULL, null=True)  # Product category
    condition = models.CharField(max_length=50, choices=[
        ('new', 'New'),
        ('used', 'Used'),
        ('refurbished', 'Refurbished')
    ], default='new')                                                       # Product condition
    is_active = models.BooleanField(default=True)                           # Is the product available for sale?
    created_at = models.DateTimeField(auto_now_add=True)                    # Timestamp when product was created
    updated_at = models.DateTimeField(auto_now=True)                        # Timestamp when product was last updated

    def save(self, *args, **kwargs):
        # Automatically generate slug from name if not provided
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1

            middle_class = self.__class__
            while middle_class.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug
        super().save(*args, **kwargs)
    class Meta:
        ordering = ['-created_at']  # Newest products first
        indexes = [models.Index(fields=['-created_at'])]  # Index for faster queries

    @property
    def price_range(self):
        # Returns price range as a string
        return f"{self.min_price} - {self.max_price}"

    @property
    def is_available(self):
        # Returns True if product is in stock and active
        return self.quantity > 0 and self.is_active

    @property
    def is_seller(self):
        # Returns True if the seller is a valid seller profile
        return hasattr(self.seller, 'profile') and self.seller.profile.role == 'seller'

    @property
    def image_count(self):
        # Returns the number of images for this product
        return self.images.count()

    def __str__(self):
        return self.name

# -----------------------------
# Product Image Gallery Model
# -----------------------------
class ProductImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)  # Unique identifier for each image
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)  # Linked product
    image = models.ImageField(upload_to='product_images/')                  # Image file
    uploaded_at = models.DateTimeField(auto_now_add=True)                   # Timestamp when image was uploaded

    def __str__(self):
        # Shows product name for clarity in admin
        return f"Image for {self.product.name}"

# -----------------------------
# Wishlist Model
# -----------------------------
class WishList(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)  # Unique identifier for each wishlist entry
    buyer = models.ForeignKey(Profile, related_name='wishlist', on_delete=models.CASCADE)  # The user who wishlisted the product
    products = models.ForeignKey(Product, related_name='wishlisted_by', on_delete=models.CASCADE)  # The product wishlisted
    added_at = models.DateTimeField(auto_now_add=True)                      # Timestamp when product was added to wishlist

    class Meta:
        unique_together = ('buyer', 'products')                             # Prevent duplicate wishlist entries
        indexes = [models.Index(fields=['-added_at'])]                      # Index for faster queries
        ordering = ['-added_at']                                            # Newest wishlists first

    def __str__(self):
        return f"{self.buyer.user.email} Wishlisted {self.products.name}"