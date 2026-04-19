from rest_framework import serializers
from .models import Category, Product, ProductImage


class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer cho ảnh sản phẩm. Dùng để hiển thị danh sách ảnh trong ProductSerializer."""

    class Meta:
        model = ProductImage
        fields = ['id', 'image_url', 'is_primary', 'sort_order']


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer cho danh mục sản phẩm.
    Kiểm tra tên danh mục không được trùng khi tạo mới hoặc cập nhật.
    """

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'is_active']

    def validate_name(self, value):
        """Kiểm tra tên danh mục không bị trùng, bỏ qua chính nó khi update."""
        instance = self.instance
        qs = Category.objects.filter(name=value)
        if instance:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Tên danh mục đã tồn tại.")
        return value


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer cho sản phẩm điện tử.
    
    - images: danh sách ảnh của sản phẩm (chỉ đọc).
    - uploaded_images: danh sách ảnh upload lên (chỉ ghi).
    - category_name: tên danh mục (chỉ đọc, lấy từ FK).
    """
    images = ProductImageSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Product
        fields = [
            'id', 'category', 'category_name', 'sku', 'name', 'brand',
            'price', 'stock_quantity', 'description', 'specifications',
            'business_status', 'rating_average', 'review_count',
            'images', 'uploaded_images', 'created_at', 'updated_at'
        ]
        read_only_fields = ['rating_average', 'review_count', 'created_at', 'updated_at']

    def validate_price(self, value):
        """Giá sản phẩm không được âm."""
        if value < 0:
            raise serializers.ValidationError("Giá không được âm.")
        return value

    def validate_stock_quantity(self, value):
        """Số lượng tồn kho không được âm."""
        if value < 0:
            raise serializers.ValidationError("Số lượng tồn kho không được âm.")
        return value

    def create(self, validated_data):
        """
        Tạo sản phẩm mới kèm ảnh nếu có.
        Ảnh đầu tiên trong danh sách sẽ được đặt là ảnh chính (is_primary=True).
        """
        uploaded_images = validated_data.pop('uploaded_images', [])
        product = Product.objects.create(**validated_data)

        for index, image in enumerate(uploaded_images):
            ProductImage.objects.create(
                product=product,
                image_url=image,
                is_primary=(index == 0),
                sort_order=index
            )
        return product

    def update(self, instance, validated_data):
        """
        Cập nhật thông tin sản phẩm.
        Nếu có ảnh mới upload thì thêm vào sau danh sách ảnh hiện tại.
        """
        uploaded_images = validated_data.pop('uploaded_images', [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if uploaded_images:
            current_max = instance.images.count()
            for index, image in enumerate(uploaded_images):
                ProductImage.objects.create(
                    product=instance,
                    image_url=image,
                    is_primary=False,
                    sort_order=current_max + index
                )
        return instance