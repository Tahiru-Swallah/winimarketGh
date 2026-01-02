from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from .models import ProductImage, Category
from django.conf import settings
import requests

UNSPLASH_ACCESS_KEY = settings.UNSPLASH_ACCESS_KEY

@receiver(post_save, sender=Category)
def fetch_unsplash_image(sender, instance, created, **kwargs):
    if created and not instance.image_url:
        try:
            query = instance.name
            res = requests.get(
                f"https://api.unsplash.com/search/photos",
                params={"query": query, "per_page": 1, "client_id": UNSPLASH_ACCESS_KEY}
            )
            print(res.status_code)
            data = res.json()
            if data.get("results"):
                instance.image_url = data["results"][0]["urls"]["small"]
                instance.save()
        except Exception as e:
            print(f"Unsplash fetch failed for {instance.name}: {e}")

@receiver(post_delete, sender=ProductImage)
def auto_assign_new_primary(sender, instance, **kwargs):
    
    product = instance.product

    if instance.is_primary:
        next_image = ProductImage.objects.filter(product=product).first()
        if next_image:
            next_image.is_primary = True
            next_image.save()


            