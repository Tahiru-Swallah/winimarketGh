from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from uuid import uuid4
from phonenumber_field.modelfields import PhoneNumberField

# -----------------------------
# Custom User Manager
# -----------------------------
class CustomUserManager(BaseUserManager):
    # Method to create a regular user
    def create_user(self, email=None, phonenumber=None, password=None, **extra_fields):
        if not email and not phonenumber:
            raise ValueError("Either email or phone number is required.")

        if email:
            email = self.normalize_email(email)

        user = self.model(email=email, phonenumber=phonenumber, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    # Method to create a superuser (admin)
    def create_superuser(self, email, phonenumber, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_superuser', True)

        if not email:
            raise ValueError("Superuser must have an email.")
        if not phonenumber:
            raise ValueError("Superuser must have a phone number.")

        return self.create_user(email=email, phonenumber=phonenumber, password=password, **extra_fields)

# -----------------------------
# Custom User Model
# -----------------------------
class CustomUser(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)  # Unique identifier for each user
    email = models.EmailField(unique=True, blank=False, db_index=True)      # User's email (unique)
    phonenumber = PhoneNumberField(unique=True, blank=True, null=True)      # User's phone number (unique, can be blank)
    date_joined = models.DateTimeField(auto_now_add=True)                   # Timestamp when user joined

    is_active = models.BooleanField(default=True)   # Is the user active?
    is_staff = models.BooleanField(default=False)   # Is the user a staff/admin?

    USERNAME_FIELD = 'email'                        # Field used for authentication
    REQUIRED_FIELDS = ['phonenumber']               # Required fields for createsuperuser

    objects = CustomUserManager()                   # Assign custom user manager

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower()         # Ensure email is always lowercase
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-date_joined']                 # Order users by join date (newest first)

    def __str__(self):
        return self.email or str(self.phonenumber)  # String representation

# -----------------------------
# Profile Model (for all users)
# -----------------------------
class Profile(models.Model):
    ROLE_CHOICES = (
        ('seller', 'Seller'),
        ('buyer', 'Buyer'),
    )

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)  # Unique identifier for each profile
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')  # Link to CustomUser
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='buyer')             # User role
    full_name = models.CharField(max_length=255, blank=True, null=True)                       # Full name
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True) # Profile picture
    created_at = models.DateTimeField(auto_now_add=True) # Profile creation time
    
    class Meta:
        ordering = ['-created_at']  # Order profiles by creation date (newest first)                            

    def __str__(self):
        return f"{self.user.email} - {self.role}"  # String representation

# -----------------------------
# Seller Profile Model (for sellers only)
# -----------------------------
class SellerProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)  # Unique identifier for each seller profile
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='seller_profile')  # Link to Profile
    store_name = models.CharField(max_length=255, unique=True)              # Store name (unique)
    store_description = models.TextField(blank=True, null=True)             # Store description
    store_logo = models.ImageField(upload_to='store_logos/', blank=True, null=True)  # Store logo
    business_address = models.CharField(max_length=255, blank=True, null=True)       # Business address
    momo_details = models.CharField(max_length=255, blank=True, null=True)           # Mobile money details
    social_links = models.JSONField(default=dict, blank=True)                        # Social media links (as JSON)
    verification_status = models.BooleanField(default=False)                         # Is the seller verified?
    created_at = models.DateTimeField(auto_now_add=True)                             # Seller profile creation time

    def __str__(self):
        return f"{self.store_name} - {self.profile.user.email}"  # String