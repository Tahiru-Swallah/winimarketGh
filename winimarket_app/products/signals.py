from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from .models import ProductImage, Category
from django.conf import settings
import requests

PEXEL_ACCESS_KEY = settings.PEXEL_ACCESS_KEY

@receiver(post_save, sender=Category)
def fetch_pexels_image(sender, instance, created, **kwargs):
    if created and not instance.image_url:
        try:
            query = instance.name

            headers = {
                "Authorization": PEXEL_ACCESS_KEY
            }

            res = requests.get(
                "https://api.pexels.com/v1/search",
                params={"query": query, "per_page": 1},
                headers=headers,
                timeout=5  # Prevents long waits if Pexels is slow
            )
            
            if res.status_code == 200:
                data = res.json()
                if data.get("photos") and len(data["photos"]) > 0:
                    # Use the 'medium' or 'large' image directly from Pexels
                    # Pexels optimizes these images automatically
                    optimized_url = data["photos"][0]["src"]["medium"]
                    
                    # Update without invoking the post_save signal loop
                    Category.objects.filter(pk=instance.pk).update(image_url=optimized_url)

        except Exception as e:
            print(f"Pexels fetch failed for {instance.name}: {e}")

@receiver(post_delete, sender=ProductImage)
def auto_assign_new_primary(sender, instance, **kwargs):
    
    product = instance.product

    if instance.is_primary:
        next_image = ProductImage.objects.filter(product=product).first()
        if next_image:
            next_image.is_primary = True
            next_image.save()


            