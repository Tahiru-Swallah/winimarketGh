from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser, Profile, SellerProfile, SellerAddress, SellerPayment, SellerVerification
from django.utils import timezone
from django.db import IntegrityError, transaction

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
    
class ProfileSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    class Meta:
        model = Profile
        fields = ('id', 'user', 'role', "role_confirmed", 'full_name', 'profile_picture', 'created_at')
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
    
class SellerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerAddress
        fields = ("id", "region", "city", "country", "address",)
        read_only_fields = ('id',)

    def validate(self, attrs):
        # Basic validation
        if not attrs.get('city'):
            raise serializers.ValidationError({"city": "City is required."})
        if not attrs.get('address'):
            raise serializers.ValidationError({"address": "Address line is required."})
        return attrs
class SellerPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerPayment
        fields = ("id", "bank_name", "bank_account", "momo_name", "momo_number",)
        read_only_fields = ('id',)

    def validate(self, attrs):
        momo = attrs.get('momo_number') or getattr(self.instance, 'momo_number', None)
        bank = attrs.get('bank_account') or getattr(self.instance, 'bank_account', None)

        if not momo and not bank:
            raise serializers.ValidationError("At least one payout method (MoMo or Bank) is required.")
        return attrs

class SellerVerificationSerializer(serializers.ModelSerializer):
    id_card_image = serializers.ImageField(required=True)
    selfie_with_id = serializers.ImageField(required=True)
    class Meta:
        model = SellerVerification
        fields = ("id", "id_type", "id_number", "id_card_image", "selfie_with_id", "status", "note", "submitted_at", "reviewed_at")
        read_only_fields = ('id', 'status', 'note', 'submitted_at', 'reviewed_at')

    def validate_id_card_image(self, value):
        if value:
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("ID image must be less than 5MB")
            if not getattr(value, "content_type", "").startswith('image/'):
                raise serializers.ValidationError("Uploaded file is not an image.")
        return value

    def validate_selfie_with_id(self, value):
        if value:
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("Selfie must be less than 5MB")
            if not getattr(value, "content_type", "").startswith('image/'):
                raise serializers.ValidationError("Uploaded file is not an image.")
        return value

class SellerProfileSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    store_logo = serializers.ImageField(required=False, allow_null=True)

    address = SellerAddressSerializer(read_only=True)
    payment = SellerPaymentSerializer(read_only=True)
    verification = SellerVerificationSerializer(read_only=True)   
    class Meta:
        model = SellerProfile
        fields = ('id', 'profile', 'store_name','store_logo','store_description', 'address', 'payment', 'verification', 'is_verified', 'is_blacklisted', 'created_at')
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