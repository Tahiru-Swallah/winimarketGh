from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
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

from .models import Order, OrderItem
from .serializer import OrderSerializer, OrderItemSerializer, OrderStatusSerializer
from cart.models import Cart

from django.utils import timezone
from datetime import timedelta

import requests
import hashlib
from django.conf import settings

@login_required
def order_template_view(request):
    return render(request, 'order/order_items.html')

@login_required
def payment_success(request):
    return render(request, 'order/payment_success.html')

@login_required
def payment_failed(request):
    return render(request, 'order/payment_failed.html')

@login_required
def verify_payment_page(request, order_id):
    return render(request, 'order/verify_payment.html', {'order_id': order_id})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initialize_payment(request, order_id):
    try:
        order = Order.objects.get(id=order_id, buyer=request.user.profile)
    except Order.DoesNotExist:  
        return Response({'error': 'Order does not exist'}, status=status.HTTP_400_BAD_REQUEST)
    
    amount = int(order.total_price * 100)  # Convert to the smallest currency unit (e.g., cents)
    payment_method = request.data.get('payment_method', 'card')

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_TESTED_SECRET_API_KEY}",
        "Content-Type": "application/json",
    }

    reference = f"order-{order.id}-{int(timezone.now().timestamp())}"

    data = {
        'email': request.user.email,
        'amount': amount,
        "currency": "GHS",
        "channel": ["card", "mobile_money"],
        'metadata': {"payment_method": payment_method},
        "reference": reference,
        "callback_url": request.build_absolute_uri(f'/order/verify_payment/{order.id}/page/'),
    }

    response = requests.post('https://api.paystack.co/transaction/initialize', json=data, headers=headers)
    res_data = response.json()

    if res_data.get('status'):
        order.payment_reference = reference
        order.save()
        return Response({'authorization_url': res_data['data']['authorization_url']}, status=status.HTTP_200_OK)
    return Response({'error': 'Payment initialization failed'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_payment(request, order_id):
    paystack_reference = request.GET.get('reference')
    ajax_request = request.GET.get('X-Requested-With') == 'XMLHttpRequest'

    if paystack_reference is None:
        return Response({'error': 'Reference not provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        order = Order.objects.get(id=order_id, buyer=request.user.profile)
    except Order.DoesNotExist:
        return Response({'error': 'Order does not exists'}, status=status.HTTP_404_NOT_FOUND)
    
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_TESTED_SECRET_API_KEY}",
        "Content-Type": "application/json",
    }

    url = f"https://api.paystack.co/transaction/verify/{paystack_reference}"
    response = requests.get(url, headers=headers)
    response_data = response.json()

    if response_data.get('status') and response_data['data']['status'] == 'success':
        order.status = 'paid'
        order.paid_at = timezone.now()
        order.payment_reference = paystack_reference
        order.save()

        if ajax_request:
            return redirect('order:payment_success')
        else:
            return Response({'message': 'Payment verified successfully'}, status=status.HTTP_200_OK)
    
    if ajax_request:
        return redirect('order:payment_failed')
    else:   
        return Response({'message': 'Payment verified successfully'}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def paystack_webhook(request):
    paystack_signature = request.headers.get('X-Paystack-Signature')
    payload = request.body
    hashed = hashlib.sha512(payload + settings.PAYSTACK_TESTED_SECRET_API_KEY.encode()).hexdigest()

    if hashed != paystack_signature:
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    
    event = request.data

    if event['event'] == 'charge.success':
        reference = event['data']['reference']
        try:
            order = Order.objects.get(payment_reference=reference)
            order.status = 'paid'
            order.paid_at = timezone.now()
            order.save()
        except Order.DoesNotExist:
            return JsonResponse({'error': 'Order not found'}, status=404)
    return JsonResponse({'message': 'Webhook received'}, status=200)

@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, buyer=request.user.profile)
    if order.status == 'pending':
        order.status = 'cancelled'
        order.cancelled_at = timezone.now()
        order.save()
        return JsonResponse(
            {"message": "Order cancelled successfully"}
        )
    return JsonResponse({
        "error": "Cannot cancel paid or shipped order"
    }, status=400)


def check_and_cancel(order):
    expiry_time = order.created_at + timedelta(minutes=30)

    if order.status == "pending" and timezone.now() > expiry_time:
        order.status = 'cancelled'
        order.save()
    return order

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
    buyer = request.user.profile
    cart = Cart.objects.filter(buyer=buyer).first()
    
    print(cart)
    
    if not cart or not cart.items.exists():
        return Response(
            {'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST
        )
    
    address = request.data.get('address')
    postal_code = request.data.get('postal_code')
    city = request.data.get('city')

    if not all([address, postal_code, city]):
        return Response({
            'error': 'Address, Postal Code and City are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    order = Order.objects.create(
        buyer=buyer,
        address=address,
        postal_code=postal_code,
        city=city
    )

    total_price = 0
    for item in cart.items.all():
        price = item.choice_price
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=price,
        )

        total_price += price * item.quantity

    order.total_price = total_price
    order.save()

    cart.items.all().delete()

    serializer = OrderSerializer(order, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_orders(request):
    orders = Order.objects.filter(buyer=request.user.profile)
    order = [check_and_cancel(order) for order in orders]
    serializer = OrderSerializer(order, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_detail(request, order_id):
    try:
        order = Order.objects.get(id=order_id, buyer=request.user.profile)
    except Order.DoesNotExist:
        return Response({'error': 'Order does not exist'}, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = OrderSerializer(order, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)

""" @api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_order(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return Response({
            'error': 'Order does not exist'
        }, status=status.HTTP_404_NOT_FOUND)
    
    order = check_and_cancel(order)

    if order.status == 'cancelled' and not request.user.is_staff:
        return Response({'error': 'Order is already cancelled and cannot be updated.'}, status=status.HTTP_400_BAD_REQUEST)
    
    if not (request.user.is_staff or getattr(request.user.profile, "seller_profile", None) or order.buyer == request.user.profile) :
        return Response({
            'error': 'Not authorized to update order'
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = OrderStatusSerializer(order, data=request.data, context={'request': request}, partial=True)
    if serializer.is_valid():
        serializer.save()

        full_order = OrderSerializer(order, context={'request': request})
        return Response(full_order.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) """