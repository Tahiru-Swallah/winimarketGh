from django.shortcuts import render
from django.contrib.auth.decorators import login_required 
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils.decorators import method_decorator

# REST FRAMEWORK LIBRARIES
from rest_framework.views import APIView
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes
from django.views.decorators.csrf import csrf_protect
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import CustomUser, Profile, SellerProfile
from .serializers import CustomTokenObtainPairSerializer, RegisterSerializer, ProfileSerializer, SellerProfileSerializer
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from django.utils import timezone

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

# -----------------------------
# API Views for Authentication
# -----------------------------
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        next_url = request.GET.get('next', '/')
        serializer = self.get_serializer(data=request.data)
        
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        data['next'] = next_url

        response = Response(data, status=status.HTTP_200_OK)

        response.set_cookie(
            'access_token',
            data.get("access_token"),
            httponly=True,
            secure=settings.SECURE_COOKIE, # Set to True if you're using HTTPS
            max_age=3600, 
            samesite='Lax'
        )

        # Set refresh token cookie
        response.set_cookie(
            "refresh_token",
            data.get("refresh_token"),
            httponly=True,
            secure=settings.SECURE_COOKIE,   # 🔐 change to True in production
            samesite="Lax",
            max_age=7 * 24 * 3600,  # 7 days
        )

        return response

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_protect
def registration(request):
    next_url = request.GET.get('next', '/')
    serializer = RegisterSerializer(data=request.data)

    print(request.data)

    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        response = Response(
            {
                'message': 'User registered successfully',
                'refresh_token': str(refresh),
                'access_token': access_token,
                'user': RegisterSerializer(instance=user).data,
                'next': next_url
            }, 
            status=status.HTTP_201_CREATED
        )

        response.set_cookie(
            'access_token',
            access_token,
            httponly=True,
            secure=settings.SECURE_COOKIE, # Set to True if you're using HTTPS
            samesite='Lax'
        )

        # Refresh token cookie
        response.set_cookie(
            'refresh_token',
            str(refresh),
            httponly=True,
            secure=settings.SECURE_COOKIE,  # ⚠️ True in production
            samesite='Lax',
            max_age=7 * 24 * 3600,  # 7 days
        )

        return response
    
    return Response({'errors' : serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_protect, name='dispatch')
class logOutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        tokens = OutstandingToken.objects.filter(user=request.user)

        for token in tokens:
            BlacklistedToken.objects.get_or_create(token=token)

        response = Response({
            'detail': 'Successful log out.'
        }, status=status.HTTP_200_OK)

        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')

        request.user.last_logout = timezone.now()
        request.user.save(update_fields=['last_logout'])
        
        return response

@method_decorator(csrf_protect, name='dispatch')
class ChangePasswordView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not user.check_password(current_password):
            return Response({
                'success': False, 'message': 'Current password is incorrect.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response({
                'success': False, 'message': e.messages
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(new_password)
        user.save()

        response = Response({
            'success': True, 'message': 'Password changed successfully. Please login again'
        }, status=status.HTTP_200_OK)

        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')

        return response

# -----------------------------
# Profile API Views
# -----------------------------
@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def profile_view(request):
    """
    GET: Retrieve user profile.
    PUT: Update user profile.
    """
    user = request.user

    if request.method == 'GET':
        serializer = ProfileSerializer(user.profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    serializer = ProfileSerializer(user.profile, data=request.data, context={'request': request}, partial=True)
    if serializer.is_valid():
        profile = serializer.save()
        return Response(ProfileSerializer(profile).data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# -----------------------------
# Role Selection API View
# -----------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_role(request):
    user = request.user
    profile = user.profile

    role = request.data.get('role')

    if role not in ['buyer', 'seller']:
        return Response({'error': 'Invalid role, choose buyer or seller.'}, status=status.HTTP_400_BAD_REQUEST)
    
    if profile.role == "seller":
        # Prevent downgrading from seller to buyer
        return Response({'error': 'Role already set to seller cannot be changed again.'}, status=status.HTTP_400_BAD_REQUEST)
    
    if role == 'seller':
        profile.role = 'seller'
        profile.save()
        # Create an empty SellerProfile for the user
        return Response({'message': 'Role set to seller successfully.'}, status=status.HTTP_200_OK)
    
    profile.role = "buyer"
    profile.save()

    return Response({'message': f'Role updated to buyer successfully.'}, status=status.HTTP_200_OK)

# -----------------------
# Seller onboarding
# Sequential: store -> address -> payment -> verification
# -----------------------
@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def seller_store_view(request):
    """
    Create or update the seller store info.
    This is the first onboarding step.
    """
    user = request.user
    profile = user.profile 

    if profile.role != 'seller':
        return Response({"detail": "You must set your role to seller first."}, status=status.HTTP_403_FORBIDDEN)
    
    seller = getattr(profile, 'seller_profile', None)

    if request.method == 'GET':
        if not seller:
            return Response({"detail": "Seller profile not created yet."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = SellerProfileSerializer(seller)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    if request.method in ('POST', 'PUT'):
        if not seller:
            seller = SellerProfile.objects.create(profile=profile , store_name=request.data.get('store_name', ''))
        serializer = SellerProfileSerializer(seller, data=request.data, context={'request': request}, partial=True)
    
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK if request.method == 'PUT' else status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)