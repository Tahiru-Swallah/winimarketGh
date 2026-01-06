from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import (
    CustomUser,
    Profile,
    SellerProfile,
    SellerVerification,
    SellerPayment,
    SellerAddress,
    EmailVerification,
)
from .utils import generate_verification_token

# Create Profile on user creation
@receiver(post_save, sender=CustomUser)
def create_user_profile_and_email_verification(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)

        EmailVerification.objects.create(
            user=instance,
            token=generate_verification_token(),
            expires_at=timezone.now() + timezone.timedelta(hours=24)
        )

# When user becomes seller — auto create linked seller data
@receiver(post_save, sender=Profile)
def create_seller_data(sender, instance, created, **kwargs):

    if instance.role == "seller":

        seller, _ = SellerProfile.objects.get_or_create(profile=instance)

        # Create Verification (pending)
        if not hasattr(seller, 'verification') or not SellerVerification.objects.filter(seller=seller).exists():
            SellerVerification.objects.create(seller=seller, status='pending')

        # Create empty Payment row
        SellerPayment.objects.get_or_create(seller=seller)

        # Create empty Address row
        SellerAddress.objects.get_or_create(seller=seller)
    return