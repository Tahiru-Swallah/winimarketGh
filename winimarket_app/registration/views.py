from django.shortcuts import render
from django.contrib.auth.decorators import login_required 
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

# REST FRAMEWORK LIBRARIES
from rest_framework.views import APIView
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser
from .serializers import CustomTokenObtainPairSerializer, RegisterSerializer

#TEMPLATE FOR CONSUMING THE ABOVE APIs
@login_required
def home(request):
    return render(request, 'home.html')

def login_view(request):
    return render(request, 'authentication/login.html')

def register_view(request):
    return render(request, 'authentication/register.html')

# API CODES FOR REGISTRATION AND LOGIN
class CustomTokenObtainPairView(TokenObtainPairView):
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
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
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