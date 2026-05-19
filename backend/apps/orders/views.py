import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction
from django.utils import timezone

from apps.admin_api.models import Order, OrderItem, Payment
from apps.users.models import UserAddress, Cart
from .serializers import OrderSerializer, OrderCreateSerializer, PaymentSerializer


class OrderListCreateView(APIView):
    """
    GET  /api/orders/  — Lịch sử đơn hàng
    POST /api/orders/  — Đặt hàng từ giỏ hàng
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = request.user.orders.prefetch_related(
            'items__product__images', 'payment', 'address'
        ).order_by('-order_date')
        serializer = OrderSerializer(orders, many=True, context={'request': request})
        return Response(serializer.data)

    @transaction.atomic
    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Lấy giỏ hàng
        try:
            cart = Cart.objects.prefetch_related(
                'items__product'
            ).get(user=request.user, status='active')
        except Cart.DoesNotExist:
            return Response({'error': 'Giỏ hàng không tồn tại.'}, status=status.HTTP_400_BAD_REQUEST)

        cart_items = cart.items.all()
        if not cart_items.exists():
            return Response({'error': 'Giỏ hàng đang trống.'}, status=status.HTTP_400_BAD_REQUEST)

        # Kiểm tra tồn kho + tính tiền
        subtotal = 0
        for item in cart_items:
            if item.product.business_status != 'active':
                return Response(
                    {'error': f'Sản phẩm "{item.product.name}" không còn bán.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if item.product.stock_quantity < item.quantity:
                return Response(
                    {'error': f'Sản phẩm "{item.product.name}" không đủ tồn kho.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subtotal += item.unit_price * item.quantity

        shipping_fee = data.get('shipping_fee', 0)
        total_amount = subtotal + shipping_fee
        address      = UserAddress.objects.get(id=data['address_id'])

        # Tạo order_code unique
        order_code = f'ORD-{uuid.uuid4().hex[:10].upper()}'

        # Tạo Order
        order = Order.objects.create(
            user            = request.user,
            address         = address,
            order_code      = order_code,
            note            = data.get('note', ''),
            shipping_method = data.get('shipping_method', 'standard'),
            subtotal_amount = subtotal,
            shipping_fee    = shipping_fee,
            total_amount    = total_amount,
            payment_status  = Order.PAYMENT_UNPAID,
        )

        # Tạo OrderItems + trừ tồn kho
        for item in cart_items:
            OrderItem.objects.create(
                order      = order,
                product    = item.product,
                quantity   = item.quantity,
                unit_price = item.unit_price,
            )
            item.product.stock_quantity -= item.quantity
            item.product.save(update_fields=['stock_quantity'])

        # Tạo Payment
        is_cod = data['payment_method'] == Payment.METHOD_COD
        Payment.objects.create(
            order          = order,
            payment_method = data['payment_method'],
            amount         = total_amount,
            status         = Payment.STATUS_SUCCESS if is_cod else Payment.STATUS_PENDING,
            paid_at        = timezone.now() if is_cod else None,
        )

        # Cập nhật payment_status trên Order nếu COD
        if is_cod:
            order.payment_status = Order.PAYMENT_PAID
            order.save(update_fields=['payment_status'])

        # Đánh dấu giỏ hàng đã checkout
        cart.status = 'checked_out'
        cart.save()

        result = OrderSerializer(order, context={'request': request})
        return Response(result.data, status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    """
    GET /api/orders/<id>/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            order = request.user.orders.prefetch_related(
                'items__product__images', 'payment', 'address'
            ).get(pk=pk)
        except Order.DoesNotExist:
            return Response({'error': 'Đơn hàng không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(OrderSerializer(order, context={'request': request}).data)


class OrderCancelView(APIView):
    """
    POST /api/orders/<id>/cancel/
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        try:
            order = request.user.orders.select_related('payment').prefetch_related(
                'items__product'
            ).get(pk=pk)
        except Order.DoesNotExist:
            return Response({'error': 'Đơn hàng không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)

        if order.status not in (Order.STATUS_PENDING, Order.STATUS_CONFIRMED):
            return Response(
                {'error': f'Không thể hủy đơn hàng đang ở trạng thái "{order.status}".'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cancel_reason = request.data.get('cancel_reason', '')

        # Hoàn lại tồn kho
        for item in order.items.all():
            item.product.stock_quantity += item.quantity
            item.product.save(update_fields=['stock_quantity'])

        order.status        = Order.STATUS_CANCELLED
        order.cancel_reason = cancel_reason
        order.save(update_fields=['status', 'cancel_reason'])

        # Cập nhật payment
        if hasattr(order, 'payment') and order.payment.status == Payment.STATUS_SUCCESS:
            order.payment.status = Payment.STATUS_CANCELLED
            order.payment.save(update_fields=['status'])
            order.payment_status = Order.PAYMENT_REFUNDED
            order.save(update_fields=['payment_status'])

        return Response({'message': 'Đã hủy đơn hàng thành công.'})


class PaymentListView(APIView):
    """
    GET /api/orders/payments/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        order_ids = request.user.orders.values_list('id', flat=True)
        payments  = Payment.objects.filter(order_id__in=order_ids).order_by('-created_at')
        return Response(PaymentSerializer(payments, many=True).data)


class PaymentDetailView(APIView):
    """
    GET /api/orders/payments/<id>/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        order_ids = request.user.orders.values_list('id', flat=True)
        try:
            payment = Payment.objects.get(pk=pk, order_id__in=order_ids)
        except Payment.DoesNotExist:
            return Response({'error': 'Không tìm thấy.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(PaymentSerializer(payment).data)