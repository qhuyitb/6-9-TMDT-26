from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, AllowAny
from django.db.models import Q
from .models import Category, Product, ProductImage
from .serializers import CategorySerializer, ProductSerializer, ProductImageSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet quản lý danh mục sản phẩm.
    
    - Ai cũng có thể xem danh sách và chi tiết danh mục.
    - Chỉ admin mới có thể thêm, sửa, xóa danh mục.
    - Không cho phép xóa danh mục đang chứa sản phẩm.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        """Phân quyền: xem tự do, thêm/sửa/xóa chỉ dành cho admin."""
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]

    def destroy(self, request, *args, **kwargs):
        """
        Xóa danh mục.
        Từ chối xóa nếu danh mục đang chứa ít nhất một sản phẩm.
        """
        category = self.get_object()
        if category.products.exists():
            return Response(
                {'error': 'Không thể xóa danh mục đang chứa sản phẩm.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet quản lý sản phẩm điện tử.
    
    - Ai cũng có thể xem danh sách và chi tiết sản phẩm.
    - Chỉ admin mới có thể thêm, sửa, xóa sản phẩm.
    - Hỗ trợ lọc theo danh mục, trạng thái và tìm kiếm theo tên/brand.
    - Không xóa cứng sản phẩm đang trong đơn hàng xử lý, chuyển sang inactive.
    """
    serializer_class = ProductSerializer

    def get_permissions(self):
        """Phân quyền: xem tự do, thêm/sửa/xóa chỉ dành cho admin."""
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]

    def get_queryset(self):
        """
        Trả về danh sách sản phẩm với các bộ lọc tùy chọn:
        - category: lọc theo ID danh mục.
        - status: lọc theo trạng thái kinh doanh (active/inactive/discontinued).
        - search: tìm kiếm theo tên hoặc thương hiệu.
        """
        queryset = Product.objects.select_related('category').prefetch_related('images')

        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        business_status = self.request.query_params.get('status')
        if business_status:
            queryset = queryset.filter(business_status=business_status)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(brand__icontains=search)
            )

        return queryset

    def destroy(self, request, *args, **kwargs):
        """
        Xóa sản phẩm.
        Nếu sản phẩm đang nằm trong đơn hàng chưa hoàn thành thì không xóa cứng,
        thay vào đó chuyển trạng thái sang inactive.
        """
        product = self.get_object()

        active_order_statuses = ['pending', 'confirmed', 'preparing', 'shipping']
        in_active_order = product.order_items.filter(
            order__status__in=active_order_statuses
        ).exists()

        if in_active_order:
            product.business_status = 'inactive'
            product.save()
            return Response(
                {'message': 'Sản phẩm đang trong đơn hàng xử lý, đã chuyển sang inactive.'},
                status=status.HTTP_200_OK
            )

        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['delete'], url_path='images/(?P<image_id>[^/.]+)')
    def delete_image(self, request, pk=None, image_id=None):
        """
        Xóa một ảnh cụ thể của sản phẩm.
        URL: DELETE /api/products/{id}/images/{image_id}/
        """
        product = self.get_object()
        try:
            image = product.images.get(id=image_id)
            image.delete()
            return Response({'message': 'Xóa ảnh thành công.'}, status=status.HTTP_200_OK)
        except ProductImage.DoesNotExist:
            return Response({'error': 'Ảnh không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)