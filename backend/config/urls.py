"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', TemplateView.as_view(template_name='pages/login/login.html'), name='login_page'),
    path('admin-login/', TemplateView.as_view(template_name='pages/admin-login/admin-login.html'), name='admin_login_page'),
    path('admin-home/', TemplateView.as_view(template_name='pages/admin-home/admin-home.html'), name='admin_home_page'),
    path('admin-customers/', TemplateView.as_view(template_name='pages/admin-customers/admin-customers.html'), name='admin_customers_page'),
    path('admin-orders/', TemplateView.as_view(template_name='pages/admin-orders/admin-orders.html'), name='admin_orders_page'),
    path('admin-products/', TemplateView.as_view(template_name='pages/admin-products/admin-products.html'), name='admin_dashboard_page'),
    path('admin-categories/', TemplateView.as_view(template_name='pages/admin-categories/admin-categories.html'), name='admin_categories_page'),
    path('admin-reviews/', TemplateView.as_view(template_name='pages/admin-reviews/admin-reviews.html'), name='admin_reviews_page'),
    path('admin-top-categories/', TemplateView.as_view(template_name='pages/admin-top-categories/admin-top-categories.html'), name='admin_top_categories_page'),
    path('admin-top-products/', TemplateView.as_view(template_name='pages/admin-top-products/admin-top-products.html'), name='admin_top_products_page'),
    path('admin-inventory/', TemplateView.as_view(template_name='pages/admin-inventory/admin-inventory.html'), name='admin_inventory_page'),
    path('shop/', TemplateView.as_view(template_name='pages/shop/shop.html'), name='shop_page'),
    path('cart/', TemplateView.as_view(template_name='pages/cart/cart.html'), name='cart_page'),
    path('orders/', TemplateView.as_view(template_name='pages/orders/orders.html'), name='orders_page'),
    path('api/auth/', include('apps.users.urls')),
    path('api/', include('apps.products.urls')),
    path('api/admin/', include('apps.admin_api.urls')),
    path('api/', include('apps.orders.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

