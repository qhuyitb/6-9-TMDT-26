from rest_framework import serializers
from apps.admin_api.models import Order, OrderItem, Payment
from apps.users.serializers import UserAddressSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    product_id   = serializers.IntegerField(source='product.id', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    image        = serializers.SerializerMethodField()

    class Meta:
        model  = OrderItem
        fields = ['id', 'product_id', 'product_name', 'image',
                  'quantity', 'unit_price', 'line_total']

    def get_image(self, obj):
        image = obj.product.images.order_by('sort_order').first()
        if not image:
            return ''
        request = self.context.get('request')
        url = image.image_url.url
        return request.build_absolute_uri(url) if request else url


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Payment
        fields = ['id', 'payment_method', 'status', 'amount',
                  'transaction_ref', 'paid_at', 'created_at']
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items   = OrderItemSerializer(many=True, read_only=True)
    payment = PaymentSerializer(read_only=True)
    address = UserAddressSerializer(read_only=True)

    class Meta:
        model  = Order
        fields = ['id', 'order_code', 'status', 'payment_status', 'note',
                  'address', 'subtotal_amount', 'shipping_fee', 'total_amount',
                  'items', 'payment', 'order_date']
        read_only_fields = fields


class OrderCreateSerializer(serializers.Serializer):
    address_id      = serializers.IntegerField(required=False, allow_null=True)
    payment_method  = serializers.ChoiceField(choices=Payment.METHOD_CHOICES)
    shipping_method = serializers.CharField(default='standard')
    note            = serializers.CharField(required=False, allow_blank=True)
    shipping_fee    = serializers.DecimalField(max_digits=10, decimal_places=2,
                                               required=False, default=0)

    def validate_address_id(self, value):
        if value is None:
            return value
        user = self.context['request'].user
        if not user.addresses.filter(id=value).exists():
            raise serializers.ValidationError('Địa chỉ không tồn tại hoặc không thuộc về bạn.')
        return value
