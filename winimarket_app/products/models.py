from django.db import models, transaction
from registration.models import Profile
from uuid import uuid4
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

# -----------------------------
# Category Model
# -----------------------------
class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=150, unique=True)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
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
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)            # Current price
    min_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)        # Minimum price (for price range)
    max_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)        # Maximum price (for price range)
    quantity = models.PositiveIntegerField(default=1)                       # Stock quantity
    category = models.ForeignKey(Category, related_name='products', on_delete=models.SET_NULL, null=True, blank=True)  # Product category
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
    
    def clean(self):
        if self.max_price < self.min_price:
            raise ValidationError("Max price cannot be less than min price.")

    @property
    def is_available(self):
        # Returns True if product is in stock and active
        return self.quantity > 0 and self.is_active

    @property
    
    def is_seller(self):
        return self.seller.profile.role == 'seller'

    @property
    def image_count(self):
        # Returns the number of images for this product
        return self.images.count()

    def __str__(self):
        return f"{self.name} - {self.category.name if self.category else 'Uncategorized'}"

# -----------------------------
# Product Image Gallery Model
# -----------------------------
class ProductImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)
    thumbnail = models.ImageField(upload_to='product_images/thumbnails/', null=True, blank=True, editable=False)
    medium = models.ImageField(upload_to='product_images/medium/', null=True, blank=True, editable=False)
    large = models.ImageField(upload_to='product_images/large/', null=True, blank=True, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.image and self.image.size > 5 * 1024 * 1024:
            raise ValidationError("Image size should not exceed 5MB.")
    
        valid_types = ['image/jpeg', 'image/png', 'image/jpg']
        if self.image and self.image.file.content_type not in valid_types:
            raise ValidationError("Unsupported image type. Only JPEG and PNG are allowed.")
        
        # Enforce maximum 3 images per product
        if self._state.adding:  # Only check for new images
            existing_count = ProductImage.objects.filter(product=self.product).count()
            if existing_count >= 3:
                raise ValidationError("You can upload a maximum of 3 images per product.")

    def save(self, *args, **kwargs):
        first_save = self._state.adding
        super().save(*args, **kwargs)

        if self.image:
            self.generate_variations()

        if first_save:
            with transaction.atomic():
                if not ProductImage.objects.filter(product=self.product, is_primary=True).exists():
                    self.is_primary = True
                    super().save(update_fields=['is_primary'])

    def generate_variations(self):
        sizes = {
            'thumbnail': (150, 150),
            'medium': (400, 400),
            'large': (800, 800)
        }

        for field, size in sizes.items():
            try:
                with Image.open(self.image) as img:
                    if img.mode in ("RGBA", "LA"):
                        background = Image.new("RGB", img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[3])  # 3 is the
                        img = background
                    else:
                        img = img.convert('RGB')

                    img.thumbnail(size, Image.Resampling.LANCZOS)

                    buffer = BytesIO()
                    img.save(buffer, format='JPEG', quality=85)
                    buffer.seek(0)
                    file_name = f"{uuid4()}.jpg"
                    content_file = ContentFile(buffer.getvalue(), name=file_name)

                    setattr(self, field, content_file)

            except Exception as e:
                raise ValidationError(f"Error processing image: {e}")

    def __str__(self):
        return f"Images for {self.product.name}"

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