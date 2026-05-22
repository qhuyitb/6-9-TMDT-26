from django.urls import path
from .views import (
    PaymentDetailView,
    PaymentListView,
    RegisterView,
    LoginView,
    CartView,
    CartItemAddView,
    CartItemUpdateView,
    CartItemDeleteView,
    UserAddressDetailView,
    UserAddressListCreateView,
    UserAddressSetDefaultView,
    WishlistItemAddView,
    WishlistItemDeleteView,
    WishlistView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='api_register'),
    path('login/', LoginView.as_view(), name='api_login'),
    path('cart/', CartView.as_view(), name='api_cart'),
    path('cart/items/', CartItemAddView.as_view(), name='api_cart_item_add'),
    path('cart/items/<int:item_id>/', CartItemUpdateView.as_view(), name='api_cart_item_update'),
    path('cart/items/<int:item_id>/delete/', CartItemDeleteView.as_view(), name='api_cart_item_delete'),
    # Addresses
    path('addresses/',                          UserAddressListCreateView.as_view(), name='api_address_list'),
    path('addresses/<int:pk>/',                 UserAddressDetailView.as_view(),     name='api_address_detail'),
    path('addresses/<int:pk>/set-default/',     UserAddressSetDefaultView.as_view(), name='api_address_set_default'),

    # Wishlist
    path('wishlist/',                              WishlistView.as_view(),              name='api_wishlist'),
    path('wishlist/items/',                     WishlistItemAddView.as_view(),       name='api_wishlist_add'),
    path('wishlist/items/<int:product_id>/',    WishlistItemDeleteView.as_view(),    name='api_wishlist_delete'),

    # Payments
    path('payments/',                           PaymentListView.as_view(),           name='api_payment_list'),
    path('payments/<int:pk>/',                  PaymentDetailView.as_view(),        name='api_payment_detail'),     
]
