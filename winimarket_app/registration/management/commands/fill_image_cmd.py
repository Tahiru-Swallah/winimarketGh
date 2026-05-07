from django.core.management.base import BaseCommand
from products.models import Category
import requests
from django.conf import settings

class Command(BaseCommand):
    help = 'Fetches Pexels images for existing categories with empty image_url'

    def handle(self, *args, **options):
        # Find categories that are missing an image
        categories = Category.objects.filter(image_url__in=['', None])
        self.stdout.write(f"Found {categories.count()} categories to update.")

        headers = {"Authorization": settings.PEXEL_ACCESS_KEY}

        for cat in categories:
            try:
                res = requests.get(
                    "https://pexels.com",
                    params={"query": cat.name, "per_page": 1},
                    headers=headers,
                    timeout=5
                )

                if res.status_code == 200:
                    data = res.json()
                    if data.get("photos"):
                        # Access correctly: data["photos"][0]["src"]["medium"]
                        img_url = data["photos"][0]["src"]["medium"]
                        
                        # Use update to avoid triggering signals
                        Category.objects.filter(pk=cat.pk).update(image_url=img_url)
                        self.stdout.write(self.style.SUCCESS(f"Updated {cat.name}"))
                        
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed {cat.name}: {e}"))