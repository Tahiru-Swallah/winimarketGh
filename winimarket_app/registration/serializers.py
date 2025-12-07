from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser, Profile, SellerProfile, SellerAddress, SellerPayment, SellerVerification
from django.utils import timezone

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email_or_phonenumber'

    email_or_phonenumber = serializers.CharField()
    password = serializers.CharField(write_only = True)

    def validate(self, attrs):
        email_or_phonenumber = attrs.get('email_or_phonenumber')
        password = attrs.get('password')

        user = None

        try:
            user = CustomUser.objects.get(email=email_or_phonenumber)
        except CustomUser.DoesNotExist:
            try:
                user = CustomUser.objects.get(phonenumber=email_or_phonenumber)
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError('Invalid email or phonenumber')
        
        if not user.check_password(password):
            raise serializers.ValidationError('Invalid credentials')
        
        if not user.is_active:
            raise serializers.ValidationError('User is inactive')
        
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
            raise serializers.ValidationError('Email already exists')
        return value

    def validate_phonenumber(self, value):
        if CustomUser.objects.filter(phonenumber=value).exists():
            raise serializers.ValidationError('Phonenumber already exists')
        return value

    def create(self, validated_data):
        user = CustomUser(
            email = validated_data['email'],
            phonenumber = validated_data['phonenumber'],
        )

        user.set_password(validated_data['password'])
        user.save()

        return user
    
class ProfileSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    class Meta:
        model = Profile
        fields = ('id', 'user', 'role', 'full_name', 'profile_picture', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')

    def validate_profile_picture(self, value):
        if value:
            if value.size > 2 * 1024 * 1024:
                raise serializers.ValidationError("Store logo must be less than 2MB")
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
        fields = "__all__"
        read_only_fields = ('id', 'seller')


class SellerPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerPayment
        fields = "__all__"
        read_only_fields = ('id', 'seller')


class SellerVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerVerification
        fields = "__all__"
        read_only_fields = ('id', 'seller', 'status')

    
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
            if value.size > 2 * 1024 * 1024:
                raise serializers.ValidationError("Store logo must be less than 2MB")
            if not value.content_type.startswith('image/'):
                raise serializers.ValidationError("Uploaded file is not an image.")        
        return value
    
    def create(self, validated_data):
        profile = self.context['request'].user.profile
        validated_data['profile'] = profile
        return super().create(validated_data)