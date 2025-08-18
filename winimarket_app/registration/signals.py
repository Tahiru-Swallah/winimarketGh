from django.db.models.signals import post_save
from .models import CustomUser, Profile, SellerProfile
from django.dispatch import receiver

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Create a Profile instance for the new user
        Profile.objects.create(user=instance)