from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from apps.products.models import Product
from .models import Cart, CartItem
from .serializers import RegisterSerializer, LoginSerializer, CartSerializer


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


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get_cart(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart

    def get(self, request):
        cart = self.get_cart(request)
        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class CartItemAddView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('product_id')
        try:
            quantity = int(request.data.get('quantity', 1))
        except (TypeError, ValueError):
            return Response({'error': 'So luong khong hop le.'}, status=status.HTTP_400_BAD_REQUEST)

        if quantity < 1:
            return Response({'error': 'So luong phai lon hon 0.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id, business_status='active')
        except Product.DoesNotExist:
            return Response({'error': 'San pham khong ton tai hoac khong dang ban.'}, status=status.HTTP_404_NOT_FOUND)

        if product.stock_quantity < quantity:
            return Response({'error': 'So luong ton kho khong du.'}, status=status.HTTP_400_BAD_REQUEST)

        cart, _ = Cart.objects.get_or_create(user=request.user)
        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity, 'unit_price': product.price}
        )

        if not created:
            next_quantity = item.quantity + quantity
            if product.stock_quantity < next_quantity:
                return Response({'error': 'So luong ton kho khong du.'}, status=status.HTTP_400_BAD_REQUEST)
            item.quantity = next_quantity
            item.save()

        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class CartItemUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, item_id):
        try:
            quantity = int(request.data.get('quantity', 1))
        except (TypeError, ValueError):
            return Response({'error': 'So luong khong hop le.'}, status=status.HTTP_400_BAD_REQUEST)
        cart, _ = Cart.objects.get_or_create(user=request.user)

        try:
            item = cart.items.select_related('product').get(id=item_id)
        except CartItem.DoesNotExist:
            return Response({'error': 'San pham khong co trong gio hang.'}, status=status.HTTP_404_NOT_FOUND)

        if quantity <= 0:
            item.delete()
        else:
            if item.product.stock_quantity < quantity:
                return Response({'error': 'So luong ton kho khong du.'}, status=status.HTTP_400_BAD_REQUEST)
            item.quantity = quantity
            item.save()

        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class CartItemDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        cart, _ = Cart.objects.get_or_create(user=request.user)
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
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        serializer = WishlistSerializer(wishlist, context={'request': request})
        return Response(serializer.data)


class WishlistItemAddView(APIView):
    """
    POST /api/auth/wishlist/items/  — Thêm sản phẩm vào wishlist
    Body: { "product_id": 1 }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({'error': 'Thiếu product_id.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id, business_status='active')
        except Product.DoesNotExist:
            return Response({'error': 'Sản phẩm không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)

        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        _, created = WishlistItem.objects.get_or_create(wishlist=wishlist, product=product)

        if not created:
            return Response({'message': 'Sản phẩm đã có trong wishlist.'}, status=status.HTTP_200_OK)

        serializer = WishlistSerializer(wishlist, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class WishlistItemDeleteView(APIView):
    """
    DELETE /api/auth/wishlist/items/<product_id>/  — Xóa sản phẩm khỏi wishlist
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, product_id):
        try:
            wishlist = Wishlist.objects.get(user=request.user)
        except Wishlist.DoesNotExist:
            return Response({'error': 'Wishlist không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)

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