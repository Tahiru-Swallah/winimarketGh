from rest_framework import serializers
from .models import Cart, CartItem
from products.serializers import ProductSerializer
from registration.serializers import ProfileSerializer

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    subtotal = serializers.IntegerField(read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'choice_price', 'subtotal']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    buyer = ProfileSerializer(read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'buyer', 'created_at', 'items', 'total_items', 'total_price']
        read_only_fields = ['id', 'buyer', 'created_at']  # Ensure these fields are read-only

    def create(self, validated_data):
        buyer = self.context['request'].user.profile
        validated_data['buyer'] = buyer
        return super().create(validated_data)
