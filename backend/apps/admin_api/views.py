from datetime import datetime
from django.db.models import Count, Sum, F, Q
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.products.models import Product, Category
from apps.users.models import User
from .models import Order, OrderItem, Review
from .serializers import CustomerSerializer, OrderSerializer, ReviewSerializer
from .permissions import IsAdminRole


class CustomersViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    permission_classes = [IsAdminRole]

    def get_queryset(self):
        queryset = User.objects.filter(role='customer')
        search = self.request.query_params.get('search')
        status_filter = self.request.query_params.get('status')
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search)
            )
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset.order_by('-created_at')

    def destroy(self, request, *args, **kwargs):
        return Response({'detail': 'Delete is disabled.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


class OrdersViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAdminRole]

    def get_queryset(self):
        queryset = Order.objects.select_related('user').prefetch_related('items__product')
        status_filter = self.request.query_params.get('status')
        search = self.request.query_params.get('search')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if search:
            queryset = queryset.filter(
                Q(user__full_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(shipping_phone__icontains=search)
            )
        return queryset.order_by('-created_at')


class ReviewsViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsAdminRole]

    def get_queryset(self):
        queryset = Review.objects.select_related('product', 'user', 'order')
        is_visible = self.request.query_params.get('is_visible')
        rating = self.request.query_params.get('rating')
        product_id = self.request.query_params.get('product_id')
        if is_visible in ['true', 'false']:
            queryset = queryset.filter(is_visible=(is_visible == 'true'))
        if rating:
            queryset = queryset.filter(rating=rating)
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        return queryset.order_by('-review_date')


class SummaryView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        start, end = _get_date_range(request)
        orders = Order.objects.all()
        if start and end:
            orders = orders.filter(created_at__range=(start, end))

        completed_orders = orders.filter(status=Order.STATUS_COMPLETED)

        data = {
            'total_customers': User.objects.filter(role='customer').count(),
            'total_orders': orders.count(),
            'total_products': Product.objects.count(),
            'total_categories': Category.objects.count(),
            'total_reviews': Review.objects.count(),
            'revenue': completed_orders.aggregate(total=Sum('total_amount'))['total'] or 0,
            'low_stock_count': Product.objects.filter(stock_quantity__lte=5).count(),
        }
        return Response(data)


class TopProductsView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        start, end = _get_date_range(request)
        limit = _get_limit(request)

        items = OrderItem.objects.select_related('order', 'product').filter(order__status=Order.STATUS_COMPLETED)
        if start and end:
            items = items.filter(order__created_at__range=(start, end))

        stats = items.values('product_id', 'product__name').annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum('line_total')
        ).order_by('-total_quantity')[:limit]

        return Response(list(stats))


class TopCategoriesView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        start, end = _get_date_range(request)
        limit = _get_limit(request)

        items = OrderItem.objects.select_related('order', 'product', 'product__category').filter(order__status=Order.STATUS_COMPLETED)
        if start and end:
            items = items.filter(order__created_at__range=(start, end))

        stats = items.values('product__category_id', 'product__category__name').annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum('line_total')
        ).order_by('-total_quantity')[:limit]

        return Response(list(stats))


class InventoryView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        threshold = request.query_params.get('threshold')
        try:
            threshold_value = int(threshold) if threshold is not None else 5
        except ValueError:
            return Response({'detail': 'Invalid threshold.'}, status=status.HTTP_400_BAD_REQUEST)

        products = Product.objects.select_related('category').order_by('stock_quantity')
        if threshold_value >= 0:
            products = products.filter(stock_quantity__lte=threshold_value)

        data = {
            'threshold': threshold_value,
            'total_low_stock': products.count(),
            'items': [
                {
                    'id': product.id,
                    'name': product.name,
                    'sku': product.sku,
                    'category_id': product.category_id,
                    'category_name': product.category.name,
                    'stock_quantity': product.stock_quantity,
                    'business_status': product.business_status,
                    'price': product.price,
                }
                for product in products
            ]
        }
        return Response(data)


def _get_limit(request):
    limit = request.query_params.get('limit')
    try:
        return int(limit) if limit is not None else 10
    except ValueError:
        return 10


def _get_date_range(request):
    start_raw = request.query_params.get('start')
    end_raw = request.query_params.get('end')
    if not start_raw or not end_raw:
        return None, None

    try:
        start = datetime.fromisoformat(start_raw)
        end = datetime.fromisoformat(end_raw)
    except ValueError:
        return None, None

    if timezone.is_naive(start):
        start = timezone.make_aware(start)
    if timezone.is_naive(end):
        end = timezone.make_aware(end)

    return start, end
