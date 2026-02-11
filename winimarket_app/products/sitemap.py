from django.contrib.sitemaps import Sitemap
from products.models import Product

class ProductSiteMap(Sitemap):
    changefreq = 'daily'
    priority = 0.9

    def items(self):
        return Product.objects.filter(is_active=True)

    def location(self, item):
        return f"/product/detail/{item.id}/{item.slug}/"