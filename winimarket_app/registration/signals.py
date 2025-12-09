from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import (
    CustomUser,
    Profile,
    SellerProfile,
    SellerVerification,
    SellerPayment,
    SellerAddress
)


# Create Profile on user creation
@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)

# When user becomes seller — auto create linked seller data
@receiver(post_save, sender=Profile)
def create_seller_data(sender, instance, created, **kwargs):

    if instance.role == "seller":

        seller, _ = SellerProfile.objects.get_or_create(profile=instance)

        # Create Verification (pending)
        SellerVerification.objects.get_or_create(
            seller=seller,
            defaults={'status': 'pending'}
        )

        # Create empty Payment row
        SellerPayment.objects.get_or_create(seller=seller)

        # Create empty Address row
        SellerAddress.objects.get_or_create(
            seller=seller,
            defaults={
                'region': 'Not set',
                'city': 'Not set',
                'address': 'Not set',
                'country': 'Ghana'
            }
        )
