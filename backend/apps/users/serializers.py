import re
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Cart, CartItem, UserAddress, Wishlist, WishlistItem


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer xử lý đăng ký tài khoản.
    Kiểm tra email và số điện thoại không được trùng.
    Mật khẩu phải có ít nhất 8 ký tự và 1 chữ in hoa.
    """

    password = serializers.CharField(write_only=True, min_length=8, error_messages={
        'min_length': 'Mật khẩu phải có ít nhất 8 ký tự.'
    })

    class Meta:
        model = User
        fields = ('full_name', 'email', 'phone', 'password')
        extra_kwargs = {
            'email': {
                'error_messages': {
                    'unique': 'Email này đã được đăng ký, vui lòng sử dụng email khác.'
                }
            },
            'phone': {
                'error_messages': {
                    'unique': 'Số điện thoại này đã được sử dụng.'
                }
            }
        }

    def validate_password(self, value):
        """Kiểm tra mật khẩu phải có ít nhất 1 chữ in hoa."""
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Mật khẩu phải chứa ít nhất 1 chữ in hoa.")
        return value

    def create(self, validated_data):
        """Tạo user mới với mật khẩu đã được băm."""
        user = User.objects.create_user(
            email=validated_data['email'],
            phone=validated_data['phone'],
            full_name=validated_data['full_name'],
            password=validated_data['password']
        )
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer xử lý đăng nhập.
    Kiểm tra email, mật khẩu hợp lệ và trạng thái tài khoản.
    """

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """
        Xác thực thông tin đăng nhập.
        Từ chối nếu sai email/mật khẩu hoặc tài khoản bị khóa/chưa kích hoạt.
        """
        email = data.get('email')
        password = data.get('password')

        user = authenticate(username=email, password=password)

        if not user:
            raise serializers.ValidationError("Email hoặc mật khẩu không chính xác.")

        if user.status == 'locked':
            raise serializers.ValidationError("Tài khoản của bạn đã bị khóa.")

        if user.status == 'inactive':
            raise serializers.ValidationError("Tài khoản chưa được kích hoạt.")

        data['user'] = user
        return data


class CartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source='product.id', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    brand = serializers.CharField(source='product.brand', read_only=True)
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    image = serializers.SerializerMethodField()
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            'id', 'product_id', 'product_name', 'brand', 'unit_price',
            'image', 'quantity', 'line_total'
        ]

    def get_image(self, obj):
        image = obj.product.images.order_by('sort_order').first()
        if not image:
            return ''
        request = self.context.get('request')
        url = image.image_url.url
        return request.build_absolute_uri(url) if request else url

    def get_line_total(self, obj):
        return obj.unit_price * obj.quantity


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_quantity = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_quantity', 'total_price']

    def get_total_quantity(self, obj):
        return sum(item.quantity for item in obj.items.all())

    def get_total_price(self, obj):
        return sum(item.unit_price * item.quantity for item in obj.items.all())

# ============================================================
# USER ADDRESSES
# ============================================================
class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = [
            'id', 'receiver_name', 'receiver_phone',
            'line1', 'ward', 'district', 'city',
            'postal_code', 'is_default', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def validate_receiver_phone(self, value):
        if not re.match(r'^\+?[0-9]{9,15}$', value):
            raise serializers.ValidationError("Số điện thoại không hợp lệ.")
        return value


# ============================================================
# WISHLIST
# ============================================================
class WishlistItemSerializer(serializers.ModelSerializer):
    product_id   = serializers.IntegerField(source='product.id', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    price        = serializers.DecimalField(source='product.price',
                                            max_digits=12, decimal_places=2, read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = WishlistItem
        fields = ['id', 'product_id', 'product_name', 'price', 'image', 'added_at']
        read_only_fields = fields

    def get_image(self, obj):
        image = obj.product.images.order_by('sort_order').first()
        if not image:
            return ''
        request = self.context.get('request')
        url = image.image_url.url
        return request.build_absolute_uri(url) if request else url


class WishlistSerializer(serializers.ModelSerializer):
    items = WishlistItemSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()

    class Meta:
        model = Wishlist
        fields = ['id', 'total_items', 'items']

    def get_total_items(self, obj):
        return obj.items.count()


