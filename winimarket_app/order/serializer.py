from rest_framework import serializers
from .models import Order, OrderItem
from products.serializers import ProductSerializer
from registration.serializers import ProfileSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'quantity', 'price'
        ]

class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    buyer = ProfileSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "buyer", "address", "postal_code", "city",
            "items", "status", 'total_price', 'cancelled_at', 'payment_reference', 'paid_at', "created_at", "updated_at"
        ]
        read_only = ['cancelled_at']