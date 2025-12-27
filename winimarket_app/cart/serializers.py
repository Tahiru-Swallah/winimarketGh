from rest_framework import serializers
from .models import Cart, CartItem
from products.serializers import ProductSerializer
from registration.serializers import ProfileSerializer
from products.models import Product

class CartProductMiniSerializer(serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()
    seller_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'seller_name', 'primary_image', 'price', 'is_active']

    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).first()

        if primary and primary.image:
            request = self.context.get('request')
            return request.build_absolute_uri(primary.image.url) if request else primary.image.url
        return None
    
    def get_seller_name(self, obj):
        if obj.seller:
            return obj.seller.store_name
        return None
    
class CartItemSerializer(serializers.ModelSerializer):
    product = CartProductMiniSerializer(read_only=True)
    subtotal = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'choice_price', 'subtotal', 'added_at']
        read_only_fields = ['choice_price', 'subtotal']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    buyer = ProfileSerializer(read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'buyer', 'status', 'updated_at', 'created_at', 'items', 'total_items', 'total_price']
        read_only_fields = ['id', 'buyer', 'created_at']  # Ensure these fields are read-only

    def create(self, validated_data):
        buyer = self.context['request'].user.profile
        validated_data['buyer'] = buyer
        return super().create(validated_data)
