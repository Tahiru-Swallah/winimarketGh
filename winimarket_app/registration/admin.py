from django.contrib import admin
from .models import CustomUser, Profile, SellerProfile, SellerPayment, SellerVerification, SellerAddress

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'phonenumber', 'date_joined', 'is_staff', 'is_active')

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin): 
    list_display = ('user', 'role', 'full_name', 'profile_picture', 'created_at')
@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ('store_name', 'store_logo', 'store_description', 'is_verified', 'is_blacklisted', 'created_at')

@admin.register(SellerVerification)
class SellerVerificationAdmin(admin.ModelAdmin):
    list_display = ('seller', 'id_card', 'business_certificate', 'selfie_with_id', 'status', 'submitted_at', 'reviewed_at', 'note') 

@admin.register(SellerPayment)
class SellerPaymentAdmin(admin.ModelAdmin):
    list_display = ('seller', 'momo_name', 'momo_number', 'bank_name', 'bank_account', 'created_at')

@admin.register(SellerAddress)
class SellerAddressAdmin(admin.ModelAdmin):
    list_display = ('seller', 'country', 'city', 'region', 'address')