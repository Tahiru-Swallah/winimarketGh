from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from dj_rest_auth.registration.serializers import SocialLoginSerializer
from .models import CustomUser

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
        
        data = super().get_token(user)

        return {
            "refresh_token": str(data),
            "access_token": str(data.access_token),
            "user": {
                "id": str(user.id),
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "phonenumber": str(user.phonenumber),
            },
        }
    
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'phonenumber', 'password')

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
            first_name = validated_data['first_name'],
            last_name = validated_data['last_name'],
            email = validated_data['email'],
            phonenumber = validated_data['phonenumber'],
        )

        user.set_password(validated_data['password'])
        user.save()

        return user