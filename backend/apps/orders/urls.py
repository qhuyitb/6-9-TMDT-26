from django.urls import path
from .views import (
    OrderListCreateView,
    OrderDetailView,
    OrderCancelView,
    PaymentListView,
    PaymentDetailView,
    VNPayReturnView,
    VNPayIPNView,
)

urlpatterns = [
    path('orders/',                   OrderListCreateView.as_view(), name='api_order_list'),
    path('orders/vnpay/return/',      VNPayReturnView.as_view(),     name='api_vnpay_return'),
    path('orders/vnpay/ipn/',         VNPayIPNView.as_view(),        name='api_vnpay_ipn'),
    path('orders/<int:pk>/',          OrderDetailView.as_view(),     name='api_order_detail'),
    path('orders/<int:pk>/cancel/',   OrderCancelView.as_view(),     name='api_order_cancel'),
    path('orders/payments/',          PaymentListView.as_view(),     name='api_payment_list'),
    path('orders/payments/<int:pk>/', PaymentDetailView.as_view(),   name='api_payment_detail'),
]
