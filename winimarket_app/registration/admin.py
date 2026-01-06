from django.contrib import admin
from django.utils import timezone

from .models import (
    CustomUser,
    Profile,
    SellerProfile,
    SellerPayment,
    SellerVerification,
    SellerAddress,
    SellerAuditLog,
)

# =====================================================
# Custom User Admin
# =====================================================
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'phonenumber', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('email', 'phonenumber')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    ordering = ('-date_joined',)


# =====================================================
# Profile Admin
# =====================================================
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'role_confirmed', 'full_name', 'created_at')
    search_fields = ('user__email', 'full_name')
    list_filter = ('role', 'created_at')
    readonly_fields = ('created_at',)


# =====================================================
# INLINE DEFINITIONS (Seller Sub-Models)
# =====================================================
class SellerAddressInline(admin.StackedInline):
    model = SellerAddress
    extra = 0
    can_delete = False

class SellerAuditLogInline(admin.TabularInline):
    model = SellerAuditLog
    extra = 0
    can_delete = False
    readonly_fields = ('admin_user', 'action', 'note', 'created_at')

class SellerPaymentInline(admin.StackedInline):
    model = SellerPayment
    extra = 0
    can_delete = False

    readonly_fields = ()

    def masked_momo_number(self, obj):
        if obj.momo_number:
            return f"****{obj.momo_number[-4:]}"
        return ""
    masked_momo_number.short_description = "MoMo Number"


class SellerVerificationInline(admin.StackedInline):
    model = SellerVerification
    extra = 0
    can_delete = False

    readonly_fields = (
        'id_type',
        'masked_id_number',
        'status',
        'submitted_at',
        'reviewed_at',
    )

    def masked_id_number(self, obj):
        if obj.id_number:
            return f"****{obj.id_number[-4:]}"
        return ""
    masked_id_number.short_description = "ID Number"


# =====================================================
# Seller Profile Admin (MAIN SELLER VIEW)
# =====================================================
@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = (
        'store_name',
        'get_email',
        'is_verified',
        'is_blacklisted',
        'created_at',
    )
    search_fields = ('store_name', 'profile__user__email')
    list_filter = ('is_verified', 'is_blacklisted', 'created_at')
    readonly_fields = ('created_at',)

    inlines = [
        SellerAddressInline,
        SellerPaymentInline,
        SellerVerificationInline,
        SellerAuditLogInline,
    ]

    def get_email(self, obj):
        return obj.profile.user.email
    get_email.short_description = "Seller Email"


# =====================================================
# Seller Verification Admin (Bulk Review)
# =====================================================
@admin.register(SellerVerification)
class SellerVerificationAdmin(admin.ModelAdmin):
    list_display = (
        'seller',
        'id_type',
        'masked_id_number',
        'status',
        'submitted_at',
        'reviewed_at',
    )
    list_filter = ('status', 'id_type', 'submitted_at')
    search_fields = ('seller__store_name', 'id_number')
    readonly_fields = ('submitted_at', 'reviewed_at')

    actions = ['approve_verification', 'reject_verification']

    """ def changelist_view(self, request, extra_context=None):
        print("🔥 SellerVerificationAdmin is ACTIVE")
        return super().changelist_view(request, extra_context)
 """
    def masked_id_number(self, obj):
        if obj.id_number:
            return f"****{obj.id_number[-4:]}"
        return ""
    masked_id_number.short_description = "ID Number"

    def approve_verification(self, request, queryset):
        approved = 0

        for verification in queryset:
            print(verification.seller)
            if verification.status == 'approved':
                continue  # Skip already approved verifications

            verification.status = 'approved'
            verification.reviewed_at = timezone.now()
            verification.save()

            seller = verification.seller
            seller.is_verified = True
            seller.save()

            SellerAuditLog.objects.create(
                seller=seller,
                admin_user=request.user,
                action='approved',
                note='Verification approved via admin panel'
            )
            
        approved += 1
        self.message_user(request, f"{approved} seller(s) approved successfully.")

    def reject_verification(self, request, queryset):
        rejected = 0

        for verification in queryset:
            if verification.status == 'rejected':
                continue  # Skip already rejected verifications

            verification.status = 'rejected'
            verification.reviewed_at = timezone.now()
            verification.save()

            seller = verification.seller
            seller.is_verified = False
            seller.save()

            SellerAuditLog.objects.create(
                seller=seller,
                admin_user=request.user,
                action='rejected',
                note='Verification rejected via admin panel'
            )

        rejected += 1
        self.message_user(request, f"{rejected} seller(s) rejected successfully.")

    approve_verification.short_description = "Approve selected verifications"
    reject_verification.short_description = "Reject selected verifications"


# =====================================================
# Optional: Keep These for Direct Access (Read-Only)
# =====================================================
@admin.register(SellerPayment)
class SellerPaymentAdmin(admin.ModelAdmin):
    list_display = (
        'seller',
        'momo_name',
        'masked_momo_number',
        'bank_name',
        'masked_bank_account',
    )
    search_fields = ('seller__store_name',)
    readonly_fields = ()

    def masked_momo_number(self, obj):
        if obj.momo_number:
            return f"****{obj.momo_number[-4:]}"
        return ""

    def masked_bank_account(self, obj):
        if obj.bank_account:
            return f"****{obj.bank_account[-4:]}"
        return ""


@admin.register(SellerAddress)
class SellerAddressAdmin(admin.ModelAdmin):
    list_display = ('seller', 'country', 'region', 'city', 'campus', 'campus_area', 'hall_or_hostel', 'landmark')
    search_fields = ('seller__store_name', 'city', 'region')
    list_filter = ('country', 'region')


@admin.register(SellerAuditLog)
class SellerAuditLogAdmin(admin.ModelAdmin):
    list_display = ('seller', 'admin_user', 'action', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('seller__store_name', 'admin_user__email')
    readonly_fields = ('seller', 'admin_user', 'action', 'note', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
