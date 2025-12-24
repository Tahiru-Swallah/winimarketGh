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

from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
from products.models import Product
from decimal import Decimal
from django.db import transaction

@login_required
def cart_view(request):
    return render(request, 'cart/cart_view.html')

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_cart(request):
    cart, _ = Cart.objects.get_or_create(buyer=request.user.profile, status='active')

    serializers = CartSerializer(cart, context={'request': request})
    return Response(serializers.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    product_id = request.data.get('product_id')
    quantity = int(request.data.get('quantity', 1))
    choice_price = request.data.get('choice_price')

    if quantity <= 0:
        return Response({"error": "Quantity must be greater than 0"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        product = Product.objects.select_for_update().get(id=product_id)
    except Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

    # Stock check (if applicable)
    if product.quantity < quantity:
        return Response({"error": "Not enough stock available"}, status=status.HTTP_400_BAD_REQUEST)

    # Validate choice_price
    try:
        choice_price = Decimal(choice_price) if choice_price else product.price
    except:
        return Response({"error": "Invalid choice price"}, status=status.HTTP_400_BAD_REQUEST)
    
    if not (product.price == choice_price):
        return Response({"error": "Choice price out of allowed range"}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        cart, _ = Cart.objects.get_or_create(buyer=request.user.profile, status='active')

        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': quantity, 'choice_price': choice_price})

        if not created:
            new_quantity = cart_item.quantity + quantity

            if product.quantity < new_quantity:
                return Response({"error": "Not enough stock available"}, status=status.HTTP_400_BAD_REQUEST)
            
            cart_item.quantity = new_quantity
            cart_item.choice_price = choice_price
            cart_item.save(updated_fields=['quantity', 'choice_price'])

        serializers = CartItemSerializer(cart_item, context={'request': request})
        return Response({
            **serializers.data,
            "added": True if created else False
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_cart_item(request, cart_item_id):
    try:
        cart_item = CartItem.objects.select_related('product', 'cart').get(id=cart_item_id, cart__buyer=request.user.profile, status='active')
    except CartItem.DoesNotExist:
        return Response({"error": "Cart item not found"}, status=status.HTTP_404_NOT_FOUND)
    
    quantity = request.data.get('quantity')
    if quantity is None:
        return Response({"error": "Quantity is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        return Response({"error": "Invalid quantity"}, status=status.HTTP_400_BAD_REQUEST)
    
    if quantity < 1:
        return Response({"error": "Quantity must be at least 1"}, status=status.HTTP_400_BAD_REQUEST)
    
    if quantity > cart_item.product.quantity:
        return Response({"error": "Requested quantity exceeds available stock."}, status=status.HTTP_400_BAD_REQUEST)
    
    cart_item.quantity = quantity
    cart_item.save(updated_fields=['quantity'])

    serializer = CartItemSerializer(cart_item, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_cart(request, cart_item_id):
    cart= Cart.objects.get(buyer=request.user.profile, status='active')

    try:
        cart_item = CartItem.objects.get(id=cart_item_id, cart=cart)
    except CartItem.DoesNotExist:
        return Response({"error": "Cart item not found"}, status=status.HTTP_404_NOT_FOUND)
    
    cart_item.delete()

    serializer = CartSerializer(cart, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)