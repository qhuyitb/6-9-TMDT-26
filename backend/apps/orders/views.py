import json
import uuid
from urllib.parse import urlencode

from django.conf import settings
from django.shortcuts import redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from django.db import transaction
from django.utils import timezone

from apps.admin_api.models import Order, OrderItem, Payment
from apps.users.models import UserAddress, Cart
from .serializers import OrderSerializer, OrderCreateSerializer, PaymentSerializer
from .vnpay import (
    build_payment_url,
    is_configured as vnpay_is_configured,
    validate_response as validate_vnpay_response,
)


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
        payment_method = data['payment_method']

        if payment_method not in (Payment.METHOD_COD, Payment.METHOD_VNPAY):
            return Response(
                {'error': 'Phuong thuc thanh toan nay chua duoc ho tro.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if payment_method == Payment.METHOD_VNPAY and not vnpay_is_configured():
            return Response(
                {'error': 'VNPay chua duoc cau hinh. Vui long thiet lap VNPAY_TMN_CODE va VNPAY_HASH_SECRET_KEY.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

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
        address = self.get_checkout_address(request.user, data.get('address_id'))

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
            payment_status  = Order.PAYMENT_UNPAID if payment_method == Payment.METHOD_COD else Order.PAYMENT_PENDING,
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
        payment = Payment.objects.create(
            order          = order,
            payment_method = payment_method,
            amount         = total_amount,
            status         = Payment.STATUS_PENDING,
            transaction_ref= order.order_code if payment_method == Payment.METHOD_VNPAY else None,
            paid_at        = None,
        )

        # Don hang da co ban sao OrderItem rieng, nen lam trong gio hang
        # de khach co the tiep tuc mua hang voi cung Cart OneToOne.
        cart_items.delete()
        cart.status = 'active'
        cart.save(update_fields=['status'])

        result = OrderSerializer(order, context={'request': request})
        response_data = result.data

        if payment_method == Payment.METHOD_VNPAY:
            response_data['payment_url'] = build_payment_url(
                order=order,
                request=request,
                return_url=settings.VNPAY_RETURN_URL,
            )
            response_data['payment_id'] = payment.id

        return Response(response_data, status=status.HTTP_201_CREATED)

    def get_checkout_address(self, user, address_id=None):
        if address_id:
            return UserAddress.objects.get(id=address_id, user=user)

        address = user.addresses.order_by('-is_default', '-created_at').first()
        if address:
            return address

        return UserAddress.objects.create(
            user=user,
            receiver_name=user.full_name or user.email,
            receiver_phone=user.phone or '0000000000',
            line1='Chưa cập nhật',
            ward='Chưa cập nhật',
            district='Chưa cập nhật',
            city='Chưa cập nhật',
            is_default=True,
        )


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


class VNPayReturnView(APIView):
    """
    GET /api/orders/vnpay/return/
    VNPay redirects the browser here after payment.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        result = inspect_vnpay_return(dict(request.GET.items()))
        return redirect(build_frontend_result_url(result))


class VNPayIPNView(APIView):
    """
    GET /api/orders/vnpay/ipn/
    VNPay server-to-server notification endpoint.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        result = handle_vnpay_ipn(dict(request.GET.items()))
        return Response({
            'RspCode': result['rsp_code'],
            'Message': result['message'],
        })


def inspect_vnpay_return(params):
    if not validate_vnpay_response(params):
        return {
            'ok': False,
            'payment_result': 'invalid',
            'order_id': '',
            'rsp_code': '97',
            'message': 'Invalid checksum',
        }

    txn_ref = params.get('vnp_TxnRef', '')
    response_code = params.get('vnp_ResponseCode', '')
    transaction_status = params.get('vnp_TransactionStatus', '')

    try:
        payment = Payment.objects.select_related('order').get(
            transaction_ref=txn_ref,
            payment_method=Payment.METHOD_VNPAY,
        )
    except Payment.DoesNotExist:
        return {
            'ok': False,
            'payment_result': 'failed',
            'order_id': '',
            'rsp_code': '01',
            'message': 'Order not found',
        }

    if payment.status == Payment.STATUS_PENDING:
        payment.gateway_response = json.dumps({
            'source': 'return_url',
            'params': params,
        }, ensure_ascii=True)
        payment.save(update_fields=['gateway_response'])

    if response_code == '00' and transaction_status == '00':
        if settings.VNPAY_CONFIRM_ON_RETURN:
            return handle_vnpay_ipn(params, source='return_url_fallback')

        return {
            'ok': True,
            'payment_result': 'processing',
            'order_id': payment.order_id,
            'rsp_code': '00',
            'message': 'Waiting for IPN confirmation',
        }

    return {
        'ok': False,
        'payment_result': 'failed',
        'order_id': payment.order_id,
        'rsp_code': response_code or '99',
        'message': 'Payment failed on VNPay',
    }


def handle_vnpay_ipn(params, source='ipn'):
    if not validate_vnpay_response(params):
        return {
            'ok': False,
            'payment_result': 'failed',
            'order_id': '',
            'rsp_code': '97',
            'message': 'Invalid checksum',
        }

    txn_ref = params.get('vnp_TxnRef', '')
    response_code = params.get('vnp_ResponseCode', '')
    transaction_status = params.get('vnp_TransactionStatus', '')
    vnp_amount = params.get('vnp_Amount', '0')

    try:
        with transaction.atomic():
            payment = Payment.objects.select_for_update().select_related('order').get(
                transaction_ref=txn_ref,
                payment_method=Payment.METHOD_VNPAY,
            )
            order = payment.order

            if int(vnp_amount) != int(payment.amount * 100):
                if payment.status == Payment.STATUS_PENDING:
                    payment.status = Payment.STATUS_RECONCILE_PENDING
                    payment.gateway_response = json.dumps({
                        'source': source,
                        'params': params,
                    }, ensure_ascii=True)
                    payment.save(update_fields=['status', 'gateway_response'])
                    order.payment_status = Order.PAYMENT_RECONCILE_PENDING
                    order.save(update_fields=['payment_status'])
                return {
                    'ok': False,
                    'payment_result': 'failed',
                    'order_id': order.id,
                    'rsp_code': '04',
                    'message': 'Invalid amount',
                }

            if payment.status == Payment.STATUS_SUCCESS:
                return {
                    'ok': True,
                    'payment_result': 'success',
                    'order_id': order.id,
                    'rsp_code': '00',
                    'message': 'Confirm Success',
                }

            if response_code == '00' and transaction_status == '00':
                payment.status = Payment.STATUS_SUCCESS
                payment.gateway_response = json.dumps({
                    'source': source,
                    'params': params,
                }, ensure_ascii=True)
                payment.paid_at = timezone.now()
                payment.save(update_fields=['status', 'gateway_response', 'paid_at'])

                order.payment_status = Order.PAYMENT_PAID
                order.save(update_fields=['payment_status'])

                return {
                    'ok': True,
                    'payment_result': 'success',
                    'order_id': order.id,
                    'rsp_code': '00',
                    'message': 'Confirm Success',
                }

            payment.status = Payment.STATUS_FAILED
            payment.gateway_response = json.dumps({
                'source': source,
                'params': params,
            }, ensure_ascii=True)
            payment.save(update_fields=['status', 'gateway_response'])

            order.payment_status = Order.PAYMENT_FAILED
            order.save(update_fields=['payment_status'])

            return {
                'ok': False,
                'payment_result': 'failed',
                'order_id': order.id,
                'rsp_code': '00',
                'message': 'Confirm Success',
            }
    except Payment.DoesNotExist:
        return {
            'ok': False,
            'payment_result': 'failed',
            'order_id': '',
            'rsp_code': '01',
            'message': 'Order not found',
        }
    except (TypeError, ValueError):
        return {
            'ok': False,
            'payment_result': 'failed',
            'order_id': '',
            'rsp_code': '99',
            'message': 'Unknown error',
        }


def build_frontend_result_url(result):
    query = urlencode({
        'created': result.get('order_id') or '',
        'payment': result.get('payment_result') or 'failed',
        'code': result.get('rsp_code') or '',
    })
    separator = '&' if '?' in settings.VNPAY_FRONTEND_RETURN_URL else '?'
    return f'{settings.VNPAY_FRONTEND_RETURN_URL}{separator}{query}'
