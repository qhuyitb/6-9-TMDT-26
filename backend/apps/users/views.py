from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import transaction
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from apps.products.models import Product
from .models import Cart, CartItem, Wishlist, WishlistItem
from .serializers import (
    CartSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
)


def get_guest_session_id(request):
    session_id = (
        request.headers.get('X-Guest-Session')
        or request.data.get('guest_session_id')
        or request.query_params.get('guest_session_id')
    )
    if not session_id:
        return ''

    session_id = str(session_id).strip()
    if len(session_id) > 100 or not session_id.startswith('guest_'):
        return ''
    return session_id


def get_customer_cart(request):
    if request.user and request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart, None

    session_id = get_guest_session_id(request)
    if not session_id:
        return None, Response(
            {'error': 'Thiếu mã phiên khách vãng lai.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    cart, _ = Cart.objects.get_or_create(session_id=session_id)
    return cart, None


def get_customer_wishlist(request):
    if request.user and request.user.is_authenticated:
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        return wishlist, None

    session_id = get_guest_session_id(request)
    if not session_id:
        return None, Response(
            {'error': 'Thiếu mã phiên khách vãng lai.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    wishlist, _ = Wishlist.objects.get_or_create(session_id=session_id)
    return wishlist, None


@transaction.atomic
def merge_guest_data_into_user(user, session_id):
    if not session_id:
        return

    guest_cart = Cart.objects.filter(session_id=session_id, user__isnull=True).first()
    if guest_cart:
        user_cart, _ = Cart.objects.get_or_create(user=user)
        for guest_item in guest_cart.items.select_related('product'):
            if guest_item.product.stock_quantity <= 0:
                continue
            item, created = CartItem.objects.get_or_create(
                cart=user_cart,
                product=guest_item.product,
                defaults={
                    'quantity': min(guest_item.quantity, guest_item.product.stock_quantity),
                    'unit_price': guest_item.product.price,
                }
            )
            if not created:
                item.quantity = min(item.quantity + guest_item.quantity, guest_item.product.stock_quantity)
                item.unit_price = guest_item.product.price
                item.save(update_fields=['quantity', 'unit_price', 'updated_at'])
        guest_cart.delete()

    guest_wishlist = Wishlist.objects.filter(session_id=session_id, user__isnull=True).first()
    if guest_wishlist:
        user_wishlist, _ = Wishlist.objects.get_or_create(user=user)
        for guest_item in guest_wishlist.items.select_related('product'):
            WishlistItem.objects.get_or_create(
                wishlist=user_wishlist,
                product=guest_item.product,
            )
        guest_wishlist.delete()


class RegisterView(generics.CreateAPIView):
    """
    API đăng ký tài khoản mới.
    Cho phép tất cả mọi người truy cập, không cần xác thực.
    POST /api/auth/register/
    """

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        """Tạo tài khoản mới và trả về thông báo thành công."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            'message': 'Đăng ký thành công',
            'email': user.email
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    API đăng nhập tài khoản.
    Trả về access_token và refresh_token nếu đăng nhập thành công.
    POST /api/auth/login/
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Xác thực thông tin đăng nhập và trả về JWT token."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        merge_guest_data_into_user(user, get_guest_session_id(request))
        refresh = RefreshToken.for_user(user)

        return Response({
            'message': 'Đăng nhập thành công',
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': {
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
            }
        }, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.get_user()

        response_data = {
            'message': 'Nếu email tồn tại, hệ thống đã gửi hướng dẫn đặt lại mật khẩu.'
        }

        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_path = reverse('reset_password_page', kwargs={'uid': uid, 'token': token})
            reset_url = request.build_absolute_uri(reset_path)

            send_mail(
                subject='Đặt lại mật khẩu TechShop',
                message=(
                    f'Xin chào {user.full_name},\n\n'
                    f'Bạn có thể đặt lại mật khẩu tại liên kết sau:\n{reset_url}\n\n'
                    'Nếu bạn không yêu cầu đặt lại mật khẩu, hãy bỏ qua email này.'
                ),
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                recipient_list=[user.email],
                fail_silently=True,
            )

            if settings.DEBUG:
                response_data['reset_url'] = reset_url

        return Response(response_data, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        user.set_password(serializer.validated_data['password'])
        user.save(update_fields=['password', 'updated_at'])

        return Response({'message': 'Đặt lại mật khẩu thành công.'}, status=status.HTTP_200_OK)


class CartView(APIView):
    permission_classes = [AllowAny]

    def get_cart(self, request):
        cart, error = get_customer_cart(request)
        if error:
            return None
        return cart

    def get(self, request):
        cart, error = get_customer_cart(request)
        if error:
            return error
        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class CartItemAddView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        product_id = request.data.get('product_id')
        try:
            quantity = int(request.data.get('quantity', 1))
        except (TypeError, ValueError):
            return Response({'error': 'Số lượng không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)

        if quantity < 1:
            return Response({'error': 'Số lượng phải lớn hơn 0.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id, business_status='active')
        except Product.DoesNotExist:
            return Response({'error': 'Sản phẩm không tồn tại hoặc không đang bán.'}, status=status.HTTP_404_NOT_FOUND)

        if product.stock_quantity < quantity:
            return Response({'error': 'Số lượng tồn kho không đủ.'}, status=status.HTTP_400_BAD_REQUEST)

        cart, error = get_customer_cart(request)
        if error:
            return error
        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity, 'unit_price': product.price}
        )

        if not created:
            next_quantity = item.quantity + quantity
            if product.stock_quantity < next_quantity:
                return Response({'error': 'Số lượng tồn kho không đủ.'}, status=status.HTTP_400_BAD_REQUEST)
            item.quantity = next_quantity
            item.save()

        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class CartItemUpdateView(APIView):
    permission_classes = [AllowAny]

    def patch(self, request, item_id):
        try:
            quantity = int(request.data.get('quantity', 1))
        except (TypeError, ValueError):
            return Response({'error': 'Số lượng không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
        cart, error = get_customer_cart(request)
        if error:
            return error

        try:
            item = cart.items.select_related('product').get(id=item_id)
        except CartItem.DoesNotExist:
            return Response({'error': 'Sản phẩm không có trong giỏ hàng.'}, status=status.HTTP_404_NOT_FOUND)

        if quantity <= 0:
            item.delete()
        else:
            if item.product.stock_quantity < quantity:
                return Response({'error': 'Số lượng tồn kho không đủ.'}, status=status.HTTP_400_BAD_REQUEST)
            item.quantity = quantity
            item.save()

        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class CartItemDeleteView(APIView):
    permission_classes = [AllowAny]

    def delete(self, request, item_id):
        cart, error = get_customer_cart(request)
        if error:
            return error
        cart.items.filter(id=item_id).delete()
        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

from .models import Cart, CartItem, UserAddress, Wishlist, WishlistItem
from .serializers import (
    RegisterSerializer, LoginSerializer, CartSerializer,
    UserAddressSerializer, WishlistSerializer,
)
from apps.products.models import Product
from django.utils import timezone


# ============================================================
# USER ADDRESSES
# ============================================================
class UserAddressListCreateView(APIView):
    """
    GET  /api/auth/addresses/        — Lấy danh sách địa chỉ của user
    POST /api/auth/addresses/        — Thêm địa chỉ mới
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        addresses = request.user.addresses.order_by('-is_default', '-created_at')
        serializer = UserAddressSerializer(addresses, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = UserAddressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Nếu set is_default=True thì bỏ default của các địa chỉ cũ
        if serializer.validated_data.get('is_default', False):
            request.user.addresses.update(is_default=False)

        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserAddressDetailView(APIView):
    """
    GET    /api/auth/addresses/<id>/  — Xem chi tiết
    PATCH  /api/auth/addresses/<id>/  — Cập nhật
    DELETE /api/auth/addresses/<id>/  — Xóa
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            return request.user.addresses.get(pk=pk)
        except UserAddress.DoesNotExist:
            return None

    def get(self, request, pk):
        address = self.get_object(request, pk)
        if not address:
            return Response({'error': 'Địa chỉ không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(UserAddressSerializer(address).data)

    def patch(self, request, pk):
        address = self.get_object(request, pk)
        if not address:
            return Response({'error': 'Địa chỉ không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserAddressSerializer(address, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data.get('is_default', False):
            request.user.addresses.update(is_default=False)

        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        address = self.get_object(request, pk)
        if not address:
            return Response({'error': 'Địa chỉ không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)
        address.delete()
        return Response({'message': 'Đã xóa địa chỉ.'}, status=status.HTTP_204_NO_CONTENT)


class UserAddressSetDefaultView(APIView):
    """
    POST /api/auth/addresses/<id>/set-default/  — Đặt làm địa chỉ mặc định
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            address = request.user.addresses.get(pk=pk)
        except UserAddress.DoesNotExist:
            return Response({'error': 'Địa chỉ không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)

        request.user.addresses.update(is_default=False)
        address.is_default = True
        address.save()
        return Response({'message': 'Đã đặt làm địa chỉ mặc định.'})


# ============================================================
# WISHLIST
# ============================================================
class WishlistView(APIView):
    """
    GET /api/auth/wishlist/  — Lấy wishlist của user
    """
    permission_classes = [AllowAny]

    def get(self, request):
        wishlist, error = get_customer_wishlist(request)
        if error:
            return error
        serializer = WishlistSerializer(wishlist, context={'request': request})
        return Response(serializer.data)


class WishlistItemAddView(APIView):
    """
    POST /api/auth/wishlist/items/  — Thêm sản phẩm vào wishlist
    Body: { "product_id": 1 }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({'error': 'Thiếu product_id.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id, business_status='active')
        except Product.DoesNotExist:
            return Response({'error': 'Sản phẩm không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)

        wishlist, error = get_customer_wishlist(request)
        if error:
            return error
        _, created = WishlistItem.objects.get_or_create(wishlist=wishlist, product=product)

        if not created:
            return Response({'message': 'Sản phẩm đã có trong wishlist.'}, status=status.HTTP_200_OK)

        serializer = WishlistSerializer(wishlist, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class WishlistItemDeleteView(APIView):
    """
    DELETE /api/auth/wishlist/items/<product_id>/  — Xóa sản phẩm khỏi wishlist
    """
    permission_classes = [AllowAny]

    def delete(self, request, product_id):
        wishlist, error = get_customer_wishlist(request)
        if error:
            return error

        deleted, _ = WishlistItem.objects.filter(
            wishlist=wishlist, product_id=product_id
        ).delete()

        if not deleted:
            return Response({'error': 'Sản phẩm không có trong wishlist.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = WishlistSerializer(wishlist, context={'request': request})
        return Response(serializer.data)


# ============================================================
# PAYMENTS
# ============================================================
class PaymentListView(APIView):
    """
    GET /api/auth/payments/  — Lịch sử thanh toán của user
    (Sẽ filter theo orders của user khi có Order model)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Placeholder — mày uncomment khi có Order model:
        # from apps.orders.models import Order
        # order_ids = Order.objects.filter(user=request.user).values_list('id', flat=True)
        # payments = Payment.objects.filter(order_id__in=order_ids).order_by('-created_at')
        # serializer = PaymentSerializer(payments, many=True)
        # return Response(serializer.data)
        return Response({'message': 'Cần liên kết với Order model.'})


class PaymentDetailView(APIView):
    """
    GET /api/auth/payments/<id>/  — Xem chi tiết 1 thanh toán
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        # from apps.orders.models import Order
        # order_ids = Order.objects.filter(user=request.user).values_list('id', flat=True)
        # try:
        #     payment = Payment.objects.get(pk=pk, order_id__in=order_ids)
        # except Payment.DoesNotExist:
        #     return Response({'error': 'Không tìm thấy.'}, status=404)
        # return Response(PaymentSerializer(payment).data)
        return Response({'message': 'Cần liên kết với Order model.'})
