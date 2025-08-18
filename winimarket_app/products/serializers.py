from rest_framework import serializers
from .models import Product, ProductImage, WishList, Category

class CategorySerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)  # Allow image to be optional
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_image(self, value):
        if value:
            if value.size > 2 * 1024 * 1024:  # Limit image size to 2MB
                raise serializers.ValidationError("Image size must be less than 2MB.")
            if not value.name.lower().endswith(('.png', '.jpg', '.jpeg')):
                raise serializers.ValidationError("Image must be a PNG or JPEG file.")
            if not value.content_type.startswith('image/'):
                raise serializers.ValidationError("Uploaded file must be an image.")    
        return value

class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=True)  # Image is required for product images
    
    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'image', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']

    def validate_image(self, value):
        if value:
            if value.size > 2 * 1024 * 1024:  # Limit image size to 2MB
                raise serializers.ValidationError("Image size must be less than 2MB.")
            if not value.name.lower().endswith(('.png', '.jpg', '.jpeg')):
                raise serializers.ValidationError("Image must be a PNG or JPEG file.")
            if not value.content_type.startswith('image/'):
                raise serializers.ValidationError("Uploaded file must be an image.")    
        return value
    
class ProductImageBulkUploadSerializer(serializers.Serializer):
    images = serializers.ListField(
        child=serializers.ImageField(max_length=None, allow_empty_file=False, use_url=True),
        allow_empty=False
    )

    def validate_images(self, value):
        for image in value:
            if image.size > 5 * 1024 * 1024:  # Limit each image size to 5MB
                raise serializers.ValidationError("Each image must be less than 5MB.")
            if not image.name.lower().endswith(('.png', '.jpg', '.jpeg')):
                raise serializers.ValidationError("Each image must be a PNG or JPEG file.")
            if hasattr(image, 'content_type') and not image.content_type.startswith('image/'):
                raise serializers.ValidationError("Uploaded files must be images.")
        return value
    
    def create(self, validated_data):
        product = self.context['product']
        images = validated_data['images']
        image_objs = [
            ProductImage.objects.create(product=product, image=image)
            for image in images
        ]

        return image_objs
    
class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, required=False, allow_empty=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.UUIDField(write_only=True, required=False)


    # Expose model properties as read-only fields
    price_range = serializers.CharField(source='price_range', read_only=True)
    is_available = serializers.BooleanField(source='is_available', read_only=True)
    is_seller = serializers.BooleanField(source='is_seller', read_only=True)
    image_count = serializers.IntegerField(source='image_count', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'seller', 'name', 'slug', 'description',
            'min_price', 'max_price', 'quantity', 'category', 'category_id',
            'is_active', 'created_at', 'updated_at', 'images',
            'price_range', 'is_available', 'is_seller', 'image_count'
        ]

        read_only_fields = ['id', 'created_at', 'updated_at', 'price_range', 'is_available', 'is_seller', 'image_count']
    
    def create(self, validated_data):
        images = self.context['request'].FILES.getlist('images')
        category = self.context.get('category')
        if not category and 'category_id' in validated_data:
            from .models import Category
            category = Category.objects.get(id=validated_data.pop('category_id'))

        if category:
            validated_data['category'] = category

        product = super().create(validated_data)

        for image in images:
            ProductImage.objects.create(product=product, image=image)

        return product
    
    def update(self, instance, validated_data):
        image_data = self.context['request'].FILES.getlist('images')
        category = self.context.get('category', None)
        if not category and 'category_id' in validated_data:
            from .models import Category
            category = Category.objects.get(id=validated_data.pop('category_id'))
        if category:
            instance.category = category
        
        product = super().update(instance, validated_data)

        for image in image_data:
            ProductImage.objects.create(product=product, image=image)

        return product
    
class WishListSerializer(serializers.ModelSerializer):
    products = ProductSerializer(read_only=True)

    class Meta:
        model = WishList
        fields = ['id', 'buyer', 'products', 'added_at']
        read_only_fields = ['id', 'added_at']

    def create(self, validated_data):
        product = self.context.get('product')
        buyer = self.context.get('buyer')

        if not product or not buyer:
            raise serializers.ValidationError("Product and buyer must be provided.")
        
        validated_data['products'] = product
        validated_data['buyer'] = buyer

        return super().create(validated_data)