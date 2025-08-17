from django.contrib import admin
from .models import CustomUser, Profile, SellerProfile

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'phonenumber', 'date_joined', 'is_staff', 'is_active')

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin): 
    list_display = ('user', 'role', 'full_name', 'profile_picture', 'created_at')
@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ('store_name', 'store_logo', 'store_description', 'business_address', 'momo_details', 'social_links', 'verification_status', 'created_at')