from rest_framework import serializers
from .models import Product, ProductImage, WishList, Category
from django.utils.text import slugify
from uuid import uuid4
from registration.serializers import SellerProfileSerializer, ProfileSerializer
from cart.models import CartItem

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image_url', 'created_at']
        read_only_fields = ['id', 'created_at']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'thumbnail', 'medium', 'large', 'is_primary', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']

    def validate_image(self, image):
        if image:
            if image.size > 5 * 1024 * 1024:  # Limit image size to 2MB
                raise serializers.ValidationError("Image size must be less than 5MB.")
            
            if not image.content_type.startswith('image/'):
                raise serializers.ValidationError("Uploaded file must be an image.")    
        return image
    
class ProductImageBulkUploadSerializer(serializers.Serializer):
    images = serializers.ListField(
        child=serializers.ImageField(),
        allow_empty=False
    )

    def validate_images(self, images):
        if len(images) > 3:
            raise serializers.ValidationError("A maximum of 3 images can be uploaded.")

        for image in images:
            if image.size > 5 * 1024 * 1024:  # Limit each image size to 5MB
                raise serializers.ValidationError("Each image must be ≤ 5MB.")
            
            if hasattr(image, 'content_type') and not image.content_type.startswith('image/'):
                raise serializers.ValidationError("Uploaded files must be images.")
            
        return images
    
    def create(self, validated_data):
        product = self.context['product']
        images = validated_data['images']

        if product.images.count() + len(images) > 3:
            raise serializers.ValidationError("Total images for a product cannot exceed 3.")

        created_images = []

        for index, image in enumerate(images):
            created_images.append(
                ProductImage.objects.create(
                    product=product,
                    image=image,
                    is_primary=(index == 0 and not product.images.filter(is_primary=True).exists())
                )
            )

        return created_images
    
class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, required=False, allow_empty=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.UUIDField(write_only=True, required=False)
    seller = SellerProfileSerializer(read_only=True)

    #is_favorited = serializers.SerializerMethodField()

    # Expose model properties as read-only fields
    price_range = serializers.CharField(read_only=True)
    is_available = serializers.BooleanField( read_only=True)
    is_seller = serializers.BooleanField(read_only=True)
    image_count = serializers.IntegerField(read_only=True)

    is_in_cart = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'seller', 'name', 'slug', 'description', 'price',
            'min_price', 'max_price', 'quantity', 'category', 'category_id', 'condition',
            'is_active', 'created_at', 'updated_at', 'images',
            'price_range', 'is_available', 'is_seller', 'image_count', 'is_in_cart'
        ]

        read_only_fields = ['id', 'seller', 'slug', 'created_at', 'price_range', 'is_available', 'is_seller', 'image_count']

    def get_is_in_cart(self, obj):
        request = self.context.get('request')

        if not request or not request.user.is_authenticated:
            return False
        
        return CartItem.objects.filter(
            cart__buyer=request.user.profile,
            cart__status='active',
            product=obj
        ).exists()

    def validate_category_id(self, value):
        if not Category.objects.filter(id=value).exists():
            raise serializers.ValidationError("Category with the given ID does not exist.")
        return value
    
    def create(self, validated_data):
        request = self.context.get('request')
        images = request.FILES.getlist('images') if request else []

        if len(images) > 3:
            raise serializers.ValidationError("A maximum of 3 images can be uploaded.")
        
        category_id = validated_data.pop('category_id', None)
        if category_id:
            validated_data['category'] = Category.objects.get(id=category_id)

        validated_data['seller'] = request.user.profile.seller_profile

        product = Product.objects.create(**validated_data)

        for index, image in enumerate(images):
            ProductImage.objects.create(
                product=product,
                image=image,
                is_primary=(index == 0)
            )

        return product

    def update(self, instance, validated_data):
        request = self.context.get('request')
        images = request.FILES.getlist('images') if request else []

        category_id = validated_data.pop('category_id', None)

        if category_id:
            instance.category = Category.objects.get(id=category_id)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        for index, image in enumerate(images):
            if len(images) > 3:
                return serializers.ValidationError("A maximum of 3 images are allowed per product.")
            
            instance.images.all().delete()

            ProductImage.objects.create(
                product=instance,
                image=image,
                is_primary=(index == 0)  # New images added via update are not primary by default
            )

        return instance
    
    """ def get_is_favorited(self, obj):
        request = self.context.get('request')

        if not request or not request.user.is_authenticated:
            return False
        
        if "wishlist_ids" not in self.context:
            self.context['wishlist_ids'] = set(
                WishList.objects.filter(buyer=request.user.profile).values_list('products_id', flat=True)
            )

        return obj.id in self.context['wishlist_ids'] """

    
class WishListSerializer(serializers.ModelSerializer):
    products = ProductSerializer(read_only=True)
    buyer = ProfileSerializer(read_only=True)
    class Meta:
        model = WishList
        fields = ['id', 'buyer', 'products', 'added_at']
        read_only_fields = ['id', 'added_at']

    def create(self, validated_data):
        product = self.context.get('product')
        buyer = self.context.get('buyer')

        if not product or not buyer:
            raise serializers.ValidationError("Product and buyer must be provided.")
        
        wishlist_item, created = WishList.objects.get_or_create(products=product, buyer=buyer)
        
        if not created:
            return wishlist_item
        
        return wishlist_item
    
    def to_representation(self, instance):
        data = super().to_representation(instance)

        if 'products' in data:
            data['products']['is_favorited'] = True
        
        return data