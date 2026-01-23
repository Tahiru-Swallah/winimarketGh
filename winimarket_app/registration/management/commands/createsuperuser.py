from django.core.management.base import BaseCommand
from registration.models import CustomUser

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        u, created = CustomUser.objects.get_or_create(
            email="winimarketgh@gmail.com",
            defaults={"phonenumber": "+233595467122"},
        )
        u.set_password("Dedon@123$com")
        u.is_superuser = True
        u.is_staff = True
        u.save()
        print(f"Superuser ready: {u.email}")