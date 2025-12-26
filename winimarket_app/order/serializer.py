from rest_framework import serializers
from .models import Order, OrderItem, ShippingAddress, OrderStatus, OrderTrackingStatus
from products.models import Product
from registration.serializers import ProfileSerializer as BuyerProfileSerializer
from cart.models import Cart, CartItem

class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = ["id", "address", "state_region", "city", "country", "phonenumber"]


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_image = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product_name",
            "product_image",
            "quantity",
            "price",
            "subtotal",
        ]

    def get_subtotal(self, obj):
        return obj.price * obj.quantity

    def get_product_image(self, obj):
        if obj.product and obj.product.images.exists():
            image = obj.product.images.filter(is_main=True).first()
            return image.image.url if image else obj.product.images.first().image.url
        return None
class OrderSerializer(serializers.ModelSerializer):
    buyer = BuyerProfileSerializer(read_only=True)
    seller = serializers.SerializerMethodField(read_only=True)

    items = OrderItemSerializer(many=True, read_only=True)
    shipping_address = ShippingAddressSerializer(read_only=True)
    shipping_address_id = serializers.UUIDField(write_only=True)

    total_cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    class Meta:
        model = Order
        fields = [
            "id",
            "buyer",
            "seller",
            "shipping_address",
            "shipping_address_id",
            "status",
            "track_status",
            "is_escrow_released",
            "created_at",
            "updated_at",
            "paid_at",
            "cancelled_at",
            "total_cost",
            "items",
        ]
        read_only_fields = [
            "buyer",
            "seller",
            "status",
            "track_status",
            "is_escrow_released",
            "escrow_released_at",
            "paid_at",
            "cancelled_at",
            "created_at",
            "updated_at",
        ]

    def get_seller(self, obj):
        if obj.items.exists():
            product = obj.items.first().product
            return product.seller.store_name if product and product.seller else None
        return None
