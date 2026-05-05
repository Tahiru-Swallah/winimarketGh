from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser, Profile, SellerProfile, SellerAddress, SellerPayment, SellerVerification
from django.utils import timezone
from django.db import IntegrityError, transaction
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email_or_phonenumber'
    email_or_phonenumber = serializers.CharField()
    password = serializers.CharField(write_only = True)

    def validate(self, attrs):
        email_or_phonenumber = attrs.get('email_or_phonenumber')
        password = attrs.get('password')

        user = None

        if '@' in email_or_phonenumber:
            try:
                user = CustomUser.objects.get(email=email_or_phonenumber.lower())
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError({
                    'email_or_phonenumber': 'No account found with this email.'
                })
        
        else: 
            try:
                user = CustomUser.objects.get(phonenumber=email_or_phonenumber)
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError({
                    'email_or_phonenumber': 'No account found with this phone number.'
                })
        
        if not user.check_password(password):
            raise serializers.ValidationError({
                'password': 'Invalid credentials. Please try again.'
            })
        
        if not user.is_active:
            raise serializers.ValidationError({
                'account': 'This account is inactive. Please contact support.'
            })
        
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        data = super().get_token(user)

        return {
            "refresh_token": str(data),
            "access_token": str(data.access_token),
            "user": {
                "id": str(user.id),
                "email": user.email,
                "phonenumber": str(user.phonenumber),
            },
        }
    
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = CustomUser
        fields = ('email', 'phonenumber', 'password')

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError('An account with this email already exists')
        return value.lower()

    def validate_phonenumber(self, value):
        if CustomUser.objects.filter(phonenumber=value).exists():
            raise serializers.ValidationError('An account with this phone number already exists')
        return value

    def create(self, validated_data):
        try:
            with transaction.atomic():
                user = CustomUser(
                    email = validated_data['email'].lower(),
                    phonenumber = validated_data['phonenumber']
                )
                user.set_password(validated_data['password'])

                user.save()
                return user
            
        except IntegrityError as e:
            raise serializers.ValidationError({'detail' : 'A user with this email or phone number already exists.'}) from e

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        email = attrs.get("email")

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError({"email": "If an account exists, a reset link has been sent."})
        
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = PasswordResetTokenGenerator().make_token(user)

        reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"

        send_mail(
            subject="Reset Your Winimarket Password",
            message=f"Hi {user.email},\n\nYou requested a password reset for your Winimarket account. Click the link below to reset your password:\n\n{reset_link}\n\nIf you didn't request this, please ignore this email.\n\nBest,\nThe Winimarket Team",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            #fail_silently=False,
        )

        return {"detail": "Password reset link has been sent to your email."}
    
class PasswordResetConfirmSerializer(serializers.Serializer):
        uid = serializers.CharField()
        token = serializers.CharField()
        new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

        def validate(self, attrs):
            try:
                uid = force_str(urlsafe_base64_decode(attrs.get("uid")))
                user = CustomUser.objects.get(pk=uid)

            except Exception:
                raise serializers.ValidationError({"detail": "Invalid reset link."})
            
            if not PasswordResetTokenGenerator().check_token(user, attrs.get("token")):
                raise serializers.ValidationError({"detail": "Invalid or expired reset link."})
            
            try:
                validate_password(attrs.get("new_password"), user=user)
            except Exception as e:
                raise serializers.ValidationError({"new_password": list(e.messages)})
            
            user.set_password(attrs.get("new_password"))
            user.save()

            return {"detail": "Password has been reset successfully."}

    
class ProfileSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    seller_name = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = Profile
        fields = ('id', 'user', 'role', "role_confirmed", 'full_name', "user_email", 'profile_picture', 'seller_name', 'created_at')
        read_only_fields = ('id', 'user', 'role', 'created_at')

    def validate_profile_picture(self, value):
        if value:
            if value.size > 2 * 1024 * 1024:
                raise serializers.ValidationError("Profile Picture must be less than 2MB")
            if not value.content_type.startswith('image/'):
                raise serializers.ValidationError("Uploaded file is not an image.")        
        return value
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)
    
    def get_seller_name(self, obj):
        if hasattr(obj, 'seller_profile'):
            return obj.seller_profile.store_name
        return None
    
class SellerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerAddress
        fields = ("id", "region", "city", "country", "institution", "campus", "building", "landmark")
        read_only_fields = ('id',)

class SellerPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerPayment
        fields = ("id", "bank_name", "bank_account", 'service_provider', "momo_name", "momo_number",)
        read_only_fields = ('id',)


class SellerVerificationSerializer(serializers.ModelSerializer):
    id_card_image = serializers.ImageField(required=True)
    selfie_with_id = serializers.ImageField(required=True)
    class Meta:
        model = SellerVerification
        fields = ("id", "id_type", "id_number", "id_card_image", "selfie_with_id", "status", "note", "submitted_at", "reviewed_at")
        read_only_fields = ('id', 'status', 'note', 'submitted_at', 'reviewed_at')

    def validate_id_card_image(self, value):
        if value:
            if value.size > 10 * 1024 * 1024:
                raise serializers.ValidationError("ID image must be less than 10MB")
            if not getattr(value, "content_type", "").startswith('image/'):
                raise serializers.ValidationError("Uploaded file is not an image.")
        return value

    def validate_selfie_with_id(self, value):
        if value:
            if value.size > 10 * 1024 * 1024:
                raise serializers.ValidationError("Selfie must be less than 10MB")
            if not getattr(value, "content_type", "").startswith('image/'):
                raise serializers.ValidationError("Uploaded file is not an image.")
        return value

class SellerProfileSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    store_logo = serializers.ImageField(required=False, allow_null=True)
    phonenumber = serializers.CharField(source='profile.user.phonenumber', read_only=True)

    address = SellerAddressSerializer(read_only=True)
    payment = SellerPaymentSerializer(read_only=True)
    verification = SellerVerificationSerializer(read_only=True)   
    class Meta:
        model = SellerProfile
        fields = ('id', 'profile', 'store_name','store_logo','store_description', 'phonenumber', 'address', 'payment', 'verification', 'is_verified', 'is_blacklisted', 'created_at')
        read_only_fields = ('id', 'profile', 'created_at')

    def validate_store_logo(self, value):
        if value:
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("Store logo must be less than 5MB")
            if not value.content_type.startswith('image/'):
                raise serializers.ValidationError("Uploaded file is not an image.")        
        return value
    
    def create(self, validated_data):
        profile = self.context['request'].user.profile
        validated_data['profile'] = profile
        return super().create(validated_data)