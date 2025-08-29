from django.shortcuts import render
from django.contrib.auth.decorators import login_required 
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db.models import Q

# REST FRAMEWORK LIBRARIES
from rest_framework.views import APIView
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Product, Category, ProductImage, WishList
from .serializers import (CategorySerializer, ProductSerializer,ProductImageSerializer, ProductImageBulkUploadSerializer,WishListSerializer)

# -----------------------------
# TEMPLATE RENDERING

@login_required
def product_list_view(request):
    return render(request, 'products/product_list.html')

@login_required
def wishlist_template_view(request):
    return render(request, 'products/wishlist.html')

# -----------------------------
# Category Create, List View

@api_view(['POST', 'GET'])
@parser_classes([MultiPartParser, FormParser])
def category_list_create(request):
    if request.method == 'POST':

        if request.user.is_authenticated:
            return Response(
                {
                    "error": "Only admin users can create categories."
                },
                status=status.HTTP_403_FORBIDDEN    
            )
        
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'GET':
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
# -------------------------
# LIST + CREATE PRODUCTS
# -------------------------
@api_view(['GET', 'POST'])
@parser_classes([MultiPartParser, FormParser])
def product_list_create(request):
    if request.method == 'GET':
        products = Product.objects.all()

        # ----- FILTERING -----
        category_id = request.query_params.get('category_id')
        min_price = request.query_params.get('min_price')
        condition = request.query_params.get('condition')

        if category_id:
            products = products.filter(category__id=category_id)
        if min_price:
            products = products.filter(min_price__gte=min_price)
        if condition:
            products = products.filter(condition=condition)

        serializer = ProductSerializer(products, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        if not request.user.is_authenticated:
            return Response(
                {
                    'error': 'User must be authenticated'
                }, status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not hasattr(request.user, "profile") or (request.user.profile.role != 'seller' and not request.user.is_staff):
            return Response(
                {
                    "error": "Only sellers or Admins can create products."
                },
                status=status.HTTP_403_FORBIDDEN    
            )
        
        category_id = request.data.get('category_id')
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return Response({"error": "Category not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProductSerializer(
            data=request.data,
            context={'category': category, 'request': request}
        )
        if serializer.is_valid():
            serializer.save(seller=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# -------------------------
# RETRIEVE + UPDATE + DELETE PRODUCT
# -------------------------
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def product_detail_update_delete(request, pk):
    try:
        product = Product.objects.get(id=pk)
    except Product.DoesNotExist:
        return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

    # ------------------ GET ------------------
    if request.method == 'GET':
        serializer = ProductSerializer(product, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    # ------------------ PUT ------------------
    elif request.method == 'PUT':
        if product.seller != request.user:
            return Response({"error": "Not authorized to update this product."}, status=status.HTTP_403_FORBIDDEN)

        category_id = request.data.get('category_id')
        category = None
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                return Response({"error": "Category not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProductSerializer(
            product,
            data=request.data,
            partial=True,
            context={'category': category, 'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # ------------------ DELETE ------------------
    elif request.method == 'DELETE':
        if product.seller != request.user:
            return Response({"error": "Not authorized to delete this product."}, status=status.HTTP_403_FORBIDDEN)

        product.delete()
        return Response({"message": "Product deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


# -----------------------------
# WISHLIST CREATE, LIST, DELETE 
@api_view(['POST', 'GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def wishlist_view(request, product_id=None):
    #Add to Wishlist
    if request.method == 'POST':
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = WishListSerializer(data={}, context={'product': product, 'buyer': request.user.profile})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # List Wishlist
    elif request.method == 'GET':
        wishlist = WishList.objects.filter(buyer=request.user.profile)
        serializer = WishListSerializer(wishlist, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # Delete from Wishlist
    elif request.method == 'DELETE':
        try:
            wishlist_item = WishList.objects.get(buyer=request.user.profile, products__id=product_id)
            wishlist_item.delete()
            return Response({"message": "Product removed from wishlist."}, status=status.HTTP_204_NO_CONTENT)
        except WishList.DoesNotExist:
            return Response({"error": "Wishlist item not found."}, status=status.HTTP_404_NOT_FOUND)
