from django.urls import path
from .views import (
    OrderListCreateView,
    OrderDetailView,
    OrderCancelView,
    PaymentListView,
    PaymentDetailView,
)

urlpatterns = [
    path('orders/',                   OrderListCreateView.as_view(), name='api_order_list'),
    path('orders/<int:pk>/',          OrderDetailView.as_view(),     name='api_order_detail'),
    path('orders/<int:pk>/cancel/',   OrderCancelView.as_view(),     name='api_order_cancel'),
    path('orders/payments/',          PaymentListView.as_view(),     name='api_payment_list'),
    path('orders/payments/<int:pk>/', PaymentDetailView.as_view(),   name='api_payment_detail'),
]