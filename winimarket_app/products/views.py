from django.shortcuts import render, get_object_or_404
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
from rest_framework.pagination import PageNumberPagination

from .models import Product, Category, ProductImage, WishList
from .serializers import (CategorySerializer, ProductSerializer,ProductImageSerializer, ProductImageBulkUploadSerializer,WishListSerializer)

# -----------------------------
# TEMPLATE RENDERING

def product_list_view(request):
    return render(request, 'products/index.html')

# -----------------------------
# Category Create, List View

@api_view(['GET'])
@parser_classes([MultiPartParser, FormParser])
def category_list_create(request):
    categories = Category.objects.all()
    serializers = CategorySerializer(categories, many=True, context={'request': request})

    return Response(serializers.data, status=status.HTTP_200_OK)
    
# PAGINATION
class ProductPagination(PageNumberPagination):
    page_size = 10  # Default number of products per page
    page_size_query_param = 'page_size'  # Allow client to set custom size
    max_page_size = 50  # Prevent too-large responses
    
# -------------------------
# LIST + CREATE PRODUCTS
# -------------------------
@api_view(['GET', 'POST'])
@parser_classes([MultiPartParser, FormParser])
def product_list_create(request):
    if request.method == 'GET':
        products = Product.objects.select_related('category', 'seller').prefetch_related('images').all()

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

        paginator = ProductPagination()
        page = paginator.paginate_queryset(products, request)

        serializer = ProductSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    elif request.method == 'POST':
        if not request.user.is_authenticated:
            return Response(
                {
                    'error': 'User must be authenticated'
                }, status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not request.user.profile.role != 'seller' and not request.user.is_staff:
            return Response(
                {
                    "error": "Only sellers or Admins can create products."
                },
                status=status.HTTP_403_FORBIDDEN    
            )

        serializer = ProductSerializer(
            data=request.data,
            context={'request': request}
        )

        serializer.is_valid(raise_exception=True)
        serializer.save(seller=request.user.profile.seller_profile)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def search_products(request):
    search_query = request.query_params.get('q', None)
    products = Product.objects.all()

    if search_query:
        products = products.filter(
         Q(name__icontains = search_query) | Q(description__icontains = search_query)   
        )

    paginator = ProductPagination()
    page = paginator.paginate_queryset(products, request)
    serializer = ProductSerializer(page, many=True, context = {'request': request})

    return paginator.get_paginated_response(serializer.data)

@api_view(['GET'])
def search_suggestions(request):
    search_query = request.query_params.get('q', None)

    if not search_query:
        return Response([])
    
    products = Product.objects.filter(
        Q(name__icontains = search_query) | Q(description__icontains=search_query)
    ).values('id', 'name')[:8]

    suggestions = [{
        'id': p['id'],
        'name': p['name'],
    } for p in products]
    
    return Response(suggestions)

# -------------------------
# RETRIEVE + UPDATE + DELETE PRODUCT
# -------------------------
@api_view(['GET', 'PUT', 'DELETE'])
@parser_classes([MultiPartParser, FormParser])
def product_detail_update_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)

    # ------------------ GET ------------------
    if request.method == 'GET':
        serializer = ProductSerializer(product, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    if not request.user.is_authenticated:
            return Response({'error': "Not authorized to update this product."}, status=status.HTTP_403_FORBIDDEN)
        
    if product.seller.profile.user != request.user and not request.user.is_staff:
        return Response({"error": "Not authorized to update this product."}, status=status.HTTP_403_FORBIDDEN)

    # ------------------ PUT ------------------
    if request.method == 'PUT':
        serializer = ProductSerializer(
            product,
            data=request.data,
            partial=True,
            context={'request': request}
        )

        serializer.is_valid()(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    # ------------------ DELETE ------------------
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
        
        wishlist_item, created = WishList.objects.get_or_create(
            buyer=request.user.profile,
            products = product
        )

        if not created:
            wishlist_item.delete()
            return Response({'message': 'Product removed from wish list', 'is_favorited': False}, status=status.HTTP_200_OK)
        
        serializer = WishListSerializer(data={}, context={'product': product, 'buyer': request.user.profile})
        if serializer.is_valid():
            serializer.save()
            product_serialzer = ProductSerializer(product, context={'request': request})
            data = product_serialzer.data
            data['is_favorited'] = True
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # List Wishlist
    elif request.method == 'GET':
        wishlist = (WishList.objects.filter(buyer=request.user.profile).select_related('products__category', 'products__seller').prefetch_related('products__images'))
        serializer = WishListSerializer(wishlist, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # Delete from Wishlist
    elif request.method == 'DELETE':
        try:
            wishlist_item = WishList.objects.get(buyer=request.user.profile, products__id=product_id)
            wishlist_item.delete()
            return Response({"message": "Product removed from wishlist.", 'is_favorited': False}, status=status.HTTP_204_NO_CONTENT)
        except WishList.DoesNotExist:
            return Response({"error": "Wishlist item not found."}, status=status.HTTP_404_NOT_FOUND)
