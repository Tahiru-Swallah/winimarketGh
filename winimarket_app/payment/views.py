from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required 
from django.views.decorators.csrf import csrf_exempt

# REST FRAMEWORK LIBRARIES
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated

from django.utils import timezone
from datetime import timedelta

from order.models import Order, Payment, OrderStatus, PaymentStatus

import requests
import hashlib
from django.conf import settings
from decimal import Decimal
from cart.models import Cart, CartItem

from order.emails.dispatcher import OrderEmailDispatcher
from order.constants.email_event import OrderEmailEvent


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initialize_payment(request):
    buyer = request.user.profile
    order_ids = request.data.get('order_ids', [])

    print(order_ids)

    if not order_ids:
        return Response(
            {'error': 'No orders provided'},
            status=status.HTTP_400_BAD_REQUEST
        )

    orders = Order.objects.filter(
        id__in=order_ids,
        buyer=buyer,
        status=OrderStatus.PENDING
    )

    if not orders.exists():
        return Response(
            {'error': 'No valid pending orders found'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Ensure none are already paid / cancelled
    for order in orders:
        if order.total_cost <= 0:
            return Response(
                {'error': f'Invalid order amount for order {order.id}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    total_amount = sum(order.total_cost for order in orders)
    amount_kobo = int(total_amount * 100)

    reference = f"multi-order-{buyer.id}-{int(timezone.now().timestamp())}"

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_TESTED_SECRET_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "email": request.user.email,
        "amount": amount_kobo,
        "currency": "GHS",
        "channels": ["card", "mobile_money"],
        "reference": reference,
        "callback_url": request.build_absolute_uri('/order/payment/verify/'),
        "metadata": {
            "buyer_id": str(buyer.id),
            "order_ids": [str(o.id) for o in orders],
            "type": "multi_order_checkout",
        }
    }

    try:
        response = requests.post(
            "https://api.paystack.co/transaction/initialize",
            json=payload,
            headers=headers,
            timeout=30
        )
    except requests.RequestException:
        return Response(
            {'error': 'Payment service unavailable'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    if response.status_code != 200:
        return Response(
            {'error': 'Failed to initialize payment'},
            status=status.HTTP_400_BAD_REQUEST
        )

    payment = Payment.objects.create(
        buyer=buyer,
        amount=total_amount,
        reference=reference,
        status=PaymentStatus.PENDING
    )

    payment.orders.set(orders)

    return Response(response.json()['data'], status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_payment(request):
    """
    Verify Paystack payment for multi-order checkout
    """
    order_ids = request.data.get('order_ids', [])
    reference = request.data.get('reference')

    if not order_ids or not reference:
        return Response(
            {'error': 'order_ids and reference are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    buyer = request.user.profile

    # Get payment
    try:
        payment = Payment.objects.select_related('buyer').get(
            reference=reference,
            buyer=buyer
        )
    except Payment.DoesNotExist:
        return Response({'error': 'Payment record not found'}, status=status.HTTP_404_NOT_FOUND)

    if payment.status == PaymentStatus.SUCCESS:
        return Response({
            'message': 'Payment already verified'
        }, status=status.HTTP_200_OK)

    # Verify with Paystack
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_TESTED_SECRET_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(
            f"https://api.paystack.co/transaction/verify/{reference}",
            headers=headers,
            timeout=30
        )
    except requests.RequestException:
        return Response(
            {'error': 'Payment service unavailable'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    if response.status_code != 200:
        return Response({'error': 'Unable to verify payment'}, status=status.HTTP_400_BAD_REQUEST)

    data = response.json().get('data')

    if not data or data.get('status') != 'success':
        return Response({'error': 'Payment not successful'}, status=status.HTTP_400_BAD_REQUEST)

    paid_amount = Decimal(data['amount']) / 100

    if paid_amount != payment.amount:
        return Response({'error': 'Payment amount mismatch'}, status=status.HTTP_400_BAD_REQUEST)

    # ✅ Mark payment successful
    payment.status = PaymentStatus.SUCCESS
    payment.paid_at = timezone.now()
    payment.save()

    # ✅ Update all orders
    orders = Order.objects.filter(
        id__in=order_ids,
        buyer=buyer
    )

    verified_orders = []

    for order in orders:
        order.status = OrderStatus.PAID
        order.paid_at = timezone.now()
        order.save()
        verified_orders.append(str(order.id))

        OrderEmailDispatcher.dispatcher(
            order=order,
            event=OrderEmailEvent.ORDER_PAID
        )

    try:
        cart = Cart.objects.get(buyer=buyer)
    except Cart.DoesNotExist:
        return Response({'error': 'Cart not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    cart_items = CartItem.objects.select_related('product', 'product__seller').filter(cart=cart)
    
    cart_items.delete()
    
    return Response({
        'message': 'Payment verified successfully',
        'orders': verified_orders
    }, status=status.HTTP_200_OK)



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