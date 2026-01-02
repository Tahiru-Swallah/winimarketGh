from django.shortcuts import render, get_object_or_404
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
from .models import CustomUser, Profile, SellerProfile, SellerAddress, SellerPayment, SellerVerification, EmailVerification
from .serializers import CustomTokenObtainPairSerializer, RegisterSerializer, ProfileSerializer, SellerProfileSerializer, SellerVerificationSerializer, SellerAddressSerializer, SellerPaymentSerializer
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from django.utils import timezone
from .utils import generate_verification_token, regenerate_verification_token
from .emails import send_verification_email

from order.models import OrderStatus, OrderItem, Order, OrderTrackingStatus
from products.models import Product
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

@login_required
def seller_onboarding(request):
    # Render the seller onboarding page
    return render(request, 'authentication/onboarding.html')

@login_required
def seller_dashboard(request):
    # Render the seller dashboard page
    return render(request, 'seller/dashboard.html')

@login_required
def seller_profile(request, seller_id):
    seller = get_object_or_404(SellerProfile, id=seller_id)
    products = Product.objects.filter(seller=seller,is_active=True).select_related('category').order_by('-created_at')[:12]
    total_products = products.count()
    completed_orders = Order.objects.filter(seller=seller, status=OrderStatus.COMPLETED).count()

    return render(request, 'seller/seller_profile.html', context={"seller": seller, "products": products, "total_products": total_products, "completed_orders": completed_orders})

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
    
    elif request.method == "PUT":
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
    
    # Prevent changing role after confirmation
    if profile.role_confirmed:
        return Response(
            {'error': 'Role has already been set and cannot be changed.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    profile.role = role
    profile.role_confirmed = True
    profile.save()

    return Response({'message': f'Role updated to {profile.role} successfully.'}, status=status.HTTP_200_OK)

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
    
    """ if not user.email_verified:
        return Response({"detail": "Verify your email address before setting store info."}, status=status.HTTP_403_FORBIDDEN) """
    
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
    
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def seller_address_view(request):
    """
    Update SellerAddress. Requires store info completed (store_name must exist).
    """

    profile = request.user.profile

    if profile.role != 'seller':
        return Response({"detail": "You must set your role to seller first."}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        seller = profile.seller_profile
    except SellerProfile.DoesNotExist:
        return Response({"detail": "Seller profile not found. Complete store info first."}, status=status.HTTP_404_NOT_FOUND)
    
    if not seller.store_name:
        return Response({"detail": "Complete store info first."}, status=status.HTTP_400_BAD_REQUEST)
    
    """ if not request.user.email_verified:
        return Response({"detail": "Verify your email address before setting address info."}, status=status.HTTP_403_FORBIDDEN) """
    
    address, _ = SellerAddress.objects.get_or_create(seller=seller)
    serializer = SellerAddressSerializer(address, data=request.data, context={'request': request}, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def seller_payment_view(request):
    """
    Update SellerPayment. Requires store info and address completed.
    """

    profile = request.user.profile

    if profile.role != 'seller':
        return Response({"detail": "You must set your role to seller first."}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        seller = profile.seller_profile
    except SellerProfile.DoesNotExist:
        return Response({"detail": "Seller profile not found. Complete store info first."}, status=status.HTTP_404_NOT_FOUND)
    
    address = getattr(seller, 'address', None)

    if not address or not address.city or not address.region:
        return Response({"detail": "Complete address info first."}, status=status.HTTP_400_BAD_REQUEST)
    
    """ if not request.user.email_verified:
        return Response({"detail": "Verify your email address before setting payment info."}, status=status.HTTP_403_FORBIDDEN) """
    
    try:
        address = seller.address
    except SellerAddress.DoesNotExist:
        return Response({"detail": "Seller address not found. Complete address info first."}, status=status.HTTP_404_NOT_FOUND)
    
    payment, _ = SellerPayment.objects.get_or_create(seller=seller)
    serializer = SellerPaymentSerializer(payment, data=request.data, context={'request': request}, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
     
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def seller_verification_view(request):
    """
    Upload verification documents. Requires payment information set.
    Creates SellerVerification (status pending).
    """

    profile = request.user.profile

    if profile.role != 'seller':
        return Response({"detail": "You must set your role to seller first."}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        seller = profile.seller_profile
    except SellerProfile.DoesNotExist:
        return Response({"detail": "Seller profile not found. Complete store info first."}, status=status.HTTP_404_NOT_FOUND)
    
    payment = getattr(seller, 'payment', None)

    if not payment or (not payment.momo_number and not payment.bank_account):
        return Response({"detail": "Complete payment info first."}, status=status.HTTP_400_BAD_REQUEST)
    
    """ if not request.user.email_verified:
        return Response({"detail": "Verify your email address before submitting verification."}, status=status.HTTP_403_FORBIDDEN) """
    
    verification, _ = SellerVerification.objects.get_or_create(seller=seller)
    serializer = SellerVerificationSerializer(verification, data=request.data, context={'request': request}, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({"detail": "Verification Submitted. Await admin review."}, status=status.HTTP_201_CREATED)
    
    print(serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# -----------------------
# Admin endpoints
# -----------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_approve_verification(request, seller_id):
    """
    Admin endpoint to approve or reject a seller verification.
    Payload: {"action": "approve" | "reject", "note": "optional note"}
    """
    action = request.data.get('action')
    note = request.data.get('note', '')

    try:
        seller = SellerProfile.objects.get(id=seller_id)
    except SellerProfile.DoesNotExist:
        return Response({"detail": "Seller not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        verification = seller.verification
    except SellerVerification.DoesNotExist:
        return Response({"detail": "Verification record not found."}, status=status.HTTP_404_NOT_FOUND)

    if action == 'approve':
        verification.status = 'approved'
        verification.note = note
        verification.reviewed_at = timezone.now()
        verification.save()
        # mark seller as verified
        seller.is_verified = True
        seller.save()
        return Response({"detail": "Seller verified and approved."}, status=status.HTTP_200_OK)

    if action == 'reject':
        verification.status = 'rejected'
        verification.note = note
        verification.reviewed_at = timezone.now()
        verification.save()
        seller.is_verified = False
        seller.save()
        return Response({"detail": "Seller verification rejected."}, status=status.HTTP_200_OK)

    return Response({"detail": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def verify_email(request, token):
    try:
        verification = EmailVerification.objects.get(token=token)
    except EmailVerification.DoesNotExist:
        return Response({"detail": "Invalid verification link."}, status=status.HTTP_400_BAD_REQUEST)

    if verification.is_verified:
        return Response({"detail": "Email already verified."}, status=status.HTTP_200_OK)
    
    if verification.is_expired():
        return Response({"detail": "Verification link has expired."}, status=status.HTTP_400_BAD_REQUEST)
    
    verification.mark_verified()
    
    user = verification.user
    user.email_verified = True
    user.save(update_fields=['email_verified'])
    return Response({"detail": "Email verified successfully."}, status=status.HTTP_200_OK)

RESEND_COOLDOWN_MINUTES = 5

@api_view(['POST'])
def resend_verification_email(request):
    user = request.user

    if user.email_verified:
        return Response({"detail": "Email already verified."}, status=status.HTTP_200_OK)
    
    verification = EmailVerification.objects.get(user=user)

    if verification.created_at > timezone.now() - timezone.timedelta(minutes=RESEND_COOLDOWN_MINUTES):
        return Response({"detail": f"Please wait before requesting another verification email."}, status=status.HTTP_429_TOO_MANY_REQUESTS)
    
    if verification.is_expired():
        verification = regenerate_verification_token(verification)

    send_verification_email(user, verification.token)

    return Response({"detail": "Verification email resent."}, status=status.HTTP_200_OK)