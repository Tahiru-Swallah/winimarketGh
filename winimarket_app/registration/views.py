from django.shortcuts import render
from django.contrib.auth.decorators import login_required 
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils.decorators import method_decorator

# REST FRAMEWORK LIBRARIES
from rest_framework.views import APIView
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser, Profile, SellerProfile
from .serializers import CustomTokenObtainPairSerializer, RegisterSerializer, ProfileSerializer, SellerProfileSerializer

# -----------------------------
# Template Views
# -----------------------------

@login_required
def home(request):
    # Render the home page for logged-in users
    return render(request, 'home.html')

def login_view(request):
    # Render the login page
    return render(request, 'authentication/login.html')

def register_view(request):
    # Render the registration page
    return render(request, 'authentication/register.html')

@login_required
def change_password_view(request):
    # Render the change password page for logged-in users
    return render(request, 'authentication/change_password.html')

@login_required
def profile_template(request):
    # Render the profile onboarding page for logged-in users
    return render(request, 'authentication/profile.html')

# -----------------------------
# API Views for Authentication
# -----------------------------

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT login view using email or phone number.
    """
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        next_url = request.GET.get('next', '/')
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        data = serializer.validated_data
        data['next'] = next_url
        response = Response(data, status=status.HTTP_200_OK)
        response.set_cookie(
            'access_token',
            data.get("access_token"),
            httponly=True,
            secure=False, # Set to True if you're using HTTPS
            max_age=3600, 
            samesite='Lax'
        )

        return response

@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@csrf_exempt   
def registration(request):
    """
    User registration endpoint.
    """
    next_url = request.GET.get('next', '/')
    serializer = RegisterSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        response = Response(
            {
                'message': 'User Login successfully',
                'refresh_token': str(refresh),
                'access_token': access_token,
                'user': RegisterSerializer(instance=user).data,
                'next': next_url
            }, 
            status=status.HTTP_200_OK
        )

        response.set_cookie(
            'access_token',
            access_token,
            httponly=True,
            secure=False, # Set to True if you're using HTTPS
            samesite='Lax'
        )

        return response
    
    return Response({'errors' : serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout endpoint: Blacklists refresh token and deletes access token cookie.
    """
    refresh_token = request.data.get('refresh_token')

    if refresh_token:
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    response = Response({"message": 'Logout Successful'}, status=status.HTTP_200_OK)
    response.delete_cookie('access_token')

    return response

@method_decorator(csrf_exempt, name='dispatch')
class ChangePasswordView(APIView):
    """
    An endpoint for changing password.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not user.check_password(current_password):
            return Response({'detail': 'Current password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({'detail': 'Password updated successfully.'}, status=status.HTTP_200_OK)

# -----------------------------
# Profile API Views
# -----------------------------

@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def profile_view(request):
    """
    GET: Retrieve user profile.
    POST: Create user profile (rarely needed, profile is auto-created).
    PUT: Update user profile.
    """
    user = request.user
    if request.method == 'GET':
        serializer = ProfileSerializer(user.profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = ProfileSerializer(data=request.data, context = {'request': request})
        if serializer.is_valid():
            profile = serializer.save(user=user)
            return Response(ProfileSerializer(profile).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        serializer = ProfileSerializer(user.profile, data=request.data, context={'request': request}, partial=True)
        if serializer.is_valid():
            profile = serializer.save()
            return Response(ProfileSerializer(profile).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# -----------------------------
# Seller Profile API Views
# -----------------------------

@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def seller_profile_view(request):
    """
    GET: Retrieve seller profile.
    POST: Create seller profile (only if not already exists and user is a seller).
    PUT: Update seller profile.
    """
    user = request.user
    if request.method == 'GET':
        try:
            serializer = SellerProfileSerializer(user.profile.seller_profile)
        except SellerProfile.DoesNotExist:
            return Response({'detail': 'Seller profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            return Response({'detail': 'Profile not found.'}, status=status.HTTP_400_BAD_REQUEST)
        # Prevent duplicate seller profiles
        if hasattr(profile, 'seller_profile'):
            return Response({'detail': 'Seller profile already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = SellerProfileSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            profile = serializer.save(profile=user.profile)
            return Response(SellerProfileSerializer(profile).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        try:
            seller_profile = user.profile.seller_profile
        except SellerProfile.DoesNotExist:
            return Response({'detail': 'Seller profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = SellerProfileSerializer(seller_profile, data=request.data, context={'request': request}, partial=True)
        if serializer.is_valid():
            profile = serializer.save()
            return Response(SellerProfileSerializer(profile).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)