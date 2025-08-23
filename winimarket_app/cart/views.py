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

@login_required
def cart_view(request):
    return render(request, 'cart/cart_view.html')

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_cart(request):
    try:
        cart= Cart.objects.get(buyer=request.user.profile)
    except Cart.DoesNotExist:
        return Response({"item": [], 'total': 0}, status=status.HTTP_404_NOT_FOUND)

    cart_items = CartItem.objects.filter(cart=cart)
    serializer = CartItemSerializer(cart_items, many=True, context={'request': request})

    total_price = sum([item.choice_price * item.quantity for item in cart_items])

    return Response({
        "items": serializer.data,
        "total": total_price
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    product_id = request.data.get('product_id')
    quantity = int(request.data.get('quantity', 1))
    choice_price = request.data.get('choice_price')

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
    
    if not choice_price:
        choice_price = product.min_price
    else:
        try:
            choice_price = Decimal(choice_price)
        except:
            return Response({"error": "Invalid choice price"}, status=status.HTTP_400_BAD_REQUEST)
        
    cart, _ = Cart.objects.get_or_create(buyer=request.user.profile)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': quantity, 'choice_price': choice_price})

    if not created:
        cart_item.quantity += quantity
        cart_item.choice_price = choice_price
        cart_item.save()

    serializer = CartItemSerializer(cart_item, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_cart_item(request, product_id):
    try:
        cart_item = CartItem.objects.get(id=product_id, cart__buyer=request.user.profile)
    except CartItem.DoesNotExist:
        return Response({"error": "Cart item not found"}, status=status.HTTP_404_NOT_FOUND)
    
    quantity = request.data.get('quantity')
    if quantity is None:
        return Response({"error": "Quantity is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        quantity = int(quantity)
    except ValueError:
        return Response({"error": "Invalid quantity"}, status=status.HTTP_400_BAD_REQUEST)
    
    if quantity <= 0:
        cart_item.delete()
        return Response({"message": "Cart item removed"}, status=status.HTTP_204_NO_CONTENT)
    
    cart_item.quantity = quantity
    cart_item.save()

    serializer = CartItemSerializer(cart_item, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_cart(request, product_id):
    cart= Cart.objects.get(buyer=request.user.profile)
    try:
        cart_item = CartItem.objects.get(id=product_id, cart=cart)
        cart_item.delete()
    except CartItem.DoesNotExist:
        return Response({"error": "Cart item not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = CartSerializer(cart, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)