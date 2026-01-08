from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required 
from django.views.decorators.csrf import csrf_exempt

# REST FRAMEWORK LIBRARIES
from rest_framework.views import APIView
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Order, OrderItem, OrderStatus, OrderTrackingStatus, ShippingAddress
from .serializer import OrderSerializer, OrderItemSerializer, ShippingAddressSerializer
from cart.models import Cart, CartItem
from products.models import Product

from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.db import transaction

from order.models import OrderEmailLog
from order.constants.email_event import OrderEmailEvent
from order.emails.dispatcher import OrderEmailDispatcher

@login_required
def checkout_page(request):
    return render(request, 'order/checkout.html')

@login_required
def orders_page(request):
    return render(request, 'order/orders.html')

@login_required
def order_detail_page(request, order_id):
    order = get_object_or_404(Order, id=order_id, buyer=request.user.profile)
    return render(request, 'order/order-detail.html', context={'order': order})

@login_required
def seller_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, seller=request.user.profile.seller_profile)
    return render(request, 'order/order-detail-seller.html', context={'order': order})

@login_required
def payment_verify_template(request):
    return render(request, 'order/verify_payment.html')

# ---------------------------
# CREATE ORDER VIEW
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def checkout(request):
    buyer = request.user.profile
    shipping_address_id = request.data.get('shipping_address_id')


    if not shipping_address_id:
        return Response({'error': 'Shipping address is required.'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        address = ShippingAddress.objects.get(buyer=buyer, id=shipping_address_id)
    except ShippingAddress.DoesNotExist:
        return Response({'error': 'Invalid shipping address.'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        cart = Cart.objects.get(buyer=buyer)
    except Cart.DoesNotExist:
        return Response({'error': 'Cart not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    cart_items = CartItem.objects.select_related('product', 'product__seller').filter(cart=cart)
    
    if not cart_items.exists():
        return Response({'error': 'Cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)
    
    seller_groups = {}
    for item in cart.items.all():
        product = item.product
        seller = product.seller
        seller_groups.setdefault(seller, []).append(item)

    created_orders = []

    with transaction.atomic():
        for seller, items in seller_groups.items():
            order = Order.objects.create(
                buyer=buyer,
                seller=seller,
                shipping_address=address,
            )

            for item in items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )

            created_orders.append(order)

    serializer = OrderSerializer(created_orders, many=True, context={'request': request})

    return Response(
        {
            "message": "Order(s) created successfully.",
            "orders": serializer.data
        },
        status=status.HTTP_201_CREATED
    )

# ---------------------------
# ORDER DETAIL VIEW - BUYER
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_orders(request):
    buyer = request.user.profile
    orders = Order.objects.filter(buyer=buyer).prefetch_related('items__product__images', 'shipping_address', 'seller')

    serializer = OrderSerializer(orders, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_detail(request, order_id):
    try:
        order = Order.objects.get(id=order_id, buyer=request.user.profile)
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = OrderSerializer(order, context={"request": request})
    return Response(serializer.data, status=status.HTTP_200_OK)

# ---------------------------
# ORDER DETAIL VIEW - SELLER
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def seller_orders(request):
    seller = request.user.profile.seller_profile
    orders = (Order.objects.filter(seller=seller).prefetch_related('items__product__images', 'shipping_address', 'buyer__user').order_by('-created_at'))

    serializer = OrderSerializer(orders, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def seller_order_detail_api(request, order_id):
    seller = request.user.profile.seller_profile

    try:
        order = Order.objects.select_related(
            'buyer__user', 'shipping_address'
        ).prefetch_related('items__product').get(
            id=order_id, seller=seller
        )
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=404)

    serializer = OrderSerializer(order, context={'request': request})
    return Response(serializer.data)

# ---------------------------
# ORDER UPDATE VIEW - SELLER
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_order_status(request, order_id):
    seller = request.user.profile.seller_profile
    status_value = request.data.get('status')

    try:
        order = Order.objects.get(id=order_id, seller=seller)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    allowed = ['processing', 'shipped', 'delivered']
    if status_value not in allowed:
        return Response({'error': 'Invalid status value.'}, status=status.HTTP_400_BAD_REQUEST)
    
    order.track_status = status_value

    flow_rank = {
        'processing': 1,
        'shipped': 2,
        'delivered': 3
    }

    if flow_rank[status_value] < flow_rank[order.track_status]:
        return Response({'error': 'Cannot move order backward'}, status=status.HTTP_400_BAD_REQUEST)

    if status_value == "shipped":
        order.status = OrderStatus.SHIPPED
    elif status_value == "delivered":
        order.status = OrderStatus.DELIVERED

        OrderEmailDispatcher.dispatcher(
            order=order,
            event=OrderEmailEvent.ORDER_DELIVERED
        )

    order.save()

    serializer = OrderSerializer(order, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)

# ---------------------------
# ORDER CONFIRM VIEW - BUYER
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_delivery(request, order_id):
    buyer = request.user.profile

    try:
        order = Order.objects.get(id=order_id, buyer=buyer)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    if order.track_status != OrderTrackingStatus.DELIVERED:
        return Response({'error': 'Order has not been marked as delivered yet.'}, status=status.HTTP_400_BAD_REQUEST)
    
    if order.is_escrow_released:
        return Response({'error': 'Escrow has already been released for this order.'}, status=status.HTTP_400_BAD_REQUEST)
    
    order.status = OrderStatus.COMPLETED
    order.track_status = OrderStatus.COMPLETED
    order.is_escrow_released = True
    order.escrow_released_at = timezone.now()

    OrderEmailDispatcher.dispatcher(
        order=order,
        event=OrderEmailEvent.ORDER_COMPLETED
    )

    order.save()

    serializer = OrderSerializer(order, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)

# ---------------------------
# SHIPPING ADDRESS VIEWS

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_shipping_address(request):
    serializer = ShippingAddressSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(buyer=request.user.profile)  # link address to the logged-in user
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_shipping_addresses(request):
    addresses = ShippingAddress.objects.filter(buyer=request.user.profile)
    serializer = ShippingAddressSerializer(addresses, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_shipping_address(request, pk):
    try:
        address = ShippingAddress.objects.get(pk=pk, buyer=request.user.profile)
    except ShippingAddress.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = ShippingAddressSerializer(address, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_shipping_address(request, pk):
    try:
        address = ShippingAddress.objects.get(pk=pk, buyer=request.user.profile)
    except ShippingAddress.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    address.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)