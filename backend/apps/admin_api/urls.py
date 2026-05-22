from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomersViewSet, OrdersViewSet, ReviewsViewSet, SummaryView, TopProductsView, TopCategoriesView, InventoryView

router = DefaultRouter()
router.register(r'customers', CustomersViewSet, basename='admin-customers')
router.register(r'orders', OrdersViewSet, basename='admin-orders')
router.register(r'reviews', ReviewsViewSet, basename='admin-reviews')

urlpatterns = [
    path('', include(router.urls)),
    path('summary/', SummaryView.as_view(), name='admin-summary'),
    path('top-products/', TopProductsView.as_view(), name='admin-top-products'),
    path('top-categories/', TopCategoriesView.as_view(), name='admin-top-categories'),
    path('inventory/', InventoryView.as_view(), name='admin-inventory'),
]
