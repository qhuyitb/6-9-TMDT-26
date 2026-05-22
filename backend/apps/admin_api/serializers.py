from django.db import transaction
from rest_framework import serializers
from apps.products.models import Product, Category
from apps.users.models import User
from .models import Order, OrderItem, Review


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'phone', 'status', 'role', 'created_at', 'updated_at']
        read_only_fields = ['email', 'created_at', 'updated_at']


class OrderItemWriteSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class OrderItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source='product.id', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    category_id = serializers.IntegerField(source='product.category_id', read_only=True)
    category_name = serializers.CharField(source='product.category.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product_id', 'product_name', 'category_id', 'category_name', 'quantity', 'unit_price', 'line_total']
        read_only_fields = ['line_total']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    items_write = OrderItemWriteSerializer(many=True, write_only=True, required=False)
    customer_email = serializers.EmailField(source='user.email', read_only=True)
    customer_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'customer_email', 'customer_name', 'address', 'order_code', 'order_date',
            'status', 'payment_status', 'shipping_method', 'shipping_fee', 'subtotal_amount',
            'total_amount', 'cancel_reason', 'note',
            'items', 'items_write', 'created_at', 'updated_at'
        ]
        read_only_fields = ['subtotal_amount', 'total_amount', 'order_date', 'created_at', 'updated_at']

    def validate(self, attrs):
        items = attrs.get('items_write') or []
        if items:
            product_ids = [item['product_id'] for item in items]
            products = Product.objects.filter(id__in=product_ids).values_list('id', flat=True)
            missing = set(product_ids) - set(products)
            if missing:
                raise serializers.ValidationError({'items_write': f'Invalid product ids: {sorted(missing)}'})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items_write', [])
        if not validated_data.get('order_code'):
            validated_data['order_code'] = self._generate_order_code()
        order = Order.objects.create(**validated_data)
        self._upsert_items(order, items_data)
        self._recalculate_total(order)
        return order

    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop('items_write', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            instance.items.all().delete()
            self._upsert_items(instance, items_data)
            self._recalculate_total(instance)
        return instance

    def _upsert_items(self, order, items_data):
        for item in items_data:
            product = Product.objects.get(id=item['product_id'])
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item['quantity'],
                unit_price=product.price
            )

    def _recalculate_total(self, order):
        subtotal = sum(item.line_total for item in order.items.all())
        order.subtotal_amount = subtotal
        order.total_amount = subtotal + order.shipping_fee
        order.save(update_fields=['subtotal_amount', 'total_amount'])

    def _generate_order_code(self):
        return f'OD{Order.objects.count() + 1:06d}'


class ReviewSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    customer_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id', 'product', 'product_name', 'user', 'customer_email',
            'order', 'rating', 'comment', 'review_date', 'is_visible'
        ]
        read_only_fields = ['review_date']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError('Rating must be between 1 and 5.')
        return value
